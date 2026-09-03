# Model Credibility & Reproducibility (Phase F)

This document outlines the architecture and controls in place to guarantee the predictability, explainability, and defensibility of the SIF (Serious Injury or Fatality) prediction models used in the SIF Sentinel platform.

## 1. What model did you use?
The backend relies on a deterministic **Logistic Regression** model paired with **TF-IDF (Term Frequency-Inverse Document Frequency)** vectorization (using bi-grams). 
- It is intentionally simple rather than using a black-box LLM because it provides *exact mathematical feature importance* (coefficients mapping directly to specific words) and is 100% reproducible. 
- The model artifacts (`sif_logreg.joblib` and `tfidf.joblib`) are generated via `app/ml/training/train_sif_model.py`.

## 2. What data was it trained/evaluated on?
The model is trained on a synthetic prototype dataset (`data/training/safety_reports.csv`) containing 640 safety reports mimicking real-world industrial HSE observations.
- **Features**: Single feature used for ML is `report_text`.
- **Target**: `sif_potential` (boolean: True for SIF, False for NON_SIF).
- **Class Distribution**: Balanced via `class_weight="balanced"` during training.
- **Dataset Hash**: To guarantee provenance, the dataset is hashed (SHA-256) at training time, and this hash is persisted into `metadata.json`. If the dataset changes but the model is not retrained, this hash will prove the model is stale.

## 3. How did you prevent target leakage?
- **Feature Selection**: The model trains *strictly* on the unstructured `report_text`. It has no access to post-investigation variables such as actual injury severity, final risk ratings, or human review decisions.
- **Data Splitting**: We use a strict 80/20 train/test split utilizing `sklearn`'s `train_test_split`. All preprocessing (TF-IDF fitting) occurs *exclusively* on the training split (`fit_transform` on train, `transform` on test) to prevent data leakage into the vectorizer's IDF weights.

## 4. How do you measure model performance?
Performance is measured on the 20% held-out test set using deterministic metrics:
- **Accuracy, Precision, Recall, F1 Score** (via `classification_report`).
- **ROC-AUC** to measure the model's ability to rank SIF vs NON-SIF probabilities.
- **Confusion Matrix** to ensure no severe imbalance in false negatives (critical for HSE tasks).

*Note: As the current data is synthetically generated via permutations of prototype phrases, the metrics on the synthetic set are artificially perfect (F1=1.0). In a real deployment, these metrics will reflect actual statistical performance.*

## 5. How do you calculate confidence?
We explicitly separate **statistical probability** from **heuristic confidence scores**:
- **`sif_probability`**: The raw calibrated probability (0.0 to 1.0) emitted by the Logistic Regression model (`predict_proba`).
- **`overall_confidence`**: A bounded heuristic score (0.0 to 1.0) used purely to trigger human review. It is an arbitrary weighted blend of the model's probability, the presence of matching entities (hazards/activities), mapped Life-Saving Rules, and concrete evidence extracted from the text. 

## 6. What happens when the model is uncertain?
The system acts as **decision support**, not an autonomous safety authority. If the system is uncertain, it forces human review. 
A report is forced into `REVIEW` state if:
- `overall_confidence` falls below the configured `analysis_review_threshold`.
- `sif_probability` is statistically ambiguous (between 0.42 and 0.58).
- The model predicts HIGH/MEDIUM SIF risk but deterministic rule logic fails to map it to a Life-Saving Rule.
- No concrete evidence spans can be extracted to support the prediction.

## 7. Can a safety officer correct the prediction?
Yes. The Review Workflow (Phase C) provides API endpoints (`POST /api/v1/reviews/{id}/decision`) allowing an authorized human reviewer to `APPROVE`, `REJECT`, or `MODIFY` the AI's analysis. 

## 8. Do you preserve the original AI decision?
Yes. When a human reviewer submits a modification, the original AI predictions (`sif_probability`, `sif_level`, etc.) in the `report_analyses` table are **never overwritten**. Instead, the human's changes are stored as a `ReviewCorrection` mapped to the `Review` object. This guarantees that the AI's raw output is auditable forever.

## 9. Can you explain why the model generated the prediction?
Yes. Because we use TF-IDF + Logistic Regression, we have direct access to feature coefficients. 
The system calculates exact feature contributions by multiplying the TF-IDF vector of the incoming report text against the SIF-class coefficients of the model. The top non-zero terms pushing the probability towards SIF are exposed as `predictive_terms` in the API output and appended to the human-readable `explanation` string.

## 10. How is the result audited?
Every `ReportAnalysis` record is persisted with:
- `model_version` (e.g., `sif-tfidf-logreg-v1`)
- The explicit explanation string (including rule maps and predictive ML terms)
- The raw `sif_probability`
This ties every prediction back to a specific model artifact and dataset hash.
