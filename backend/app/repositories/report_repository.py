from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReportStatus, ReportType, SourceType
from app.models.report import Report


class ReportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_human_id(self, report_id: str) -> Report | None:
        return await self.db.scalar(select(Report).where(Report.report_id == report_id))

    async def list(self, *, page: int, page_size: int, site_id: UUID | None, report_type: ReportType | None,
                   status: ReportStatus | None, source_type: SourceType | None, date_from: datetime | None,
                   date_to: datetime | None, search: str | None) -> tuple[list[Report], int]:
        filters = []
        for field, value in ((Report.site_id, site_id), (Report.report_type, report_type), (Report.status, status), (Report.source_type, source_type)):
            if value is not None:
                filters.append(field == value)
        if date_from:
            filters.append(Report.reported_at >= date_from)
        if date_to:
            filters.append(Report.reported_at <= date_to)
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(Report.report_id.ilike(term), Report.report_text.ilike(term), Report.location.ilike(term), Report.department.ilike(term)))
        statement = select(Report).where(*filters).order_by(Report.reported_at.desc())
        total = await self.db.scalar(select(func.count()).select_from(Report).where(*filters)) or 0
        rows = await self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size))
        return list(rows), total
