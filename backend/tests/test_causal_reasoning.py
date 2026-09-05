"""
SIF Sentinel — Phase 5B Causal Safety Reasoning Engine Test Suite

Comprehensive tests for:
- Activity -> Hazard relationship inference
- Hazard -> Control mapping
- Control Status classification (VERIFIED, NOT_VERIFIED, PERFORMED, NOT_PERFORMED, FAILED, BYPASSED, MISSING, EXPIRED, UNKNOWN)
- Causal Barrier Failure reasoning
- Temporal Sequencing & Inversion detection
- Advanced Negation, Prevention, and Double-Negation parsing
- Safety Reasoning Graph construction and Evidence Grounding
- End-to-end Pipeline and API integration
"""

from app.services.nlp.analysis_pipeline import analyze_text
from app.services.nlp.causal_engine import (
    HAZARD_TO_CONTROL_MAP,
    ControlStatus,
    SafetyCausalReasoningEngine,
)
from app.services.nlp.entity_extractor import get_structured_evidence
from app.services.nlp.preprocessing import preprocess_text

# ==============================================================================
# 1. ACTIVITY -> HAZARD RELATIONSHIP INFERENCE
# ==============================================================================

def test_activity_to_hazard_inference():
    text = "Operator entered nitrogen tank to perform vessel inspection."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.90)

    assert len(graph.causal_chains) > 0
    primary_chain = graph.causal_chains[0]
    assert primary_chain.activity == "Confined Space Work"
    assert primary_chain.hazard in ("Toxic Atmosphere", "Oxygen Deficiency", "Stored Energy")


def test_work_at_height_hazard_inference():
    text = "Technician worked at height on elevated platform."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.85)

    assert len(graph.causal_chains) > 0
    primary_chain = graph.causal_chains[0]
    assert primary_chain.activity == "Work at Height"
    assert primary_chain.hazard == "Fall Hazard"


# ==============================================================================
# 2. HAZARD -> CONTROL MAPPING
# ==============================================================================

def test_hazard_to_control_mapping_fall_hazard():
    assert "Fall Protection" in HAZARD_TO_CONTROL_MAP["Fall Hazard"]
    assert "Guardrail" in HAZARD_TO_CONTROL_MAP["Fall Hazard"]


def test_hazard_to_control_mapping_toxic_atmosphere():
    assert "Gas Testing" in HAZARD_TO_CONTROL_MAP["Toxic Atmosphere"]
    assert "Permit" in HAZARD_TO_CONTROL_MAP["Toxic Atmosphere"]


def test_hazard_to_control_mapping_stored_energy():
    assert "Energy Isolation" in HAZARD_TO_CONTROL_MAP["Stored Energy"]
    assert "Lockout Tagout" in HAZARD_TO_CONTROL_MAP["Stored Energy"]


# ==============================================================================
# 3. CONTROL STATUS REASONING (9 STATES)
# ==============================================================================

def test_control_status_verified():
    text = "Gas testing was completed and 0% LEL verified prior to welding."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.10)

    assert any(c.control_status == ControlStatus.VERIFIED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is False


def test_control_status_not_verified():
    text = "Energy isolation was not verified before pipe maintenance commenced."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.95)

    assert any(c.control_status == ControlStatus.NOT_VERIFIED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True


def test_control_status_not_performed_without():
    text = "Rigger climbed to 25ft derrick level without safety harness."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.98)

    assert any(c.control_status == ControlStatus.NOT_PERFORMED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True
    assert graph.precursor_detected is True


def test_control_status_bypassed():
    text = "Operator jumpered high-pressure trip safety interlock."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.92)

    assert any(c.control_status == ControlStatus.BYPASSED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True


def test_control_status_missing():
    text = "Scaffold was erected with fall protection missing."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.94)

    assert any(c.control_status == ControlStatus.MISSING for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True


def test_control_status_failed():
    text = "Safety harness lanyard broke and failed under tension."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.97)

    assert any(c.control_status == ControlStatus.FAILED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True


def test_control_status_expired():
    text = "Hot work permit expired at 14:00 but welding continued."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.88)

    assert any(c.control_status == ControlStatus.EXPIRED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is True


# ==============================================================================
# 4. TEMPORAL INVERSION REASONING
# ==============================================================================

def test_temporal_inversion_unsafe():
    text = "Worker entered tank before gas testing was completed."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.95)

    assert graph.barrier_failure_detected is True
    assert any(c.relationship_type == "TEMPORAL_VIOLATION" for c in graph.causal_chains)


def test_temporal_sequencing_safe():
    text = "Gas testing was completed before entry into the vessel."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.05)

    assert graph.barrier_failure_detected is False
    assert any(c.control_status == ControlStatus.VERIFIED for c in graph.causal_chains)


# ==============================================================================
# 5. ADVANCED NEGATION, PREVENTION & DOUBLE NEGATION
# ==============================================================================

def test_prevention_intervention_halts_exposure():
    text = "Safety supervisor prevented worker from entering without safety harness."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.05)

    assert graph.prevented_intervention is True
    assert graph.barrier_failure_detected is False


def test_double_negation_enforces_barrier():
    text = "Fall protection was not missing during scaffold maintenance."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.08)

    assert any(c.control_status == ControlStatus.VERIFIED for c in graph.causal_chains)
    assert graph.barrier_failure_detected is False


# ==============================================================================
# 6. SAFETY REASONING GRAPH & EVIDENCE GROUNDING
# ==============================================================================

def test_safety_graph_structure_and_grounding():
    text = "Fitter opened pressurized line without energy isolation verified."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.96)

    # Check Graph Nodes
    node_types = {n["type"] for n in graph.nodes}
    assert "HAZARD" in node_types
    assert "CONTROL" in node_types
    assert "STATUS" in node_types
    assert "EXPOSURE" in node_types

    # Check Edges
    assert len(graph.edges) >= 3

    # Check Groundings
    assert len(graph.causal_chains) > 0
    groundings = graph.causal_chains[0].evidence_groundings
    assert len(groundings) > 0
    assert groundings[0].evidence_text != ""
    assert groundings[0].match_method != ""
    assert 0.0 <= groundings[0].confidence <= 1.0


# ==============================================================================
# 7. MULTI-DIMENSIONAL CONFIDENCE
# ==============================================================================

def test_reasoning_confidence_components():
    text = "Operator climbed 20ft ladder without fall arrest harness."
    doc = preprocess_text(text)
    evidence = get_structured_evidence(doc)
    graph = SafetyCausalReasoningEngine.evaluate_causal_safety(doc, evidence, 0.99)

    conf = graph.confidence
    assert 0.0 <= conf.model_confidence <= 1.0
    assert 0.0 <= conf.extraction_confidence <= 1.0
    assert 0.0 <= conf.relationship_confidence <= 1.0
    assert 0.0 <= conf.evidence_confidence <= 1.0
    assert 0.0 <= conf.overall_confidence <= 1.0


# ==============================================================================
# 8. END-TO-END PIPELINE INTEGRATION
# ==============================================================================

def test_pipeline_returns_causal_safety_graph():
    text = "Electrician opened 4160V switchgear compartment while bus bar remained energized."
    res = analyze_text(text)

    assert res.safety_graph is not None
    assert "nodes" in res.safety_graph
    assert "edges" in res.safety_graph
    assert "causal_chains" in res.safety_graph
    assert res.causal_chains is not None
    assert len(res.causal_chains) > 0
    assert res.reasoning_summary is not None
    assert "4160V" in text


def test_pipeline_counterfactual_comparison():
    unsafe_text = "Worker worked at height without fall protection."
    safe_text = "Worker worked at height with approved fall protection."

    res_unsafe = analyze_text(unsafe_text)
    res_safe = analyze_text(safe_text)

    # Unsafe should flag barrier failure
    assert res_unsafe.safety_graph["barrier_failure_detected"] is True

    # Safe should verify barrier
    assert res_safe.safety_graph["barrier_failure_detected"] is False
