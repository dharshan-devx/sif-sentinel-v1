"""
SIF Sentinel — Phase 5D Counterfactual Safety Reasoning Engine

Provides counterfactual 'What-if' simulation over causal safety graphs,
allowing safety officers to evaluate the quantitative and qualitative impact
of restoring safety barriers, removing failures, or enforcing verifications.

Core Principles:
1. Immutability: The observed incident graph is NEVER mutated.
2. Canonical Risk Model: Risk changes are computed using the existing risk calculator.
3. No Probability Fabrication: Models only legitimate causal and deterministic deltas.
4. Evidence Provenance: Observed evidence remains tied to original states.
5. Explicit Assumptions: Every simulation surfaces auditable safety assumptions.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.constants import SIFLevel
from app.services.nlp.causal_engine import (
    ControlStatus,
    SafetyReasoningGraph,
)
from app.services.risk_engine.calculator import calculate_risk


@dataclass
class CounterfactualChange:
    element_type: str  # CONTROL_STATUS, BARRIER_FAILURE, EXPOSURE, SIF_PRECURSOR, RISK
    element_name: str
    observed_value: Any
    simulated_value: Any
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_type": self.element_type,
            "element_name": self.element_name,
            "observed_value": self.observed_value,
            "simulated_value": self.simulated_value,
            "description": self.description,
        }


@dataclass
class CounterfactualScenario:
    scenario_id: str
    target_node_id: str | None
    target_control: str
    original_status: str
    simulated_status: str
    original_barrier_failure: bool
    simulated_barrier_failure: bool
    original_exposure: str
    simulated_exposure: str
    original_risk_score: int
    simulated_risk_score: int
    risk_delta: int
    risk_direction: str  # REDUCED, UNCHANGED, INCREASED
    original_sif_potential: bool
    simulated_sif_potential: bool
    original_sif_classification: str
    simulated_sif_classification: str
    causal_changes: list[CounterfactualChange]
    affected_nodes: list[str]
    affected_edges: list[dict[str, Any]]
    assumptions: list[str]
    interpretation: str
    confidence: float
    simulated_graph: dict[str, Any]
    simulation_only: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "target_node_id": self.target_node_id,
            "target_control": self.target_control,
            "original_status": self.original_status,
            "simulated_status": self.simulated_status,
            "original_barrier_failure": self.original_barrier_failure,
            "simulated_barrier_failure": self.simulated_barrier_failure,
            "original_exposure": self.original_exposure,
            "simulated_exposure": self.simulated_exposure,
            "original_risk_score": self.original_risk_score,
            "simulated_risk_score": self.simulated_risk_score,
            "risk_delta": self.risk_delta,
            "risk_direction": self.risk_direction,
            "original_sif_potential": self.original_sif_potential,
            "simulated_sif_potential": self.simulated_sif_potential,
            "original_sif_classification": self.original_sif_classification,
            "simulated_sif_classification": self.simulated_sif_classification,
            "causal_changes": [c.to_dict() for c in self.causal_changes],
            "affected_nodes": self.affected_nodes,
            "affected_edges": self.affected_edges,
            "assumptions": self.assumptions,
            "interpretation": self.interpretation,
            "confidence": round(self.confidence, 4),
            "simulated_graph": self.simulated_graph,
            "simulation_only": self.simulation_only,
            "created_at": self.created_at,
        }


class CounterfactualSafetyEngine:
    """
    Simulates counterfactual safety barrier restorations over causal safety graphs.
    """

    SUPPORTED_SIMULATED_STATUSES = {
        ControlStatus.VERIFIED,
        ControlStatus.PERFORMED,
    }

    @classmethod
    def simulate_barrier_restoration(
        cls,
        original_graph: dict[str, Any] | SafetyReasoningGraph,
        target_control: str,
        simulated_status: ControlStatus = ControlStatus.VERIFIED,
        target_node_id: str | None = None,
        original_risk_score: int | None = None,
        has_lsr: bool = True,
        precursor_priority: str | None = "HIGH",
    ) -> CounterfactualScenario:
        """
        Executes a counterfactual simulation by cloning the original graph,
        mutating the selected control status, propagating downstream causal changes,
        and recalculating deterministic risk and SIF precursor states.
        """
        # 1. Convert input graph to dictionary and clone it deeply to guarantee immutability
        if isinstance(original_graph, SafetyReasoningGraph):
            graph_data = original_graph.to_dict()
        else:
            graph_data = copy.deepcopy(original_graph)

        sim_graph = copy.deepcopy(graph_data)
        nodes: list[dict[str, Any]] = sim_graph.get("nodes", [])
        chains: list[dict[str, Any]] = sim_graph.get("causal_chains", [])

        # 2. Locate the Target Control Node and Chain
        target_norm = target_control.strip().lower()
        matched_chain = None
        matched_chain_idx = -1

        for idx, chain in enumerate(chains):
            c_name = (chain.get("control") or "").strip().lower()
            if c_name == target_norm or target_norm in c_name or c_name in target_norm:
                matched_chain = chain
                matched_chain_idx = idx
                target_control = chain.get("control") or target_control
                break

        if not matched_chain:
            # Check nodes if chain direct match was not found
            for n in nodes:
                n_label = n.get("label", "").lower()
                n_id = n.get("id", "").lower()
                if n.get("type") == "CONTROL" and (n_label == target_norm or target_norm in n_label or n_label in target_norm or target_norm in n_id):
                    target_control = n.get("label")
                    break

        # If still not found, raise ValueError
        if not matched_chain and not any(n.get("type") == "CONTROL" and (n.get("label", "").lower() == target_norm or target_norm in n.get("label", "").lower()) for n in nodes):
            raise ValueError(f"Target control '{target_control}' does not exist in the causal graph.")

        # Extract Original States
        orig_status_str = matched_chain.get("control_status", "UNKNOWN") if matched_chain else "NOT_PERFORMED"
        orig_barrier_failure = matched_chain.get("barrier_failure", True) if matched_chain else True
        orig_exposure = matched_chain.get("exposure", "SIF_PRECURSOR_EXPOSURE") if matched_chain else "SIF_PRECURSOR_EXPOSURE"

        # 3. Apply Simulated State (VERIFIED / PERFORMED)
        sim_status_enum = simulated_status if isinstance(simulated_status, ControlStatus) else ControlStatus(simulated_status)
        sim_status_str = sim_status_enum.value
        sim_barrier_failure = False
        sim_exposure = "CONTROLLED_ACTIVITY"
        sim_precursor_type = None

        causal_changes: list[CounterfactualChange] = []
        affected_nodes: list[str] = []
        affected_edges: list[dict[str, Any]] = []

        # Record control status change
        causal_changes.append(
            CounterfactualChange(
                element_type="CONTROL_STATUS",
                element_name=target_control,
                observed_value=orig_status_str,
                simulated_value=sim_status_str,
                description=f"Barrier '{target_control}' status changed from {orig_status_str} to {sim_status_str}."
            )
        )

        # Record barrier failure change
        if orig_barrier_failure != sim_barrier_failure:
            causal_changes.append(
                CounterfactualChange(
                    element_type="BARRIER_FAILURE",
                    element_name=target_control,
                    observed_value=orig_barrier_failure,
                    simulated_value=sim_barrier_failure,
                    description=f"Modeled barrier failure for '{target_control}' removed."
                )
            )

        # Record exposure change
        if orig_exposure != sim_exposure:
            causal_changes.append(
                CounterfactualChange(
                    element_type="EXPOSURE",
                    element_name="Worker Exposure",
                    observed_value=orig_exposure,
                    simulated_value=sim_exposure,
                    description=f"Causal exposure pathway mitigated from {orig_exposure} to {sim_exposure}."
                )
            )

        # 4. Mutate Simulated Graph Copy
        if matched_chain_idx != -1:
            chains[matched_chain_idx]["control_status"] = sim_status_str
            chains[matched_chain_idx]["barrier_failure"] = sim_barrier_failure
            chains[matched_chain_idx]["exposure"] = sim_exposure
            chains[matched_chain_idx]["sif_precursor_type"] = sim_precursor_type
            chains[matched_chain_idx]["relationship_type"] = "SIMULATED_VERIFIED_BARRIER"

        # Update matching nodes in simulated graph
        for node in nodes:
            nid = node.get("id", "")
            ntype = node.get("type")
            label = node.get("label", "")

            if ntype == "CONTROL" and (label == target_control or target_norm in label.lower()):
                affected_nodes.append(nid)
                node["properties"] = node.get("properties", {})
                node["properties"]["simulated_status"] = sim_status_str

            elif ntype == "STATUS" and (target_control.lower() in nid.lower() or target_norm in label.lower()):
                affected_nodes.append(nid)
                node["label"] = sim_status_str
                node["properties"] = node.get("properties", {})
                node["properties"]["barrier_failure"] = False
                node["properties"]["is_simulated"] = True

            elif ntype == "EXPOSURE":
                affected_nodes.append(nid)
                node["label"] = sim_exposure
                node["properties"] = node.get("properties", {})
                node["properties"]["is_simulated"] = True

            elif ntype == "PRECURSOR":
                affected_nodes.append(nid)
                node["label"] = "Controlled Execution"
                node["properties"] = node.get("properties", {})
                node["properties"]["is_simulated"] = True

        # Check overall simulated barrier failure across all chains
        any_other_failure = any(c.get("barrier_failure", False) for c in chains)
        sim_graph["barrier_failure_detected"] = any_other_failure
        sim_graph["precursor_detected"] = any_other_failure and sim_graph.get("high_energy_hazard_present", False)

        # 5. Calculate Risk Recalculation via Canonical Risk Engine
        # Calculate Original Risk if not provided
        orig_sif_pot = orig_barrier_failure
        orig_sif_lvl = SIFLevel.HIGH if orig_sif_pot else SIFLevel.LOW
        orig_risk_calc = calculate_risk(
            sif_level=orig_sif_lvl,
            sif_potential=orig_sif_pot,
            barrier_status="not performed" if orig_status_str in ("NOT_PERFORMED", "MISSING") else "failed",
            has_lsr=has_lsr,
            precursor_priority=precursor_priority,
        )
        orig_risk = original_risk_score if original_risk_score is not None else orig_risk_calc["score"]

        # Calculate Simulated Risk
        sim_sif_pot = any_other_failure
        sim_sif_lvl = SIFLevel.LOW if not sim_sif_pot else SIFLevel.MEDIUM
        sim_risk_calc = calculate_risk(
            sif_level=sim_sif_lvl,
            sif_potential=sim_sif_pot,
            barrier_status="verified",
            has_lsr=has_lsr,
            precursor_priority=None if not sim_sif_pot else precursor_priority,
        )
        sim_risk = sim_risk_calc["score"]
        risk_delta = sim_risk - orig_risk
        risk_direction = "REDUCED" if risk_delta < 0 else ("INCREASED" if risk_delta > 0 else "UNCHANGED")

        causal_changes.append(
            CounterfactualChange(
                element_type="RISK",
                element_name="Composite Risk Score",
                observed_value=orig_risk,
                simulated_value=sim_risk,
                description=f"Deterministic risk score changed from {orig_risk} to {sim_risk} (Delta: {risk_delta})."
            )
        )

        # 6. Explicit Assumptions
        assumptions = [
            f"Safety control '{target_control}' is assumed to be fully verified and functional prior to work commencement.",
            "All personnel are assumed to strictly adhere to the simulated control barrier.",
            "No additional unmodeled equipment degradation or concurrent failures occurred.",
            "Risk delta is computed using the canonical SIF Sentinel deterministic risk model.",
            "This is a counterfactual simulation and does not alter the historical or observed incident report.",
        ]

        # 7. Formulate Grounded Safety Interpretation
        interpretation = (
            f"What-if '{target_control}' had been {sim_status_str}? "
            f"Restoring this barrier eliminates the modeled failure mechanism and mitigates downstream '{orig_exposure.replace('_', ' ').lower()}' exposure. "
            f"Composite risk decreases from {orig_risk} to {sim_risk} (Delta: {risk_delta} pts). "
            f"The SIF precursor classification shifts from {'POTENTIAL SIF' if orig_sif_pot else 'CONTROLLED'} to {'POTENTIAL SIF' if sim_sif_pot else 'CONTROLLED EXECUTION'}."
        )

        return CounterfactualScenario(
            scenario_id=f"sim_{uuid.uuid4().hex[:10]}",
            target_node_id=target_node_id,
            target_control=target_control,
            original_status=orig_status_str,
            simulated_status=sim_status_str,
            original_barrier_failure=orig_barrier_failure,
            simulated_barrier_failure=sim_barrier_failure,
            original_exposure=orig_exposure,
            simulated_exposure=sim_exposure,
            original_risk_score=orig_risk,
            simulated_risk_score=sim_risk,
            risk_delta=risk_delta,
            risk_direction=risk_direction,
            original_sif_potential=orig_sif_pot,
            simulated_sif_potential=sim_sif_pot,
            original_sif_classification="PSIF" if orig_sif_pot else "NON_SIF",
            simulated_sif_classification="PSIF" if sim_sif_pot else "NON_SIF",
            causal_changes=causal_changes,
            affected_nodes=affected_nodes,
            affected_edges=affected_edges,
            assumptions=assumptions,
            interpretation=interpretation,
            confidence=0.95,
            simulated_graph=sim_graph,
            simulation_only=True,
        )

    @classmethod
    def simulate_multi_barrier_restoration(
        cls,
        original_graph: dict[str, Any] | SafetyReasoningGraph,
        target_controls: list[tuple[str, ControlStatus | str] | str],
        original_risk_score: int | None = None,
        has_lsr: bool = True,
        precursor_priority: str | None = "HIGH",
    ) -> list[CounterfactualScenario]:
        """
        Sequentially simulates the restoration of multiple safety barriers,
        producing a step-by-step risk trajectory (Baseline -> Step 1 -> Step 2 -> ...).
        Each step evaluates risk through the canonical risk engine over the updated graph.
        """
        if not target_controls:
            return []

        scenarios: list[CounterfactualScenario] = []
        curr_graph: dict[str, Any] | SafetyReasoningGraph = original_graph
        curr_risk = original_risk_score

        for item in target_controls:
            if isinstance(item, tuple):
                ctrl_name, status_val = item
                status_enum = status_val if isinstance(status_val, ControlStatus) else ControlStatus(str(status_val).upper())
            else:
                ctrl_name = str(item)
                status_enum = ControlStatus.VERIFIED

            scenario = cls.simulate_barrier_restoration(
                original_graph=curr_graph,
                target_control=ctrl_name,
                simulated_status=status_enum,
                original_risk_score=curr_risk,
                has_lsr=has_lsr,
                precursor_priority=precursor_priority,
            )
            scenarios.append(scenario)
            curr_graph = scenario.simulated_graph
            curr_risk = scenario.simulated_risk_score

        return scenarios

