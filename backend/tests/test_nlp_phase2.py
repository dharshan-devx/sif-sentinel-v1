"""Phase 2 — Safety-Aware NLP Preprocessing & Entity/Barrier Intelligence Unit Tests.

Comprehensive unit tests covering:
1. Safety-aware normalization & contraction expansion
2. Robust sentence segmentation (protecting abbreviations, decimals, bullets)
3. Taxonomy canonical concepts & alias/synonym matching
4. Conservative fuzzy matching (RapidFuzz)
5. Negation detection & positive vs negative distinction
6. Temporal context & inversion analysis
7. Activity, hazard, and barrier extraction
8. Barrier status & failure reason extraction
9. Multiple entity tracking
10. Evidence extraction & LSR mapping compatibility
"""

import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test_phase2.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-that-is-long-enough")

from app.core.constants import BarrierStatus
from app.services.nlp.analysis_pipeline import analyze_text
from app.services.nlp.entity_extractor import extract_entities, _fuzzy_match_phrase
from app.services.nlp.evidence_model import EvidenceType
from app.services.nlp.preprocessing import preprocess_text, split_sentences


# ---------------------------------------------------------------------------
# 1. Safety-Aware Normalization Tests
# ---------------------------------------------------------------------------

class TestSafetyAwareNormalization:
    """Verify normalization preserves original text, expands contractions, and cleans formatting."""

    def test_unicode_and_smart_quotes(self):
        text = "Worker\u2019s harness wasn\u2019t \u201cinspected\u201d before work."
        doc = preprocess_text(text)
        assert doc.original_text == text
        assert "was not" in doc.normalized_text
        assert "'" in doc.normalized_text or '"' in doc.normalized_text

    def test_contraction_expansion(self):
        text = "Gas test wasn't done and worker couldn't find permit."
        doc = preprocess_text(text)
        assert "was not" in doc.normalized_text
        assert "could not" in doc.normalized_text

    def test_whitespace_and_newlines_collapse_in_normalized(self):
        text = "Line break here.\n\nAnother line   with   extra spaces."
        doc = preprocess_text(text)
        assert "\n" not in doc.normalized_text
        assert "   " not in doc.normalized_text

    def test_preserves_safety_critical_words(self):
        safety_words = ["not", "no", "never", "without", "before", "after", "during", "failed", "bypassed"]
        text = "Worker entered without harness before testing; did not follow procedure."
        doc = preprocess_text(text)
        for word in safety_words:
            if word in text.lower():
                assert word in doc.tokens or word in doc.normalized_text

    def test_preserves_technical_identifiers_and_decimals(self):
        text = "Pump P-101.A pressure was 15.5 bar."
        doc = preprocess_text(text)
        assert "p-101" in doc.normalized_text
        assert "15.5" in doc.normalized_text or "15" in doc.normalized_text


# ---------------------------------------------------------------------------
# 2. Robust Sentence Segmentation Tests
# ---------------------------------------------------------------------------

class TestSentenceSegmentation:
    """Verify sentence segmentation protects abbreviations, decimals, and splits on clauses."""

    def test_normal_sentences(self):
        text = "First observation noted. Second observation followed. Third concluded."
        sentences = split_sentences(text)
        assert len(sentences) == 3

    def test_abbreviation_protection(self):
        text = "Technician checked pump at approx. 10m height. Area was clean."
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert "approx." in sentences[0]

    def test_decimal_number_protection(self):
        text = "Scaffold was 10.5m above ground. Wind was 3.2 m/s."
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert "10.5m" in sentences[0]

    def test_bullet_point_cleanup(self):
        text = "- Hazard observed near valve.\n* Barrier was missing.\n1. Supervisor notified."
        sentences = split_sentences(text)
        assert len(sentences) == 3
        assert not sentences[0].startswith("- ")
        assert not sentences[1].startswith("* ")
        assert not sentences[2].startswith("1. ")

    def test_semicolon_clause_split(self):
        text = "Isolation was not verified; technician proceeded with pump repair."
        sentences = split_sentences(text)
        assert len(sentences) == 2


# ---------------------------------------------------------------------------
# 3. Alias and Synonym Matching Tests
# ---------------------------------------------------------------------------

class TestAliasAndSynonymMatching:
    """Verify canonical concept resolution through rich aliases and synonyms."""

    def test_confined_space_aliases(self):
        for phrase in ["entered the vessel", "tank entry", "entry into vessel"]:
            doc = preprocess_text(f"Technician engaged in {phrase} yesterday.")
            entities = extract_entities(doc)
            assert entities.activity == "Confined Space Work"

    def test_energy_isolation_aliases(self):
        for phrase in ["isolation of energy", "zero energy state", "mechanical isolation"]:
            doc = preprocess_text(f"Worker checked the {phrase} before repair.")
            entities = extract_entities(doc)
            assert entities.barrier == "Energy Isolation"

    def test_gas_testing_aliases(self):
        for phrase in ["atmospheric verification", "gas monitoring", "multigas detector"]:
            doc = preprocess_text(f"The crew carried out {phrase} before entry.")
            entities = extract_entities(doc)
            assert entities.barrier == "Gas Testing"

    def test_fall_protection_aliases(self):
        for phrase in ["safety harness", "fall arrest", "tie-off", "lanyard"]:
            doc = preprocess_text(f"Worker inspected the {phrase} at the jobsite.")
            entities = extract_entities(doc)
            assert entities.barrier == "Fall Protection"


# ---------------------------------------------------------------------------
# 4. Conservative Fuzzy Matching Tests
# ---------------------------------------------------------------------------

class TestFuzzyMatching:
    """Verify conservative fuzzy matching for minor typos while rejecting false positives."""

    def test_recognizes_typo_in_long_phrase(self):
        # Typo: 'atmosphric' instead of 'atmospheric'
        assert _fuzzy_match_phrase("atmospheric testing", ["atmosphric", "testing"]) is True

    def test_recognizes_typo_in_loto_procedure(self):
        # Typo: 'loto procedur'
        assert _fuzzy_match_phrase("loto procedure", ["loto", "procedur"]) is True

    def test_rejects_unrelated_short_words(self):
        # 'fire' should not match 'fire watch'
        assert _fuzzy_match_phrase("fire watch", ["fire"]) is False

    def test_fuzzy_matching_extracts_barrier(self):
        doc = preprocess_text("Worker carried out atmosphric testing before entering the tank.")
        entities = extract_entities(doc)
        assert entities.barrier == "Gas Testing"


# ---------------------------------------------------------------------------
# 5. Negation and Positive vs Negative Distinction Tests
# ---------------------------------------------------------------------------

class TestNegationAndVerification:
    """Verify differentiation between verified controls and safety failures."""

    def test_positive_fall_protection_is_effective(self):
        res = analyze_text("Worker used fall protection while working at height.")
        assert res.barrier == "Fall Protection"
        assert res.barrier_status == "EFFECTIVE"
        assert res.barrier_failure is None

    def test_negative_fall_protection_is_failed(self):
        res = analyze_text("Worker did not use fall protection while working at height.")
        assert res.barrier == "Fall Protection"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "not performed"

    def test_positive_isolation_is_effective(self):
        res = analyze_text("Before maintenance, energy isolation was verified by the supervisor.")
        assert res.barrier == "Energy Isolation"
        assert res.barrier_status == "EFFECTIVE"

    def test_negative_isolation_is_failed(self):
        res = analyze_text("The isolation was installed but was not verified before maintenance started.")
        assert res.barrier == "Energy Isolation"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "not verified"

    def test_without_preposition_negation(self):
        res = analyze_text("Worker entered confined space without gas testing.")
        assert res.barrier == "Gas Testing"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "not performed"

    def test_no_determiner_negation(self):
        res = analyze_text("Welder started hot work with no fire watch present.")
        assert res.barrier == "Fire Watch"
        assert res.barrier_status == "FAILED"


# ---------------------------------------------------------------------------
# 6. Temporal Context & Inversion Tests
# ---------------------------------------------------------------------------

class TestTemporalContext:
    """Verify temporal order distinguishes compliance from safety violations."""

    def test_action_before_verification_is_failure(self):
        # Activity started BEFORE control was completed
        res = analyze_text("Technician entered the vessel before gas testing was completed.")
        assert res.barrier == "Gas Testing"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "not verified"

    def test_verification_before_action_is_effective(self):
        # Control completed BEFORE activity
        res = analyze_text("Gas testing was completed before the technician entered the vessel.")
        assert res.barrier == "Gas Testing"
        assert res.barrier_status == "EFFECTIVE"
        assert res.barrier_failure is None


# ---------------------------------------------------------------------------
# 7. Barrier Status and Failure Reason Extraction Tests
# ---------------------------------------------------------------------------

class TestBarrierStatusAndFailure:
    """Verify extraction of specific failure descriptions (bypassed, expired, etc.)."""

    def test_bypassed_control(self):
        res = analyze_text("The required LOTO procedure was bypassed during maintenance.")
        assert res.barrier == "Lockout Tagout"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "bypassed"

    def test_expired_permit(self):
        res = analyze_text("Hot work proceeded with an expired permit.")
        assert res.barrier == "Permit"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "expired"

    def test_missing_barrier(self):
        res = analyze_text("Guardrail was missing along the elevated walkway.")
        assert res.barrier == "Guardrail"
        assert res.barrier_status == "FAILED"
        assert res.barrier_failure == "missing"


# ---------------------------------------------------------------------------
# 8. Multiple Entities Tracking Tests
# ---------------------------------------------------------------------------

class TestMultipleEntities:
    """Verify extraction of multiple activities, hazards, and barriers in complex reports."""

    def test_multiple_activities_and_barriers(self):
        text = (
            "During maintenance and confined space work, technician entered the vessel "
            "without gas testing and isolation was not verified."
        )
        doc = preprocess_text(text)
        entities = extract_entities(doc)
        assert len(entities.all_activities) >= 2
        assert "Maintenance" in entities.all_activities
        assert "Confined Space Work" in entities.all_activities
        assert len(entities.all_barriers) >= 2
        assert "Gas Testing" in entities.all_barriers
        assert "Energy Isolation" in entities.all_barriers

    def test_primary_barrier_prioritizes_failed_control(self):
        # One control verified, one failed: primary should be the failed one
        text = "Permit was approved, but the required safety harness was not used at height."
        doc = preprocess_text(text)
        entities = extract_entities(doc)
        assert entities.barrier == "Fall Protection"
        assert entities.barrier_status == BarrierStatus.FAILED


# ---------------------------------------------------------------------------
# 9. Evidence and Life-Saving Rule Compatibility Tests
# ---------------------------------------------------------------------------

class TestEvidenceAndLSRCompatibility:
    """Verify evidence spans and LSR mapping are compatible with the enhanced NLP layer."""

    def test_evidence_span_is_from_original_text(self):
        text = "Technician entered the vessel before gas testing was completed."
        res = analyze_text(text)
        assert res.evidence_span is not None
        assert "gas testing was completed" in res.evidence_span

    def test_lsr_confined_space_mapped(self):
        res = analyze_text("Atmospheric verification was not carried out prior to entry.")
        assert res.life_saving_rule == "Confined Space"
        assert res.rule_confidence > 0.3

    def test_lsr_energy_isolation_mapped(self):
        res = analyze_text("The required LOTO procedure was bypassed during maintenance.")
        assert res.life_saving_rule == "Energy Isolation"
        assert res.rule_confidence > 0.3

    def test_lsr_working_at_height_mapped(self):
        res = analyze_text("Worker did not use fall protection while working at height.")
        assert res.life_saving_rule == "Working at Height"
        assert res.rule_confidence > 0.3

    def test_unrelated_text_produces_no_lsr(self):
        res = analyze_text("Routine administrative work was completed in the office.")
        assert res.life_saving_rule is None
        assert res.barrier_status == "UNKNOWN"
