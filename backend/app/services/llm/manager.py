from app.core.config import get_settings
from app.services.llm.provider_interface import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
import structlog

logger = structlog.get_logger(__name__)

class LLMManager:
    """
    Responsible for selecting and returning the configured LLMProvider.
    """
    
    @staticmethod
    def get_provider() -> LLMProvider | None:
        settings = get_settings()
        
        if not settings.llm_enabled:
            return None
            
        provider_name = settings.llm_provider.lower()
        
        if provider_name == "gemini":
            return GeminiProvider()
        else:
            logger.error(f"Unsupported LLM provider configured: {provider_name}")
            return None
