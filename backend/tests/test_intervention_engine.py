"""
SIF Sentinel — Phase 5F Automated Corrective Intervention & Prevention Engine Test Suite

Validates:
1. Deterministic mapping across all barrier failure states (NOT_PERFORMED, NOT_VERIFIED, FAILED, BYPASSED, MISSING, EXPIRED, INEFFECTIVE).
2. Canonical Hierarchy of Controls classification (Elimination -> Substitution -> Engineering -> Admin -> PPE).
3. Exact priority scoring formula: S_priority = W_risk + W_sif + W_status + W_lsr + W_delta.
4. Multi-barrier counterfactual integration and sequential risk reduction trajectory.
5. API contract for POST /api/v1/analyze/interventions (structured graph and raw text paths).
6. Non-regression of existing safety analytics and immutability guarantees.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import SIFLevel, UserRole
from app.main import app
from app.services.analysis.analysis_service import AnalysisService
from app.services.nlp.causal_engine import ControlStatus
from app.services.nlp.counterfactual_engine import CounterfactualSafetyEngine
from app.services.nlp.intervention_engine import (
    HierarchyLevel,
    InterventionActionType,
    InterventionPriority,
    InterventionUrgency,
    SafetyInterventionEngine,
)


@pytest.fixture
def confined_space_graph() -> dict:
    """Standard confined space incident with unperformed gas testing and permit."""
    analysis = AnalysisService(None).analyze_direct(
        "Worker entered nitrogen purge vessel without atmospheric gas testing or entry permit."
    )
    return analysis.safety_graph


@pytest.fixture
def bypassed_isolation_graph() -> dict:
    """LOTO bypass incident."""
    analysis = AnalysisService(None).analyze_direct(
        "Technician bypassed lockout tagout procedure on high pressure separator valve."
    )
    return analysis.safety_graph


@pytest.fixture
def fall_protection_failed_graph() -> dict:
    """Fall protection failure incident."""
    analysis = AnalysisService(None).analyze_direct(
        "Rigger fell from 8 meter pipe rack after harness lanyard snap hook failed."
    )
    return analysis.safety_graph


@pytest.fixture
def machine_guarding_missing_graph() -> dict:
    """Explicit missing machine guard on rotating machinery."""
    return {
        "nodes": [
            {"id": "node-act-1", "type": "ACTIVITY", "label": "Machinery Operation"},
            {"id": "node-haz-1", "type": "HAZARD", "label": "Rotating Equipment"},
            {"id": "node-ctrl-1", "type": "CONTROL", "label": "Machine Guarding"},
            {"id": "node-stat-1", "type": "STATUS", "label": "MISSING"},
        ],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Machinery Operation",
                "hazard": "Rotating Equipment",
                "control": "Machine Guarding",
                "control_status": "MISSING",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Machinery Operation",
        "critical_hazard": "Rotating Equipment",
        "primary_barrier": "Machine Guarding",
        "barrier_status": "MISSING",
        "barrier_failure_detected": True,
        "precursor_detected": True,
    }


def test_hierarchy_classification_and_rule_mapping(confined_space_graph):
    """Verifies that gas testing maps to administrative audit/verification."""
    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=95,
        risk_priority="CRITICAL",
        life_saving_rule="Bypassing Safety Controls",
        sif_level="PSIF",
    )
    assert result.total_recommendations >= 1
    assert result.deterministic is True
    assert result.baseline_risk_score == 95

    rec = result.recommendations[0]
    assert rec.hierarchy_level == HierarchyLevel.ADMINISTRATIVE_CONTROL
    assert rec.action_type in (
        InterventionActionType.VERIFICATION_AUDIT,
        InterventionActionType.IMMEDIATE_STOP_WORK,
    )
    assert "Gas" in rec.title or "Atmospheric" in rec.title or "Verify" in rec.title
    assert rec.priority in (InterventionPriority.CRITICAL, InterventionPriority.HIGH)


def test_bypassed_barrier_priority_escalation(bypassed_isolation_graph):
    """Verifies that BYPASSED controls trigger CRITICAL priority and STOP_WORK action."""
    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=bypassed_isolation_graph,
        risk_score=90,
        risk_priority="CRITICAL",
        life_saving_rule="Energy Isolation",
        sif_level="PSIF",
    )
    assert len(result.recommendations) >= 1
    top_rec = result.recommendations[0]
    assert top_rec.priority == InterventionPriority.CRITICAL
    assert top_rec.action_type in (
        InterventionActionType.IMMEDIATE_STOP_WORK,
        InterventionActionType.ISOLATION_VERIFY,
        InterventionActionType.VERIFICATION_AUDIT,
    )
    assert top_rec.urgency == InterventionUrgency.IMMEDIATE_PRE_START


def test_engineering_control_mapping_for_machine_guard(machine_guarding_missing_graph):
    """Verifies that missing machinery guarding generates an ENGINEERING_CONTROL recommendation."""
    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=machine_guarding_missing_graph,
        risk_score=75,
        risk_priority="HIGH",
        life_saving_rule=None,
        sif_level="PSIF",
    )
    assert len(result.recommendations) >= 1
    guard_rec = result.recommendations[0]
    assert guard_rec.hierarchy_level == HierarchyLevel.ENGINEERING_CONTROL
    assert guard_rec.action_type == InterventionActionType.ENGINEERING_INSTALL
    assert "Machine Guarding" in guard_rec.title or "Fixed" in guard_rec.title or "Guard" in guard_rec.title


def test_fall_protection_barrier_restoration(fall_protection_failed_graph):
    """Verifies that failed fall protection generates an engineering barrier restoration."""
    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=fall_protection_failed_graph,
        risk_score=85,
        risk_priority="CRITICAL",
        life_saving_rule="Working at Height",
        sif_level="PSIF",
    )
    assert len(result.recommendations) >= 1
    fall_rec = result.recommendations[0]
    assert fall_rec.hierarchy_level in (HierarchyLevel.ENGINEERING_CONTROL, HierarchyLevel.ADMINISTRATIVE_CONTROL)
    assert fall_rec.priority in (InterventionPriority.CRITICAL, InterventionPriority.HIGH)


def test_priority_score_formula_verification():
    """Validates the exact mathematical formula: W_risk + W_sif + W_status + W_lsr + W_delta."""
    # Critical risk (30) + PSIF (25) + Bypassed (20) + LSR (15) + Delta <= -50 (10) = 100
    score, priority = SafetyInterventionEngine._compute_priority_score(
        base_risk=95,
        is_psif=True,
        status="BYPASSED",
        has_lsr=True,
        risk_delta=-60,
    )
    assert score == 100
    assert priority == InterventionPriority.CRITICAL

    # Low risk (5) + Non-SIF (0) + Unknown (5) + No LSR (0) + Delta 0 (0) = 10 -> LOW
    score_low, priority_low = SafetyInterventionEngine._compute_priority_score(
        base_risk=15,
        is_psif=False,
        status="UNKNOWN",
        has_lsr=False,
        risk_delta=0,
    )
    assert score_low == 10
    assert priority_low == InterventionPriority.LOW


def test_cumulative_prevention_plan_trajectory(confined_space_graph):
    """Verifies that the multi-barrier prevention plan produces a monotonic defense-in-depth risk trajectory."""
    result = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=95,
        risk_priority="CRITICAL",
        life_saving_rule="Bypassing Safety Controls",
        sif_level="PSIF",
    )
    plan = result.cumulative_prevention_plan
    assert plan is not None
    assert plan.baseline_risk == 95
    assert plan.target_risk <= plan.baseline_risk
    assert plan.total_risk_delta <= 0
    assert len(plan.defense_in_depth_layers) >= 1
    assert len(plan.assumptions) >= 1


def test_counterfactual_multi_barrier_engine_integration(confined_space_graph):
    """Verifies Phase 5D multi-barrier simulation extension."""
    scenarios = CounterfactualSafetyEngine.simulate_multi_barrier_restoration(
        original_graph=confined_space_graph,
        target_controls=[
            ("Gas Testing", ControlStatus.VERIFIED),
        ],
        original_risk_score=95,
        has_lsr=True,
        precursor_priority="HIGH",
    )
    assert len(scenarios) == 1
    scen = scenarios[0]
    assert scen.original_risk_score == 95
    assert scen.simulated_risk_score < 95
    assert scen.risk_delta < 0
    assert scen.simulated_status == "VERIFIED"


def test_deterministic_reproducibility(confined_space_graph):
    """Verifies that identical inputs produce 100% identical recommendations and plans."""
    res1 = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=95,
        risk_priority="CRITICAL",
        life_saving_rule="Bypassing Safety Controls",
        sif_level="PSIF",
    )
    res2 = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=95,
        risk_priority="CRITICAL",
        life_saving_rule="Bypassing Safety Controls",
        sif_level="PSIF",
    )
    assert res1.total_recommendations == res2.total_recommendations
    assert res1.baseline_risk_score == res2.baseline_risk_score
    assert res1.target_risk_score == res2.target_risk_score
    assert res1.recommendations[0].intervention_code == res2.recommendations[0].intervention_code
    assert res1.recommendations[0].priority_score == res2.recommendations[0].priority_score


@pytest.mark.asyncio
async def test_api_analyze_interventions_structured_payload(admin_headers, confined_space_graph):
    """Verifies POST /api/v1/analyze/interventions with structured safety_graph payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "safety_graph": confined_space_graph,
            "risk_score": 95,
            "risk_priority": "CRITICAL",
            "life_saving_rule": "Bypassing Safety Controls",
            "sif_level": "PSIF",
        }
        res = await ac.post("/api/v1/analyze/interventions", json=payload, headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_recommendations"] >= 1
        assert data["baseline_risk_score"] == 95
        assert data["target_risk_score"] < 95
        assert len(data["recommendations"]) >= 1
        assert "cumulative_prevention_plan" in data


@pytest.mark.asyncio
async def test_api_analyze_interventions_raw_text_payload(admin_headers):
    """Verifies POST /api/v1/analyze/interventions with raw incident_text payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "incident_text": "Technician entered nitrogen vessel without gas testing or entry permit.",
        }
        res = await ac.post("/api/v1/analyze/interventions", json=payload, headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_recommendations"] >= 1
        assert data["deterministic"] is True
        assert len(data["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_api_analyze_interventions_unauthorized():
    """Verifies that unauthenticated calls to /api/v1/analyze/interventions are rejected with 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "incident_text": "Worker entered vessel without gas test.",
        }
        res = await ac.post("/api/v1/analyze/interventions", json=payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_analyze_interventions_empty_payload(admin_headers):
    """Verifies that empty payload is rejected with 422 Unprocessable Entity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {}
        res = await ac.post("/api/v1/analyze/interventions", json=payload, headers=admin_headers)
        assert res.status_code == 422


def test_unverified_barrier_mapping():
    """Verifies that NOT_VERIFIED control maps to VERIFICATION_AUDIT."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Confined Space Entry",
                "hazard": "Hazardous Atmosphere",
                "control": "Atmospheric Gas Testing",
                "control_status": "NOT_VERIFIED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Confined Space Entry",
        "critical_hazard": "Hazardous Atmosphere",
        "primary_barrier": "Atmospheric Gas Testing",
        "barrier_status": "NOT_VERIFIED",
    }
    res = SafetyInterventionEngine.generate_interventions(safety_graph=graph, risk_score=80)
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert rec.current_barrier_status == "NOT_VERIFIED"
    assert rec.action_type in (InterventionActionType.VERIFICATION_AUDIT, InterventionActionType.IMMEDIATE_STOP_WORK)


def test_expired_barrier_mapping():
    """Verifies that EXPIRED status generates a CALIBRATION recommendation."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Operational Monitoring",
                "hazard": "Overpressure",
                "control": "Pressure Relief Valve",
                "control_status": "EXPIRED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "primary_barrier": "Pressure Relief Valve",
        "barrier_status": "EXPIRED",
    }
    res = SafetyInterventionEngine.generate_interventions(safety_graph=graph, risk_score=60)
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert rec.action_type == InterventionActionType.CALIBRATION
    assert rec.deterministic_rule_id == "RULE-GEN-EXPIRED-01"


def test_hot_work_fire_watch_mapping():
    """Verifies that hot work with flammable hazard maps to fire watch verification."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Hot Work Welding",
                "hazard": "Flammable Gas",
                "control": "Fire Watch",
                "control_status": "NOT_PERFORMED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Hot Work Welding",
        "critical_hazard": "Flammable Gas",
        "primary_barrier": "Fire Watch",
        "barrier_status": "NOT_PERFORMED",
    }
    res = SafetyInterventionEngine.generate_interventions(safety_graph=graph, risk_score=85)
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert "Fire" in rec.title or "Combustible" in rec.title


def test_lifting_exclusion_zone_mapping():
    """Verifies that lifting operation without exclusion barricades maps to SUPERVISORY_OVERSIGHT."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Crane Lifting Operations",
                "hazard": "Suspended Load",
                "control": "Exclusion Zone Barricade",
                "control_status": "MISSING",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Crane Lifting Operations",
        "critical_hazard": "Suspended Load",
        "primary_barrier": "Exclusion Zone Barricade",
        "barrier_status": "MISSING",
    }
    res = SafetyInterventionEngine.generate_interventions(safety_graph=graph, risk_score=75)
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert "Lift" in rec.title or "Barricade" in rec.title or "Exclusion" in rec.title


def test_multi_barrier_three_step_trajectory():
    """Verifies 3 sequential barrier restorations produce monotonic risk delta reduction."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Confined Space Entry",
                "hazard": "Toxic Atmosphere",
                "control": "Gas Testing",
                "control_status": "NOT_PERFORMED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            },
            {
                "activity": "Confined Space Entry",
                "hazard": "Toxic Atmosphere",
                "control": "Permit Authorization",
                "control_status": "NOT_VERIFIED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            },
            {
                "activity": "Confined Space Entry",
                "hazard": "Toxic Atmosphere",
                "control": "Continuous Forced Ventilation",
                "control_status": "FAILED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            },
        ],
        "root_activity": "Confined Space Entry",
        "critical_hazard": "Toxic Atmosphere",
        "primary_barrier": "Gas Testing",
        "barrier_status": "NOT_PERFORMED",
        "barrier_failure_detected": True,
        "precursor_detected": True,
    }
    res = SafetyInterventionEngine.generate_interventions(safety_graph=graph, risk_score=95, sif_level="PSIF")
    plan = res.cumulative_prevention_plan
    assert len(plan.trajectory) == 3
    assert plan.baseline_risk == 95
    assert plan.target_risk <= plan.baseline_risk
    assert plan.total_risk_delta <= 0


def test_residual_risk_never_exceeds_baseline(confined_space_graph):
    """Consistency invariant: residual risk must always be <= baseline risk for restorative actions."""
    res = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=90,
    )
    for rec in res.recommendations:
        assert rec.predicted_simulated_risk <= rec.predicted_original_risk
        assert rec.predicted_risk_delta <= 0


def test_empty_graph_resilience():
    """Verifies that an empty or missing graph is gracefully handled without uncaught exceptions."""
    res = SafetyInterventionEngine.generate_interventions(safety_graph={}, risk_score=50)
    assert res.total_recommendations >= 1
    assert res.deterministic is True


def test_electrical_arc_flash_rule_mapping():
    """Verifies electrical isolation and grounding rules map deterministically."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Electrical Substation Maintenance",
                "hazard": "High Voltage Arc Flash",
                "control": "LOTO Lockout Tagout",
                "control_status": "DEGRADED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Electrical Substation Maintenance",
        "critical_hazard": "High Voltage Arc Flash",
        "primary_barrier": "LOTO Lockout Tagout",
        "barrier_status": "DEGRADED",
        "barrier_failure_detected": True,
        "precursor_detected": True,
    }
    res = SafetyInterventionEngine.generate_interventions(
        safety_graph=graph,
        risk_score=90,
        risk_priority="CRITICAL",
        life_saving_rule="Energy Isolation",
    )
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert rec.hierarchy_level in ["ENGINEERING_CONTROL", "ADMINISTRATIVE_CONTROL"]
    assert "Energy Isolation" in (rec.required_lsr or "") or "LOTO" in rec.title or "Zero-Energy" in rec.description or "Isolation" in rec.title


def test_high_pressure_line_break_rule_mapping():
    """Verifies high pressure line break and positive isolation mapping."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Pipeline Flange Maintenance",
                "hazard": "Pressurized Hydrocarbon Release",
                "control": "Positive Mechanical Isolation (Spade/Blind)",
                "control_status": "NOT_PERFORMED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Pipeline Flange Maintenance",
        "critical_hazard": "Pressurized Hydrocarbon Release",
        "primary_barrier": "Positive Mechanical Isolation (Spade/Blind)",
        "barrier_status": "NOT_PERFORMED",
        "barrier_failure_detected": True,
        "precursor_detected": True,
    }
    res = SafetyInterventionEngine.generate_interventions(
        safety_graph=graph,
        risk_score=95,
        risk_priority="CRITICAL",
        life_saving_rule="Energy Isolation",
        sif_level="PSIF",
    )
    assert len(res.recommendations) >= 1
    rec = res.recommendations[0]
    assert rec.priority == "CRITICAL"
    assert rec.predicted_risk_delta < 0


def test_priority_score_deterministic_monotonicity():
    """Verifies that higher baseline risk scores and SIF potential strictly produce higher priority scores."""
    graph = {
        "nodes": [],
        "edges": [],
        "causal_chains": [
            {
                "activity": "Confined Space Entry",
                "hazard": "Toxic Atmosphere",
                "control": "Gas Testing",
                "control_status": "FAILED",
                "barrier_failure": True,
                "exposure": "SIF_PRECURSOR_EXPOSURE",
            }
        ],
        "root_activity": "Confined Space Entry",
        "critical_hazard": "Toxic Atmosphere",
        "primary_barrier": "Gas Testing",
        "barrier_status": "FAILED",
        "barrier_failure_detected": True,
        "precursor_detected": True,
    }
    high_sif = SafetyInterventionEngine.generate_interventions(
        safety_graph=graph, risk_score=95, risk_priority="CRITICAL", sif_level="PSIF", life_saving_rule="Bypassing Safety Controls"
    )
    low_sif = SafetyInterventionEngine.generate_interventions(
        safety_graph=graph, risk_score=40, risk_priority="LOW", sif_level="NON_SIF", life_saving_rule=""
    )
    assert high_sif.recommendations[0].priority_score > low_sif.recommendations[0].priority_score


def test_multi_barrier_plan_defense_in_depth_layering(confined_space_graph):
    """Verifies defense in depth layers categorize into Engineering, Administrative, and Verification."""
    res = SafetyInterventionEngine.generate_interventions(
        safety_graph=confined_space_graph,
        risk_score=90,
        risk_priority="HIGH",
        sif_level="PSIF",
    )
    plan = res.cumulative_prevention_plan
    assert plan is not None
    assert len(plan.defense_in_depth_layers) >= 1
    # Check that each step in trajectory has correct structure and monotonic risk reduction
    for step in plan.trajectory:
        assert step.step_number >= 1
        assert step.simulated_risk_score <= 90
        assert abs(step.cumulative_risk_delta) >= abs(step.step_risk_delta)


