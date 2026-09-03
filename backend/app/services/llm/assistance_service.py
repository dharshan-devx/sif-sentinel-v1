from app.services.llm.manager import LLMManager
from app.services.llm.result import LLMResult
from app.core.config import get_settings
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

class LLMAssistanceService:
    """
    Orchestrates optional LLM assistance for the safety analysis pipeline.
    Ensures safe fallback behavior if the provider is disabled or fails.
    """
    
    @staticmethod
    async def request_reviewer_summary(
        report_text: str,
        structured_evidence: dict[str, Any],
        authoritative_results: dict[str, Any]
    ) -> LLMResult:
        settings = get_settings()
        
        if not settings.llm_enabled:
            return LLMResult(
                success=False,
                provider="none",
                model="none",
                operation="reviewer_summary",
                error_code="LLM_DISABLED"
            )
            
        provider = LLMManager.get_provider()
        if not provider:
            return LLMResult(
                success=False,
                provider=settings.llm_provider,
                model=settings.llm_model,
                operation="reviewer_summary",
                error_code="PROVIDER_UNAVAILABLE"
            )
            
        # Build tightly scoped context
        context = {
            "report_text": report_text,
            "structured_evidence": structured_evidence,
            "authoritative_safety_results": authoritative_results
        }
        
        try:
            # We don't implement aggressive retry loops as per requirement
            # Max 1 retry for transient API errors could be added here if needed,
            # but standard is just bounded call. 
            # Given the prompt says "If retries are implemented: 0-2 retries", 
            # we'll stick to a single attempt for safety and latency.
            result = await provider.generate_reviewer_summary(context)
            return result
        except Exception as e:
            logger.error("Unexpected error in LLMAssistanceService", error=str(e))
            return LLMResult(
                success=False,
                provider=settings.llm_provider,
                model=settings.llm_model,
                operation="reviewer_summary",
                error_code="UNEXPECTED_ERROR"
            )
