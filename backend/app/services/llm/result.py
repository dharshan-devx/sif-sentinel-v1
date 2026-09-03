"""LLMResult — the validated result object returned by every LLM operation.

This model acts as the boundary between the provider implementation and the
rest of the application.  Raw provider responses must never reach business
logic or database models directly.

Failure semantics
-----------------
LLM unavailability must NOT be misrepresented as a successful provider call.

  success=False, error_code="LLM_DISABLED"   → LLM was not enabled
  success=False, error_code="TIMEOUT"         → provider timed out
  success=False, error_code="INVALID_API_KEY" → bad credentials
  success=False, error_code="MALFORMED_OUTPUT"→ JSON parse failure
  success=False, error_code="INVALID_RESPONSE"→ Pydantic validation failure
  success=False, error_code="EMPTY_RESPONSE"  → provider returned nothing
  success=False, error_code="RATE_LIMITED"    → 429 after retry exhausted
  success=True,  summary="..."                → usable reviewer summary
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LLMResult(BaseModel):
    """Immutable result returned by every LLM assistance operation."""

    success: bool
    summary: str | None = None
    provider: str
    model: str
    operation: str
    timestamp: datetime = Field(default_factory=_utcnow)
    latency_ms: int | None = None
    error_code: str | None = None
    # Optional observability field — populated when token metadata is available
    token_count: int | None = None
