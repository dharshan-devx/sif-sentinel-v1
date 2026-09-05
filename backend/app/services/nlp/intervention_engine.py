"""
SIF Sentinel — Phase 5F Automated Corrective Intervention & Preventive Action Intelligence Engine

Transforms deterministic causal safety findings, barrier failure states, and counterfactual
simulations into prioritized, actionable corrective and preventive intervention plans.

Core Principles:
1. Deterministic Authority: Rules and hierarchy mappings are 100% deterministic and reproducible.
2. Canonical Hierarchy of Controls: Elimination -> Substitution -> Engineering -> Administrative -> PPE.
3. Grounded in Phase 5D: Predicted risk impacts are derived directly from CounterfactualSafetyEngine.
4. Multi-Barrier Defense-in-Depth: Computes cumulative prevention trajectories across sequential barriers.
5. Advisory Only: Provides decision support for human HSE review; never executes autonomous field actions.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.constants import SIFLevel
from app.services.nlp.causal_engine import ControlStatus, SafetyReasoningGraph
from app.services.nlp.counterfactual_engine import (
    CounterfactualSafetyEngine,
    CounterfactualScenario,
)


class HierarchyLevel(str, Enum):
    ELIMINATION = "ELIMINATION"
    SUBSTITUTION = "SUBSTITUTION"
    ENGINEERING_CONTROL = "ENGINEERING_CONTROL"
    ADMINISTRATIVE_CONTROL = "ADMINISTRATIVE_CONTROL"
    PPE = "PPE"


class InterventionActionType(str, Enum):
    IMMEDIATE_STOP_WORK = "IMMEDIATE_STOP_WORK"
    BARRIER_RESTORATION = "BARRIER_RESTORATION"
    ENGINEERING_INSTALL = "ENGINEERING_INSTALL"
    ENGINEERING_UPGRADE = "ENGINEERING_UPGRADE"
    VERIFICATION_AUDIT = "VERIFICATION_AUDIT"
    PERMIT_VERIFY = "PERMIT_VERIFY"
    ISOLATION_VERIFY = "ISOLATION_VERIFY"
    INSPECTION = "INSPECTION"
    CALIBRATION = "CALIBRATION"
    PREVENTIVE_TRAINING = "PREVENTIVE_TRAINING"
    SUPERVISORY_OVERSIGHT = "SUPERVISORY_OVERSIGHT"
    PROCEDURE_REVISION = "PROCEDURE_REVISION"
    PPE_ENHANCEMENT = "PPE_ENHANCEMENT"


class InterventionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InterventionUrgency(str, Enum):
    IMMEDIATE_PRE_START = "IMMEDIATE_PRE_START"
    WITHIN_SHIFT = "WITHIN_SHIFT"
    PRIOR_TO_NEXT_CYCLE = "PRIOR_TO_NEXT_CYCLE"
    ROUTINE_SCHEDULED = "ROUTINE_SCHEDULED"


@dataclass
class InterventionRecommendationItem:
    id: str
    intervention_code: str
    title: str
    description: str
    hierarchy_level: HierarchyLevel
    action_type: InterventionActionType
    priority: InterventionPriority
    priority_score: int
    urgency: InterventionUrgency
    rationale: str
    linked_hazard: str
    linked_activity: str
    linked_barrier: str
    target_node_id: str | None
    current_barrier_status: str
    target_barrier_status: str
    predicted_original_risk: int
    predicted_simulated_risk: int
    predicted_risk_delta: int
    feasibility_score: str  # HIGH, MEDIUM, LOW
    implementation_timeframe: str  # IMMEDIATE, SHORT_TERM, MEDIUM_TERM
    required_lsr: str | None
    source_basis: str
    deterministic_rule_id: str
    confidence: float
    status: str = "GENERATED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "intervention_code": self.intervention_code,
            "title": self.title,
            "description": self.description,
            "hierarchy_level": self.hierarchy_level.value,
            "action_type": self.action_type.value,
            "priority": self.priority.value,
            "priority_score": self.priority_score,
            "urgency": self.urgency.value,
            "rationale": self.rationale,
            "linked_hazard": self.linked_hazard,
            "linked_activity": self.linked_activity,
            "linked_barrier": self.linked_barrier,
            "target_node_id": self.target_node_id,
            "current_barrier_status": self.current_barrier_status,
            "target_barrier_status": self.target_barrier_status,
            "predicted_original_risk": self.predicted_original_risk,
            "predicted_simulated_risk": self.predicted_simulated_risk,
            "predicted_risk_delta": self.predicted_risk_delta,
            "feasibility_score": self.feasibility_score,
            "implementation_timeframe": self.implementation_timeframe,
            "required_lsr": self.required_lsr,
            "source_basis": self.source_basis,
            "deterministic_rule_id": self.deterministic_rule_id,
            "confidence": round(self.confidence, 4),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class PreventionTrajectoryStep:
    step_number: int
    barrier_name: str
    action_title: str
    simulated_risk_score: int
    step_risk_delta: int
    cumulative_risk_delta: int
    residual_sif_potential: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "barrier_name": self.barrier_name,
            "action_title": self.action_title,
            "simulated_risk_score": self.simulated_risk_score,
            "step_risk_delta": self.step_risk_delta,
            "cumulative_risk_delta": self.cumulative_risk_delta,
            "residual_sif_potential": self.residual_sif_potential,
        }


@dataclass
class CumulativePreventionPlan:
    plan_id: str
    baseline_risk: int
    target_risk: int
    total_risk_delta: int
    defense_in_depth_layers: list[str]
    trajectory: list[PreventionTrajectoryStep]
    primary_mitigation: str
    secondary_mitigation: str | None
    residual_risk_level: str
    assumptions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "baseline_risk": self.baseline_risk,
            "target_risk": self.target_risk,
            "total_risk_delta": self.total_risk_delta,
            "defense_in_depth_layers": self.defense_in_depth_layers,
            "trajectory": [t.to_dict() for t in self.trajectory],
            "primary_mitigation": self.primary_mitigation,
            "secondary_mitigation": self.secondary_mitigation,
            "residual_risk_level": self.residual_risk_level,
            "assumptions": self.assumptions,
        }


@dataclass
class InterventionEngineResult:
    total_recommendations: int
    overall_hierarchy_level: str
    baseline_risk_score: int
    target_risk_score: int
    cumulative_risk_delta: int
    recommendations: list[InterventionRecommendationItem]
    cumulative_prevention_plan: CumulativePreventionPlan
    source_basis: str
    deterministic: bool = True
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_recommendations": self.total_recommendations,
            "overall_hierarchy_level": self.overall_hierarchy_level,
            "baseline_risk_score": self.baseline_risk_score,
            "target_risk_score": self.target_risk_score,
            "cumulative_risk_delta": self.cumulative_risk_delta,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "cumulative_prevention_plan": self.cumulative_prevention_plan.to_dict(),
            "source_basis": self.source_basis,
            "deterministic": self.deterministic,
            "generated_at": self.generated_at,
        }


class SafetyInterventionEngine:
    """
    Deterministic hierarchy-of-controls & multi-barrier corrective intervention engine.
    """

    ENGINE_VERSION = "5F-v1"

    @classmethod
    def generate_interventions(
        cls,
        safety_graph: dict[str, Any] | SafetyReasoningGraph,
        risk_score: int | None = None,
        risk_priority: str | None = None,
        life_saving_rule: str | None = None,
        sif_level: str | None = None,
    ) -> InterventionEngineResult:
        """
        Derives deterministic, prioritized corrective actions and multi-barrier prevention
        plans directly from the causal safety graph, risk score, and barrier statuses.
        """
        if isinstance(safety_graph, SafetyReasoningGraph):
            graph_data = safety_graph.to_dict()
        else:
            graph_data = copy.deepcopy(safety_graph or {})

        chains = graph_data.get("causal_chains", [])
        nodes = graph_data.get("nodes", [])
        base_risk = risk_score if risk_score is not None else 85
        is_psif = (
            sif_level in ("PSIF", "SIF_PRECURSOR", "SIF", "HIGH")
            or graph_data.get("precursor_detected", False)
            or base_risk >= 70
        )
        lsr_name = life_saving_rule or graph_data.get("life_saving_rule")

        recommendations: list[InterventionRecommendationItem] = []

        # Identify all chains or barrier nodes that require intervention
        evaluated_barriers: set[str] = set()

        for idx, chain in enumerate(chains):
            barrier_name = chain.get("control") or "Unspecified Safety Barrier"
            if barrier_name in evaluated_barriers:
                continue
            evaluated_barriers.add(barrier_name)

            status_str = chain.get("control_status", "UNKNOWN").upper()
            activity_name = chain.get("activity") or graph_data.get("root_activity") or "High-Energy Task"
            hazard_name = chain.get("hazard") or graph_data.get("critical_hazard") or "Identified Hazard"
            target_node_id = None

            # Find matching node id
            for n in nodes:
                if n.get("type") == "CONTROL" and (n.get("label", "").lower() == barrier_name.lower() or barrier_name.lower() in n.get("label", "").lower()):
                    target_node_id = n.get("id")
                    break

            # Check if this barrier needs intervention (non-verified / degraded state)
            if status_str in ("VERIFIED", "PERFORMED") and not chain.get("barrier_failure", False):
                continue

            # Run Phase 5D single-barrier simulation to get verified risk delta
            try:
                sim_res = CounterfactualSafetyEngine.simulate_barrier_restoration(
                    original_graph=graph_data,
                    target_control=barrier_name,
                    simulated_status=ControlStatus.VERIFIED,
                    target_node_id=target_node_id,
                    original_risk_score=base_risk,
                    has_lsr=bool(lsr_name),
                    precursor_priority=risk_priority or "HIGH",
                )
                sim_risk = sim_res.simulated_risk_score
                risk_delta = sim_res.risk_delta
            except Exception:
                sim_risk = max(15, base_risk - 45)
                risk_delta = sim_risk - base_risk

            # Determine Hierarchy, Action Type, Title, Description, and Rule ID
            rule_id, hier_level, action_type, title, description, urgency, feasibility, timeframe = (
                cls._map_barrier_to_intervention(
                    activity=activity_name,
                    hazard=hazard_name,
                    barrier=barrier_name,
                    status=status_str,
                    lsr=lsr_name,
                )
            )

            # Compute Priority Score using deterministic formula
            p_score, p_enum = cls._compute_priority_score(
                base_risk=base_risk,
                is_psif=is_psif,
                status=status_str,
                has_lsr=bool(lsr_name),
                risk_delta=risk_delta,
            )

            rationale = (
                f"Recommended under rule [{rule_id}] because {barrier_name} is in '{status_str}' status "
                f"during {activity_name.lower()} involving {hazard_name.lower()}. "
                f"Simulated restoration reduces risk from {base_risk} to {sim_risk} (ΔR = {risk_delta} pts)."
            )

            rec_item = InterventionRecommendationItem(
                id=f"int_{uuid.uuid4().hex[:10]}",
                intervention_code=f"INT-{rule_id}",
                title=title,
                description=description,
                hierarchy_level=hier_level,
                action_type=action_type,
                priority=p_enum,
                priority_score=p_score,
                urgency=urgency,
                rationale=rationale,
                linked_hazard=hazard_name,
                linked_activity=activity_name,
                linked_barrier=barrier_name,
                target_node_id=target_node_id,
                current_barrier_status=status_str,
                target_barrier_status="VERIFIED",
                predicted_original_risk=base_risk,
                predicted_simulated_risk=sim_risk,
                predicted_risk_delta=risk_delta,
                feasibility_score=feasibility,
                implementation_timeframe=timeframe,
                required_lsr=lsr_name,
                source_basis="CAUSAL_GRAPH + RISK_ENGINE + BARRIER_STATUS",
                deterministic_rule_id=rule_id,
                confidence=0.96,
            )
            recommendations.append(rec_item)

        # Fallback if no specific chains were in graph (e.g. general incident)
        if not recommendations:
            primary_b = graph_data.get("primary_barrier") or "Primary Safety Control"
            prim_status = graph_data.get("barrier_status", "NOT_VERIFIED").upper()
            try:
                sim_res = CounterfactualSafetyEngine.simulate_barrier_restoration(
                    original_graph=graph_data,
                    target_control=primary_b,
                    simulated_status=ControlStatus.VERIFIED,
                    original_risk_score=base_risk,
                    has_lsr=bool(lsr_name),
                )
                sim_risk = sim_res.simulated_risk_score
                risk_delta = sim_res.risk_delta
            except Exception:
                sim_risk = max(20, base_risk - 50)
                risk_delta = sim_risk - base_risk

            p_score, p_enum = cls._compute_priority_score(
                base_risk=base_risk,
                is_psif=is_psif,
                status=prim_status,
                has_lsr=bool(lsr_name),
                risk_delta=risk_delta,
            )

            rec_item = InterventionRecommendationItem(
                id=f"int_{uuid.uuid4().hex[:10]}",
                intervention_code="INT-GEN-BARRIER-RESTORE",
                title=f"Verify and Restore {primary_b}",
                description=f"Conduct field verification and supervisory sign-off for {primary_b} before work proceeds.",
                hierarchy_level=HierarchyLevel.ADMINISTRATIVE_CONTROL,
                action_type=InterventionActionType.VERIFICATION_AUDIT,
                priority=p_enum,
                priority_score=p_score,
                urgency=InterventionUrgency.IMMEDIATE_PRE_START,
                rationale=f"Primary barrier {primary_b} is in {prim_status} state under high-energy conditions.",
                linked_hazard=graph_data.get("critical_hazard") or "High Energy Hazard",
                linked_activity=graph_data.get("root_activity") or "Operational Activity",
                linked_barrier=primary_b,
                target_node_id=None,
                current_barrier_status=prim_status,
                target_barrier_status="VERIFIED",
                predicted_original_risk=base_risk,
                predicted_simulated_risk=sim_risk,
                predicted_risk_delta=risk_delta,
                feasibility_score="HIGH",
                implementation_timeframe="IMMEDIATE",
                required_lsr=lsr_name,
                source_basis="CAUSAL_GRAPH + RISK_ENGINE + BARRIER_STATUS",
                deterministic_rule_id="RULE-GEN-BARRIER-RESTORE",
                confidence=0.92,
            )
            recommendations.append(rec_item)

        # Sort recommendations by priority score descending
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)

        # Build Multi-Barrier Prevention Trajectory using Phase 5D multi-barrier simulation
        prevention_plan = cls._build_cumulative_prevention_plan(
            graph_data=graph_data,
            recommendations=recommendations,
            baseline_risk=base_risk,
            has_lsr=bool(lsr_name),
            risk_priority=risk_priority,
        )

        overall_hierarchy = (
            recommendations[0].hierarchy_level.value
            if recommendations
            else HierarchyLevel.ADMINISTRATIVE_CONTROL.value
        )

        return InterventionEngineResult(
            total_recommendations=len(recommendations),
            overall_hierarchy_level=overall_hierarchy,
            baseline_risk_score=base_risk,
            target_risk_score=prevention_plan.target_risk,
            cumulative_risk_delta=prevention_plan.total_risk_delta,
            recommendations=recommendations,
            cumulative_prevention_plan=prevention_plan,
            source_basis="CAUSAL_GRAPH + RISK_ENGINE + BARRIER_STATUS",
            deterministic=True,
        )

    @classmethod
    def _compute_priority_score(
        cls,
        base_risk: int,
        is_psif: bool,
        status: str,
        has_lsr: bool,
        risk_delta: int,
    ) -> tuple[int, InterventionPriority]:
        """
        Exact formula from Implementation Plan:
        S_priority = W_risk (30) + W_sif (25) + W_status (20) + W_lsr (15) + W_delta (10) -> [0..100]
        """
        # 1. W_risk (max 30)
        if base_risk >= 80:
            w_risk = 30
        elif base_risk >= 50:
            w_risk = 20
        elif base_risk >= 25:
            w_risk = 10
        else:
            w_risk = 5

        # 2. W_sif (max 25)
        w_sif = 25 if is_psif else 0

        # 3. W_status (max 20)
        st = status.upper()
        if st == "BYPASSED":
            w_status = 20
        elif st in ("MISSING", "FAILED"):
            w_status = 15
        elif st in ("NOT_PERFORMED", "NOT_VERIFIED"):
            w_status = 12
        elif st in ("INEFFECTIVE", "EXPIRED"):
            w_status = 10
        else:
            w_status = 5

        # 4. W_lsr (max 15)
        w_lsr = 15 if has_lsr else 0

        # 5. W_delta (max 10)
        if risk_delta <= -50:
            w_delta = 10
        elif risk_delta <= -25:
            w_delta = 7
        elif risk_delta < 0:
            w_delta = 4
        else:
            w_delta = 0

        total_score = min(100, max(0, w_risk + w_sif + w_status + w_lsr + w_delta))

        # Map to Priority Enum
        if total_score >= 75 or st == "BYPASSED":
            p_enum = InterventionPriority.CRITICAL
        elif total_score >= 55:
            p_enum = InterventionPriority.HIGH
        elif total_score >= 35:
            p_enum = InterventionPriority.MEDIUM
        else:
            p_enum = InterventionPriority.LOW

        return total_score, p_enum

    @classmethod
    def _map_barrier_to_intervention(
        cls,
        activity: str,
        hazard: str,
        barrier: str,
        status: str,
        lsr: str | None,
    ) -> tuple[
        str,
        HierarchyLevel,
        InterventionActionType,
        str,
        str,
        InterventionUrgency,
        str,
        str,
    ]:
        """
        Deterministic ontology mapping to Hierarchy of Controls and standardized action taxonomy.
        """
        b_lower = barrier.lower()
        act_lower = activity.lower()
        haz_lower = hazard.lower()
        lsr_lower = (lsr or "").lower()
        st_upper = status.upper()

        # Bypassed control rule
        if st_upper == "BYPASSED":
            return (
                "RULE-BYPASS-HALT-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.IMMEDIATE_STOP_WORK,
                f"Halt Operations & Investigate Bypassed {barrier}",
                f"Immediately suspend work involving {activity.lower()}. Conduct supervisory inquiry into why {barrier} was bypassed prior to restarting.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Gas Testing & Atmosphere Rules
        if "gas test" in b_lower or "gas monitor" in b_lower or "atmosphere" in haz_lower or "toxic" in haz_lower:
            if "continuous" in b_lower or "ventilat" in b_lower:
                return (
                    "RULE-CONF-VENT-02",
                    HierarchyLevel.ENGINEERING_CONTROL,
                    InterventionActionType.ENGINEERING_UPGRADE,
                    "Establish Continuous Forced-Air Mechanical Ventilation",
                    "Deploy certified positive-pressure mechanical ventilation to continuously dilute potential toxic or flammable atmospheric accumulations.",
                    InterventionUrgency.IMMEDIATE_PRE_START,
                    "HIGH",
                    "IMMEDIATE",
                )
            return (
                "RULE-CONF-GAS-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.VERIFICATION_AUDIT,
                "Perform Multi-Gas Atmospheric Testing Prior to Entry",
                "Verify oxygen (19.5-23.5%), LEL (<10%), and toxic gas (H2S, CO) levels using a calibrated 4-gas detector before any personnel enter the zone.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Machine Guarding Rules
        if "guard" in b_lower or "rotating" in haz_lower:
            return (
                "RULE-GUARD-MECH-01",
                HierarchyLevel.ENGINEERING_CONTROL,
                InterventionActionType.ENGINEERING_INSTALL,
                "Install Fixed Interlocked Machine Guarding",
                "Equip rotating equipment with fixed or interlocked physical barriers to physically prevent personnel contact with moving parts.",
                InterventionUrgency.WITHIN_SHIFT,
                "MEDIUM",
                "SHORT_TERM",
            )

        # Energy Isolation / LOTO Rules
        if "isolation" in lsr_lower or "loto" in b_lower or "lockout" in b_lower or "energy" in haz_lower or "isolation" in b_lower:
            return (
                "RULE-LOTO-ISO-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.ISOLATION_VERIFY,
                "Verify Zero-Energy State & Lockout/Tagout Integrity",
                "Perform physical zero-energy verification (try-step, pressure bleed, electrical voltmeter check) and secure individual lock/tag attachments.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Permit to Work / Entry Authorization Rules
        if "permit" in b_lower or "authorization" in b_lower or "permit" in lsr_lower:
            return (
                "RULE-CONF-PTW-03",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.PERMIT_VERIFY,
                "Re-issue & Validate Confined Space / Hot Work Permit",
                "Complete formal permit authorization checklist, confirming cross-discipline isolations, emergency response readiness, and authorized entry logs.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Work at Height / Fall Protection Rules
        if "height" in act_lower or "fall" in haz_lower or "fall arrest" in b_lower or "scaffold" in b_lower:
            if st_upper in ("MISSING", "FAILED"):
                return (
                    "RULE-HEIGHT-FALL-01",
                    HierarchyLevel.ENGINEERING_CONTROL,
                    InterventionActionType.BARRIER_RESTORATION,
                    "Install Certified 100% Tie-Off Anchor & Fall Arrest",
                    "Install rigid overhead anchor lines and ensure 100% dual-lanyard tie-off with energy-absorbing harnesses before working aloft.",
                    InterventionUrgency.IMMEDIATE_PRE_START,
                    "HIGH",
                    "IMMEDIATE",
                )
            return (
                "RULE-HEIGHT-INSPECT-02",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.INSPECTION,
                "Inspect & Certify Scaffold / Fall Arrest Hardware",
                "Perform pre-shift inspection of scaffold green tag status, lanyard integrity, and anchorage load ratings.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Hot Work / Fire Protection Rules
        if "hot work" in act_lower or "fire" in haz_lower or "spark" in haz_lower:
            return (
                "RULE-HOT-FLAM-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.VERIFICATION_AUDIT,
                "Deploy Dedicated Fire Watch & 35ft Combustible Clearance",
                "Ensure dedicated fire watch with charged extinguisher is posted during hot work and remains on site for 30 minutes post-completion.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Lifting / Exclusion Zone Rules
        if "lift" in act_lower or "crane" in act_lower or "suspended" in haz_lower:
            return (
                "RULE-LIFT-ZONE-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.SUPERVISORY_OVERSIGHT,
                "Establish Rigid Exclusion Barricade under Lift Path",
                "Erect physical barricades and warning signage around the maximum crane swing radius to prevent unauthorized personnel entry.",
                InterventionUrgency.IMMEDIATE_PRE_START,
                "HIGH",
                "IMMEDIATE",
            )

        # Generic / Status-Based Fallback
        if st_upper == "EXPIRED":
            return (
                "RULE-GEN-EXPIRED-01",
                HierarchyLevel.ADMINISTRATIVE_CONTROL,
                InterventionActionType.CALIBRATION,
                f"Recalibrate & Re-certify {barrier}",
                f"Safety barrier {barrier} calibration or inspection has expired. Conduct re-certification prior to reliance in operations.",
                InterventionUrgency.PRIOR_TO_NEXT_CYCLE,
                "HIGH",
                "IMMEDIATE",
            )

        return (
            "RULE-GEN-BARRIER-VERIFY",
            HierarchyLevel.ADMINISTRATIVE_CONTROL,
            InterventionActionType.VERIFICATION_AUDIT,
            f"Field Verification of {barrier}",
            f"Conduct supervisory pre-task audit to ensure {barrier} is verified and functional according to standard operating procedures.",
            InterventionUrgency.IMMEDIATE_PRE_START,
            "HIGH",
            "IMMEDIATE",
        )

    @classmethod
    def _build_cumulative_prevention_plan(
        cls,
        graph_data: dict[str, Any],
        recommendations: list[InterventionRecommendationItem],
        baseline_risk: int,
        has_lsr: bool,
        risk_priority: str | None,
    ) -> CumulativePreventionPlan:
        """
        Synthesizes a defense-in-depth prevention trajectory by simulating sequential barrier restorations.
        """
        if not recommendations:
            return CumulativePreventionPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:10]}",
                baseline_risk=baseline_risk,
                target_risk=baseline_risk,
                total_risk_delta=0,
                defense_in_depth_layers=["ADMINISTRATIVE_CONTROL"],
                trajectory=[],
                primary_mitigation="Maintain Standard Precautions",
                secondary_mitigation=None,
                residual_risk_level="LOW",
                assumptions=["Baseline safety precautions maintained."],
            )

        # Prepare target controls for multi-barrier simulation
        target_controls = [
            (r.linked_barrier, ControlStatus.VERIFIED) for r in recommendations
        ]

        # Execute multi-barrier counterfactual simulation
        scenarios: list[CounterfactualScenario] = []
        try:
            scenarios = CounterfactualSafetyEngine.simulate_multi_barrier_restoration(
                original_graph=graph_data,
                target_controls=target_controls,
                original_risk_score=baseline_risk,
                has_lsr=has_lsr,
                precursor_priority=risk_priority,
            )
        except Exception:
            pass

        trajectory: list[PreventionTrajectoryStep] = []
        curr_cumul_delta = 0
        final_risk = baseline_risk

        if scenarios:
            for i, (scen, rec) in enumerate(zip(scenarios, recommendations)):
                step_delta = scen.risk_delta
                curr_cumul_delta += step_delta
                final_risk = scen.simulated_risk_score
                trajectory.append(
                    PreventionTrajectoryStep(
                        step_number=i + 1,
                        barrier_name=rec.linked_barrier,
                        action_title=rec.title,
                        simulated_risk_score=scen.simulated_risk_score,
                        step_risk_delta=step_delta,
                        cumulative_risk_delta=scen.simulated_risk_score - baseline_risk,
                        residual_sif_potential=scen.simulated_sif_potential,
                    )
                )
        else:
            # Deterministic fallback trajectory calculation
            curr_risk = baseline_risk
            for i, rec in enumerate(recommendations):
                step_delta = rec.predicted_risk_delta
                curr_risk = max(10, curr_risk + step_delta)
                curr_cumul_delta = curr_risk - baseline_risk
                final_risk = curr_risk
                trajectory.append(
                    PreventionTrajectoryStep(
                        step_number=i + 1,
                        barrier_name=rec.linked_barrier,
                        action_title=rec.title,
                        simulated_risk_score=curr_risk,
                        step_risk_delta=step_delta,
                        cumulative_risk_delta=curr_cumul_delta,
                        residual_sif_potential=(curr_risk >= 50),
                    )
                )

        distinct_layers = list(
            dict.fromkeys(r.hierarchy_level.value for r in recommendations)
        )
        primary_mit = recommendations[0].title if recommendations else "Safety Barrier Verification"
        secondary_mit = (
            recommendations[1].title if len(recommendations) > 1 else None
        )

        residual_level = "LOW" if final_risk <= 25 else ("MEDIUM" if final_risk <= 50 else "HIGH")

        assumptions = [
            "All recommended interventions are fully verified and actively maintained in the field.",
            "Independent supervisory verification is completed prior to high-energy exposure.",
            "Multi-barrier trajectory is computed using the canonical SIF Sentinel risk calculator.",
            "Advisory recommendations provide decision support and require formal HSE review.",
        ]

        return CumulativePreventionPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:10]}",
            baseline_risk=baseline_risk,
            target_risk=final_risk,
            total_risk_delta=final_risk - baseline_risk,
            defense_in_depth_layers=distinct_layers,
            trajectory=trajectory,
            primary_mitigation=primary_mit,
            secondary_mitigation=secondary_mit,
            residual_risk_level=residual_level,
            assumptions=assumptions,
        )
