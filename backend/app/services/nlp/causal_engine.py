"""
SIF Sentinel — Phase 5B Causal Safety Reasoning Engine

Provides causal relation extraction, structured safety graph reasoning,
advanced negation/prevention resolution, temporal sequencing validation,
and evidence-grounded explainability.

Reasoning Chain:
Activity -> Hazard -> Required Safety Barrier -> Control Status ->
Barrier Failure -> SIF Exposure -> SIF Precursor -> Risk / Priority
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.services.nlp.evidence_model import EvidenceItem, EvidenceType, StructuredEvidence
from app.services.nlp.preprocessing import PreprocessedText


class ControlStatus(StrEnum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    PERFORMED = "PERFORMED"
    NOT_PERFORMED = "NOT_PERFORMED"
    FAILED = "FAILED"
    BYPASSED = "BYPASSED"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


# Canonical Knowledge Mappings
ACTIVITY_TO_HAZARD_MAP: dict[str, list[str]] = {
    "Confined Space Work": ["Toxic Atmosphere", "Oxygen Deficiency", "Stored Energy"],
    "Work at Height": ["Fall Hazard"],
    "Hot Work": ["Fire", "Explosion"],
    "Electrical Work": ["Electrical Energy", "Stored Energy"],
    "Maintenance": ["Stored Energy", "Pressure", "Mechanical Energy", "Electrical Energy"],
    "Pipeline/Line Work": ["Pressure", "Stored Energy", "Toxic Atmosphere", "Chemical Exposure"],
    "Lifting": ["Suspended Load", "Line of Fire"],
    "Driving": ["Vehicle Movement"],
    "Excavation": ["Excavation Collapse", "Stored Energy"],
    "Material Handling": ["Line of Fire", "Mechanical Energy"],
    "Loading/Unloading": ["Line of Fire", "Chemical Exposure", "Vehicle Movement"],
    "Operations": ["Stored Energy", "Moving Machinery", "Pressure"],
    "Inspection": ["Fall Hazard", "Toxic Atmosphere"],
    "Construction": ["Fall Hazard", "Excavation Collapse", "Line of Fire"],
}

HAZARD_TO_CONTROL_MAP: dict[str, list[str]] = {
    "Fall Hazard": ["Fall Protection", "Guardrail"],
    "Toxic Atmosphere": ["Gas Testing", "Atmospheric Monitoring", "Permit"],
    "Oxygen Deficiency": ["Gas Testing", "Atmospheric Monitoring", "Permit"],
    "Stored Energy": ["Energy Isolation", "Lockout Tagout"],
    "Electrical Energy": ["Energy Isolation", "Lockout Tagout", "PPE"],
    "Pressure": ["Energy Isolation", "Lockout Tagout", "Procedure"],
    "Suspended Load": ["Barricading", "Lifting Plan", "Spotter", "Competent Person"],
    "Line of Fire": ["Barricading", "Spotter"],
    "Fire": ["Fire Watch", "Permit"],
    "Explosion": ["Gas Testing", "Permit", "Fire Watch"],
    "Vehicle Movement": ["Vehicle Controls", "Spotter"],
    "Moving Machinery": ["Interlock", "Procedure"],
    "Excavation Collapse": ["Procedure", "Competent Person"],
    "Chemical Exposure": ["PPE", "Permit", "Procedure"],
    "Mechanical Energy": ["Interlock", "Energy Isolation"],
}

CONTROL_TO_HAZARD_MAP: dict[str, str] = {
    "Fall Protection": "Fall Hazard",
    "Guardrail": "Fall Hazard",
    "Gas Testing": "Toxic Atmosphere",
    "Atmospheric Monitoring": "Toxic Atmosphere",
    "Energy Isolation": "Stored Energy",
    "Lockout Tagout": "Stored Energy",
    "Interlock": "Moving Machinery",
    "Fire Watch": "Fire",
    "Barricading": "Suspended Load",
    "Lifting Plan": "Suspended Load",
    "Spotter": "Suspended Load",
    "Vehicle Controls": "Vehicle Movement",
}

PRIORITY_ACTIVITIES: list[str] = [
    "Confined Space Work", "Work at Height", "Hot Work", "Electrical Work",
    "Lifting", "Excavation", "Pipeline/Line Work", "Loading/Unloading",
    "Maintenance", "Construction", "Driving", "Operations", "Material Handling", "Inspection"
]

HIGH_ENERGY_HAZARDS = {
    "Fall Hazard", "Toxic Atmosphere", "Oxygen Deficiency",
    "Stored Energy", "Electrical Energy", "Pressure", "Suspended Load", "Explosion"
}

PREVENTION_PATTERNS = [
    re.compile(r"\b(?:prevented|stopped|halted|intervened|prohibited)\b.*?\b(?:from|prior\s+to|before)\b", re.IGNORECASE),
    re.compile(r"\b(?:refused|declined|aborted)\b.*?\b(?:without|until|prior)\b", re.IGNORECASE),
    re.compile(r"\b(?:intervention|safety\s+standdown|stop\s+work)\b.*?\b(?:prevented|avoided|stopped)\b", re.IGNORECASE),
]

DOUBLE_NEGATION_PATTERNS = [
    re.compile(r"\b(?:not|never)\s+(?:missing|absent|lacking|unavailable|bypassed|failed|defeated)\b", re.IGNORECASE),
    re.compile(r"\b(?:did\s+not|was\s+not|were\s+not)\s+(?:work|enter|operate)\s+without\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class EvidenceGrounding:
    claim: str
    evidence_text: str
    sentence_idx: int
    matched_term: str
    match_method: str  # EXACT, FUZZY, TEMPORAL_INVERSION, SYNTAX_DEPENDENCY
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence_text": self.evidence_text,
            "sentence_idx": self.sentence_idx,
            "matched_term": self.matched_term,
            "match_method": self.match_method,
            "confidence": round(self.confidence, 4),
        }


@dataclass(frozen=True)
class CausalChain:
    activity: str | None
    hazard: str | None
    control: str | None
    control_status: ControlStatus
    barrier_failure: bool
    exposure: str  # SIF_PRECURSOR_EXPOSURE, CONTROLLED_ACTIVITY, UNMITIGATED_HAZARD, UNKNOWN_CONTROL_STATE
    relationship_type: str  # DIRECT_FAILURE, TEMPORAL_VIOLATION, PREVENTED_INTERVENTION, VERIFIED_BARRIER, UNKNOWN_STATE
    sif_precursor_type: str | None  # CONTROL_MISSING, CONTROL_UNVERIFIED, ENERGY_CONTROL_FAILURE, CONTROL_DEGRADATION, EXPOSURE
    confidence: float
    evidence_groundings: list[EvidenceGrounding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity": self.activity,
            "hazard": self.hazard,
            "control": self.control,
            "control_status": self.control_status.value,
            "barrier_failure": self.barrier_failure,
            "exposure": self.exposure,
            "relationship_type": self.relationship_type,
            "sif_precursor_type": self.sif_precursor_type,
            "confidence": round(self.confidence, 4),
            "evidence": [e.to_dict() for e in self.evidence_groundings],
        }


@dataclass(frozen=True)
class ReasoningConfidence:
    model_confidence: float
    extraction_confidence: float
    relationship_confidence: float
    evidence_confidence: float
    overall_confidence: float

    def to_dict(self) -> dict[str, float]:
        return {
            "model_confidence": round(self.model_confidence, 4),
            "extraction_confidence": round(self.extraction_confidence, 4),
            "relationship_confidence": round(self.relationship_confidence, 4),
            "evidence_confidence": round(self.evidence_confidence, 4),
            "overall_confidence": round(self.overall_confidence, 4),
        }


@dataclass(frozen=True)
class SafetyReasoningGraph:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    causal_chains: list[CausalChain]
    barrier_failure_detected: bool
    high_energy_hazard_present: bool
    precursor_detected: bool
    prevented_intervention: bool
    confidence: ReasoningConfidence
    reasoning_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "causal_chains": [c.to_dict() for c in self.causal_chains],
            "barrier_failure_detected": self.barrier_failure_detected,
            "high_energy_hazard_present": self.high_energy_hazard_present,
            "precursor_detected": self.precursor_detected,
            "prevented_intervention": self.prevented_intervention,
            "confidence": self.confidence.to_dict(),
            "reasoning_summary": self.reasoning_summary,
        }


class SafetyCausalReasoningEngine:
    """
    Core causal safety reasoning engine synthesizing multi-source NLP evidence,
    semantic representations, and domain safety taxonomy.
    """

    @classmethod
    def evaluate_causal_safety(
        cls,
        document: PreprocessedText,
        structured_evidence: StructuredEvidence,
        model_probability: float,
    ) -> SafetyReasoningGraph:
        """
        Main entrypoint: constructs causal chains, evaluates barrier states,
        resolves complex negations and temporal inversions, and builds the safety graph.
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        node_ids: set[str] = set()

        def add_node(nid: str, ntype: str, label: str, props: dict[str, Any] | None = None) -> None:
            if nid not in node_ids:
                node_ids.add(nid)
                nodes.append({
                    "id": nid,
                    "type": ntype,
                    "label": label,
                    "properties": props or {},
                })

        def add_edge(src: str, dst: str, rel: str, conf: float = 1.0) -> None:
            edges.append({
                "source": src,
                "target": dst,
                "relationship": rel,
                "confidence": round(conf, 4),
            })

        # 1. Identify Prevention & Interventions
        is_prevented = any(p.search(document.normalized_text) for p in PREVENTION_PATTERNS)

        # 2. Extract Base Entities from StructuredEvidence with hierarchy
        raw_activities = [item.normalized_concept for item in structured_evidence.get_by_type(EvidenceType.ACTIVITY)]
        raw_hazards = [item.normalized_concept for item in structured_evidence.get_by_type(EvidenceType.HAZARD)]
        controls = structured_evidence.get_by_type(EvidenceType.CONTROL)

        primary_activity = next((p for p in PRIORITY_ACTIVITIES if p in raw_activities), (raw_activities[0] if raw_activities else None))
        primary_hazard = raw_hazards[0] if raw_hazards else None

        # Infer hazard from control if not explicitly mentioned
        if not primary_hazard and controls:
            for c in controls:
                if c.normalized_concept in CONTROL_TO_HAZARD_MAP:
                    primary_hazard = CONTROL_TO_HAZARD_MAP[c.normalized_concept]
                    break

        # Infer hazard from activity if not explicitly mentioned
        if not primary_hazard and primary_activity:
            inferred_hazards = ACTIVITY_TO_HAZARD_MAP.get(primary_activity, [])
            if inferred_hazards:
                primary_hazard = inferred_hazards[0]

        # 3. Process Controls and Determine Rigorous Status
        control_status_map: dict[str, tuple[ControlStatus, str, list[EvidenceGrounding]]] = {}
        for c in controls:
            status, rel_type, groundings = cls._resolve_control_status(document, c)
            control_status_map[c.normalized_concept] = (status, rel_type, groundings)

        # 4. Infer Missing Required Controls if Hazard Exists
        if primary_hazard and not controls:
            required_controls = HAZARD_TO_CONTROL_MAP.get(primary_hazard, [])
            for req in required_controls[:1]:
                # Hazard present with zero control mentioned -> MISSING / UNKNOWN
                grounding = EvidenceGrounding(
                    claim=f"No safety control mentioned for {primary_hazard}",
                    evidence_text=document.original_text,
                    sentence_idx=0,
                    matched_term="<no_control>",
                    match_method="INFERRED_ABSENCE",
                    confidence=0.85,
                )
                control_status_map[req] = (ControlStatus.MISSING, "INFERRED_MISSING_CONTROL", [grounding])

        # 5. Build Causal Chains
        causal_chains: list[CausalChain] = []
        any_barrier_failed = False
        high_energy_present = (primary_hazard in HIGH_ENERGY_HAZARDS) or any(c in ("Fall Protection", "Gas Testing", "Energy Isolation", "Lockout Tagout") for c in control_status_map)

        if control_status_map:
            for ctrl_name, (c_status, rel_type, groundings) in control_status_map.items():
                chain_hazard = primary_hazard or CONTROL_TO_HAZARD_MAP.get(ctrl_name)
                chain_high_energy = (chain_hazard in HIGH_ENERGY_HAZARDS) or (ctrl_name in ("Fall Protection", "Gas Testing", "Energy Isolation", "Lockout Tagout"))
                if chain_high_energy:
                    high_energy_present = True

                is_fail = c_status in (
                    ControlStatus.NOT_VERIFIED,
                    ControlStatus.NOT_PERFORMED,
                    ControlStatus.FAILED,
                    ControlStatus.BYPASSED,
                    ControlStatus.MISSING,
                    ControlStatus.EXPIRED,
                )
                if is_prevented:
                    is_fail = False
                    rel_type = "PREVENTED_INTERVENTION"

                if is_fail:
                    any_barrier_failed = True

                # Exposure evaluation
                if is_prevented:
                    exposure = "CONTROLLED_ACTIVITY"
                    precursor_type = None
                elif is_fail:
                    exposure = "SIF_PRECURSOR_EXPOSURE" if chain_high_energy else "UNMITIGATED_HAZARD"
                    if c_status in (ControlStatus.MISSING, ControlStatus.NOT_PERFORMED):
                        precursor_type = "CONTROL_MISSING"
                    elif c_status == ControlStatus.NOT_VERIFIED:
                        precursor_type = "CONTROL_UNVERIFIED"
                    elif c_status in (ControlStatus.FAILED, ControlStatus.BYPASSED):
                        precursor_type = "ENERGY_CONTROL_FAILURE" if "Energy" in (chain_hazard or "") else "CONTROL_DEGRADATION"
                    else:
                        precursor_type = "CONTROL_DEGRADATION"
                elif c_status in (ControlStatus.VERIFIED, ControlStatus.PERFORMED):
                    exposure = "CONTROLLED_ACTIVITY"
                    precursor_type = None
                else:
                    exposure = "UNKNOWN_CONTROL_STATE"
                    precursor_type = "CONTROL_UNVERIFIED"

                chain_conf = 0.95 if groundings else 0.75
                chain = CausalChain(
                    activity=primary_activity,
                    hazard=chain_hazard,
                    control=ctrl_name,
                    control_status=c_status,
                    barrier_failure=is_fail,
                    exposure=exposure,
                    relationship_type=rel_type,
                    sif_precursor_type=precursor_type,
                    confidence=chain_conf,
                    evidence_groundings=groundings,
                )
                causal_chains.append(chain)

                # Graph Nodes & Edges
                c_node_id = f"control:{ctrl_name}"
                stat_node_id = f"status:{ctrl_name}:{c_status.value}"
                exp_node_id = f"exposure:{exposure}"

                add_node(c_node_id, "CONTROL", ctrl_name)
                add_node(stat_node_id, "STATUS", c_status.value, {"barrier_failure": is_fail})
                add_node(exp_node_id, "EXPOSURE", exposure)

                add_edge(c_node_id, stat_node_id, "HAS_STATUS", chain_conf)
                add_edge(stat_node_id, exp_node_id, "EVALUATES_TO", chain_conf)

                if primary_hazard:
                    h_node_id = f"hazard:{primary_hazard}"
                    add_node(h_node_id, "HAZARD", primary_hazard)
                    add_edge(h_node_id, c_node_id, "REQUIRES_BARRIER", 0.90)

                if primary_activity:
                    a_node_id = f"activity:{primary_activity}"
                    add_node(a_node_id, "ACTIVITY", primary_activity)
                    if primary_hazard:
                        add_edge(a_node_id, f"hazard:{primary_hazard}", "EXPOSES_TO", 0.90)

        elif primary_hazard:
            # Hazard detected with no controls mentioned
            chain = CausalChain(
                activity=primary_activity,
                hazard=primary_hazard,
                control=None,
                control_status=ControlStatus.MISSING,
                barrier_failure=True,
                exposure="SIF_PRECURSOR_EXPOSURE" if high_energy_present else "UNMITIGATED_HAZARD",
                relationship_type="UNCONTROLLED_HAZARD",
                sif_precursor_type="EXPOSURE",
                confidence=0.85,
                evidence_groundings=[
                    EvidenceGrounding(
                        claim=f"Unmitigated hazard exposure: {primary_hazard}",
                        evidence_text=document.original_text,
                        sentence_idx=0,
                        matched_term=primary_hazard,
                        match_method="EXACT",
                        confidence=0.85,
                    )
                ],
            )
            causal_chains.append(chain)
            any_barrier_failed = True

        # 6. Calculate Rigorous Multi-Dimensional Confidence
        model_conf = min(1.0, max(0.0, abs(model_probability - 0.5) * 2.0))
        ext_conf = 1.0 if (primary_activity and primary_hazard) else (0.8 if (primary_activity or primary_hazard) else 0.5)
        rel_conf = 0.95 if causal_chains else 0.50
        ev_conf = 0.90 if document.sentences else 0.40
        overall_conf = (model_conf * 0.35) + (ext_conf * 0.25) + (rel_conf * 0.25) + (ev_conf * 0.15)

        conf_obj = ReasoningConfidence(
            model_confidence=model_conf,
            extraction_confidence=ext_conf,
            relationship_confidence=rel_conf,
            evidence_confidence=ev_conf,
            overall_confidence=overall_conf,
        )

        # 7. Synthesize Explanations
        summary = cls._synthesize_causal_summary(
            primary_activity, primary_hazard, causal_chains, any_barrier_failed, is_prevented
        )

        return SafetyReasoningGraph(
            nodes=nodes,
            edges=edges,
            causal_chains=causal_chains,
            barrier_failure_detected=any_barrier_failed,
            high_energy_hazard_present=high_energy_present,
            precursor_detected=any_barrier_failed and high_energy_present,
            prevented_intervention=is_prevented,
            confidence=conf_obj,
            reasoning_summary=summary,
        )

    @classmethod
    def _resolve_control_status(
        cls,
        document: PreprocessedText,
        item: EvidenceItem,
    ) -> tuple[ControlStatus, str, list[EvidenceGrounding]]:
        """
        Performs advanced syntax-aware negation, prevention, double-negation,
        and temporal inversion parsing on a specific control evidence item.
        """
        concept = item.normalized_concept
        phrase = item.original_span.lower()
        full_text = document.normalized_text

        # 1. Double Negation Check
        # e.g., "Fall protection was not missing", "Did not work without harness"
        for d_pat in DOUBLE_NEGATION_PATTERNS:
            if d_pat.search(full_text):
                g = EvidenceGrounding(
                    claim=f"{concept} was present (double negation verified)",
                    evidence_text=document.original_text,
                    sentence_idx=0,
                    matched_term=d_pat.pattern,
                    match_method="DOUBLE_NEGATION_ANALYSIS",
                    confidence=0.95,
                )
                return ControlStatus.VERIFIED, "DOUBLE_NEGATION_ENFORCED", [g]

        # 2. Prevention / Intervention Check
        for p_pat in PREVENTION_PATTERNS:
            if p_pat.search(full_text):
                g = EvidenceGrounding(
                    claim=f"Intervention prevented unsafe exposure regarding {concept}",
                    evidence_text=document.original_text,
                    sentence_idx=0,
                    matched_term=p_pat.pattern,
                    match_method="PREVENTION_INTERVENTION",
                    confidence=0.98,
                )
                return ControlStatus.PERFORMED, "PREVENTED_INTERVENTION", [g]

        # 3. Locate Sentence & Context Window for Control
        matching_sentence = ""
        sentence_idx = 0
        for idx, s in enumerate(document.sentences):
            if phrase in s.lower():
                matching_sentence = s
                sentence_idx = idx
                break

        target_sentence = matching_sentence or document.normalized_text
        tokens = re.findall(r"\b\w+\b", target_sentence.lower())

        phrase_tokens = re.findall(r"\b\w+\b", phrase)
        start_idx = tokens.index(phrase_tokens[0]) if (phrase_tokens and phrase_tokens[0] in tokens) else 0
        end_idx = tokens.index(phrase_tokens[-1]) if (phrase_tokens and phrase_tokens[-1] in tokens) else len(tokens) - 1

        window_start = max(0, start_idx - 7)
        window_end = min(len(tokens), end_idx + 8)
        window = tokens[window_start:window_end]
        window_str = " ".join(window)

        # 4. Temporal Inversion Check
        # e.g., "Worker entered vessel before gas testing was completed"
        has_before = any(t in tokens for t in ("before", "prior"))
        before_idx = next((tokens.index(t) for t in ("before", "prior") if t in tokens), -1)

        temporal_inversion = False
        if has_before and before_idx != -1 and start_idx != -1:
            if before_idx < start_idx:
                # Action preceded control check
                prefix_tokens = tokens[:before_idx]
                has_action = any(
                    act in prefix_tokens for act in (
                        "entered", "working", "worked", "opened", "climbed",
                        "operated", "performed", "started", "began", "commenced",
                        "disassembled", "jumpered", "welded", "cut"
                    )
                )
                if has_action:
                    temporal_inversion = True

        if temporal_inversion:
            g = EvidenceGrounding(
                claim=f"{concept} verification occurred after hazardous work commenced",
                evidence_text=target_sentence,
                sentence_idx=sentence_idx,
                matched_term="before / prior temporal inversion",
                match_method="TEMPORAL_INVERSION",
                confidence=0.96,
            )
            return ControlStatus.NOT_VERIFIED, "TEMPORAL_VIOLATION", [g]

        # 5. Direct Negation & State Matchers
        has_not = any(t in window for t in ("not", "no", "never", "without", "absent", "missing", "unverified", "lacking"))
        has_verified = any(t in window for t in ("verified", "completed", "confirmed", "applied", "checked", "tested", "used", "installed", "functional"))
        has_bypassed = any(t in window_str for t in ("bypassed", "override", "overridden", "defeated", "jumpered"))
        has_missing = any(t in window for t in ("missing", "absent", "lacking", "unavailable", "omitted"))
        has_failed = any(t in window for t in ("failed", "damaged", "broken", "defective", "inadequate"))
        has_expired = "expired" in window
        has_without = "without" in window or "not used" in window_str or "did not use" in window_str

        status = ControlStatus.UNKNOWN
        rel_type = "OBSERVED_STATE"

        if has_bypassed:
            status = ControlStatus.BYPASSED
            rel_type = "DIRECT_BYPASS"
        elif has_expired:
            status = ControlStatus.EXPIRED
            rel_type = "EXPIRED_PERMIT"
        elif has_missing:
            status = ControlStatus.MISSING
            rel_type = "MISSING_BARRIER"
        elif has_failed:
            status = ControlStatus.FAILED
            rel_type = "EQUIPMENT_FAILURE"
        elif has_without:
            status = ControlStatus.NOT_PERFORMED
            rel_type = "UNPERFORMED_CONTROL"
        elif has_not and has_verified:
            status = ControlStatus.NOT_VERIFIED
            rel_type = "FAILED_VERIFICATION"
        elif has_not:
            status = ControlStatus.NOT_PERFORMED
            rel_type = "NEGATED_CONTROL"
        elif has_verified:
            status = ControlStatus.VERIFIED
            rel_type = "VERIFIED_BARRIER"
        elif any(t in window for t in ("planned", "scheduled", "discussed", "requested")):
            status = ControlStatus.UNKNOWN
            rel_type = "PROSPECTIVE_ACTION"

        g = EvidenceGrounding(
            claim=f"Control {concept} evaluated as {status.value}",
            evidence_text=target_sentence,
            sentence_idx=sentence_idx,
            matched_term=phrase,
            match_method="CONTEXT_WINDOW_ANALYSIS",
            confidence=0.92,
        )
        return status, rel_type, [g]

    @classmethod
    def _synthesize_causal_summary(
        cls,
        activity: str | None,
        hazard: str | None,
        chains: list[CausalChain],
        barrier_failed: bool,
        is_prevented: bool,
    ) -> str:
        """Synthesizes human-readable, grounded causal reasoning text."""
        parts: list[str] = []

        if is_prevented:
            parts.append("Safety intervention successfully halted operations before hazardous exposure occurred.")
            return " ".join(parts)

        if activity and hazard:
            parts.append(f"Activity '{activity}' exposed personnel to high-consequence hazard '{hazard}'.")
        elif hazard:
            parts.append(f"High-consequence hazard '{hazard}' was identified in the narrative.")

        for chain in chains:
            if chain.control:
                if chain.barrier_failure:
                    parts.append(
                        f"Required barrier '{chain.control}' was {chain.control_status.value.replace('_', ' ').lower()}, "
                        f"resulting in unmitigated {chain.exposure.replace('_', ' ').lower()}."
                    )
                else:
                    parts.append(f"Required barrier '{chain.control}' was confirmed {chain.control_status.value.lower()}.")

        if barrier_failed:
            parts.append("This causal chain represents an active SIF precursor condition requiring immediate operational review.")
        else:
            parts.append("All identified critical barriers were verified effective.")

        return " ".join(parts)
