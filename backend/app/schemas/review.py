"""Review schemas for Phase C.

Design notes:
- ReviewQueueItem is used for BOTH pending queue and history queries.
  reviewer_id and reviewed_at are Optional because PENDING reviews
  may conceptually not have a human decision yet (the DB columns are NOT NULL
  and store the analyst who triggered analysis, but we expose None for callers
  who want to distinguish pending from reviewed state).
- ReviewStatusFilter is a typed enum for ?status= query parameter.
  This prevents arbitrary unchecked string comparison.
- DecisionResponse is a concise response for POST decision endpoints.
- The corrected_* fields are exposed in ReviewQueueItem so history queries
  include what the reviewer actually changed.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import BarrierStatus, ReviewDecision, SIFLevel
from app.schemas.common import ORMModel


class ReviewStatusFilter(StrEnum):
    """Allowed values for GET /reviews?status= query parameter.

    PENDING   — reviews awaiting human decision (default)
    REVIEWED  — reviews where a final decision (APPROVE/REJECT/MODIFY) was made
    ALL       — no filter; returns full queue including both states
    """
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    ALL = "ALL"


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
    """Returned by GET /reviews and GET /reviews/{id}.

    Works for both PENDING and REVIEWED states.
    reviewer_id is the human who made the final decision (None if still pending).
    reviewed_at is the timestamp of the decision (None if still pending).
    """
    id: UUID
    report_id: str
    decision: ReviewDecision
    # Human reviewer — None while PENDING (DB may hold analyst id as placeholder)
    reviewer_id: UUID | None
    reviewed_at: datetime | None
    report_text: str
    evidence_span: str | None
    overall_confidence: float | None
    explanation: str | None
    reviewer_comment: str | None
    # Corrected fields — populated when decision == MODIFY
    corrected_sif_level: SIFLevel | None = None
    corrected_activity: str | None = None
    corrected_hazard: str | None = None
    corrected_barrier: str | None = None
    corrected_barrier_status: BarrierStatus | None = None
    corrected_barrier_failure: str | None = None
    corrected_life_saving_rule: str | None = None


class DecisionResponse(BaseModel):
    """Concise response body for POST /reviews/{id}/decision.

    Contains enough information for the frontend to update the UI
    without a separate GET request.
    """
    review_id: UUID
    decision: ReviewDecision
    report_id: str
    report_status: str
    reviewer_id: UUID
    reviewed_at: datetime
    message: str
