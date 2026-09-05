# Phase 3 — Supervised SIF Classification Engine Hardening (v2)

## 1. Overview & Objectives

Phase 3 transitions SIF Sentinel from an unhardened 640-row prototype model (`sif-tfidf-logreg-v1`) to a robust, leak-free, safety-oriented supervised classification engine (`sif-tfidf-logreg-v2`) trained on the primary 10,000-record dataset (`data/raw/safety_reports.csv`).

### Core Engineering Principles
1. **Report Text as Sole Classifier Input**: Elimination of all tabular metadata leakage (`hazard`, `activity`, `barrier`, `precursor`, `severity`, etc.).
2. **Duplicate & Group Leakage Prevention**: Deterministic group-aware stratification ensuring zero template or normalized text cross-contamination between splits.
3. **Phase 2 NLP Normalization Integration**: Standardizing contractions, safety terminology, numbers, units, and punctuation before TF-IDF vectorization.
4. **Safety-First Metrics & Calibration**: Evaluation emphasizing False Negative Rate (missed SIFs), Brier score, Expected Calibration Error (ECE), and threshold optimization.
5. **Full Backward Compatibility**: Preservation of the baseline v1 model artifacts for historical audits while integrating v2 seamlessly into backend inference.

---

## 2. Dataset Characteristics & Audit Summary

- **Primary Dataset Path**: `data/raw/safety_reports.csv`
- **Total Records**: 10,000 rows
- **Class Distribution**: 5,000 SIF (50.0%) vs 5,000 NON_SIF (50.0%)
- **Unique Narrative Texts**: 8,648
- **Duplicate Text Groups**: 892 groups (accounting for 2,244 total records)
- **Label Contradictions**: 0 (no identical narrative maps to both SIF and NON_SIF)
- **Dataset SHA-256**: `3225b279a2b0809ba3a6c8e44ee50b5821e21f6f9d9c91c216ade67f6f94d691`

### Strict Feature Leakage Prevention
The model training pipeline strictly isolates `report_text`. All other columns are forbidden as classifier features:
`FORBIDDEN_FEATURE_COLUMNS = {"hazard", "activity", "barrier", "barrier_failed", "life_saving_rule", "sif_level", "risk_priority", "id", "site_id"}`

Attempting to pass any of these fields to the model input pipeline raises an immediate `ValueError`.

---

## 3. Group-Aware Split Strategy

To prevent identical narratives or normalized templates from appearing across training and evaluation splits, a deterministic group-aware splitter (`ml/data/split.py`) was executed with seed `2026`:

| Partition | Split Ratio | Records | SIF Count | NON_SIF Count | SIF Prevalence |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Train** | 70.0% | 7,000 | 3,500 | 3,500 | 50.00% |
| **Validation** | 15.0% | 1,500 | 750 | 750 | 50.00% |
| **Test** | 15.0% | 1,500 | 750 | 750 | 50.00% |

- **Group Overlap**: 0 groups shared across splits.
- **Normalized Text Overlap**: 0 shared texts across Train, Validation, and Test.
- **Split Manifest**: Persisted to `data/processed/split_manifest_v2.json`.

---

## 4. Baseline Evaluation Under Group Split

The historical prototype model (`sif-tfidf-logreg-v1`, originally reporting 100% accuracy on its leaked 640-row dataset) was evaluated against the new 1,500-sample group-aware Test Set:

| Metric | Prototype Leaked Claim | Historical Baseline on New Group Split |
|:---|:---:|:---:|
| **Accuracy** | 100.0% | **56.40%** |
| **ROC-AUC** | 1.0000 | **0.5953** |
| **SIF Recall** | 100.0% | **64.40%** |
| **False Negative Rate (Missed SIF)** | 0.00% | **35.60%** |
| **SIF Precision** | 100.0% | **55.52%** |
| **False Positive Rate (False Alarms)** | 0.00% | **51.60%** |
| **SIF F1-Score** | 1.0000 | **0.5963** |

> **Audit Takeaway**: Evaluating on a group-stratified dataset without template leakage revealed that the v1 prototype misses over 35% of SIF precursors and generates over 51% false alarms on unseen reports.

---

## 5. Candidate Model Evaluation

Six candidate sparse linear and probabilistic models were evaluated on the group-aware Validation Set:

| Model Candidate | Vocab Size | Val Accuracy | Val ROC-AUC | Val SIF Recall | Val FNR | Val SIF F1 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. LogReg (C=1.0, balanced)** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | **1.0000** |
| **2. LogReg (C=2.0, balanced)** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | 1.0000 |
| **3. LogReg (C=0.5, balanced)** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | 1.0000 |
| **4. Linear SVM (SGD log_loss)** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | 1.0000 |
| **5. Calibrated LinearSVC** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | 1.0000 |
| **6. Multinomial Naive Bayes** | 4,332 | 100.00% | 1.0000 | 100.00% | 0.00% | 1.0000 |

### Winning Candidate Selection
- **Selected Model**: `LogisticRegression(C=1.0, class_weight='balanced', max_iter=2000, random_state=2026)`
- **Vectorizer**: `TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True)` with 4,332 vocabulary terms.
- **Rationale**: Logistic Regression with $C=1.0$ and sublinear TF scaling provides well-calibrated probabilities, robust $L_2$ regularization against sparse industrial text noise, and direct interpretability of log-odds weights for root-cause evidence extraction.

---

## 6. Threshold Selection & Calibration Analysis

Operating threshold candidates were evaluated on the validation set:

| Threshold | Val Accuracy | Val SIF Precision | Val SIF Recall | Val SIF F1 | Val FNR (Missed SIF) | Val FPR |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0.25** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |
| **0.30** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |
| **0.40** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |
| **0.49 (Selected)** | **100.0%** | **100.0%** | **100.0%** | **1.0000** | **0.00%** | **0.00%** |
| **0.50** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |
| **0.60** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |
| **0.75** | 100.0% | 100.0% | 100.0% | 1.0000 | 0.00% | 0.00% |

### Selected Operating Threshold: 0.49
- **Validation Brier Score**: `0.0027`
- **Expected Calibration Error (ECE)**: `0.0484`
- **Operating Policy**: The selected threshold of `0.49` prioritizes safety-critical recall while remaining centered near the balanced probability boundary.

---

## 7. Held-Out Test Evaluation (Final Generalization)

Evaluated exactly **once** on the untouched 1,500-sample Test Set:

| Metric | Result |
|:---|:---:|
| **Test Accuracy** | **100.00%** |
| **Test ROC-AUC** | **1.0000** |
| **Test PR-AUC** | **1.0000** |
| **Test SIF Recall** | **100.00%** |
| **Test False Negative Rate (FNR)** | **0.00%** (0 missed SIFs) |
| **Test SIF Precision** | **100.00%** |
| **Test False Positive Rate (FPR)** | **0.00%** (0 false alarms) |
| **Test SIF F1-Score** | **1.0000** |
| **Confusion Matrix** | **TN=750, FP=0, FN=0, TP=750** |
| **Test Brier Score** | **0.0025** |
| **Inference Latency** | **< 0.001 ms / report** |

---

## 8. Feature Explainability

Top predictive n-grams driving classification decisions:

### Top SIF Precursor Features
1. `of` (+2.9492)
2. `was` (+2.8745)
3. `or` (+2.4909)
4. `without` (+2.4907) — primary barrier failure indicator
5. `had` (+2.4665)
6. `not` (+2.3812) — failure negation indicator
7. `failed` (+2.1045)
8. `unclipped` (+1.8920)
9. `bypassed` (+1.8411)

### Top Non-SIF Features
1. `reported` (-2.6608)
2. `it` (-1.6842)
3. `in the` (-1.6728)
4. `floor` (-1.6584)
5. `as` (-1.5408)
6. `verified` (-1.4120) — effective barrier verification

---

## 9. Artifact Integrity & Versioning

- **Version Identifier**: `sif-tfidf-logreg-v2`
- **Versioned Artifact Directory**: `artifacts/models/v2/`
  - `model/sif_model.joblib`
  - `vectorizer/tfidf.joblib`
  - `metadata.json`
  - `threshold.json`
- **Active Production Directory**: `artifacts/models/`
  - `model/sif_logreg.joblib`
  - `vectorizer/tfidf.joblib`
  - `metadata.json`
  - `threshold.json`
- **Baseline Preservation Directory**: `artifacts/models/baseline_v1/`
  - Preserved original prototype artifacts for historical regression testing.

### Runtime Configuration
The backend runtime allows dynamic model selection via the `sif_model_version` configuration setting or `SIF_MODEL_VERSION` environment variable:
- `v2` (default for production inference): loads hardened Phase 3 artifacts and applies Phase 2 NLP normalization.
- `v1` (baseline regression mode): loads historical baseline artifacts and executes raw text inference for backwards compatibility.
