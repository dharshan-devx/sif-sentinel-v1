from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.core.constants import ReportStatus, ReportType, SourceType
from app.core.validators import validate_report_text
from app.schemas.common import ORMModel


class ReportCreate(ORMModel):
    report_id: str | None = Field(default=None, min_length=3, max_length=64)
    report_type: ReportType
    # Outer max_length acts as an HTTP-boundary guard against absurdly large JSON
    # before Pydantic even calls the field_validator.  The real configurable
    # limit is enforced inside validate_report_text() via settings.
    report_text: str = Field(min_length=1, max_length=100_000)
    site_id: UUID
    location: str = Field(min_length=1, max_length=255)
    department: str = Field(min_length=1, max_length=255)
    activity: str | None = Field(default=None, max_length=255)
    reported_at: datetime
    source_type: SourceType

    @field_validator("report_text")
    @classmethod
    def _validate_report_text(cls, v: str) -> str:
        return validate_report_text(v)


class ReportUpdate(ORMModel):
    # report_text is optional in a PATCH — when omitted the field_validator is
    # not called, preserving correct partial-update semantics.
    report_text: str | None = Field(default=None, min_length=1, max_length=100_000)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    activity: str | None = Field(default=None, max_length=255)
    status: ReportStatus | None = None

    @field_validator("report_text")
    @classmethod
    def _validate_report_text(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_report_text(v)


class ReportRead(ORMModel):
    id: UUID
    report_id: str
    report_type: ReportType
    report_text: str
    site_id: UUID
    location: str
    department: str
    activity: str | None
    reported_at: datetime
    source_type: SourceType
    status: ReportStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ReportPage(ORMModel):
    items: list[ReportRead]
    total: int
    page: int
    page_size: int
