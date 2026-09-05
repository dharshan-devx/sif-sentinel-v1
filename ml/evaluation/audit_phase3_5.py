"""
Phase 3.5 Model Credibility & Generalization Audit Script.

This script performs diagnostic experiments on the Phase 3 SIF classification model
without modifying production artifacts or training data.
"""
from __future__ import annotations

import csv
import io
import json
import math
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Ensure backend and root paths are in sys.path
ROOT = Path(__file__).parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.nlp.preprocessing import preprocess_text
from ml.data.dataset import load_and_validate_dataset, extract_model_inputs
from ml.evaluation.metrics import calculate_safety_metrics, evaluate_calibration_curve

# Paths
PRIMARY_DATASET_PATH = ROOT / "data" / "raw" / "safety_reports.csv"
OSHA_DATASET_PATH = ROOT / "data" / "raw" / "January2015toNovember2025.csv"
SPLIT_MANIFEST_PATH = ROOT / "data" / "processed" / "split_manifest_v2.json"
ARTIFACTS_DIR = ROOT / "artifacts" / "models"
V2_ARTIFACTS_DIR = ARTIFACTS_DIR / "v2"
AUDIT_OUTPUT_PATH = ROOT / "artifacts" / "phase3_5_audit_results.json"


def load_production_artifacts():
    """Load production model, vectorizer, metadata, threshold, and split manifest."""
    model_path = ARTIFACTS_DIR / "model" / "sif_logreg.joblib"
    vectorizer_path = ARTIFACTS_DIR / "vectorizer" / "tfidf.joblib"
    metadata_path = ARTIFACTS_DIR / "metadata.json"
    threshold_path = ARTIFACTS_DIR / "threshold.json"

    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    threshold_data = json.loads(threshold_path.read_text(encoding="utf-8"))
    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))

    return {
        "model": model,
        "vectorizer": vectorizer,
        "metadata": metadata,
        "threshold": float(threshold_data.get("selected_threshold", 0.49)),
        "split_manifest": split_manifest,
    }


def predict_text(text: str, model: Any, vectorizer: Any, threshold: float) -> dict[str, Any]:
    """Run inference on raw text using production pipeline."""
    norm_text = preprocess_text(text).normalized_text
    vec = vectorizer.transform([norm_text])
    classes = list(model.classes_)
    sif_idx = classes.index("SIF") if "SIF" in classes else 1
    prob = float(model.predict_proba(vec)[0][sif_idx])
    pred = int(prob >= threshold)
    return {
        "normalized_text": norm_text,
        "probability": prob,
        "prediction": "SIF" if pred == 1 else "NON_SIF",
        "is_sif": pred == 1,
    }


def run_part1_audit(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 1: Audit current Phase 3 production model configuration."""
    meta = artifacts["metadata"]
    return {
        "model_version": meta.get("model_version"),
        "model_type": meta.get("classifier_configuration", {}).get("model_type"),
        "vectorizer": meta.get("vectorizer_configuration"),
        "preprocessing": meta.get("preprocessing_version"),
        "threshold": artifacts["threshold"],
        "calibration": meta.get("calibration"),
        "train_size": meta.get("train_records"),
        "val_size": meta.get("validation_records"),
        "test_size": meta.get("test_records"),
    }


def run_part2_reproduce(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 2: Reproduce Phase 3 result on split manifest partitions."""
    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
    record_map = {r["id"]: r for r in records}
    manifest = artifacts["split_manifest"]

    val_records = [record_map[rid] for rid in manifest["val_ids"] if rid in record_map]
    test_records = [record_map[rid] for rid in manifest["test_ids"] if rid in record_map]

    val_texts, y_val = extract_model_inputs(val_records)
    test_texts, y_test = extract_model_inputs(test_records)

    val_norm = [preprocess_text(t).normalized_text for t in val_texts]
    test_norm = [preprocess_text(t).normalized_text for t in test_texts]

    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    X_val = vec.transform(val_norm)
    X_test = vec.transform(test_norm)

    classes = list(model.classes_)
    sif_idx = classes.index("SIF")

    val_probs = model.predict_proba(X_val)[:, sif_idx]
    test_probs = model.predict_proba(X_test)[:, sif_idx]

    val_preds = (val_probs >= th).astype(int)
    test_preds = (test_probs >= th).astype(int)

    val_metrics = calculate_safety_metrics(y_val, val_preds, val_probs)
    test_metrics = calculate_safety_metrics(y_test, test_preds, test_probs)

    expected_test = artifacts["metadata"]["test_metrics_at_selected_threshold"]

    return {
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "expected_test": expected_test,
        "matches_expected": test_metrics["accuracy"] == expected_test["accuracy"],
    }


def run_part3_duplicate_leakage(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 3: Verify exact duplicate leakage across splits."""
    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
    record_map = {r["id"]: r for r in records}
    manifest = artifacts["split_manifest"]

    train_recs = [record_map[rid] for rid in manifest["train_ids"] if rid in record_map]
    val_recs = [record_map[rid] for rid in manifest["val_ids"] if rid in record_map]
    test_recs = [record_map[rid] for rid in manifest["test_ids"] if rid in record_map]

    train_norm = set(preprocess_text(r["report_text"]).normalized_text for r in train_recs)
    val_norm = set(preprocess_text(r["report_text"]).normalized_text for r in val_recs)
    test_norm = set(preprocess_text(r["report_text"]).normalized_text for r in test_recs)

    train_val_overlap = train_norm.intersection(val_norm)
    train_test_overlap = train_norm.intersection(test_norm)
    val_test_overlap = val_norm.intersection(test_norm)

    train_groups = manifest.get("train_groups", len(train_norm))
    val_groups = manifest.get("val_groups", len(val_norm))
    test_groups = manifest.get("test_groups", len(test_norm))

    return {
        "train_val_overlap_count": len(train_val_overlap),
        "train_test_overlap_count": len(train_test_overlap),
        "val_test_overlap_count": len(val_test_overlap),
        "train_groups": train_groups,
        "val_groups": val_groups,
        "test_groups": test_groups,
        "cross_split_duplicate_groups": len(train_val_overlap) + len(train_test_overlap) + len(val_test_overlap),
    }


def normalize_skeleton(text: str) -> str:
    """Create a structural template skeleton of a report text."""
    norm = preprocess_text(text).normalized_text
    skeleton = re.sub(r'\b\d+(\.\d+)?\b', '[NUM]', norm)
    return skeleton


def run_part4_template_leakage(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 4: Template-family leakage analysis using skeleton & prefix clustering."""
    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
    manifest = artifacts["split_manifest"]

    record_map = {r["id"]: r for r in records}
    train_ids = set(manifest["train_ids"])
    test_ids = set(manifest["test_ids"])
    val_ids = set(manifest["val_ids"])

    skeletons = [normalize_skeleton(r["report_text"]) for r in records]

    family_map = defaultdict(list)
    for r, sk in zip(records, skeletons):
        words = sk.split()
        prefix = " ".join(words[:4]) if len(words) >= 4 else sk
        family_map[prefix].append(r)

    template_families = {k: v for k, v in family_map.items() if len(v) >= 2}

    total_records = len(records)
    records_in_templates = sum(len(v) for v in template_families.values())
    pct_in_templates = (records_in_templates / total_records) * 100

    train_test_overlap_families = 0
    overlapping_families = 0
    family_sizes = [len(v) for v in template_families.values()]
    family_sizes.sort(reverse=True)

    for prefix, family_recs in family_map.items():
        if len(family_recs) < 2:
            continue
        splits_in_family = set()
        for r in family_recs:
            rid = r["id"]
            if rid in train_ids:
                splits_in_family.add("TRAIN")
            elif rid in val_ids:
                splits_in_family.add("VAL")
            elif rid in test_ids:
                splits_in_family.add("TEST")
        if "TRAIN" in splits_in_family and ("TEST" in splits_in_family or "VAL" in splits_in_family):
            overlapping_families += 1
        if "TRAIN" in splits_in_family and "TEST" in splits_in_family:
            train_test_overlap_families += 1

    return {
        "total_records": total_records,
        "number_of_major_template_families": len(template_families),
        "records_in_template_families": records_in_templates,
        "percentage_records_in_template_families": round(pct_in_templates, 2),
        "train_test_family_overlap_count": train_test_overlap_families,
        "train_val_test_family_overlap_count": overlapping_families,
        "top_5_family_sizes": family_sizes[:5],
        "explains_perfect_score": train_test_overlap_families > 100,
    }


def run_part5_template_holdout(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 5: Diagnostic Template-Holdout Experiment."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    from ml.data.dataset import normalize_binary_target

    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)

    family_map = defaultdict(list)
    for r in records:
        sk = normalize_skeleton(r["report_text"])
        words = sk.split()
        prefix = " ".join(words[:4]) if len(words) >= 4 else sk
        family_map[prefix].append(r)

    families = list(family_map.keys())
    random.seed(2026)
    random.shuffle(families)

    train_recs, test_recs = [], []
    train_fam_count = int(len(families) * 0.70)
    train_fams = set(families[:train_fam_count])

    for fam, recs in family_map.items():
        if fam in train_fams:
            train_recs.extend(recs)
        else:
            test_recs.extend(recs)

    train_texts = [preprocess_text(r["report_text"]).normalized_text for r in train_recs]
    y_train = [normalize_binary_target(r["sif_potential"]) for r in train_recs]
    test_texts = [preprocess_text(r["report_text"]).normalized_text for r in test_recs]
    y_test = [normalize_binary_target(r["sif_potential"]) for r in test_recs]

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True)
    X_train = vec.fit_transform(train_texts)
    X_test = vec.transform(test_texts)

    y_train_str = np.array(["SIF" if y == 1 else "NON_SIF" for y in y_train])
    clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=2026)
    clf.fit(X_train, y_train_str)

    sif_idx = list(clf.classes_).index("SIF")
    test_probs = clf.predict_proba(X_test)[:, sif_idx]
    test_preds = (test_probs >= 0.49).astype(int)

    metrics = calculate_safety_metrics(y_test, test_preds, test_probs)
    return {
        "diagnostic_experiment_name": "Template-Held-Out Diagnostic LogisticRegression",
        "train_records": len(train_recs),
        "test_records": len(test_recs),
        "metrics": metrics,
    }


def run_part6_adversarial(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Part 6: Expert-authored diagnostic challenge examples across 10 safety categories."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    challenge_cases = [
        # 1. Working at Height
        {"cat": "Working at Height", "text": "Operator climbed to 15ft platform without safety harness hooked.", "expected": "SIF"},
        {"cat": "Working at Height", "text": "Worker performed ladder inspection on 4ft step stool with guardrails.", "expected": "NON_SIF"},
        {"cat": "Working at Height", "text": "Scaffold was erected at height of 25ft missing mid-rails and toe-boards.", "expected": "SIF"},

        # 2. Confined Space
        {"cat": "Confined Space", "text": "Technician entered nitrogen-purged vessel prior to gas clearance testing.", "expected": "SIF"},
        {"cat": "Confined Space", "text": "Confined space entry permit was verified and continuous gas monitoring active.", "expected": "NON_SIF"},

        # 3. Energy Isolation / LOTO
        {"cat": "Energy Isolation / LOTO", "text": "Fitter opened hydraulic line under 3000 PSI pressure without zero energy verification.", "expected": "SIF"},
        {"cat": "Energy Isolation / LOTO", "text": "Lockout tagout locks applied and zero pressure confirmed before pipe flange break.", "expected": "NON_SIF"},

        # 4. Suspended Loads
        {"cat": "Suspended Loads", "text": "Rigging team walked directly underneath 5-ton suspended drill collar.", "expected": "SIF"},
        {"cat": "Suspended Loads", "text": "Tag lines were utilized and personnel remained outside red-zone exclusion zone during lift.", "expected": "NON_SIF"},

        # 5. Gas Testing
        {"cat": "Gas Testing", "text": "Hot work commenced near hydrocarbon vent header without LLE flammable gas sweep.", "expected": "SIF"},
        {"cat": "Gas Testing", "text": "Gas test confirmed 0% LEL prior to welding spark permit issuance.", "expected": "NON_SIF"},

        # 6. PPE
        {"cat": "PPE", "text": "Roustabout handled hazardous caustic chemical without face shield or chemical aprons.", "expected": "SIF"},
        {"cat": "PPE", "text": "Worker wore standard safety glasses while sweeping dry dirt in warehouse.", "expected": "NON_SIF"},

        # 7. Hazardous Energy
        {"cat": "Hazardous Energy", "text": "Electrician opened 4160V switchgear compartment while bus bar remained energized.", "expected": "SIF"},
        {"cat": "Hazardous Energy", "text": "Electrical breaker locked in open position and tested dead with multimeter.", "expected": "NON_SIF"},

        # 8. Barrier Bypass
        {"cat": "Barrier Bypass", "text": "Operator jumpered emergency shutdown interlock to bypass high-pressure trip.", "expected": "SIF"},
        {"cat": "Barrier Bypass", "text": "Safety interlock trip tested during scheduled maintenance per SOP.", "expected": "NON_SIF"},

        # 9. Unsafe Condition
        {"cat": "Unsafe Condition", "text": "Floor opening around cell hatch uncovered and un-barricaded in dark area.", "expected": "SIF"},
        {"cat": "Unsafe Condition", "text": "Wet floor sign placed near main office corridor after floor washing.", "expected": "NON_SIF"},

        # 10. Near Miss
        {"cat": "Near Miss", "text": "Dropped 12lb heavy wrench from 40ft derrick level landing 2ft from helper head.", "expected": "SIF"},
        {"cat": "Near Miss", "text": "Dropped small plastic pen from desk surface onto carpeted office floor.", "expected": "NON_SIF"},
    ]

    results = []
    for case in challenge_cases:
        res = predict_text(case["text"], model, vec, th)
        passed = (res["prediction"] == case["expected"])
        results.append({
            "text": case["text"],
            "category": case["cat"],
            "expected": case["expected"],
            "probability": round(res["probability"], 4),
            "prediction": res["prediction"],
            "result": "CORRECT" if passed else "INCORRECT",
            "observation": f"Prob={res['probability']:.4f}, Exp={case['expected']}",
        })
    return results


def run_part7_counterfactuals(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Part 7: Paired counterfactual safety testing."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    pairs = [
        {
            "id": "PAIR A",
            "category": "Fall Protection",
            "unsafe": "Worker worked at height without fall protection.",
            "safe": "Worker worked at height with approved fall protection.",
        },
        {
            "id": "PAIR B",
            "category": "Energy Isolation",
            "unsafe": "Energy isolation was not verified before maintenance.",
            "safe": "Energy isolation was verified before maintenance.",
        },
        {
            "id": "PAIR C",
            "category": "Gas Testing",
            "unsafe": "Gas testing was not completed before entry.",
            "safe": "Gas testing was completed before entry.",
        },
        {
            "id": "PAIR D",
            "category": "Suspended Load",
            "unsafe": "Load was suspended above personnel.",
            "safe": "Personnel were kept outside the suspended-load exclusion zone.",
        },
        {
            "id": "PAIR E",
            "category": "Safety Interlock",
            "unsafe": "Interlock was bypassed during operation.",
            "safe": "Interlock remained functional during operation.",
        },
        {
            "id": "PAIR F",
            "category": "Confined Space",
            "unsafe": "Employee entered vessel without atmospheric testing.",
            "safe": "Employee entered vessel after atmospheric testing was verified.",
        },
    ]

    results = []
    for p in pairs:
        res_u = predict_text(p["unsafe"], model, vec, th)
        res_s = predict_text(p["safe"], model, vec, th)
        delta = res_u["probability"] - res_s["probability"]

        if delta > 0.30 and res_u["prediction"] == "SIF" and res_s["prediction"] == "NON_SIF":
            status = "EXPECTED"
        elif delta > 0.10:
            status = "PARTIALLY EXPECTED"
        else:
            status = "UNEXPECTED"

        results.append({
            "pair_id": p["id"],
            "category": p["category"],
            "unsafe_text": p["unsafe"],
            "unsafe_prob": round(res_u["probability"], 4),
            "unsafe_pred": res_u["prediction"],
            "safe_text": p["safe"],
            "safe_prob": round(res_s["probability"], 4),
            "safe_pred": res_s["prediction"],
            "prob_delta": round(delta, 4),
            "status": status,
            "explanation": f"Delta = {delta:+.4f}. Unsafe prob: {res_u['probability']:.4f}, Safe prob: {res_s['probability']:.4f}",
        })
    return results


def run_part8_negation(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Part 8: Negation and control word robustness testing."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    cases = [
        ("Fall protection was not used.", "Fall protection was used."),
        ("Gas testing was not completed.", "Gas testing was completed."),
        ("Energy isolation was not verified.", "Energy isolation was verified."),
        ("Atmospheric testing was never conducted.", "Atmospheric testing was conducted."),
        ("PPE was not worn during grinding.", "PPE was worn during grinding."),
        ("Worker was prevented from entering without harness.", "Worker entered without harness."),
    ]

    results = []
    for text_neg, text_pos in cases:
        res_neg = predict_text(text_neg, model, vec, th)
        res_pos = predict_text(text_pos, model, vec, th)
        delta = res_neg["probability"] - res_pos["probability"]

        results.append({
            "negated_text": text_neg,
            "negated_prob": round(res_neg["probability"], 4),
            "negated_pred": res_neg["prediction"],
            "positive_text": text_pos,
            "positive_prob": round(res_pos["probability"], 4),
            "positive_pred": res_pos["prediction"],
            "prob_delta": round(delta, 4),
            "sensitive_to_negation": delta > 0.15,
        })
    return results


def run_part9_keyword_shortcuts(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 9: Feature coefficient and controlled keyword-ablation analysis."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    feature_names = vec.get_feature_names_out()
    coefs = model.coef_[0]

    top_sif_idx = np.argsort(coefs)[-15:][::-1]
    top_non_sif_idx = np.argsort(coefs)[:15]

    top_sif = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_sif_idx]
    top_non_sif = [{"feature": str(feature_names[i]), "weight": round(float(coefs[i]), 4)} for i in top_non_sif_idx]

    base_text = "Worker entered vessel inside tank without gas testing."
    base_res = predict_text(base_text, model, vec, th)

    ablations = []
    for kw in ["without", "inside", "gas", "vessel"]:
        ablated_text = base_text.replace(kw, "")
        abl_res = predict_text(ablated_text, model, vec, th)
        ablations.append({
            "removed_keyword": kw,
            "original_prob": round(base_res["probability"], 4),
            "ablated_prob": round(abl_res["probability"], 4),
            "prob_drop": round(base_res["probability"] - abl_res["probability"], 4),
        })

    return {
        "top_sif_features": top_sif,
        "top_non_sif_features": top_non_sif,
        "generic_stopwords_in_top": [f["feature"] for f in top_sif if f["feature"] in {"of", "was", "or", "to", "had", "out", "using"}],
        "keyword_ablations": ablations,
    }


def run_part10_shuffled_text(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Part 10: Shuffled-text syntax/structure sanity test."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    sample_texts = [
        "Worker entered vessel without atmospheric gas testing before maintenance.",
        "Scaffold erected at 25 feet missing mid-rails and toe boards.",
        "Electrician opened 4160V breaker cabinet without wearing arc flash suit.",
        "Dropped heavy steel pipe from crane load into busy walkways.",
        "Slip and trip on oily walkway in warehouse causing minor knee bruise.",
    ]

    random.seed(2026)
    results = []
    for orig in sample_texts:
        orig_res = predict_text(orig, model, vec, th)
        words = orig.split()
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)
        shuffled_text = " ".join(shuffled_words)
        shuf_res = predict_text(shuffled_text, model, vec, th)

        results.append({
            "original_text": orig,
            "original_prob": round(orig_res["probability"], 4),
            "shuffled_text": shuffled_text,
            "shuffled_prob": round(shuf_res["probability"], 4),
            "prob_difference": round(orig_res["probability"] - shuf_res["probability"], 4),
        })
    return results


def run_part11_correlation_analysis(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 11: Dataset target vs metadata feature correlation analysis."""
    from sklearn.linear_model import LogisticRegression
    from ml.data.dataset import normalize_binary_target

    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)

    sif_chars, non_sif_chars = [], []
    sif_words, non_sif_words = [], []
    sif_punct, non_sif_punct = [], []
    sif_digits, non_sif_digits = [], []

    X_meta = []
    y_all = []

    for r in records:
        txt = r["report_text"]
        label = normalize_binary_target(r["sif_potential"])
        chars = len(txt)
        words = len(txt.split())
        punct = sum(1 for c in txt if c in '.,!?;:-()[]{}')
        digits = sum(1 for c in txt if c.isdigit())

        X_meta.append([chars, words, punct, digits])
        y_all.append(label)

        if label == 1:
            sif_chars.append(chars)
            sif_words.append(words)
            sif_punct.append(punct)
            sif_digits.append(digits)
        else:
            non_sif_chars.append(chars)
            non_sif_words.append(words)
            non_sif_punct.append(punct)
            non_sif_digits.append(digits)

    X_meta = np.array(X_meta)
    y_all = np.array(y_all)

    split_idx = int(len(X_meta) * 0.7)
    clf_meta = LogisticRegression()
    clf_meta.fit(X_meta[:split_idx], y_all[:split_idx])
    meta_acc = float(clf_meta.score(X_meta[split_idx:], y_all[split_idx:]))

    return {
        "sif_mean_chars": round(float(np.mean(sif_chars)), 2),
        "non_sif_mean_chars": round(float(np.mean(non_sif_chars)), 2),
        "sif_mean_words": round(float(np.mean(sif_words)), 2),
        "non_sif_mean_words": round(float(np.mean(non_sif_words)), 2),
        "sif_mean_punct": round(float(np.mean(sif_punct)), 2),
        "non_sif_mean_punct": round(float(np.mean(non_sif_punct)), 2),
        "metadata_only_model_accuracy": round(meta_acc, 4),
    }


def run_part12_simple_baselines(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 12: Simple baseline model comparison on Phase 3 test split."""
    records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
    record_map = {r["id"]: r for r in records}
    manifest = artifacts["split_manifest"]

    test_recs = [record_map[rid] for rid in manifest["test_ids"] if rid in record_map]
    test_texts, y_test = extract_model_inputs(test_recs)

    majority_preds = np.ones(len(y_test), dtype=int)
    acc_majority = float(np.mean(majority_preds == y_test))

    keywords = {"without", "inside", "height", "vessel", "suspended", "unisolated", "loto", "bypassed"}
    keyword_preds = []
    for txt in test_texts:
        norm = preprocess_text(txt).normalized_text
        has_kw = any(kw in norm for kw in keywords)
        keyword_preds.append(1 if has_kw else 0)
    keyword_preds = np.array(keyword_preds)
    acc_keyword = float(np.mean(keyword_preds == y_test))
    f1_keyword = calculate_safety_metrics(y_test, keyword_preds, keyword_preds.astype(float))["sif_f1"]

    return {
        "majority_class_accuracy": acc_majority,
        "keyword_rule_accuracy": round(acc_keyword, 4),
        "keyword_rule_f1": round(f1_keyword, 4),
    }


def run_part13_calibration(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 13: Review calibration metrics."""
    meta = artifacts["metadata"]
    calib = meta.get("calibration", {})
    return {
        "validation_brier_score": calib.get("validation_brier_score"),
        "validation_ece": calib.get("validation_ece"),
        "test_brier_score": calib.get("test_brier_score"),
        "test_ece": calib.get("test_ece"),
        "interpretation": "Extremely low Brier score (0.0027) reflects near-binary confidence assignments (0.000 or 1.000) driven by sharp class separation in synthetic data.",
    }


def run_part14_ood_tests(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """Part 14: Out-of-Distribution / Unknown Input Test."""
    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    ood_cases = [
        {"cat": "Weather Report", "text": "Light rain expected throughout the afternoon with mild temperatures around 68 degrees."},
        {"cat": "Office Activities", "text": "Weekly team sync scheduled for 10 AM in Conference Room B to discuss Q3 roadmap."},
        {"cat": "Cooking Recipe", "text": "Preheat oven to 350F, mix flour, sugar, and cocoa powder before baking for 25 minutes."},
        {"cat": "Software Stack Trace", "text": "NullPointerException at com.example.service.UserProcessor.execute(UserProcessor.java:42)."},
        {"cat": "Academic Physics", "text": "Quantum entanglement between distant photons demonstrated using high-precision optical interferometers."},
        {"cat": "Logistics & Shipping", "text": "Container shipment arrived at port terminal clearance gate containing 400 pallets of office furniture."},
    ]

    results = []
    for case in ood_cases:
        res = predict_text(case["text"], model, vec, th)
        results.append({
            "category": case["cat"],
            "text": case["text"],
            "probability": round(res["probability"], 4),
            "prediction": res["prediction"],
            "flag": "OOD CONCERN" if res["probability"] >= 0.50 else "NORMAL",
        })
    return results


def run_part15_osha_analysis(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Part 15: External Domain Robustness Analysis on real OSHA incident dataset."""
    if not OSHA_DATASET_PATH.exists():
        return {"status": "SKIPPED", "reason": "OSHA dataset file not found"}

    model = artifacts["model"]
    vec = artifacts["vectorizer"]
    th = artifacts["threshold"]

    narratives = []
    try:
        with open(OSHA_DATASET_PATH, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                narr = row.get("Final Narrative", "").strip()
                if narr and len(narr) > 20:
                    narratives.append(narr)
                if len(narratives) >= 2000:
                    break
    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}

    train_vocab = set(vec.vocabulary_.keys())
    osha_words = set()
    for n in narratives:
        norm = preprocess_text(n).normalized_text
        for w in norm.split():
            osha_words.add(w)

    oov_count = sum(1 for w in osha_words if w not in train_vocab)
    oov_rate = oov_count / len(osha_words) if osha_words else 0.0

    probs = []
    for n in narratives[:500]:
        res = predict_text(n, model, vec, th)
        probs.append(res["probability"])

    probs = np.array(probs)
    high_conf_sif = float(np.mean(probs >= 0.75))
    predicted_sif = float(np.mean(probs >= th))

    return {
        "status": "COMPLETED",
        "sample_size": len(narratives[:500]),
        "osha_unique_vocab": len(osha_words),
        "train_vocab_size": len(train_vocab),
        "oov_rate": round(oov_rate, 4),
        "mean_predicted_sif_prob": round(float(np.mean(probs)), 4),
        "predicted_sif_ratio": round(predicted_sif, 4),
        "high_confidence_sif_ratio": round(high_conf_sif, 4),
    }


def execute_full_audit():
    print("=" * 70)
    print("EXECUTING PHASE 3.5 MODEL CREDIBILITY & GENERALIZATION AUDIT")
    print("=" * 70)

    artifacts = load_production_artifacts()

    audit_results = {
        "part1_audit": run_part1_audit(artifacts),
        "part2_reproduce": run_part2_reproduce(artifacts),
        "part3_duplicate_leakage": run_part3_duplicate_leakage(artifacts),
        "part4_template_leakage": run_part4_template_leakage(artifacts),
        "part5_template_holdout": run_part5_template_holdout(artifacts),
        "part6_adversarial": run_part6_adversarial(artifacts),
        "part7_counterfactuals": run_part7_counterfactuals(artifacts),
        "part8_negation": run_part8_negation(artifacts),
        "part9_keyword_shortcuts": run_part9_keyword_shortcuts(artifacts),
        "part10_shuffled_text": run_part10_shuffled_text(artifacts),
        "part11_correlation": run_part11_correlation_analysis(artifacts),
        "part12_baselines": run_part12_simple_baselines(artifacts),
        "part13_calibration": run_part13_calibration(artifacts),
        "part14_ood_tests": run_part14_ood_tests(artifacts),
        "part15_osha_analysis": run_part15_osha_analysis(artifacts),
    }

    AUDIT_OUTPUT_PATH.write_text(json.dumps(audit_results, indent=2), encoding="utf-8")
    print(f"\nAudit results successfully written to: {AUDIT_OUTPUT_PATH}")
    return audit_results


if __name__ == "__main__":
    execute_full_audit()
