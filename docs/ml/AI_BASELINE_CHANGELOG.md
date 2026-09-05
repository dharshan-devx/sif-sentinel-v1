# AI/NLP Baseline Changelog

## Phase 1 — Baseline Established

**Date:** September 3, 2026  
**Model Version:** `sif-tfidf-logreg-v1`  
**Dataset Version:** `synthetic-safety-reports-v1` (hash: `4512698c...`)

### Actual Metrics (Synthetic Evaluation Split)

| Metric | Value |
|---|---|
| Accuracy | 1.0 |
| Precision (SIF) | 1.0 |
| Recall (SIF) | 1.0 |
| F1-Score (SIF) | 1.0 |
| ROC-AUC | 1.0 |

> **Note:** These metrics are artificially inflated due to template-level data leakage in the synthetic dataset.

### Tests Executed

| Suite | Total | Passed | Failed |
|---|---|---|---|
| Existing Backend Tests | 158 | 158 | 0 |
| AI Baseline Regression | 38 | 38 | 0 |
| **Combined** | **196** | **196** | **0** |

### Known Limitations

1. Training data is synthetic (16 unique templates × 40 repetitions).
2. Template-level data leakage inflates evaluation metrics.
3. Dictionary-based entity extraction with hardcoded keyword lists.
4. TF-IDF bag-of-words classifier — no contextual understanding.
5. No lemmatization or advanced NLP preprocessing.
6. Heuristic confidence scoring — not statistically calibrated.

### Files Changed

| File | Action | Reason |
|---|---|---|
| `backend/tests/test_ai_baseline.py` | **CREATED** | 38 AI/NLP regression tests covering model loading, classification, preprocessing, entity extraction, LSR mapping, evidence, confidence, and edge cases. |
| `docs/ml/BASELINE_EVALUATION.md` | **CREATED** | Comprehensive baseline evaluation documentation with environment, dataset, model, pipeline, metrics, and limitation details. |
| `docs/ml/AI_BASELINE_CHANGELOG.md` | **CREATED** | This file. Phase 1 baseline changelog. |
| `backend/.venv/` | **CREATED** | Python 3.13.5 virtual environment with all project dependencies. |

### Files NOT Changed

- No frontend files modified.
- No backend production source code modified.
- No database schema or migration files modified.
- No existing test files modified.
- No configuration files modified.
- No model artifacts modified (retrained identically for verification only).
- No API contracts modified.

---

## Phase 3 — Supervised SIF Classification Engine Hardening

**Date:** September 3, 2026  
**Model Version:** `sif-tfidf-logreg-v2`  
**Dataset Version:** `data/raw/safety_reports.csv` (10,000 records, hash: `3225b279...`)  
**Split Strategy:** Deterministic group-aware 70/15/15 (`split_manifest_v2.json`, seed: 2026)  
**Operating Threshold:** 0.49 (selected on validation set)  

### Key Upgrades
1. **Zero Feature Leakage**: Model inputs strictly restricted to `report_text`; forbidden metadata columns (`hazard`, `barrier`, `activity`, `sif_level`, etc.) explicitly blocked.
2. **Zero Duplicate/Template Leakage**: 892 duplicate text groups partitioned cleanly across splits with 0 shared texts.
3. **Phase 2 Normalization**: Applied canonical contraction expansion, safety unit standardization, and text cleansing before TF-IDF vectorization.
4. **Safety-Oriented Evaluation**: Assessed 6 model candidates; calibrated Logistic Regression selected with 0.00% FNR and Brier score of 0.0025.
5. **Historical Baseline Preserved**: v1 baseline archived in `artifacts/models/baseline_v1/`; measured at 56.40% accuracy and 35.60% FNR under group-aware evaluation.
6. **Predictor & Backend Integration**: Dynamic model version switching (`v1` vs `v2`), operating threshold support, and backwards compatibility preserved.

### Test Suite Execution
- **Existing Backend Suite**: 232 / 232 PASSED
- **Phase 3 Hardening Suite**: 21 / 21 PASSED
- **Total Repository Tests**: 253 / 253 PASSED (100% green)

