"""
Unit and Integration Tests for SIF Sentinel Phase 5D Counterfactual Reasoning Engine.
"""

import copy
import pytest
from app.core.constants import BarrierStatus, SIFLevel
from app.services.nlp.causal_engine import ControlStatus, SafetyCausalReasoningEngine
from app.services.nlp.counterfactual_engine import (
    CounterfactualChange,
    CounterfactualSafetyEngine,
    CounterfactualScenario,
)
from app.services.nlp.preprocessing import preprocess_text
from app.services.nlp.evidence_model import StructuredEvidence, EvidenceItem, EvidenceType


@pytest.fixture
def confined_space_graph():
    raw_text = "Worker entered nitrogen purge vessel without atmospheric gas testing or permit."
    prep = preprocess_text(raw_text)
    ev = StructuredEvidence(
        items=[
            EvidenceItem(EvidenceType.ACTIVITY, "Confined Space Work", "entered nitrogen purge vessel", False, None, None, 1.0, "EXACT"),
            EvidenceItem(EvidenceType.HAZARD, "Toxic Atmosphere", "nitrogen purge vessel", False, None, None, 0.9, "EXACT"),
            EvidenceItem(EvidenceType.CONTROL, "Gas Testing", "without atmospheric gas testing", True, "not performed", None, 0.95, "EXACT"),
        ]
    )
    return SafetyCausalReasoningEngine.evaluate_causal_safety(prep, ev, 0.95)


@pytest.fixture
def height_work_graph():
    raw_text = "Rigger climbed monkey board on derrick without safety harness or fall arrest system."
    prep = preprocess_text(raw_text)
    ev = StructuredEvidence(
        items=[
            EvidenceItem(EvidenceType.ACTIVITY, "Work at Height", "climbed monkey board", False, None, None, 1.0, "EXACT"),
            EvidenceItem(EvidenceType.CONTROL, "Fall Protection", "without safety harness", True, "missing", None, 0.95, "EXACT"),
        ]
    )
    return SafetyCausalReasoningEngine.evaluate_causal_safety(prep, ev, 0.96)


@pytest.fixture
def loto_unverified_graph():
    raw_text = "Technician opened high pressure valve before energy isolation was verified."
    prep = preprocess_text(raw_text)
    ev = StructuredEvidence(
        items=[
            EvidenceItem(EvidenceType.ACTIVITY, "Maintenance", "opened high pressure valve", False, None, None, 1.0, "EXACT"),
            EvidenceItem(EvidenceType.HAZARD, "Pressure", "high pressure valve", False, None, None, 0.9, "EXACT"),
            EvidenceItem(EvidenceType.CONTROL, "Energy Isolation", "energy isolation was verified", False, "verified", "before", 0.95, "EXACT"),
        ]
    )
    return SafetyCausalReasoningEngine.evaluate_causal_safety(prep, ev, 0.94)


def test_simulate_not_performed_to_performed(confined_space_graph):
    orig_dict = copy.deepcopy(confined_space_graph.to_dict())
    scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
        original_graph=confined_space_graph,
        target_control="Gas Testing",
        simulated_status=ControlStatus.PERFORMED,
        original_risk_score=85,
    )

    assert scenario.target_control == "Gas Testing"
    assert scenario.original_status in ("NOT_PERFORMED", "MISSING")
    assert scenario.simulated_status == "PERFORMED"
    assert scenario.original_barrier_failure is True
    assert scenario.simulated_barrier_failure is False
    assert scenario.simulated_exposure == "CONTROLLED_ACTIVITY"
    assert scenario.simulated_risk_score < scenario.original_risk_score
    assert scenario.risk_delta < 0
    assert scenario.risk_direction == "REDUCED"
    assert scenario.simulation_only is True
    assert len(scenario.assumptions) >= 3

    # Verify immutability of original graph
    assert confined_space_graph.to_dict() == orig_dict


def test_simulate_not_verified_to_verified(loto_unverified_graph):
    scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
        original_graph=loto_unverified_graph,
        target_control="Energy Isolation",
        simulated_status=ControlStatus.VERIFIED,
        original_risk_score=80,
    )

    assert scenario.target_control == "Energy Isolation"
    assert scenario.simulated_status == "VERIFIED"
    assert scenario.simulated_barrier_failure is False
    assert scenario.simulated_sif_potential is False
    assert scenario.risk_delta < 0
    assert "Energy Isolation" in scenario.interpretation


def test_simulate_missing_to_performed(height_work_graph):
    scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
        original_graph=height_work_graph,
        target_control="Fall Protection",
        simulated_status=ControlStatus.PERFORMED,
        original_risk_score=88,
    )

    assert scenario.target_control == "Fall Protection"
    assert scenario.simulated_status == "PERFORMED"
    assert scenario.simulated_barrier_failure is False
    assert scenario.simulated_exposure == "CONTROLLED_ACTIVITY"
    assert scenario.simulated_sif_classification == "NON_SIF"
    assert scenario.risk_delta <= -20


def test_simulate_failed_and_bypassed_controls():
    # Construct a graph with bypassed interlock
    graph = {
        "nodes": [
            {"id": "c1", "type": "CONTROL", "label": "Interlock"},
            {"id": "s1", "type": "STATUS", "label": "BYPASSED"},
            {"id": "e1", "type": "EXPOSURE", "label": "UNMITIGATED_HAZARD"},
        ],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Operations",
                "hazard": "Moving Machinery",
                "control": "Interlock",
                "control_status": "BYPASSED",
                "barrier_failure": True,
                "exposure": "UNMITIGATED_HAZARD",
                "sif_precursor_type": "CONTROL_DEGRADATION",
                "confidence": 0.95,
                "evidence": [],
            }
        ],
        "barrier_failure_detected": True,
        "high_energy_hazard_present": False,
    }

    scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
        original_graph=graph,
        target_control="Interlock",
        simulated_status=ControlStatus.VERIFIED,
        original_risk_score=75,
    )

    assert scenario.original_status == "BYPASSED"
    assert scenario.simulated_status == "VERIFIED"
    assert scenario.simulated_barrier_failure is False
    assert scenario.risk_delta < 0


def test_simulation_rejects_invalid_target_control(confined_space_graph):
    with pytest.raises(ValueError, match="does not exist in the causal graph"):
        CounterfactualSafetyEngine.simulate_barrier_restoration(
            original_graph=confined_space_graph,
            target_control="NonExistentControlXYZ",
            simulated_status=ControlStatus.VERIFIED,
        )


def test_causal_changes_and_grounded_assumptions(confined_space_graph):
    scenario = CounterfactualSafetyEngine.simulate_barrier_restoration(
        original_graph=confined_space_graph,
        target_control="Gas Testing",
        simulated_status=ControlStatus.VERIFIED,
    )

    change_types = [c.element_type for c in scenario.causal_changes]
    assert "CONTROL_STATUS" in change_types
    assert "BARRIER_FAILURE" in change_types
    assert "EXPOSURE" in change_types
    assert "RISK" in change_types

    # Ensure explicit simulation assumptions
    assert any("assumed to be fully verified" in a for a in scenario.assumptions)
    assert any("counterfactual simulation" in a for a in scenario.assumptions)
    assert scenario.simulation_only is True


def test_counterfactual_api_endpoint(client, admin_headers, confined_space_graph):
    headers = admin_headers
    payload = {
        "target_control": "Gas Testing",
        "simulated_status": "VERIFIED",
        "safety_graph": confined_space_graph.to_dict(),
        "risk_score": 85,
    }

    res = client.post("/api/v1/analyze/counterfactual", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["target_control"] == "Gas Testing"
    assert data["simulated_status"] == "VERIFIED"
    assert data["simulated_barrier_failure"] is False
    assert data["risk_delta"] < 0
    assert data["simulation_only"] is True


def test_counterfactual_api_with_raw_text(client, admin_headers):
    headers = admin_headers
    payload = {
        "report_text": "Worker entered nitrogen vessel without gas testing.",
        "target_control": "Gas Testing",
        "simulated_status": "VERIFIED",
    }

    res = client.post("/api/v1/analyze/counterfactual", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["target_control"] == "Gas Testing"
    assert data["simulated_status"] == "VERIFIED"
    assert data["risk_delta"] < 0

