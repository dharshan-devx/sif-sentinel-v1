"""
SIF Sentinel Phase 3 — Hardened Supervised SIF Classification Pipeline.

Features:
- Validates 10,000-row primary dataset and prevents structured feature leakage.
- Enforces deterministic 70/15/15 group-aware split (no duplicate text crossing partitions).
- Integrates Phase 2 NLP text normalization consistently.
- Evaluates historical baseline vs Candidate A (Logistic Regression), Candidate B (Linear SVM), Candidate C (Naive Bayes).
- Performs hyperparameter selection and threshold tuning on TRAIN/VALIDATION only.
- Evaluates held-out TEST set exactly once.
- Evaluates probability calibration (Brier score).
- Exports versioned artifacts (sif-tfidf-logreg-v2) and comprehensive metadata.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

# Setup paths
ROOT = Path(__file__).parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.nlp.preprocessing import preprocess_text
from ml.data.dataset import (
    FORBIDDEN_FEATURE_COLUMNS,
    extract_model_inputs,
    load_and_validate_dataset,
)
from ml.data.split import group_aware_split, persist_split_manifest
from ml.evaluation.metrics import (
    calculate_safety_metrics,
    evaluate_calibration_curve,
    evaluate_threshold_candidates,
    select_operating_threshold,
)

PRIMARY_DATASET_PATH = ROOT / "data" / "raw" / "safety_reports.csv"
SPLIT_MANIFEST_PATH = ROOT / "data" / "processed" / "split_manifest_v2.json"
ARTIFACTS_DIR = ROOT / "artifacts" / "models"
V2_ARTIFACTS_DIR = ARTIFACTS_DIR / "v2"
BASELINE_DIR = ARTIFACTS_DIR / "baseline_v1"


def apply_phase2_preprocessing(texts: list[str]) -> list[str]:
    """Preprocess raw texts using Phase 2 canonical normalization."""
    return [preprocess_text(t).normalized_text for t in texts]


def evaluate_historical_baseline(
    x_test_raw: list[str], y_test: list[int]
) -> dict[str, Any] | None:
    """Evaluate the historical baseline model on the new group-aware test split."""
    model_path = BASELINE_DIR / "model" / "sif_logreg.joblib"
    vec_path = BASELINE_DIR / "vectorizer" / "tfidf.joblib"
    if not (model_path.exists() and vec_path.exists()):
        return None

    model = joblib.load(model_path)
    vectorizer = joblib.load(vec_path)

    # Historical baseline was trained on unnormalized raw text with prototype suffixes
    X_test_vec = vectorizer.transform(x_test_raw)
    classes = list(model.classes_)
    sif_idx = classes.index("SIF") if "SIF" in classes else 1
    y_prob = model.predict_proba(X_test_vec)[:, sif_idx]
    y_pred = (y_prob >= 0.50).astype(int)

    return calculate_safety_metrics(y_test, y_pred, y_prob)


def run_experiments() -> dict[str, Any]:
    print("=" * 70)
    print("SIF SENTINEL PHASE 3 — SUPERVISED SIF CLASSIFICATION PIPELINE")
    print("=" * 70)

    # 1. Dataset Loading & Validation
    print("\n[Step 1/8] Loading and validating primary dataset...")
    records, dataset_summary = load_and_validate_dataset(PRIMARY_DATASET_PATH)
    print(f"  Loaded {dataset_summary.usable_rows} usable records from {dataset_summary.file_path}")
    print(f"  Class balance: {dataset_summary.positive_count} SIF vs {dataset_summary.negative_count} NON_SIF ({dataset_summary.positive_ratio*100:.1f}% SIF)")
    print(f"  Unique text groups: {dataset_summary.unique_text_count}")
    print(f"  Duplicate text groups: {dataset_summary.duplicate_text_groups} (Contradictions: {dataset_summary.duplicate_label_contradictions})")
    print(f"  Dataset SHA-256: {dataset_summary.sha256_hash}")

    # 2. Group-Aware Split
    print("\n[Step 2/8] Creating deterministic 70/15/15 group-aware data split...")
    train_recs, val_recs, test_recs, split_manifest = group_aware_split(
        records, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=2026
    )
    persist_split_manifest(split_manifest, SPLIT_MANIFEST_PATH)
    print(f"  Train: {len(train_recs)} records ({split_manifest.train_positive_count} SIF, {split_manifest.train_positive_ratio*100:.1f}%)")
    print(f"  Val:   {len(val_recs)} records ({split_manifest.val_positive_count} SIF, {split_manifest.val_positive_ratio*100:.1f}%)")
    print(f"  Test:  {len(test_recs)} records ({split_manifest.test_positive_count} SIF, {split_manifest.test_positive_ratio*100:.1f}%)")
    print(f"  Manifest persisted to: {SPLIT_MANIFEST_PATH}")

    # 3. Input Extraction & Feature Leakage Isolation
    print("\n[Step 3/8] Extracting report_text only and enforcing zero feature leakage...")
    train_texts_raw, y_train = extract_model_inputs(train_recs)
    val_texts_raw, y_val = extract_model_inputs(val_recs)
    test_texts_raw, y_test = extract_model_inputs(test_recs)

    # 4. Phase 2 Preprocessing Integration
    print("\n[Step 4/8] Applying Phase 2 text normalization...")
    t0 = time.perf_counter()
    train_texts = apply_phase2_preprocessing(train_texts_raw)
    val_texts = apply_phase2_preprocessing(val_texts_raw)
    test_texts = apply_phase2_preprocessing(test_texts_raw)
    t_prep = time.perf_counter() - t0
    print(f"  Normalized {len(train_texts) + len(val_texts) + len(test_texts)} texts in {t_prep:.2f}s")

    # 5. Evaluate Historical Baseline on New Test Split
    print("\n[Step 5/8] Evaluating historical baseline prototype on new group-aware test split...")
    baseline_metrics = evaluate_historical_baseline(test_texts_raw, y_test)
    if baseline_metrics:
        print(f"  Historical Baseline on New Test Split:")
        print(f"    Accuracy:  {baseline_metrics['accuracy']*100:.2f}%")
        print(f"    ROC-AUC:   {baseline_metrics['roc_auc']:.4f}")
        print(f"    SIF Recall:{baseline_metrics['sif_recall']*100:.2f}% | FNR: {baseline_metrics['false_negative_rate']*100:.2f}%")
        print(f"    SIF Prec:  {baseline_metrics['sif_precision']*100:.2f}% | FPR: {baseline_metrics['false_positive_rate']*100:.2f}%")
        print(f"    SIF F1:    {baseline_metrics['sif_f1']:.4f}")

    # 6. Model Exploration & Hyperparameter Comparison (Train & Val ONLY)
    print("\n[Step 6/8] Comparing candidate sparse linear classifiers on Validation Set...")

    candidates = [
        # Candidate 1: Logistic Regression (default C=1.0, balanced)
        {
            "name": "Logistic Regression (C=1.0, balanced, n-grams 1-2)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True),
            "model": LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=2026),
            "supports_proba": True,
        },
        # Candidate 2: Logistic Regression (tuned C=2.0, balanced, n-grams 1-2)
        {
            "name": "Logistic Regression (C=2.0, balanced, n-grams 1-2)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True),
            "model": LogisticRegression(C=2.0, class_weight="balanced", max_iter=2000, random_state=2026),
            "supports_proba": True,
        },
        # Candidate 3: Logistic Regression (C=0.5, balanced, n-grams 1-2)
        {
            "name": "Logistic Regression (C=0.5, balanced, n-grams 1-2)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True),
            "model": LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000, random_state=2026),
            "supports_proba": True,
        },
        # Candidate 4: Linear SVM (SGDClassifier log_loss, elasticnet)
        {
            "name": "Linear SVM / SGD (log_loss, alpha=1e-4, balanced)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True),
            "model": SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, class_weight="balanced", max_iter=2000, random_state=2026),
            "supports_proba": True,
        },
        # Candidate 5: Calibrated LinearSVC (LinearSVC + Platt scaling)
        {
            "name": "Calibrated Linear SVM (LinearSVC, C=1.0, Platt scaling)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True),
            "model": CalibratedClassifierCV(LinearSVC(C=1.0, class_weight="balanced", random_state=2026), method="sigmoid", cv=3),
            "supports_proba": True,
        },
        # Candidate 6: Multinomial Naive Bayes (alpha=0.5)
        {
            "name": "Multinomial Naive Bayes (alpha=0.5, n-grams 1-2)",
            "vectorizer": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=False),
            "model": MultinomialNB(alpha=0.5),
            "supports_proba": True,
        },
    ]

    experiment_results: list[dict[str, Any]] = []
    best_candidate_idx = -1
    best_val_f1 = -1.0

    # Map numeric labels to standard string class names: ['NON_SIF', 'SIF']
    y_train_str = np.array(["SIF" if y == 1 else "NON_SIF" for y in y_train])
    y_val_str = np.array(["SIF" if y == 1 else "NON_SIF" for y in y_val])
    y_test_str = np.array(["SIF" if y == 1 else "NON_SIF" for y in y_test])

    for idx, cand in enumerate(candidates):
        cand_name = cand["name"]
        vec = cand["vectorizer"]
        clf = cand["model"]

        # Fit vectorizer strictly on training data
        X_train_vec = vec.fit_transform(train_texts)
        X_val_vec = vec.transform(val_texts)

        clf.fit(X_train_vec, y_train_str)

        classes = list(clf.classes_)
        sif_idx = classes.index("SIF")

        if cand["supports_proba"]:
            y_val_prob = clf.predict_proba(X_val_vec)[:, sif_idx]
        else:
            y_val_prob = clf.decision_function(X_val_vec)

        y_val_pred = (y_val_prob >= 0.50).astype(int)
        val_metrics = calculate_safety_metrics(y_val, y_val_pred, y_val_prob)

        cand_result = {
            "index": idx,
            "name": cand_name,
            "vocab_size": len(vec.vocabulary_),
            "val_accuracy": val_metrics["accuracy"],
            "val_roc_auc": val_metrics["roc_auc"],
            "val_pr_auc": val_metrics["pr_auc"],
            "val_sif_precision": val_metrics["sif_precision"],
            "val_sif_recall": val_metrics["sif_recall"],
            "val_sif_f1": val_metrics["sif_f1"],
            "val_fnr": val_metrics["false_negative_rate"],
            "val_fpr": val_metrics["false_positive_rate"],
            "val_brier_score": val_metrics.get("brier_score"),
        }
        experiment_results.append(cand_result)

        print(f"  [{idx+1}/{len(candidates)}] {cand_name}")
        print(f"      Vocab: {cand_result['vocab_size']} | Acc: {val_metrics['accuracy']*100:.2f}% | F1: {val_metrics['sif_f1']:.4f} | ROC-AUC: {val_metrics['roc_auc']:.4f} | SIF Recall: {val_metrics['sif_recall']*100:.2f}% | FNR: {val_metrics['false_negative_rate']*100:.2f}%")

        # Select model based on validation F1 and ROC-AUC
        if val_metrics["sif_f1"] > best_val_f1:
            best_val_f1 = val_metrics["sif_f1"]
            best_candidate_idx = idx

    winning_candidate_config = candidates[best_candidate_idx]
    print(f"\n  Winning Candidate on Validation Set: {winning_candidate_config['name']} (Val F1: {best_val_f1:.4f})")

    # 7. Threshold Selection & Calibration Analysis on Validation Set
    print("\n[Step 7/8] Threshold selection and calibration analysis on Validation Set...")
    winning_vec = winning_candidate_config["vectorizer"]
    winning_model = winning_candidate_config["model"]

    # Refit vectorizer and model on Train
    X_train_vec = winning_vec.fit_transform(train_texts)
    X_val_vec = winning_vec.transform(val_texts)
    winning_model.fit(X_train_vec, y_train_str)

    sif_idx = list(winning_model.classes_).index("SIF")
    val_probs = winning_model.predict_proba(X_val_vec)[:, sif_idx]

    # Evaluate calibration
    calib_analysis = evaluate_calibration_curve(y_val, val_probs, n_bins=10)
    print(f"  Validation Brier Score: {calib_analysis['brier_score']:.4f}")
    print(f"  Expected Calibration Error (ECE): {calib_analysis['expected_calibration_error']:.4f}")

    # Threshold grid evaluation
    th_table = evaluate_threshold_candidates(y_val, val_probs)
    print("\n  Validation Threshold Trade-off Table:")
    print("  | Threshold | Accuracy | SIF Prec | SIF Recall | SIF F1 | FNR (Missed SIF) | FPR |")
    print("  |:---------:|:--------:|:--------:|:----------:|:------:|:----------------:|:---:|")
    for row in th_table:
        print(f"  |   {row['threshold']:<7.2f} |  {row['accuracy']*100:<7.2f}% |  {row['sif_precision']*100:<7.2f}% |  {row['sif_recall']*100:<9.2f}% | {row['sif_f1']:<6.4f} |     {row['fnr']*100:<11.2f}% | {row['fpr']*100:<4.2f}% |")

    # Choose threshold: safety first strategy with high recall target >= 0.80
    selected_threshold, selected_th_metrics = select_operating_threshold(
        y_val, val_probs, min_recall=0.80, strategy="safety_first"
    )
    print(f"\n  Selected Operating Threshold (Validation-driven): {selected_threshold:.2f}")
    print(f"    Validation Metrics at Selected Threshold ({selected_threshold:.2f}):")
    print(f"    Accuracy:   {selected_th_metrics['accuracy']*100:.2f}%")
    print(f"    SIF Recall: {selected_th_metrics['sif_recall']*100:.2f}% (FNR: {selected_th_metrics['fnr']*100:.2f}%)")
    print(f"    SIF Prec:   {selected_th_metrics['sif_precision']*100:.2f}% (FPR: {selected_th_metrics['fpr']*100:.2f}%)")
    print(f"    SIF F1:     {selected_th_metrics['sif_f1']:.4f}")

    # 8. Single Final Evaluation on Held-Out Test Set
    print("\n[Step 8/8] Evaluating winning model ONCE on held-out Test Set...")
    X_test_vec = winning_vec.transform(test_texts)
    t_inf_start = time.perf_counter()
    test_probs = winning_model.predict_proba(X_test_vec)[:, sif_idx]
    t_inf = (time.perf_counter() - t_inf_start) / len(test_texts) * 1000  # ms per sample

    test_preds_selected = (test_probs >= selected_threshold).astype(int)
    test_preds_default = (test_probs >= 0.50).astype(int)

    final_test_metrics_selected = calculate_safety_metrics(y_test, test_preds_selected, test_probs)
    final_test_metrics_default = calculate_safety_metrics(y_test, test_preds_default, test_probs)
    test_calib = evaluate_calibration_curve(y_test, test_probs, n_bins=10)

    print(f"  Final Test Metrics at Operating Threshold ({selected_threshold:.2f}):")
    print(f"    Accuracy:   {final_test_metrics_selected['accuracy']*100:.2f}%")
    print(f"    ROC-AUC:    {final_test_metrics_selected['roc_auc']:.4f}")
    print(f"    PR-AUC:     {final_test_metrics_selected['pr_auc']:.4f}")
    print(f"    SIF Recall: {final_test_metrics_selected['sif_recall']*100:.2f}% (FNR: {final_test_metrics_selected['false_negative_rate']*100:.2f}%)")
    print(f"    SIF Prec:   {final_test_metrics_selected['sif_precision']*100:.2f}% (FPR: {final_test_metrics_selected['false_positive_rate']*100:.2f}%)")
    print(f"    SIF F1:     {final_test_metrics_selected['sif_f1']:.4f}")
    print(f"    Confusion Matrix: TN={final_test_metrics_selected['confusion_matrix']['tn']}, FP={final_test_metrics_selected['confusion_matrix']['fp']}, FN={final_test_metrics_selected['confusion_matrix']['fn']}, TP={final_test_metrics_selected['confusion_matrix']['tp']}")
    print(f"    Inference Latency: {t_inf:.3f} ms / report")

    # 9. Extract Top Predictive Features (Explainability)
    feature_names = winning_vec.get_feature_names_out()
    if hasattr(winning_model, "coef_"):
        coefs = winning_model.coef_[0]
        top_sif_indices = np.argsort(coefs)[-15:][::-1]
        top_non_sif_indices = np.argsort(coefs)[:15]

        top_sif_features = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_sif_indices]
        top_non_sif_features = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_non_sif_indices]
    elif hasattr(winning_model, "calibrated_classifiers_"):
        # For CalibratedClassifierCV
        base_clf = winning_model.calibrated_classifiers_[0].estimator
        coefs = base_clf.coef_[0]
        top_sif_indices = np.argsort(coefs)[-15:][::-1]
        top_non_sif_indices = np.argsort(coefs)[:15]
        top_sif_features = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_sif_indices]
        top_non_sif_features = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_non_sif_indices]
    else:
        top_sif_features = []
        top_non_sif_features = []

    print("\n  Top 5 SIF Predictive Features:")
    for f in top_sif_features[:5]:
        print(f"    + {f['feature']:<25} (weight: +{f['weight']:.4f})")
    print("  Top 5 NON_SIF Predictive Features:")
    for f in top_non_sif_features[:5]:
        print(f"    - {f['feature']:<25} (weight: {f['weight']:.4f})")

    # 10. Model Artifact Serialization & Versioning
    print("\n[Step 9/9] Serializing versioned model artifacts to artifacts/models/v2 and updating active artifacts...")
    V2_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (V2_ARTIFACTS_DIR / "model").mkdir(parents=True, exist_ok=True)
    (V2_ARTIFACTS_DIR / "vectorizer").mkdir(parents=True, exist_ok=True)

    # Dump to v2 directory
    joblib.dump(winning_model, V2_ARTIFACTS_DIR / "model" / "sif_model.joblib")
    joblib.dump(winning_vec, V2_ARTIFACTS_DIR / "vectorizer" / "tfidf.joblib")

    threshold_config = {
        "selected_threshold": selected_threshold,
        "default_threshold": 0.50,
        "min_recall_constraint": 0.80,
        "selection_strategy": "safety_first",
    }
    (V2_ARTIFACTS_DIR / "threshold.json").write_text(
        json.dumps(threshold_config, indent=2), encoding="utf-8"
    )

    metadata = {
        "model_name": "sif-tfidf-logreg",
        "model_version": "sif-tfidf-logreg-v2",
        "training_timestamp": datetime.now(UTC).isoformat(),
        "training_dataset_identifier": "safety-reports-raw-10k",
        "dataset_filename": str(PRIMARY_DATASET_PATH.name),
        "dataset_hash": dataset_summary.sha256_hash,
        "total_records": dataset_summary.usable_rows,
        "positive_count": dataset_summary.positive_count,
        "negative_count": dataset_summary.negative_count,
        "split_strategy": "deterministic_group_aware_70_15_15",
        "split_seed": split_manifest.random_seed,
        "train_records": split_manifest.train_records,
        "validation_records": split_manifest.val_records,
        "test_records": split_manifest.test_records,
        "preprocessing_version": "phase2_canonical_normalization",
        "scikit_learn_version": sklearn.__version__,
        "vectorizer_configuration": {
            "ngram_range": list(winning_vec.ngram_range),
            "min_df": winning_vec.min_df,
            "max_df": winning_vec.max_df,
            "sublinear_tf": winning_vec.sublinear_tf,
            "vocabulary_size": len(winning_vec.vocabulary_),
        },
        "classifier_configuration": {
            "model_type": type(winning_model).__name__,
            "winning_candidate_name": winning_candidate_config["name"],
        },
        "operating_threshold": selected_threshold,
        "threshold_config": threshold_config,
        "class_labels": ["NON_SIF", "SIF"],
        "metrics": {
            "classification_report": {
                "NON_SIF": {
                    "precision": final_test_metrics_selected["non_sif_precision"],
                    "recall": final_test_metrics_selected["non_sif_recall"],
                    "f1-score": final_test_metrics_selected["non_sif_f1"],
                    "support": final_test_metrics_selected["non_sif_support"],
                },
                "SIF": {
                    "precision": final_test_metrics_selected["sif_precision"],
                    "recall": final_test_metrics_selected["sif_recall"],
                    "f1-score": final_test_metrics_selected["sif_f1"],
                    "support": final_test_metrics_selected["sif_support"],
                },
                "accuracy": final_test_metrics_selected["accuracy"],
            },
            "confusion_matrix": final_test_metrics_selected["confusion_matrix"]["matrix"],
            "roc_auc": final_test_metrics_selected["roc_auc"],
            "pr_auc": final_test_metrics_selected["pr_auc"],
            "brier_score": test_calib["brier_score"],
            "test_records": final_test_metrics_selected["total_samples"],
        },
        "validation_metrics_at_selected_threshold": selected_th_metrics,
        "test_metrics_at_selected_threshold": final_test_metrics_selected,
        "test_metrics_at_default_threshold": final_test_metrics_default,
        "calibration": {
            "validation_brier_score": calib_analysis["brier_score"],
            "validation_ece": calib_analysis["expected_calibration_error"],
            "test_brier_score": test_calib["brier_score"],
            "test_ece": test_calib["expected_calibration_error"],
        },
        "historical_baseline_comparison": baseline_metrics,
        "experiment_comparison": experiment_results,
        "top_sif_features": top_sif_features,
        "top_non_sif_features": top_non_sif_features,
        "inference_latency_ms": round(t_inf, 3),
    }

    (V2_ARTIFACTS_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # Update active artifacts in artifacts/models/ for FastAPI backend
    (ARTIFACTS_DIR / "model").mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / "vectorizer").mkdir(parents=True, exist_ok=True)
    joblib.dump(winning_model, ARTIFACTS_DIR / "model" / "sif_logreg.joblib")
    joblib.dump(winning_vec, ARTIFACTS_DIR / "vectorizer" / "tfidf.joblib")
    (ARTIFACTS_DIR / "threshold.json").write_text(
        json.dumps(threshold_config, indent=2), encoding="utf-8"
    )
    (ARTIFACTS_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("\nArtifacts successfully written to:")
    print(f"  - Versioned: {V2_ARTIFACTS_DIR}")
    print(f"  - Active:    {ARTIFACTS_DIR}")
    print(f"  - Baseline:  {BASELINE_DIR}")

    return metadata


if __name__ == "__main__":
    run_experiments()
