"""SIF Sentinel ML Evaluation Layer — Safety-oriented classification metrics and calibration."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    auc,
)


def calculate_safety_metrics(
    y_true: list[int] | np.ndarray,
    y_pred: list[int] | np.ndarray,
    y_prob: list[float] | np.ndarray | None = None,
) -> dict[str, Any]:
    """
    Calculate comprehensive safety-oriented classification metrics.
    Emphasizes false negatives (missed SIF precursors) alongside precision and specificity.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_pred_arr = np.asarray(y_pred, dtype=int)

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    # Negative class metrics
    non_sif_prec = float(precision_score(1 - y_true_arr, 1 - y_pred_arr, zero_division=0))
    non_sif_rec = float(recall_score(1 - y_true_arr, 1 - y_pred_arr, zero_division=0))
    non_sif_f1 = float(f1_score(1 - y_true_arr, 1 - y_pred_arr, zero_division=0))

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    metrics: dict[str, Any] = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "specificity": round(specificity, 4),
        "false_negative_rate": round(fnr, 4),
        "false_positive_rate": round(fpr, 4),
        "sif_precision": round(prec, 4),
        "sif_recall": round(rec, 4),
        "sif_f1": round(f1, 4),
        "non_sif_precision": round(non_sif_prec, 4),
        "non_sif_recall": round(non_sif_rec, 4),
        "non_sif_f1": round(non_sif_f1, 4),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix": [[tn, fp], [fn, tp]],
        },
        "total_samples": len(y_true_arr),
        "sif_support": int(tp + fn),
        "non_sif_support": int(tn + fp),
    }

    if y_prob is not None:
        y_prob_arr = np.asarray(y_prob, dtype=float)
        try:
            roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
            metrics["roc_auc"] = round(roc_auc, 4)
        except Exception:
            metrics["roc_auc"] = None

        try:
            prec_curve, rec_curve, _ = precision_recall_curve(y_true_arr, y_prob_arr)
            pr_auc = float(auc(rec_curve, prec_curve))
            metrics["pr_auc"] = round(pr_auc, 4)
        except Exception:
            metrics["pr_auc"] = None

        try:
            brier = float(brier_score_loss(y_true_arr, y_prob_arr))
            metrics["brier_score"] = round(brier, 4)
        except Exception:
            metrics["brier_score"] = None

    return metrics


def evaluate_threshold_candidates(
    y_true: list[int] | np.ndarray,
    y_prob: list[float] | np.ndarray,
    thresholds: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate performance across a grid of decision thresholds."""
    if thresholds is None:
        thresholds = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]

    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    results = []
    for th in thresholds:
        y_pred = (y_prob_arr >= th).astype(int)
        m = calculate_safety_metrics(y_true_arr, y_pred, y_prob_arr)
        results.append({
            "threshold": round(th, 2),
            "accuracy": m["accuracy"],
            "sif_precision": m["sif_precision"],
            "sif_recall": m["sif_recall"],
            "sif_f1": m["sif_f1"],
            "fnr": m["false_negative_rate"],
            "fpr": m["false_positive_rate"],
            "tn": m["confusion_matrix"]["tn"],
            "fp": m["confusion_matrix"]["fp"],
            "fn": m["confusion_matrix"]["fn"],
            "tp": m["confusion_matrix"]["tp"],
        })
    return results


def select_operating_threshold(
    y_true: list[int] | np.ndarray,
    y_prob: list[float] | np.ndarray,
    min_recall: float = 0.80,
    strategy: str = "safety_first",
) -> tuple[float, dict[str, Any]]:
    """
    Select an optimal operating threshold on VALIDATION data.
    'safety_first': Select highest F1 threshold among those achieving recall >= min_recall.
    'balanced_f1': Select threshold maximizing F1 score.
    'default': Return 0.50.
    """
    candidates = evaluate_threshold_candidates(
        y_true, y_prob, thresholds=[t / 100.0 for t in range(25, 75, 2)]
    )

    if strategy == "safety_first":
        # Filter candidates meeting minimum recall constraint
        valid = [c for c in candidates if c["sif_recall"] >= min_recall]
        if valid:
            # Tie-break: maximize F1, then minimize distance to 0.50, then maximize precision
            best = max(
                valid,
                key=lambda c: (c["sif_f1"], -abs(c["threshold"] - 0.50), c["sif_precision"]),
            )
            return float(best["threshold"]), best

    if strategy == "balanced_f1" or not valid:
        best = max(
            candidates,
            key=lambda c: (c["sif_f1"], -abs(c["threshold"] - 0.50), c["sif_precision"]),
        )
        return float(best["threshold"]), best

    # Default fallback
    default_entry = next((c for c in candidates if abs(c["threshold"] - 0.50) < 1e-4), candidates[0])
    return 0.50, default_entry


def evaluate_calibration_curve(
    y_true: list[int] | np.ndarray,
    y_prob: list[float] | np.ndarray,
    n_bins: int = 10,
) -> dict[str, Any]:
    """Calculate empirical calibration bins and Expected Calibration Error (ECE)."""
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    true_fractions = []
    pred_means = []
    bin_counts = []
    ece = 0.0

    n_total = len(y_true_arr)
    for i in range(n_bins):
        low, high = bins[i], bins[i + 1]
        mask = (y_prob_arr >= low) & (y_prob_arr <= high if i == n_bins - 1 else y_prob_arr < high)
        count = int(np.sum(mask))
        bin_counts.append(count)

        if count > 0:
            actual_mean = float(np.mean(y_true_arr[mask]))
            pred_mean = float(np.mean(y_prob_arr[mask]))
            true_fractions.append(round(actual_mean, 4))
            pred_means.append(round(pred_mean, 4))
            ece += (count / n_total) * abs(actual_mean - pred_mean)
        else:
            true_fractions.append(round(float(bin_centers[i]), 4))
            pred_means.append(round(float(bin_centers[i]), 4))

    return {
        "n_bins": n_bins,
        "bin_counts": bin_counts,
        "true_fractions": true_fractions,
        "predicted_means": pred_means,
        "expected_calibration_error": round(float(ece), 4),
        "brier_score": round(float(brier_score_loss(y_true_arr, y_prob_arr)), 4),
    }
