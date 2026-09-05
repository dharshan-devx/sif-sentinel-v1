# Phase 4B — Genuine Transformer Semantic Benchmark

## Executive Overview
Phase 4B implements, fine-tunes, and evaluates a **genuine pretrained Transformer-based semantic classifier** (`distilbert-base-uncased`, 66.95M parameters) alongside a **Calibrated Transformer-Hybrid** architecture for Serious Injury and Fatality (SIF) precursor detection in Oil & Gas safety narratives.

### Core Research Question
Does a genuine pretrained Transformer architecture improve semantic generalization across unseen syntactic structures and domain-specific edge cases, while maintaining low false-negative rates, high calibration, and acceptable inference latency?

---

## Model Architectures Compared
1. **Model A (Phase 3 Baseline)**: Classical Word N-Gram TF-IDF (1-3 ngrams, 4,332 features) + Logistic Regression ($C=1.0$, L2 penalty).
2. **Model B (Phase 4A Neural)**: Subword Character N-Gram TF-IDF (3-5 char ngrams, 10,000 features) + MLPClassifier (2 hidden layers: 128, 64).
3. **Model C (Phase 4B Transformer)**: Pretrained `distilbert-base-uncased` (6 transformer layers, 12 attention heads, 768 hidden dimension, 66.95M parameters) fine-tuned on safety narratives.
4. **Model D (Phase 4B Hybrid)**: Calibrated Logistic Meta-Classifier fusing Phase 3 Baseline probability, Phase 4B Transformer contextual probability, and Phase 2 structured safety evidence counts.

---

## Empirical Benchmark Summary

### 1. Locked Test Set (1,500 reports, Group-Aware Split)
All models achieve 100.00% separation on the frozen group-aware test split due to underlying dataset consistency.

| Metric | Model A (TF-IDF) | Model B (Subword MLP) | Model C (DistilBERT) | Model D (Hybrid) |
|---|---|---|---|---|
| **Accuracy** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Precision** | 100.00% | 100.00% | 100.00% | 100.00% |
| **Recall** | 100.00% | 100.00% | 100.00% | 100.00% |
| **F1 Score** | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **ROC-AUC** | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Brier Score** | 0.0027 | 0.0021 | 0.0000 | 0.0000 |
| **Expected Calibration Error (ECE)** | 0.0483 | 0.0314 | 0.0002 | 0.0019 |
| **Mean Latency (CPU)** | 1.36 ms | 1.24 ms | 41.92 ms | 41.84 ms |
| **Model Size** | 34.7 KB | 7.4 MB | 256.1 MB | 256.1 MB |

---

### 2. Diagnostic Template-Held-Out Evaluation (101 Unseen Template Families, 2,000 reports)
This diagnostic isolates semantic generalization by completely holding out 101 template families during training.

| Metric | Model A (TF-IDF) | Model B (Subword MLP) | Model C (DistilBERT) |
|---|---|---|---|
| **Accuracy** | 81.50% | 77.30% | **98.95%** |
| **SIF Precision** | 99.86% | 98.37% | **100.00%** |
| **SIF Recall** | 66.67% | 59.98% | **98.10%** |
| **SIF F1** | 0.7996 | 0.7452 | **0.9904** |
| **False Negative Rate (FNR)** | 33.33% | 40.02% | **1.90%** |
| **ROC-AUC** | 0.9899 | 0.9670 | **1.0000** |

**Key Takeaway**: Classical TF-IDF and Subword MLPs suffer a 33%–40% false negative rate when encountering unseen sentence templates due to surface lexical overfitting. The genuine Transformer reduces FNR to 1.90%, proving genuine contextual generalization across varied syntax.

---

### 3. External OSHA Domain Robustness Analysis
- **Sample Evaluated**: 500 real-world incident narratives from `January2015toNovember2025.csv` (15,774 words).
- **TF-IDF OOV Rate**: **43.39%** (6,845 words dropped due to vocabulary limits).
- **Transformer Subword Tokenizer**: Tokenized 15,774 words into 20,411 subword tokens (1.294 tokens/word) with **0.0% dropped words**.
- **Conclusion**: Transformer WordPiece tokenization provides robust representation for unseen field terminology without catastrophic OOV failure.

---

## Production Recommendation
- **Production Primary**: Phase 3 Baseline (`v2`) remains the locked, low-latency, deterministic production default.
- **Semantic & High-Risk Engine**: Phase 4B Genuine Transformer (`v4b_transformer`) and Hybrid (`v4b_hybrid`) are integrated as selectable inference backends (`SIF_MODEL_BACKEND=transformer` or `v4b_hybrid`) for high-consequence auditing and complex narrative disambiguation.
