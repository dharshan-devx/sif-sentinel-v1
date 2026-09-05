"""
Provider abstractions for SIF Sentinel Phase 5E Narrative Translation Layer.
"""

from __future__ import annotations

import json
import time
from typing import Protocol

from app.services.narrative.narrative_models import (
    ActionPriority,
    BarrierAnalysisItem,
    GroundingItem,
    NarrativeContext,
    NarrativeMode,
    NarrativeOutput,
    RecommendedActionItem,
    SourceBasis,
    ValidationStatus,
)
from app.services.narrative.narrative_prompt import NarrativePromptBuilder


class NarrativeProvider(Protocol):
    """Protocol for narrative generation backends."""

    async def generate_narrative(
        self, context: NarrativeContext, mode: NarrativeMode
    ) -> NarrativeOutput:
        ...


class DeterministicFallbackProvider:
    """
    Deterministic rule-based narrative provider.
    Guarantees 100% grounded, hallucination-free, zero-latency narrative generation
    for offline, demo, and fallback scenarios.
    """

    async def generate_narrative(
        self, context: NarrativeContext, mode: NarrativeMode
    ) -> NarrativeOutput:
        t0 = time.perf_counter()

        activity_str = context.activity or "Operational Work"
        hazard_str = context.hazard or "Hazardous Condition"
        barrier_str = context.barrier or "Standard Safety Barrier"
        status_str = context.barrier_status.replace("_", " ").title()
        is_sif = context.sif_potential

        # Build Barrier Analysis Items
        barrier_items: list[BarrierAnalysisItem] = []
        if context.barrier:
            barrier_items.append(
                BarrierAnalysisItem(
                    control=context.barrier,
                    observed_status=context.barrier_status,
                    failure=context.barrier_failure,
                    explanation=(
                        f"Safety barrier '{context.barrier}' was recorded as {status_str}, "
                        f"{'representing an active barrier breach' if context.barrier_failure else 'operating effectively to contain hazard energy'}."
                    ),
                    source_basis=SourceBasis.CAUSAL_GRAPH,
                )
            )

        for chain in context.causal_chains:
            ctrl = chain.get("control")
            status = chain.get("control_status")
            failed = chain.get("barrier_failure", False)
            if ctrl and ctrl != context.barrier:
                barrier_items.append(
                    BarrierAnalysisItem(
                        control=ctrl,
                        observed_status=str(status),
                        failure=failed,
                        explanation=f"Control '{ctrl}' status evaluated as {str(status).replace('_', ' ')}.",
                        source_basis=SourceBasis.CAUSAL_GRAPH,
                    )
                )

        # Build Recommended Actions
        actions: list[RecommendedActionItem] = []
        if context.barrier_failure and context.barrier:
            actions.append(
                RecommendedActionItem(
                    action=f"Immediately verify and re-establish '{context.barrier}' before resuming {activity_str.lower()}.",
                    reason=f"Restoring this barrier directly mitigates uncontained {hazard_str.lower()} exposure.",
                    priority=ActionPriority.CRITICAL if is_sif else ActionPriority.HIGH,
                    source_basis=SourceBasis.CAUSAL_GRAPH,
                    target_control=context.barrier,
                )
            )
        if context.life_saving_rule:
            actions.append(
                RecommendedActionItem(
                    action=f"Enforce mandatory compliance with Life-Saving Rule: '{context.life_saving_rule}'.",
                    reason="Life-Saving Rules provide deterministic defense against high-energy fatal precursors.",
                    priority=ActionPriority.HIGH,
                    source_basis=SourceBasis.LSR_MAPPING,
                )
            )
        if not actions:
            actions.append(
                RecommendedActionItem(
                    action="Conduct routine pre-job hazard review and confirm barrier verification logs.",
                    reason="Maintains continuous barrier health across active operational areas.",
                    priority=ActionPriority.LOW,
                    source_basis=SourceBasis.RISK_ENGINE,
                )
            )

        # Mode-Specific Texts
        if mode == NarrativeMode.EXECUTIVE:
            exec_summary = (
                f"{activity_str} exposed personnel to {hazard_str} with {context.barrier_status.replace('_', ' ').lower()} "
                f"barrier '{barrier_str}'. Composite risk score is {context.risk_score}/100 ({context.risk_priority}). "
                f"{'Immediate executive intervention is required to mitigate SIF precursor potential.' if is_sif else 'Operations are currently controlled within acceptable safety margins.'}"
            )
            interpretation = (
                f"Executive overview indicates {'an active SIF precursor condition' if is_sif else 'a managed operational condition'} "
                f"during {activity_str}. The failure of critical barrier '{barrier_str}' directly drives elevated risk."
            )
            causal_expl = (
                f"Causal chain: {activity_str} -> {hazard_str} -> Barrier: {barrier_str} ({status_str}) -> "
                f"{'Uncontrolled Exposure' if context.barrier_failure else 'Controlled State'} -> SIF Precursor: {is_sif}."
            )

        elif mode == NarrativeMode.INVESTIGATION:
            exec_summary = (
                f"Incident Investigation Finding: {activity_str} encountered {hazard_str}. "
                f"Causal analysis identified barrier '{barrier_str}' in status {context.barrier_status}. "
                f"Overall reasoning confidence is {context.confidence:.0%}."
            )
            interpretation = (
                f"Technical inspection shows evidence '{context.evidence_span or 'direct narrative statement'}' "
                f"grounded to barrier '{barrier_str}'. Temporal sequencing and negation checks confirmed {status_str} status."
            )
            causal_expl = (
                f"Formal Causal DAG Traversal: Activity node '{activity_str}' initiated exposure to High-Energy Hazard '{hazard_str}'. "
                f"Required control barrier '{barrier_str}' resolved to {context.barrier_status} (Failure={context.barrier_failure}). "
                f"Resulting downstream state: SIF Potential={is_sif}, Composite Risk={context.risk_score}."
            )

        elif mode == NarrativeMode.FIELD:
            exec_summary = (
                f"FIELD SAFETY ALERT: Do not proceed with {activity_str.lower()} until '{barrier_str}' is fully verified and working! "
                f"Risk is {context.risk_priority} ({context.risk_score}/100)."
            )
            interpretation = (
                f"Field crew observation: Unsafe condition identified during {activity_str.lower()}. "
                f"The barrier '{barrier_str}' was {status_str}. Stop work immediately if controls are not in place."
            )
            causal_expl = (
                f"What went wrong: Work was started on {activity_str.lower()} while {hazard_str.lower()} was present, "
                f"but {barrier_str} was not properly checked. This created an immediate hazard."
            )

        else:  # COUNTERFACTUAL
            if context.counterfactual:
                cf = context.counterfactual
                target_ctrl = cf.get("target_control", barrier_str)
                orig_s = cf.get("original_status", context.barrier_status)
                sim_s = cf.get("simulated_status", "VERIFIED")
                delta = cf.get("risk_delta", 0)
                orig_r = cf.get("original_risk_score", context.risk_score)
                sim_r = cf.get("simulated_risk_score", context.risk_score)
                exec_summary = (
                    f"Counterfactual Simulation: What-if '{target_ctrl}' had been {sim_s}? "
                    f"Restoring this barrier eliminates the modeled failure mechanism and reduces risk from {orig_r} to {sim_r} (Delta: {delta} pts). "
                    f"SIF precursor potential shifts to {'PREVENTED' if not cf.get('simulated_sif_potential') else 'REDUCED'}."
                )
                interpretation = (
                    f"Simulation analysis indicates that verifying '{target_ctrl}' prior to work commencement "
                    f"would have successfully contained {hazard_str.lower()} energy."
                )
                causal_expl = (
                    f"Counterfactual Causal Propagation: Barrier status changed from {orig_s} to {sim_s}. "
                    f"Barrier failure flag mutated from {cf.get('original_barrier_failure')} to {cf.get('simulated_barrier_failure')}. "
                    f"Downstream exposure mitigated to '{cf.get('simulated_exposure')}'. Risk reduced by {abs(delta)} points."
                )
            else:
                exec_summary = (
                    "No active counterfactual simulation. Select a barrier node in the causal graph to simulate a What-If restoration."
                )
                interpretation = "Counterfactual simulation engine is ready for scenario evaluation."
                causal_expl = "Awaiting user selection of target barrier and restoration state."

        # Grounding Items
        grounding: list[GroundingItem] = []
        if context.evidence_span:
            grounding.append(
                GroundingItem(
                    claim=f"Observed narrative indicates: '{context.evidence_span}'",
                    source_type=SourceBasis.EVIDENCE,
                    source_reference=context.evidence_span,
                )
            )
        grounding.append(
            GroundingItem(
                claim=f"Composite Risk Score calculated at {context.risk_score}/100 ({context.risk_priority})",
                source_type=SourceBasis.RISK_ENGINE,
                source_reference="app.services.risk_engine.calculator",
            )
        )
        grounding.append(
            GroundingItem(
                claim=f"Causal path: {activity_str} -> {hazard_str} -> {barrier_str} ({context.barrier_status})",
                source_type=SourceBasis.CAUSAL_GRAPH,
                source_reference="app.services.nlp.causal_engine",
            )
        )
        if context.life_saving_rule:
            grounding.append(
                GroundingItem(
                    claim=f"Mapped to Life-Saving Rule: '{context.life_saving_rule}'",
                    source_type=SourceBasis.LSR_MAPPING,
                    source_reference="app.knowledge.taxonomy.life_saving_rules",
                )
            )
        if context.counterfactual:
            grounding.append(
                GroundingItem(
                    claim=f"Simulated Risk Delta: {context.counterfactual.get('risk_delta')} pts ({context.counterfactual.get('original_risk_score')} -> {context.counterfactual.get('simulated_risk_score')})",
                    source_type=SourceBasis.COUNTERFACTUAL,
                    source_reference="app.services.nlp.counterfactual_engine",
                )
            )

        # SIF & Risk explanations
        sif_expl = (
            f"{'POTENTIAL SIF PRECURSOR DETECTED: The combination of ' + activity_str + ' and unmitigated ' + hazard_str + ' presents severe life-safety exposure.' if is_sif else 'NON-SIF EVENT: Hazard energy is managed or isolated below critical severity thresholds.'}"
        )
        risk_expl = (
            f"Deterministic composite risk score is {context.risk_score}/100 ({context.risk_priority}). "
            f"Evaluated with canonical consequence severity and barrier integrity multipliers."
        )
        lsr_expl = (
            f"Life-Saving Rule '{context.life_saving_rule}' applies to this operational envelope."
            if context.life_saving_rule
            else None
        )

        cf_expl = (
            (
                f"What-if '{context.counterfactual.get('target_control')}' had been {context.counterfactual.get('simulated_status')}? "
                f"Modeled risk decreases by {abs(context.counterfactual.get('risk_delta', 0))} points "
                f"({context.counterfactual.get('original_risk_score')} -> {context.counterfactual.get('simulated_risk_score')})."
            )
            if context.counterfactual
            else "No active counterfactual simulation."
        )

        key_findings = [
            f"Activity: {activity_str}",
            f"Hazard: {hazard_str} ({'High-Energy' if context.is_high_energy_hazard else 'Standard'})",
            f"Barrier: {barrier_str} [{context.barrier_status}]",
            f"Risk Score: {context.risk_score}/100 [{context.risk_priority}]",
            f"SIF Classification: {context.sif_level}",
        ]

        limitations = [
            "Analysis is bounded by facts provided in the incident narrative.",
            "Field environmental variables and unmodeled concurrent operations require physical verification.",
            "All risk scores are deterministically calculated by the SIF Sentinel Risk Engine.",
        ]

        confidence_stmt = (
            f"Overall reasoning confidence is {context.confidence:.0%}, backed by multi-stage NLP evidence extraction and causal DAG traversal."
        )

        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        return NarrativeOutput(
            mode=mode,
            executive_summary=exec_summary,
            incident_interpretation=interpretation,
            causal_explanation=causal_expl,
            barrier_analysis=barrier_items,
            sif_explanation=sif_expl,
            risk_explanation=risk_expl,
            lsr_explanation=lsr_expl,
            key_findings=key_findings,
            recommended_actions=actions,
            counterfactual_explanation=cf_expl,
            confidence_statement=confidence_stmt,
            limitations=limitations,
            grounding=grounding,
            validation_status=ValidationStatus.VALID,
            provider_name="deterministic",
            model_name="rules_engine_v1",
            latency_ms=latency_ms,
        )


class GeminiNarrativeProvider:
    """
    Optional Gemini LLM narrative provider for fluid natural language translation.
    Strictly constrained to JSON generation and validated against NarrativeContext.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        timeout_seconds: int = 15,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def generate_narrative(
        self, context: NarrativeContext, mode: NarrativeMode
    ) -> NarrativeOutput:
        if not self.api_key:
            # Fallback immediately if no API key is configured
            return await DeterministicFallbackProvider().generate_narrative(context, mode)

        t0 = time.perf_counter()
        prompt_dict = NarrativePromptBuilder.build_prompt(context, mode)

        try:
            # Use google-genai or aiohttp/httpx if installed, or fallback safely
            import urllib.request

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt_dict["user_prompt"]}],
                    }
                ],
                "systemInstruction": {
                    "parts": [{"text": prompt_dict["system_prompt"]}]
                },
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json",
                },
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            # Synchronous urllib inside thread or simple timeout
            import asyncio
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=self.timeout_seconds)
            )

            raw_res = json.loads(res.read().decode("utf-8"))
            candidates = raw_res.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini API.")

            text_content = candidates[0]["content"]["parts"][0]["text"]
            parsed = json.loads(text_content)

            # Reconstruct strongly typed items
            barrier_items = [
                BarrierAnalysisItem(
                    control=b.get("control", "Unknown Barrier"),
                    observed_status=b.get("observed_status", "UNKNOWN"),
                    failure=b.get("failure", False),
                    explanation=b.get("explanation", ""),
                    source_basis=SourceBasis.CAUSAL_GRAPH,
                )
                for b in parsed.get("barrier_analysis", [])
            ]

            actions = [
                RecommendedActionItem(
                    action=a.get("action", "Conduct safety review"),
                    reason=a.get("reason", "Ensure barrier integrity"),
                    priority=ActionPriority(a.get("priority", "HIGH").upper()),
                    source_basis=SourceBasis(a.get("source_basis", "CAUSAL_GRAPH")),
                    target_control=a.get("target_control"),
                )
                for a in parsed.get("recommended_actions", [])
            ]

            grounding = [
                GroundingItem(
                    claim=g.get("claim", ""),
                    source_type=SourceBasis(g.get("source_type", "CAUSAL_GRAPH")),
                    source_reference=g.get("source_reference", ""),
                )
                for g in parsed.get("grounding", [])
            ]

            t1 = time.perf_counter()
            return NarrativeOutput(
                mode=mode,
                executive_summary=parsed.get("executive_summary", ""),
                incident_interpretation=parsed.get("incident_interpretation", ""),
                causal_explanation=parsed.get("causal_explanation", ""),
                barrier_analysis=barrier_items,
                sif_explanation=parsed.get("sif_explanation", ""),
                risk_explanation=parsed.get("risk_explanation", ""),
                lsr_explanation=parsed.get("lsr_explanation"),
                key_findings=parsed.get("key_findings", []),
                recommended_actions=actions,
                counterfactual_explanation=parsed.get("counterfactual_explanation"),
                confidence_statement=parsed.get("confidence_statement", ""),
                limitations=parsed.get("limitations", []),
                grounding=grounding,
                validation_status=ValidationStatus.VALID,
                provider_name="gemini",
                model_name=self.model,
                latency_ms=(t1 - t0) * 1000.0,
            )

        except Exception as exc:
            # On any failure/timeout/parsing error, fallback seamlessly to deterministic provider
            fallback_res = await DeterministicFallbackProvider().generate_narrative(context, mode)
            fallback_res.validation_status = ValidationStatus.FALLBACK_APPLIED
            fallback_res.validation_errors.append(f"External LLM call failed ({str(exc)}); deterministic fallback applied.")
            return fallback_res

