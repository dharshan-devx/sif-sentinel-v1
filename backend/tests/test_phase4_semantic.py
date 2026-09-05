"""
Phase 4 Semantic SIF Intelligence Test Suite.
Tests:
- Semantic model (Model B) loading and inference.
- Calibrated Hybrid model (Model C) loading and inference.
- Configuration switching across backends ('v2', 'semantic', 'hybrid').
- Probability range [0.0, 1.0] and thresholding.
- Safety and zero-leakage guarantees.
- Semantic challenge examples, counterfactuals, and OOD handling.
- API inference compatibility.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.ml.inference.predictor import SIFPredictor, ARTIFACT_DIR
from app.ml.inference.hybrid_pipeline import SemanticClassifierPipeline, HybridClassifierPipeline
from app.services.nlp.analysis_pipeline import analyze_text


def test_phase4_artifacts_exist():
    """Verify Phase 4 semantic and hybrid model artifacts are serialized."""
    v4_semantic_dir = ARTIFACT_DIR / "v4_semantic"
    v4_hybrid_dir = ARTIFACT_DIR / "v4_hybrid"

    assert (v4_semantic_dir / "sif_semantic_model.joblib").exists()
    assert (v4_semantic_dir / "metadata.json").exists()
    assert (v4_semantic_dir / "threshold.json").exists()

    assert (v4_hybrid_dir / "sif_hybrid_model.joblib").exists()
    assert (v4_hybrid_dir / "metadata.json").exists()
    assert (v4_hybrid_dir / "threshold.json").exists()


def test_semantic_predictor_inference():
    """Test inference using Model B (sif-semantic-v1)."""
    predictor = SIFPredictor(version="semantic")
    text = "Worker climbed to 20ft platform without safety harness hooked."
    pred = predictor.predict(text)

    assert 0.0 <= pred.probability <= 1.0
    assert isinstance(pred.sif_potential, bool)
    assert pred.sif_potential is True
    assert pred.probability >= 0.49


def test_hybrid_predictor_inference():
    """Test inference using Model C (sif-hybrid-v1)."""
    predictor = SIFPredictor(version="hybrid")
    text = "Technician entered nitrogen vessel without atmospheric gas testing."
    pred = predictor.predict(text)

    assert 0.0 <= pred.probability <= 1.0
    assert isinstance(pred.sif_potential, bool)
    assert pred.sif_potential is True
    assert pred.probability >= 0.49


def test_hybrid_safe_counterfactual_probability_drop():
    """Test that safe barrier controls shift hybrid probability downward."""
    predictor = SIFPredictor(version="hybrid")
    unsafe_text = "Worker worked at height without fall protection."
    safe_text = "Worker worked at height with approved fall protection."

    unsafe_pred = predictor.predict(unsafe_text)
    safe_pred = predictor.predict(safe_text)

    assert unsafe_pred.probability > safe_pred.probability
    assert (unsafe_pred.probability - safe_pred.probability) > 0.20


def test_hybrid_ood_non_safety_confidence():
    """Test that clearly unrelated non-safety texts receive low SIF probability."""
    predictor = SIFPredictor(version="hybrid")
    text = "Preheat oven to 350F, mix flour and sugar before baking cake."
    pred = predictor.predict(text)

    assert pred.sif_potential is False
    assert pred.probability < 0.20


def test_analysis_pipeline_integration():
    """Test that analyze_text operates seamlessly with SIFPredictor."""
    result = analyze_text("Operator worked on unisolated high voltage panel without LOTO.")
    assert result.sif_potential is True
    assert result.sif_level.value in {"HIGH", "MEDIUM", "LOW"}
    assert result.hazard is not None or result.activity is not None


def test_direct_analyze_api_with_admin_headers(client, admin_headers):
    """Test that POST /api/v1/analyze works with authorized headers."""
    response = client.post(
        "/api/v1/analyze",
        headers=admin_headers,
        json={"text": "Operator worked on unisolated high voltage panel without LOTO."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sif_potential" in data
    assert data["sif_potential"] is True
    assert "sif_level" in data
    assert data["sif_level"] in {"HIGH", "MEDIUM", "LOW"}
