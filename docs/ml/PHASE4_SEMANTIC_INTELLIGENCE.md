# Phase 4 — Semantic SIF Intelligence Documentation

## 1. Executive Summary
Phase 4 advances the SIF Sentinel classification engine from classical keyword pattern matching to **Semantic SIF Intelligence**. While Phase 3 established a TF-IDF baseline that achieved 100% on synthetic splits, the Phase 3.5 audit revealed template memorization (99.69% of records belonging to template families) and performance degradation (79.17% accuracy / 63.61% recall) on held-out template structures.

Phase 4 developed, evaluated, and compared three distinct architectures:
- **Model A**: Preserved Phase 3 Classical TF-IDF + Logistic Regression Baseline (`sif-tfidf-logreg-v2`).
- **Model B**: Semantic Subword Neural Classifier (`sif-semantic-v1`) trained with controlled semantic data augmentation.
- **Model C**: Calibrated Hybrid Classifier (`sif-hybrid-v1`) fusing classical TF-IDF evidence, semantic neural encodings, and Phase 2 NLP safety signals.

## 2. Model Architectures
```
                  ┌────────────────────────────────────────┐
                  │          Report Text Narrative         │
                  └───────────────────┬────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 │    Phase 2 Canonical Text Normalizer    │
                 └─────────┬───────────────────┬───────────┘
                           │                   │
         ┌─────────────────┴────────┐ ┌────────┴────────────────┐
         │ Classical TF-IDF Feature │ │ Subword Neural Semantic │
         │      Representation      │ │      Representation     │
         └─────────────────┬────────┘ └────────┬────────────────┘
                           │                   │
                           ▼                   ▼
                     [Model A Prob]      [Model B Prob]
                           │                   │
                           └─────────┬─────────┘
                                     │   + Phase 2 NLP Domain Signals
                                     ▼
                   ┌───────────────────────────────────┐
                   │    Calibrated Hybrid Ensemble     │
                   │        (sif-hybrid-v1)            │
                   └─────────────────┬─────────────────┘
                                     ▼
                        Calibrated SIF Probability
```

### Model Summary
1. **Model A (Baseline)**: TF-IDF unigram+bigram vectorizer (4,332 vocab) with balanced Logistic Regression.
2. **Model B (Semantic)**: Character-subword n-gram vectorizer (1-3 chars) + multi-layer neural network (MLP 128x64) with early stopping.
3. **Model C (Hybrid - Winning Model)**: Logistic meta-fusion combining Model A probability, Model B probability, and pre-extracted NLP domain signals (hazard presence, barrier failure, LOTO/height/vessel indicators).

## 3. Controlled Semantic Augmentation (Train Set Only)
- **Rule**: Augmentation was applied **STRICTLY to the Train set** (7,000 records) and never contaminated Validation or Test splits.
- **Method**: Generated 2,523 domain-aware semantic variants (synonym substitution, barrier syntax alterations) expanding the training pool from 7,000 to 9,523 records with full parent-ID traceability.

## 4. Locked Test Set Performance Comparison
All models evaluated once on the locked 1,500-sample test set:

| Model | Accuracy | SIF Prec | SIF Recall | SIF F1 | ROC-AUC | FNR | FPR | Brier | Latency | Size |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A (Baseline TF-IDF)** | 100.0% | 100.0% | 100.0% | 1.0000 | 1.0000 | 0.0% | 0.0% | 0.0027 | 0.41 ms | 34.7 KB |
| **Model B (Semantic Subword)** | 100.0% | 100.0% | 100.0% | 1.0000 | 1.0000 | 0.0% | 0.0% | 0.0021 | 0.49 ms | 7.4 MB |
| **Model C (Calibrated Hybrid)** | **100.0%** | **100.0%** | **100.0%** | **1.0000** | **1.0000** | **0.0%** | **0.0%** | **0.0000** | **1.01 ms** | **7.6 MB** |

## 5. Diagnostic Template-Held-Out Evaluation
Retrained strictly on 70% of template families and tested on 30% held-out families (3,029 records):

| Model | Accuracy | SIF Prec | SIF Recall | SIF F1 | ROC-AUC | FNR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A (Baseline TF-IDF)** | 79.17% | 94.43% | 63.61% | 0.7602 | 0.9698 | 36.39% |
| **Model B (Semantic Subword)** | 72.10% | 94.71% | 48.98% | 0.6457 | 0.9568 | 51.02% |
| **Model C (Calibrated Hybrid)** | **75.04%** | **94.25%** | **55.28%** | **0.6969** | **0.9596** | **44.72%** |

## 6. Stress-Testing Benchmarks
1. **Semantic Challenge Set (17 Cases)**:
   - Model A: 10/17 (58.8%)
   - Model B: 9/17 (52.9%)
   - **Model C (Hybrid)**: **11/17 (64.7%)**
2. **Counterfactual Probability Shifts**:
   - Fall Protection (PAIR A): Model C shifted from 0.6210 (Unsafe) to 0.2188 (Safe) — **$\Delta = +0.4022$** (vs +0.1030 for baseline).
   - Safety Interlock (PAIR E): Model C shifted from 0.9534 (Unsafe) to 0.0224 (Safe) — **$\Delta = +0.9310$** (vs +0.3329 for baseline).
3. **Out-of-Distribution (OOD)**:
   - Model C assigns minimal false positive probability to non-safety domains: Weather ($p=0.0018$), Office ($p=0.0103$), Cooking ($p=0.0142$), Software ($p=0.0200$), Logistics ($p=0.0254$).

## 7. Configuration & Backend Switching
Configured via `SIF_MODEL_BACKEND` in `.env` or `Settings.sif_model_backend`:
- `v2` (or `baseline`): Phase 3 classical TF-IDF model.
- `semantic`: Phase 4 subword neural model.
- `hybrid`: Phase 4 calibrated hybrid model (Production default).
