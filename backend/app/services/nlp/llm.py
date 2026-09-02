"""Optional validated LLM extension boundary; deterministic analysis never depends on it."""
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class LLMEnrichment(BaseModel):
    explanation: str = Field(max_length=2000)


class BaseLLMProvider(ABC):
    @abstractmethod
    def enrich(self, text: str) -> LLMEnrichment | None:
        """Return validated enrichment when configured, otherwise no enrichment."""


class DisabledLLMProvider(BaseLLMProvider):
    """Explicit no-key provider; prevents an external dependency from affecting analysis."""

    def enrich(self, text: str) -> LLMEnrichment | None:
        return None
