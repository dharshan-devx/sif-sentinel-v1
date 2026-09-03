from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReportStatus, ReportType, SourceType
from app.core.exceptions import AppError, NotFoundError
from app.models.report import Report
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate, ReportUpdate
from app.services.audit_service import record_audit


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db, self.repo = db, ReportRepository(db)

    async def create(self, payload: ReportCreate, user_id: UUID, ip_address: str | None) -> Report:
        from app.models.site import Site
        if not await self.db.get(Site, payload.site_id):
            raise AppError("SITE_NOT_FOUND", "Site not found", 404)
        human_id = payload.report_id or self._new_human_id()
        if await self.repo.get_by_human_id(human_id):
            raise AppError("REPORT_ID_EXISTS", "Report identifier already exists", 409)
        report = Report(**payload.model_dump(exclude={"report_id"}), report_id=human_id, created_by=user_id)
        self.db.add(report)
        await self.db.flush()
        await record_audit(self.db, user_id=user_id, action="REPORT_CREATED", entity_type="report", entity_id=report.id,
                           details={"report_id": report.report_id}, ip_address=ip_address)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get(self, human_id: str) -> Report:
        report = await self.repo.get_by_human_id(human_id)
        if not report:
            raise NotFoundError("report")
        return report

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        site_id: UUID | None = None,
        report_type: ReportType | None = None,
        status: ReportStatus | None = None,
        source_type: SourceType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
    ) -> tuple[list[Report], int]:
        """Return paginated reports with optional filters.

        Delegates entirely to ReportRepository so route handlers never
        access the repository directly.
        """
        return await self.repo.list(
            page=page,
            page_size=page_size,
            site_id=site_id,
            report_type=report_type,
            status=status,
            source_type=source_type,
            date_from=date_from,
            date_to=date_to,
            search=search,
        )

    async def update(self, human_id: str, payload: ReportUpdate, user_id: UUID, ip_address: str | None) -> Report:
        report = await self.get(human_id)
        for name, value in payload.model_dump(exclude_unset=True).items():
            setattr(report, name, value)
        await record_audit(self.db, user_id=user_id, action="REPORT_UPDATED", entity_type="report", entity_id=report.id,
                           details={"fields": list(payload.model_dump(exclude_unset=True))}, ip_address=ip_address)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def delete(self, human_id: str, user_id: UUID, ip_address: str | None) -> None:
        report = await self.get(human_id)
        await record_audit(self.db, user_id=user_id, action="REPORT_DELETED", entity_type="report", entity_id=report.id,
                           details={"report_id": report.report_id}, ip_address=ip_address)
        await self.db.delete(report)
        await self.db.commit()

    @staticmethod
    def _new_human_id() -> str:
        return f"SIF-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}"

