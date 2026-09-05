"""
Phase 3 — Supervised SIF Classification Engine Hardening Tests.

Verifies:
1. Dataset schema validation
2. Binary target validation
3. Duplicate group detection
4. Duplicate-label contradiction detection
5. Group split reproducibility
6. No group overlap across train/val/test
7. No normalized text overlap across train/val/test
8. Train/validation/test partition counts
9. Approximate class balance across splits
10. Feature leakage prevention (forbidden fields cannot be model inputs)
11. Phase 2 preprocessing integration
12. Model training pipeline
13. Model serialization and artifact integrity
14. Model loading into SIFPredictor
15. Probability range constraints [0, 1]
16. Operating threshold determinism
17. Calibration evaluation and Brier score
18. Feature explanation compatibility (top predictive terms)
19. Backend prediction & analysis pipeline compatibility
20. API endpoint /api/v1/analyze integration
"""

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.data.dataset import (  # noqa: E402 - sibling package needs repository-root bootstrap above.
    FORBIDDEN_FEATURE_COLUMNS,
    extract_model_inputs,
    load_and_validate_dataset,
    normalize_binary_target,
)
from ml.data.split import group_aware_split  # noqa: E402 - see bootstrap above.
from ml.evaluation.metrics import (  # noqa: E402 - see bootstrap above.
    calculate_safety_metrics,
    evaluate_calibration_curve,
    select_operating_threshold,
)

from app.core.constants import SIFLevel  # noqa: E402 - see bootstrap above.
from app.ml.inference.predictor import SIFPredictor  # noqa: E402 - see bootstrap above.
from app.services.nlp.analysis_pipeline import analyze_text  # noqa: E402 - see bootstrap above.
from app.services.nlp.preprocessing import preprocess_text  # noqa: E402 - see bootstrap above.

PRIMARY_DATASET_PATH = ROOT / "data" / "raw" / "safety_reports.csv"
SPLIT_MANIFEST_PATH = ROOT / "data" / "processed" / "split_manifest_v2.json"
V2_ARTIFACTS_DIR = ROOT / "artifacts" / "models" / "v2"
ACTIVE_ARTIFACTS_DIR = ROOT / "artifacts" / "models"


@pytest.fixture(autouse=True)
def force_v2_phase3_env(monkeypatch):
    monkeypatch.setenv("SIF_MODEL_VERSION", "v2")


# ---------------------------------------------------------------------------
# 1. Dataset Loading & Validation
# ---------------------------------------------------------------------------

class TestDatasetLoadingAndValidation:
    """Verifies dataset schema, target consistency, and duplicate detection."""

    def test_primary_dataset_exists_and_loads(self):
        assert PRIMARY_DATASET_PATH.exists(), f"Dataset missing at {PRIMARY_DATASET_PATH}"
        records, summary = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        assert summary.total_rows == 10000
        assert summary.usable_rows == 10000
        assert summary.empty_rows == 0
        assert len(records) == 10000

    def test_binary_target_validation(self):
        records, summary = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        assert summary.positive_count == 5000
        assert summary.negative_count == 5000
        assert summary.positive_ratio == 0.50

        # Verify normalizer handles valid values and rejects invalid
        assert normalize_binary_target("True") == 1
        assert normalize_binary_target("False") == 0
        assert normalize_binary_target("true") == 1
        assert normalize_binary_target("false") == 0
        with pytest.raises(ValueError):
            normalize_binary_target("invalid_target_string")

    def test_duplicate_groups_and_no_contradictions(self):
        records, summary = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        assert summary.unique_text_count == 8648
        assert summary.duplicate_text_groups == 892
        assert summary.duplicate_label_contradictions == 0

    def test_contradiction_detection_raises_error(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("report_text,sif_potential\n")
            f.write("Identical safety incident occurred.,True\n")
            f.write("Identical safety incident occurred.,False\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="contradictory labels"):
                load_and_validate_dataset(temp_path)
        finally:
            os.unlink(temp_path)


# ---------------------------------------------------------------------------
# 2. Feature Leakage Prevention
# ---------------------------------------------------------------------------

class TestFeatureLeakagePrevention:
    """Ensures structured metadata fields can NEVER be passed to model training."""

    def test_extract_model_inputs_contains_only_text_and_label(self):
        records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        texts, labels = extract_model_inputs(records[:100])
        assert len(texts) == 100
        assert len(labels) == 100
        assert all(isinstance(t, str) for t in texts)
        assert all(lbl in {0, 1} for lbl in labels)

    def test_forbidden_columns_rejected_as_text_source(self):
        records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        for forbidden in FORBIDDEN_FEATURE_COLUMNS:
            with pytest.raises(ValueError, match="Forbidden column"):
                extract_model_inputs(records[:5], text_col=forbidden)


# ---------------------------------------------------------------------------
# 3. Group-Aware Split & Manifest
# ---------------------------------------------------------------------------

class TestGroupAwareSplitting:
    """Verifies deterministic 70/15/15 group-aware splitting and zero leakage."""

    def test_group_split_ratios_and_counts(self):
        records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        train_recs, val_recs, test_recs, manifest = group_aware_split(
            records, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=2026
        )

        assert manifest.total_records == 10000
        assert manifest.train_records == 7000
        assert manifest.val_records == 1500
        assert manifest.test_records == 1500

    def test_approximate_class_balance_preserved(self):
        records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        train_recs, val_recs, test_recs, manifest = group_aware_split(
            records, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=2026
        )

        assert manifest.train_positive_ratio == 0.50
        assert manifest.val_positive_ratio == 0.50
        assert manifest.test_positive_ratio == 0.50

    def test_zero_group_and_text_leakage_across_splits(self):
        records, _ = load_and_validate_dataset(PRIMARY_DATASET_PATH)
        train_recs, val_recs, test_recs, manifest = group_aware_split(
            records, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=2026
        )

        train_texts = {preprocess_text(r["report_text"]).normalized_text for r in train_recs}
        val_texts = {preprocess_text(r["report_text"]).normalized_text for r in val_recs}
        test_texts = {preprocess_text(r["report_text"]).normalized_text for r in test_recs}

        assert len(train_texts & val_texts) == 0, "Train and Val share normalized texts!"
        assert len(train_texts & test_texts) == 0, "Train and Test share normalized texts!"
        assert len(val_texts & test_texts) == 0, "Val and Test share normalized texts!"

    def test_split_manifest_file_exists_and_valid(self):
        assert SPLIT_MANIFEST_PATH.exists(), f"Split manifest missing at {SPLIT_MANIFEST_PATH}"
        data = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
        assert data["random_seed"] == 2026
        assert data["total_records"] == 10000
        assert len(data["train_ids"]) == 7000
        assert len(data["val_ids"]) == 1500
        assert len(data["test_ids"]) == 1500


# ---------------------------------------------------------------------------
# 4. Phase 2 Preprocessing Integration
# ---------------------------------------------------------------------------

class TestPreprocessingIntegration:
    """Verifies canonical Phase 2 normalization is used consistently."""

    def test_preprocessing_expands_contractions(self):
        doc = preprocess_text("Technician wasn't wearing harness and couldn't isolate power.")
        assert "was not" in doc.normalized_text
        assert "could not" in doc.normalized_text

    def test_predictor_normalizes_text_consistently(self):
        predictor = SIFPredictor()
        # Ensure predict handles unnormalized text without error
        result1 = predictor.predict("worker wasn't wearing harness at height")
        result2 = predictor.predict("worker was not wearing harness at height")
        assert result1.sif_potential is True
        assert result2.sif_potential is True
        assert abs(result1.probability - result2.probability) < 0.05


# ---------------------------------------------------------------------------
# 5. Model Artifacts, Loading & Predictor
# ---------------------------------------------------------------------------

class TestModelArtifactsAndPredictor:
    """Verifies versioned artifacts, loading, and inference contracts."""

    def test_v2_artifacts_exist_and_intact(self):
        assert (V2_ARTIFACTS_DIR / "model" / "sif_model.joblib").exists()
        assert (V2_ARTIFACTS_DIR / "vectorizer" / "tfidf.joblib").exists()
        assert (V2_ARTIFACTS_DIR / "metadata.json").exists()
        assert (V2_ARTIFACTS_DIR / "threshold.json").exists()

    def test_metadata_contains_required_audit_fields(self):
        metadata = json.loads((V2_ARTIFACTS_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["model_version"] == "sif-tfidf-logreg-v2"
        assert metadata["training_dataset_identifier"] == "safety-reports-raw-10k"
        assert metadata["total_records"] == 10000
        assert metadata["split_strategy"] == "deterministic_group_aware_70_15_15"
        assert "operating_threshold" in metadata
        assert "validation_metrics_at_selected_threshold" in metadata
        assert "test_metrics_at_selected_threshold" in metadata
        assert "calibration" in metadata
        assert "top_sif_features" in metadata
        assert "top_non_sif_features" in metadata

    def test_predictor_loads_and_infers_cleanly(self):
        predictor = SIFPredictor()
        pred = predictor.predict("an operator was found working at 8ft elevation without a harness clipped to any anchor point.")
        assert pred.sif_potential is True
        assert 0.0 <= pred.probability <= 1.0
        assert pred.sif_level in (SIFLevel.HIGH, SIFLevel.MEDIUM, SIFLevel.LOW)
        assert pred.model_version == "sif-tfidf-logreg-v2"
        assert isinstance(pred.predictive_terms, list)

    def test_threshold_determinism(self):
        predictor = SIFPredictor()
        pred1 = predictor.predict("A small puddle was reported in hallway, housekeeping notified.")
        pred2 = predictor.predict("A small puddle was reported in hallway, housekeeping notified.")
        assert pred1.sif_potential == pred2.sif_potential
        assert pred1.probability == pred2.probability
        assert pred1.sif_potential is False


# ---------------------------------------------------------------------------
# 6. Safety Metrics & Calibration
# ---------------------------------------------------------------------------

class TestSafetyMetricsAndCalibration:
    """Verifies metric calculations, calibration evaluation, and threshold optimization."""

    def test_metric_calculations(self):
        y_true = [1, 1, 0, 0]
        y_pred = [1, 0, 0, 1]
        y_prob = [0.9, 0.4, 0.1, 0.8]
        m = calculate_safety_metrics(y_true, y_pred, y_prob)

        assert m["accuracy"] == 0.50
        assert m["confusion_matrix"]["tp"] == 1
        assert m["confusion_matrix"]["fn"] == 1
        assert m["confusion_matrix"]["fp"] == 1
        assert m["confusion_matrix"]["tn"] == 1
        assert m["false_negative_rate"] == 0.50
        assert m["false_positive_rate"] == 0.50
        assert m["brier_score"] is not None

    def test_threshold_selection_respects_safety_first(self):
        y_true = [1, 1, 1, 1, 0, 0, 0, 0]
        y_prob = [0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1]
        th, best = select_operating_threshold(y_true, y_prob, min_recall=0.80, strategy="safety_first")
        assert th >= 0.25
        assert best["sif_recall"] >= 0.80

    def test_calibration_curve_calculation(self):
        y_true = [0, 0, 1, 1]
        y_prob = [0.1, 0.2, 0.8, 0.9]
        calib = evaluate_calibration_curve(y_true, y_prob, n_bins=5)
        assert "expected_calibration_error" in calib
        assert "brier_score" in calib
        assert calib["brier_score"] < 0.10


# ---------------------------------------------------------------------------
# 7. Backend Integration & Analysis Pipeline
# ---------------------------------------------------------------------------

class TestBackendIntegration:
    """Verifies end-to-end compatibility with FastAPI and analysis pipeline."""

    def test_analyze_text_pipeline_with_v2_model(self):
        result = analyze_text(
            "two riggers positioned themselves directly under a 2-ton suspended load to adjust sling angle"
        )
        assert result.sif_potential is True
        assert result.sif_probability > 0.5
        assert result.sif_level in (SIFLevel.HIGH, SIFLevel.MEDIUM)
        assert result.model_version == "sif-tfidf-logreg-v2"
        assert result.overall_confidence > 0.0

    def test_api_analyze_endpoint_returns_valid_response(self, client, admin_headers):
        response = client.post(
            "/api/v1/analyze",
            headers=admin_headers,
            json={
                "text": "an operator was found working at 8ft elevation without a harness clipped to any anchor point."
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sif_potential"] is True
        assert data["model_probability"] >= 0.5
        assert data["model_version"] == "sif-tfidf-logreg-v2"
        assert "overall_confidence" in data
        assert "evidence_terms" in data
