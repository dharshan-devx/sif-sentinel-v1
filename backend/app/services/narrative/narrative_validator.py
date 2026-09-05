"""
Deterministic post-generation validator for SIF Sentinel Phase 5E.

Ensures that LLM or generated narratives never contradict, hallucinate,
or mutate the deterministic safety findings.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.narrative.narrative_models import (
    NarrativeContext,
    NarrativeMode,
    NarrativeOutput,
    ValidationResult,
    ValidationStatus,
)


class NarrativeValidator:
    """
    Validates generated narrative output against the authoritative NarrativeContext.
    Rejects hallucinations, contradictory numbers, inverted barrier states,
    or falsified counterfactual transitions.
    """

    @classmethod
    def validate(cls, output: NarrativeOutput, context: NarrativeContext) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Validate SIF Potential Consistency
        cls._validate_sif_consistency(output, context, errors)

        # 2. Validate Risk Score Consistency
        cls._validate_risk_consistency(output, context, errors)

        # 3. Validate Barrier Analysis Integrity
        cls._validate_barrier_analysis(output, context, errors)

        # 4. Validate Counterfactual Consistency (if in COUNTERFACTUAL mode or scenario present)
        cls._validate_counterfactual(output, context, errors)

        # 5. Validate Grounding Claims
        cls._validate_grounding(output, context, warnings)

        if errors:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.REJECTED,
                errors=errors,
                warnings=warnings,
            )

        return ValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            errors=[],
            warnings=warnings,
        )

    @classmethod
    def _validate_sif_consistency(
        cls, output: NarrativeOutput, context: NarrativeContext, errors: list[str]
    ) -> None:
        # 1. Anti-Jailbreak / Prompt Injection Leakage Check
        all_text = (
            output.executive_summary
            + " "
            + output.incident_interpretation
            + " "
            + output.causal_explanation
            + " "
            + output.sif_explanation
            + " "
            + output.risk_explanation
        ).lower()

        jailbreak_signatures = [
            "ignore all previous",
            "ignore previous instructions",
            "i am now a poet",
            "as an ai language model, i can ignore",
            "system override",
            "classified as safe because user said",
        ]
        for sig in jailbreak_signatures:
            if sig in all_text:
                errors.append(f"Prompt injection artifact or jailbreak signature detected: '{sig}'.")

        # 2. SIF Potential Consistency
        sif_text = (output.sif_explanation + " " + output.executive_summary).lower()

        if context.sif_potential:
            # Check for hallucinated claim of non-SIF
            if re.search(r"\b(no sif potential|not a sif|non-sif|completely safe|zero risk)\b", sif_text):
                # Only flag if not discussing counterfactual simulation
                if output.mode != NarrativeMode.COUNTERFACTUAL:
                    errors.append("Output incorrectly claims incident is non-SIF despite deterministic SIF finding.")
        else:
            if re.search(r"\b(confirmed sif precursor|critical fatality precursor)\b", sif_text):
                if not context.is_high_energy_hazard:
                    errors.append("Output claims confirmed SIF precursor when deterministic engine classified as non-SIF.")

        # 3. SIF Classification Level Check (PSIF vs SIF vs NON_SIF)
        if context.sif_level and output.mode != NarrativeMode.COUNTERFACTUAL:
            if context.sif_level == "NON_SIF" and "potential sif" in sif_text:
                errors.append("Output claims Potential SIF when deterministic classification is NON_SIF.")
            elif context.sif_level == "PSIF" and "non-sif" in sif_text:
                errors.append("Output claims NON_SIF when deterministic classification is PSIF.")

    @classmethod
    def _validate_risk_consistency(
        cls, output: NarrativeOutput, context: NarrativeContext, errors: list[str]
    ) -> None:
        # Extract explicit risk score numbers from risk_explanation or executive_summary
        full_text = output.risk_explanation + " " + output.executive_summary
        
        # Look for explicit statements like "risk score is 45", "score of 30", "risk score: 25"
        matches = re.findall(r"risk\s+score\s*(?:of|is|:)?\s*(\d{1,3})", full_text, re.IGNORECASE)
        for m in matches:
            score_val = int(m)
            # In counterfactual mode, both original and simulated scores may appear
            if output.mode == NarrativeMode.COUNTERFACTUAL and context.counterfactual:
                sim_score = context.counterfactual.get("simulated_risk_score")
                orig_score = context.counterfactual.get("original_risk_score", context.risk_score)
                if score_val not in (context.risk_score, sim_score, orig_score):
                    errors.append(
                        f"Hallucinated risk score {score_val} detected. Expected observed {context.risk_score} or simulated {sim_score}."
                    )
            else:
                if score_val != context.risk_score:
                    errors.append(
                        f"Hallucinated risk score {score_val} detected. Deterministic risk score is {context.risk_score}."
                    )

    @classmethod
    def _validate_barrier_analysis(
        cls, output: NarrativeOutput, context: NarrativeContext, errors: list[str]
    ) -> None:
        if not output.barrier_analysis and context.barrier:
            errors.append(f"Missing barrier analysis for identified barrier '{context.barrier}'.")

        context_barriers = {}
        if context.barrier:
            context_barriers[context.barrier.lower()] = context.barrier_status
        for chain in context.causal_chains:
            ctrl = chain.get("control")
            status = chain.get("control_status")
            if ctrl and status:
                context_barriers[ctrl.lower()] = str(status)

        for item in output.barrier_analysis:
            ctrl_name = item.control.lower()
            # If control exists in context, check status
            for k, expected_status in context_barriers.items():
                if k in ctrl_name or ctrl_name in k:
                    if item.observed_status.upper() != expected_status.upper():
                        # In non-counterfactual modes, observed status must strictly match
                        if output.mode != NarrativeMode.COUNTERFACTUAL:
                            errors.append(
                                f"Contradictory barrier status for '{item.control}'. Generated '{item.observed_status}', expected '{expected_status}'."
                            )

    @classmethod
    def _validate_counterfactual(
        cls, output: NarrativeOutput, context: NarrativeContext, errors: list[str]
    ) -> None:
        if output.mode == NarrativeMode.COUNTERFACTUAL:
            if not context.counterfactual:
                # Must acknowledge no simulation is active rather than hallucinating
                if "no simulation" not in output.counterfactual_explanation.lower() and "no active" not in output.counterfactual_explanation.lower():
                    # If it fabricated a specific scenario without context
                    if re.search(r"simulat(ed|ion)\s+risk\s+of\s+\d+", output.counterfactual_explanation, re.IGNORECASE):
                        errors.append("Hallucinated counterfactual simulation details when no simulation was active.")
            else:
                cf = context.counterfactual
                exp_delta = cf.get("risk_delta")
                # Look for delta mentions
                matches = re.findall(r"delta\s*(?:of|:)?\s*(-?\d+)", output.counterfactual_explanation, re.IGNORECASE)
                for m in matches:
                    delta_val = int(m)
                    if exp_delta is not None and delta_val != exp_delta and abs(delta_val) != abs(exp_delta):
                        errors.append(
                            f"Contradictory counterfactual risk delta {delta_val}. Deterministic delta is {exp_delta}."
                        )

    @classmethod
    def _validate_grounding(
        cls, output: NarrativeOutput, context: NarrativeContext, warnings: list[str]
    ) -> None:
        if not output.grounding:
            warnings.append("Narrative output contains no grounding provenance records.")
        for g in output.grounding:
            if not g.claim or not g.source_reference:
                warnings.append("Grounding record has empty claim or source reference.")

