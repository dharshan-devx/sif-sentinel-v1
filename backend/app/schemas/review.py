from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import BarrierStatus, ReviewDecision, SIFLevel
from app.schemas.common import ORMModel


class ReviewRead(ORMModel):
    decision: str


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision
    corrected_sif_level: SIFLevel | None = None
    corrected_activity: str | None = Field(default=None, max_length=255)
    corrected_hazard: str | None = Field(default=None, max_length=255)
    corrected_barrier: str | None = Field(default=None, max_length=255)
    corrected_barrier_status: BarrierStatus | None = None
    corrected_barrier_failure: str | None = Field(default=None, max_length=1000)
    corrected_life_saving_rule: str | None = Field(default=None, max_length=255)
    reviewer_comment: str | None = Field(default=None, max_length=4000)


class ReviewQueueItem(BaseModel):
    id: UUID
    report_id: str
    decision: ReviewDecision
    reviewer_id: UUID
    reviewed_at: datetime
    report_text: str
    evidence_span: str | None
    overall_confidence: float | None
    explanation: str | None
