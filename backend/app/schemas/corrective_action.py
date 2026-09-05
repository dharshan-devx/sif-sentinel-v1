from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CorrectiveActionCreate(BaseModel):
    report_id: UUID | None = None
    intervention_recommendation_id: UUID | None = None
    intervention_code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    hierarchy_level: str = Field(min_length=1, max_length=50)
    action_type: str = Field(min_length=1, max_length=50)
    priority: str = Field(min_length=1, max_length=20)
    assigned_to: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    original_recommendation: dict = Field(default_factory=dict)


class CorrectiveActionModifyRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    assigned_to: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    modification_reason: str = Field(min_length=3, max_length=1000)


class CorrectiveActionDecisionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)


class CorrectiveActionVerifyRequest(BaseModel):
    verification_notes: str = Field(min_length=3, max_length=4000)
    effective: bool = True


class CorrectiveActionRead(ORMModel):
    id: UUID
    report_id: UUID | None
    intervention_recommendation_id: UUID | None
    intervention_code: str
    title: str
    description: str
    hierarchy_level: str
    action_type: str
    priority: str
    status: str
    original_recommendation: dict
    user_modifications: list[dict]
    assigned_to: str | None
    due_date: datetime | None
    created_by: UUID
    reviewed_by: UUID | None
    approved_by: UUID | None
    verified_by: UUID | None
    closed_by: UUID | None
    approved_at: datetime | None
    completed_at: datetime | None
    verified_at: datetime | None
    closed_at: datetime | None
    verification_notes: str | None
    rejection_reason: str | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime


class CorrectiveActionListResponse(BaseModel):
    total: int
    items: list[CorrectiveActionRead]


class CorrectiveActionExportItem(BaseModel):
    action_id: str
    report_id: str | None
    intervention_code: str
    title: str
    hierarchy_level: str
    action_type: str
    priority: str
    status: str
    assigned_to: str | None
    due_date: str | None
    approved_at: str | None
    verified_at: str | None
    closed_at: str | None
    original_rule: str
    source_basis: str
