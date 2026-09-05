import json
from pathlib import Path
import pytest
import numpy as np

from app.ml.inference.predictor import SIFPredictor
from app.services.nlp.preprocessing import preprocess_text

ROOT = Path(__file__).parents[2]
TRANSFORMER_DIR = ROOT / "artifacts" / "models" / "v4b_transformer"
HYBRID_DIR = ROOT / "artifacts" / "models" / "v4b_hybrid"
BENCHMARK_RESULTS_PATH = ROOT / "artifacts" / "phase4b_benchmark_results.json"
TEMPLATE_HOLDOUT_PATH = ROOT / "artifacts" / "phase4b_template_holdout_results.json"


def test_transformer_artifacts_exist():
    assert TRANSFORMER_DIR.exists(), "v4b_transformer directory must exist"
    assert (TRANSFORMER_DIR / "config.json").exists(), "config.json missing"
    assert (TRANSFORMER_DIR / "tokenizer.json").exists() or (TRANSFORMER_DIR / "vocab.txt").exists(), "Tokenizer missing"
    assert (TRANSFORMER_DIR / "metadata.json").exists(), "metadata.json missing"
    assert (TRANSFORMER_DIR / "threshold.json").exists(), "threshold.json missing"


def test_transformer_metadata_integrity():
    meta = json.loads((TRANSFORMER_DIR / "metadata.json").read_text(encoding="utf-8"))
    assert "transformer" in meta["model_name"]
    assert "DistilBert" in meta["architecture"] or "Transformer" in meta["architecture"]
    assert meta["parameter_count"] == 66955010
    assert "dataset_fingerprint" in meta
    assert meta["dataset_fingerprint"]["total_rows"] == 10000
    assert "locked_test_metrics" in meta
    assert meta["locked_test_metrics"]["accuracy"] == 1.0


def test_transformer_predictor_inference():
    predictor = SIFPredictor(version="v4b_transformer")
    text = "Operator climbed 20ft ladder without fall arrest harness."
    pred = predictor.predict(text)
    
    assert pred is not None
    assert 0.0 <= pred.probability <= 1.0
    assert pred.sif_potential in [True, False]
    assert "v4b" in pred.model_version or "transformer" in pred.model_version


def test_transformer_ood_rejection():
    predictor = SIFPredictor(version="v4b_transformer")
    ood_texts = [
        "Light rain expected throughout the afternoon with mild temperatures around 68 degrees.",
        "Preheat oven to 350F, mix flour, sugar, and cocoa powder before baking for 25 minutes.",
        "NullPointerException at com.example.service.UserProcessor.execute(UserProcessor.java:42).",
    ]
    for text in ood_texts:
        pred = predictor.predict(text)
        # OOD texts should have low probability and not trigger SIF
        assert pred.probability < 0.50
        assert pred.sif_potential is False


def test_transformer_counterfactual_sensitivity():
    predictor = SIFPredictor(version="v4b_transformer")
    unsafe_text = "Worker worked at height without fall protection."
    safe_text = "Worker worked at height with approved fall protection."
    
    p_unsafe = predictor.predict(unsafe_text).probability
    p_safe = predictor.predict(safe_text).probability
    
    assert p_unsafe > p_safe, f"Expected P(unsafe) > P(safe), got {p_unsafe} vs {p_safe}"


def test_transformer_negation_awareness():
    predictor = SIFPredictor(version="v4b_transformer")
    negated_text = "Energy isolation was not verified before maintenance."
    verified_text = "Energy isolation was verified before maintenance."
    
    p_neg = predictor.predict(negated_text).probability
    p_ver = predictor.predict(verified_text).probability
    
    assert p_neg > p_ver, f"Expected P(not verified) > P(verified), got {p_neg} vs {p_ver}"


def test_template_holdout_results_file():
    assert TEMPLATE_HOLDOUT_PATH.exists(), "phase4b_template_holdout_results.json must exist"
    data = json.loads(TEMPLATE_HOLDOUT_PATH.read_text(encoding="utf-8"))
    assert "model_a_metrics" in data
    assert "model_b_metrics" in data
    assert "model_c_metrics" in data
    
    # Transformer should demonstrate higher recall on held-out template families
    rec_c = data["model_c_metrics"]["recall"]
    rec_a = data["model_a_metrics"]["recall"]
    assert rec_c >= rec_a, f"Transformer holdout recall ({rec_c}) should be >= TF-IDF ({rec_a})"


def test_benchmark_suite_results_file():
    assert BENCHMARK_RESULTS_PATH.exists(), "phase4b_benchmark_results.json must exist"
    data = json.loads(BENCHMARK_RESULTS_PATH.read_text(encoding="utf-8"))
    assert "locked_test_comparison" in data
    assert "calibration" in data
    assert "semantic_challenge" in data
    assert "counterfactual_pairs" in data
    assert "osha_domain_robustness" in data
    
    # Locked test set accuracy must be 1.0 on the frozen split
    assert data["locked_test_comparison"]["model_c_distilbert"]["accuracy"] == 1.0
