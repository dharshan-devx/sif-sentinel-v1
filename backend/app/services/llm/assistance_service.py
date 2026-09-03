"""LLMAssistanceService — orchestrates optional LLM assistance.

Responsibilities
----------------
- Determines whether LLM assistance is enabled.
- Obtains the configured provider from LLMManager.
- Builds a tightly scoped context (no JWTs, no credentials).
- Enforces the LLM_MAX_CALLS_PER_ANALYSIS limit (default: 1).
- Handles provider failures and produces a safe fallback LLMResult.
- Exposes provider provenance metadata.

Authority boundary
------------------
This service NEVER modifies SIF, LSR, risk, precursor, or review fields.
It returns an LLMResult whose `summary` field is assistive content only.
"""

from typing import Any

import structlog

from app.core.config import get_settings
from app.services.llm.manager import LLMManager
from app.services.llm.result import LLMResult

logger = structlog.get_logger(__name__)


class LLMAssistanceService:
    """Application-level service for optional LLM reviewer assistance."""

    @staticmethod
    async def request_reviewer_summary(
        report_text: str,
        structured_evidence: dict[str, Any],
        authoritative_results: dict[str, Any],
    ) -> LLMResult:
        """Request a reviewer summary from the configured LLM provider.

        Returns an LLMResult with success=False and an appropriate error_code
        in every failure scenario — the caller is never expected to handle
        exceptions from this method.

        Parameters
        ----------
        report_text:
            The original, untrusted report text.  Passed to the provider as
            source data (not as an instruction).
        structured_evidence:
            Extracted NLP entities (activity, hazard, barrier, …).
        authoritative_results:
            Deterministic safety outputs (SIF, risk score, priority, …).
            These are informational context for the reviewer summary only.
        """
        settings = get_settings()

        # ── Fast-path: LLM disabled ────────────────────────────────────────
        if not settings.llm_enabled:
            return LLMResult(
                success=False,
                provider="none",
                model="none",
                operation="reviewer_summary",
                error_code="LLM_DISABLED",
            )

        # ── Validate call limit ────────────────────────────────────────────
        # Per spec: LLM_MAX_CALLS_PER_ANALYSIS defaults to 1.
        # If misconfigured (< 1), fail safely rather than silently skipping.
        max_calls = settings.llm_max_calls_per_analysis
        if max_calls < 1:
            logger.error(
                "LLM_MAX_CALLS_PER_ANALYSIS is set below 1; "
                "refusing to proceed to avoid silent misconfiguration",
                configured_value=max_calls,
            )
            return LLMResult(
                success=False,
                provider=settings.llm_provider,
                model=settings.llm_model,
                operation="reviewer_summary",
                error_code="CONFIGURATION_ERROR",
            )

        # ── Obtain provider ────────────────────────────────────────────────
        provider = LLMManager.get_provider()
        if provider is None:
            logger.warning(
                "LLM is enabled but no provider could be obtained",
                configured_provider=settings.llm_provider,
            )
            return LLMResult(
                success=False,
                provider=settings.llm_provider,
                model=settings.llm_model,
                operation="reviewer_summary",
                error_code="PROVIDER_UNAVAILABLE",
            )

        # ── Build tightly scoped context ───────────────────────────────────
        # Only the minimum necessary data is transmitted.
        # NO: JWTs, API keys, passwords, audit history, internal secrets.
        # The report text is explicitly labelled as untrusted data when
        # the provider builds the prompt.
        context: dict[str, Any] = {
            "report_text": report_text,
            "structured_evidence": structured_evidence,
            "authoritative_safety_results": authoritative_results,
        }

        # ── Single bounded call (max_calls == 1 in default config) ─────────
        logger.info(
            "Requesting LLM reviewer summary",
            provider=settings.llm_provider,
            model=settings.llm_model,
        )

        try:
            result = await provider.generate_reviewer_summary(context)
        except Exception as exc:
            # The provider should never raise, but be defensive.
            logger.error(
                "Unexpected error from LLM provider",
                # Do not log exc directly — it may contain API response details
                error_type=type(exc).__name__,
            )
            return LLMResult(
                success=False,
                provider=settings.llm_provider,
                model=settings.llm_model,
                operation="reviewer_summary",
                error_code="UNEXPECTED_ERROR",
            )

        logger.info(
            "LLM reviewer summary complete",
            provider=settings.llm_provider,
            success=result.success,
            latency_ms=result.latency_ms,
            error_code=result.error_code,
        )
        return result
