from typing import Any, Protocol

from app.services.llm.result import LLMResult


class LLMProvider(Protocol):
    async def generate_reviewer_summary(self, context: dict[str, Any]) -> LLMResult:
        """
        Generate a concise, reviewer-facing summary based on the provided context.
        The context should contain only the minimal necessary structured data to avoid 
        prompt injection and minimize token usage.
        """
        ...

    async def check_health(self) -> bool:
        """
        Optional diagnostic check to determine if the provider is reachable.
        Should NOT be called inline with every generation request.
        """
        ...
