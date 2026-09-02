from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.constants import ReportStatus, ReportType, SourceType
from app.schemas.common import ORMModel


class ReportCreate(ORMModel):
    report_id: str | None = Field(default=None, min_length=3, max_length=64)
    report_type: ReportType
    report_text: str = Field(min_length=10, max_length=20000)
    site_id: UUID
    location: str = Field(min_length=1, max_length=255)
    department: str = Field(min_length=1, max_length=255)
    activity: str | None = Field(default=None, max_length=255)
    reported_at: datetime
    source_type: SourceType


class ReportUpdate(ORMModel):
    report_text: str | None = Field(default=None, min_length=10, max_length=20000)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    activity: str | None = Field(default=None, max_length=255)
    status: ReportStatus | None = None


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
