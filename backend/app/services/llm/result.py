from datetime import datetime, timezone
from pydantic import BaseModel, Field

def utcnow():
    return datetime.now(timezone.utc)

class LLMResult(BaseModel):
    success: bool
    summary: str | None = None
    provider: str
    model: str
    operation: str
    timestamp: datetime = Field(default_factory=utcnow)
    latency_ms: int | None = None
    error_code: str | None = None
