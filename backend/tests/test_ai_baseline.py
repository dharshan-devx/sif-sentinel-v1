"""Phase 1 — AI/NLP Baseline Regression Tests.

These tests verify the CURRENT behaviour of the existing NLP pipeline.
They capture the baseline so that future improvements can be measured against it.
They do NOT encode ideal behaviour; they encode actual observed behaviour.
"""

import os
import sys

import pytest

# Ensure environment variables are set before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_baseline.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-that-is-long-enough")

from app.core.constants import BarrierStatus, SIFLevel
from app.ml.inference.predictor import SIFPredictor, level_for_probability
from app.services.nlp.analysis_pipeline import PipelineResult, analyze_text
from app.services.nlp.entity_extractor import ExtractedEntities, extract_entities
from app.services.nlp.evidence_extractor import Evidence, extract_evidence
from app.services.nlp.preprocessing import PreprocessedText, preprocess_text


@pytest.fixture(autouse=True)
def force_v1_baseline_env(monkeypatch):
    monkeypatch.setenv("SIF_MODEL_VERSION", "v1")


# ---------------------------------------------------------------------------
# 1. Model loading & inference
# ---------------------------------------------------------------------------

class TestModelLoading:
    """Verify model artifacts can be loaded and produce predictions."""

    def test_predictor_loads_without_error(self):
        predictor = SIFPredictor()
        result = predictor.predict("test input text for loading")
        assert result is not None
        assert isinstance(result.probability, float)

    def test_predictor_metadata_available(self):
        predictor = SIFPredictor()
        metadata = predictor.metadata()
        assert metadata["model_name"] == "sif-tfidf-logreg"
        assert metadata["model_version"] == "sif-tfidf-logreg-v1"
        assert "metrics" in metadata
        assert "class_labels" in metadata
        assert "NON_SIF" in metadata["class_labels"]
        assert "SIF" in metadata["class_labels"]

    def test_predictor_returns_predictive_terms(self):
        predictor = SIFPredictor()
        result = predictor.predict("Worker fell from scaffold without harness")
        assert isinstance(result.predictive_terms, list)


# ---------------------------------------------------------------------------
# 2. SIF classification — obvious cases
# ---------------------------------------------------------------------------

class TestSIFClassification:
    """Verify the classifier produces directionally correct outputs on clear cases."""

    def test_obvious_sif_report(self):
        """A report with clear barrier failure language should classify as SIF."""
        result = analyze_text(
            "The required fall protection was not used while working at height."
        )
        assert result.sif_potential is True
        assert result.sif_probability > 0.5

    def test_obvious_non_sif_report(self):
        """A routine office report should not classify as SIF."""
        result = analyze_text(
            "Routine office paperwork was completed during the morning shift."
        )
        assert result.sif_potential is False
        assert result.sif_probability < 0.5

    def test_barrier_failure_high_probability(self):
        """Explicit barrier failure language from training templates should score high."""
        result = analyze_text(
            "Technician started maintenance on the pump before energy isolation was verified."
        )
        assert result.sif_potential is True
        assert result.sif_probability > 0.7


# ---------------------------------------------------------------------------
# 3. Probability level mapping
# ---------------------------------------------------------------------------

class TestLevelMapping:
    """Verify the probability-to-SIFLevel mapping function."""

    def test_high_level(self):
        assert level_for_probability(0.80) == SIFLevel.HIGH

    def test_medium_level(self):
        assert level_for_probability(0.65) == SIFLevel.MEDIUM

    def test_low_level(self):
        assert level_for_probability(0.57) == SIFLevel.LOW

    def test_review_level(self):
        assert level_for_probability(0.48) == SIFLevel.REVIEW

    def test_non_sif_level(self):
        assert level_for_probability(0.30) == SIFLevel.NON_SIF


# ---------------------------------------------------------------------------
# 4. Preprocessing
# ---------------------------------------------------------------------------

class TestPreprocessing:
    """Verify the text preprocessing pipeline."""

    def test_normalizes_unicode(self):
        doc = preprocess_text("Worker\u2019s harness wasn\u2019t checked")
        assert "\u2019" not in doc.normalized_text

    def test_preserves_original_text(self):
        original = "Test with   extra  spaces"
        doc = preprocess_text(original)
        assert doc.original_text == original

    def test_produces_sentences(self):
        doc = preprocess_text("First sentence. Second sentence. Third sentence.")
        assert len(doc.sentences) >= 2

    def test_produces_tokens(self):
        doc = preprocess_text("Worker fell from scaffold")
        assert len(doc.tokens) >= 3

    def test_lowercases_normalized_text(self):
        doc = preprocess_text("UPPER CASE Text")
        assert doc.normalized_text == doc.normalized_text.lower()


# ---------------------------------------------------------------------------
# 5. Entity extraction
# ---------------------------------------------------------------------------

class TestEntityExtraction:
    """Verify entity extraction identifies activities, hazards, and barriers."""

    def test_extracts_activity_maintenance(self):
        doc = preprocess_text("Technician started maintenance on the pump.")
        entities = extract_entities(doc)
        assert entities.activity == "Maintenance"

    def test_extracts_hazard_stored_energy(self):
        doc = preprocess_text("Energy isolation was not verified before work started.")
        entities = extract_entities(doc)
        assert entities.hazard == "Stored Energy"

    def test_extracts_barrier_energy_isolation(self):
        doc = preprocess_text("The energy isolation procedure was not followed.")
        entities = extract_entities(doc)
        assert entities.barrier == "Energy Isolation"

    def test_barrier_status_failed_on_negation(self):
        doc = preprocess_text(
            "Energy isolation was not verified before maintenance started."
        )
        entities = extract_entities(doc)
        assert entities.barrier_status in (BarrierStatus.FAILED, BarrierStatus.UNKNOWN)

    def test_extracts_fall_hazard(self):
        doc = preprocess_text("Worker was at height without fall protection.")
        entities = extract_entities(doc)
        assert entities.hazard == "Fall Hazard"

    def test_extracts_fall_protection_barrier(self):
        doc = preprocess_text("The harness was not used during work at height.")
        entities = extract_entities(doc)
        assert entities.barrier is not None

    def test_no_entities_for_generic_text(self):
        doc = preprocess_text("General administrative meeting held in office.")
        entities = extract_entities(doc)
        # At least one of these should be None for generic text
        assert entities.activity is None or entities.hazard is None


# ---------------------------------------------------------------------------
# 6. LSR mapping
# ---------------------------------------------------------------------------

class TestLSRMapping:
    """Verify Life-Saving Rule mapping."""

    def test_energy_isolation_lsr(self):
        result = analyze_text(
            "Technician started maintenance on the pump before energy isolation was verified."
        )
        assert result.life_saving_rule == "Energy Isolation"

    def test_working_at_height_lsr(self):
        result = analyze_text(
            "The required fall protection was not used while working at height."
        )
        assert result.life_saving_rule == "Working at Height"

    def test_no_lsr_for_generic_text(self):
        result = analyze_text(
            "The meeting room was booked for the morning training session."
        )
        assert result.life_saving_rule is None


# ---------------------------------------------------------------------------
# 7. Evidence extraction
# ---------------------------------------------------------------------------

class TestEvidenceExtraction:
    """Verify evidence extraction identifies relevant sentence spans."""

    def test_evidence_exists_for_safety_text(self):
        result = analyze_text(
            "Worker entered confined space without gas testing before inspection."
        )
        assert result.evidence_span is not None
        assert len(result.evidence_span) > 0

    def test_evidence_terms_populated(self):
        result = analyze_text(
            "Technician started maintenance before energy isolation was verified."
        )
        assert isinstance(result.evidence_terms, list)
        assert len(result.evidence_terms) > 0


# ---------------------------------------------------------------------------
# 8. Confidence scoring
# ---------------------------------------------------------------------------

class TestConfidenceScoring:
    """Verify confidence scores are within expected bounds."""

    def test_confidence_between_zero_and_one(self):
        result = analyze_text(
            "Worker stood below a suspended load during crane lifting."
        )
        assert 0.0 <= result.overall_confidence <= 1.0

    def test_high_confidence_for_clear_report(self):
        result = analyze_text(
            "Technician started maintenance on the pump before energy isolation was verified."
        )
        assert result.overall_confidence > 0.5

    def test_low_confidence_for_vague_report(self):
        result = analyze_text(
            "Something happened near the equipment area today."
        )
        assert result.overall_confidence < 0.7


# ---------------------------------------------------------------------------
# 9. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Verify safe handling of edge-case inputs."""

    def test_very_short_input(self):
        result = analyze_text("Slip near valve.")
        assert isinstance(result, PipelineResult)
        assert isinstance(result.sif_probability, float)

    def test_unknown_terminology(self):
        """Text with no safety keywords should still produce a valid result."""
        result = analyze_text(
            "The quantum flux capacitor experienced a minor calibration deviation."
        )
        assert isinstance(result, PipelineResult)
        assert result.sif_potential is False or result.sif_potential is True  # valid bool

    def test_multiple_safety_signals(self):
        """Text with multiple hazards and barriers."""
        result = analyze_text(
            "During hot work near the pressurized pipeline, the fire watch was not present "
            "and the lockout tagout was not performed before the welder started cutting."
        )
        assert isinstance(result, PipelineResult)
        assert result.activity is not None or result.hazard is not None

    def test_pipeline_returns_all_required_fields(self):
        result = analyze_text(
            "Worker fell from scaffold without harness at construction site."
        )
        # Verify all expected fields exist in PipelineResult
        assert hasattr(result, "sif_potential")
        assert hasattr(result, "sif_level")
        assert hasattr(result, "sif_probability")
        assert hasattr(result, "activity")
        assert hasattr(result, "hazard")
        assert hasattr(result, "barrier")
        assert hasattr(result, "barrier_status")
        assert hasattr(result, "barrier_failure")
        assert hasattr(result, "life_saving_rule")
        assert hasattr(result, "rule_confidence")
        assert hasattr(result, "evidence_span")
        assert hasattr(result, "overall_confidence")
        assert hasattr(result, "review_required")
        assert hasattr(result, "model_version")
        assert hasattr(result, "explanation")
        assert hasattr(result, "precursor_candidates")
        assert hasattr(result, "risk")

    def test_review_required_for_low_confidence(self):
        """Vague reports should trigger review requirement."""
        result = analyze_text(
            "The worker approached the equipment and observed the area before beginning work."
        )
        assert result.review_required is True

    def test_explanation_is_nonempty_string(self):
        result = analyze_text(
            "Technician started maintenance before energy isolation was verified."
        )
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 10

    def test_risk_dict_has_expected_keys(self):
        result = analyze_text(
            "Worker fell from scaffold without harness at construction site."
        )
        assert isinstance(result.risk, dict)
        assert "score" in result.risk
        assert "priority" in result.risk
