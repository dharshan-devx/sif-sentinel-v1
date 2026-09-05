"""
Orchestration service for SIF Sentinel Phase 5E Narrative Translation & Explainability Layer.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.services.narrative.narrative_models import (
    NarrativeContext,
    NarrativeMode,
    NarrativeOutput,
    ValidationStatus,
)
from app.services.narrative.narrative_provider import (
    DeterministicFallbackProvider,
    GeminiNarrativeProvider,
    NarrativeProvider,
)
from app.services.narrative.narrative_validator import NarrativeValidator

logger = logging.getLogger(__name__)


class NarrativeTranslationService:
    """
    Main service coordinating context assembly, narrative provider invocation,
    post-generation fact validation, and deterministic fallback enforcement.
    """

    def __init__(self, provider: NarrativeProvider | None = None) -> None:
        self.settings = get_settings()
        if provider is not None:
            self.provider = provider
        else:
            # Check configuration for LLM provider
            if self.settings.llm_enabled and self.settings.llm_api_key:
                self.provider = GeminiNarrativeProvider(
                    api_key=self.settings.llm_api_key,
                    model=self.settings.llm_model,
                    timeout_seconds=self.settings.llm_timeout_seconds,
                )
            else:
                self.provider = DeterministicFallbackProvider()

    async def translate(
        self,
        context: NarrativeContext,
        mode: NarrativeMode = NarrativeMode.EXECUTIVE,
    ) -> NarrativeOutput:
        """
        Translates deterministic safety context into a validated structured narrative.
        """
        # 1. Execute Provider Generation
        try:
            raw_output = await self.provider.generate_narrative(context, mode)
        except Exception as exc:
            logger.warning("Narrative provider generation exception: %s. Applying fallback.", exc)
            fallback = await DeterministicFallbackProvider().generate_narrative(context, mode)
            fallback.validation_status = ValidationStatus.FALLBACK_APPLIED
            fallback.validation_errors.append(f"Provider exception: {str(exc)}")
            return fallback

        # 2. Deterministic Post-Generation Validation
        val_result = NarrativeValidator.validate(raw_output, context)

        if not val_result.is_valid:
            logger.warning(
                "Generated narrative failed deterministic fact validation: %s. Applying fallback.",
                val_result.errors,
            )
            # Apply deterministic fallback to guarantee safety and mathematical truth
            fallback = await DeterministicFallbackProvider().generate_narrative(context, mode)
            fallback.validation_status = ValidationStatus.FALLBACK_APPLIED
            fallback.validation_errors = val_result.errors
            return fallback

        raw_output.validation_status = ValidationStatus.VALID
        return raw_output

    @classmethod
    def build_context_from_analysis(
        cls,
        incident_text: str,
        safety_graph: dict[str, Any] | None = None,
        causal_chains: list[dict[str, Any]] | None = None,
        risk_score: int | None = None,
        risk_priority: str | None = None,
        sif_potential: bool | None = None,
        sif_level: str | None = None,
        life_saving_rule: str | None = None,
        evidence_span: str | None = None,
        evidence_terms: list[str] | None = None,
        counterfactual: dict[str, Any] | None = None,
        confidence: float | None = None,
        reasoning_summary: str | None = None,
    ) -> NarrativeContext:
        """
        Helper to construct a robust NarrativeContext from loose or dictionary-based API inputs.
        """
        chains = causal_chains or (safety_graph.get("causal_chains") if safety_graph else []) or []
        primary_chain = chains[0] if chains else {}

        # Derive barrier information
        barrier = primary_chain.get("control")
        status = primary_chain.get("control_status", "UNKNOWN")
        failure = primary_chain.get("barrier_failure", False)
        activity = primary_chain.get("activity")
        hazard = primary_chain.get("hazard")

        if not activity and safety_graph and "activity" in safety_graph:
            act_obj = safety_graph["activity"]
            activity = act_obj.get("activity_type") if isinstance(act_obj, dict) else str(act_obj)

        if not hazard and safety_graph and "hazard" in safety_graph:
            haz_obj = safety_graph["hazard"]
            hazard = haz_obj.get("hazard_type") if isinstance(haz_obj, dict) else str(haz_obj)

        if not barrier and safety_graph and "control" in safety_graph:
            ctrl_obj = safety_graph["control"]
            if isinstance(ctrl_obj, dict):
                barrier = ctrl_obj.get("control_name")
                status = ctrl_obj.get("control_status", status)

        resolved_sif_potential = (
            sif_potential
            if sif_potential is not None
            else bool(safety_graph.get("precursor_detected", True) if safety_graph else True)
        )

        resolved_risk_score = risk_score if risk_score is not None else 85
        resolved_risk_priority = (
            risk_priority
            if risk_priority is not None
            else ("CRITICAL" if resolved_risk_score >= 81 else "HIGH" if resolved_risk_score >= 56 else "MEDIUM")
        )

        return NarrativeContext(
            incident_text=incident_text,
            sif_potential=resolved_sif_potential,
            sif_level=sif_level or ("PSIF" if resolved_sif_potential else "NON_SIF"),
            model_probability=0.95 if resolved_sif_potential else 0.15,
            risk_score=resolved_risk_score,
            risk_priority=resolved_risk_priority,
            activity=activity,
            hazard=hazard,
            is_high_energy_hazard=bool(hazard in ["Toxic Atmosphere", "High Pressure", "Stored Energy", "Flammable Gas"]),
            barrier=barrier,
            barrier_status=str(status),
            barrier_failure=bool(failure or str(status).upper() in ["NOT_PERFORMED", "FAILED", "BYPASSED", "MISSING", "EXPIRED"]),
            life_saving_rule=life_saving_rule,
            evidence_span=evidence_span,
            evidence_terms=evidence_terms or [],
            causal_chains=chains,
            confidence=confidence if confidence is not None else 0.92,
            reasoning_summary=reasoning_summary,
            counterfactual=counterfactual,
        )
