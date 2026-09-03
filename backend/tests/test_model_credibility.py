import hashlib
import json
from pathlib import Path

import sklearn

from app.ml.inference.predictor import ARTIFACT_DIR, SIFPredictor

DATASET = Path(__file__).parents[2] / "data" / "processed" / "safety_reports_v1.csv"
from app.services.nlp.confidence import overall_confidence


def test_model_predictive_terms():
    """Ensure the model extracts top terms that drive the prediction."""
    predictor = SIFPredictor()
    text = "Worker entered confined space without gas testing before inspection."
    prediction = predictor.predict(text)
    
    assert prediction.probability > 0.5
    assert len(prediction.predictive_terms) > 0
    # 'confined space' or similar should be a top term
    assert any("confined" in term or "space" in term or "without" in term for term in prediction.predictive_terms)


def test_model_reproducibility():
    """Ensure prediction is completely deterministic for the same input."""
    predictor = SIFPredictor()
    text = "Technician started maintenance on the pump before energy isolation was verified."
    
    pred1 = predictor.predict(text)
    pred2 = predictor.predict(text)
    
    assert pred1.probability == pred2.probability
    assert pred1.predictive_terms == pred2.predictive_terms


def test_dataset_hash_and_runtime_provenance_match_training_input():
    """The committed artifact must identify its exact versioned training source."""
    metadata_path = ARTIFACT_DIR / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    canonical_source = DATASET.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    assert metadata["dataset_hash"] == hashlib.sha256(canonical_source).hexdigest()
    assert metadata["scikit_learn_version"] == sklearn.__version__


def test_overall_confidence_boundaries():
    """Ensure heuristic confidence score stays bound between 0 and 1."""
    # Test maximum possible inputs
    score_max = overall_confidence(1.0, 1.0, 1.0, 1.0)
    assert score_max == 1.0
    
    # Test minimum possible inputs
    score_min = overall_confidence(0.0, 0.0, 0.0, 0.0)
    assert score_min == 0.0
    
    # Test standard inputs
    score_mid = overall_confidence(0.5, 0.5, 0.5, 0.5)
    assert 0.0 < score_mid < 1.0
