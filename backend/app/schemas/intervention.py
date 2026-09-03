from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import InterventionReviewStatus
from app.schemas.common import ORMModel


class InterventionRead(ORMModel):
    id: UUID
    report_id: UUID | None
    precursor_pattern_id: UUID | None
    intervention_rule_id: str
    category: str
    title: str
    description: str
    rationale: str
    priority: str
    action_type: str
    review_required: bool
    evidence_snapshot: dict
    source_rule: str
    engine_version: str
    risk_priority: str | None
    life_saving_rule: str | None
    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    reviewer_comments: str | None
    reviewer_title: str | None
    reviewer_description: str | None
    reviewer_rationale: str | None
    created_at: datetime


class InterventionReviewRequest(BaseModel):
    decision: InterventionReviewStatus
    reviewer_comments: str | None = Field(default=None, max_length=4000)
    reviewer_title: str | None = Field(default=None, max_length=255)
    reviewer_description: str | None = Field(default=None, max_length=4000)
    reviewer_rationale: str | None = Field(default=None, max_length=4000)


class InterventionSummary(BaseModel):
    total: int
    critical: int
    pending: int
    by_category: dict[str, int]
