from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import DBSession, require_roles
from app.core.constants import ReportStatus, ReportType, SourceType, UserRole
from app.models.user import User
from app.schemas.analysis import AnalysisResponse
from app.schemas.common import Message
from app.schemas.report import ReportCreate, ReportPage, ReportRead, ReportUpdate
from app.services.analysis.analysis_service import AnalysisService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/{report_id}/analyze",
    response_model=AnalysisResponse,
    summary="Run and persist the SIF NLP analysis pipeline",
)
async def analyze_report(
    report_id: str,
    request: Request,
    db: DBSession,
    user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER)
    ),
) -> AnalysisResponse:
    return await AnalysisService(db).analyze_report(
        report_id, user.id, request.client.host if request.client else None
    )

@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED, summary="Create an unsafe-act or near-miss report")
async def create_report(payload: ReportCreate, request: Request, db: DBSession, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER))) -> ReportRead:
    return await ReportService(db).create(payload, user.id, request.client.host if request.client else None)

@router.get("", response_model=ReportPage, summary="List reports with database-backed filtering and pagination")
async def list_reports(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), site_id: UUID | None = None, report_type: ReportType | None = None, status: ReportStatus | None = None, source_type: SourceType | None = None, date_from: datetime | None = None, date_to: datetime | None = None, search: str | None = Query(default=None, max_length=200)) -> ReportPage:
    reports, total = await ReportService(db).list(page=page, page_size=page_size, site_id=site_id, report_type=report_type, status=status, source_type=source_type, date_from=date_from, date_to=date_to, search=search)
    return ReportPage(items=reports, total=total, page=page, page_size=page_size)

@router.get("/{report_id}", response_model=ReportRead, summary="Get a report by human-readable ID")
async def get_report(report_id: str, db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER))) -> ReportRead:
    return await ReportService(db).get(report_id)

@router.patch("/{report_id}", response_model=ReportRead, summary="Update a report")
async def update_report(report_id: str, payload: ReportUpdate, request: Request, db: DBSession, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER))) -> ReportRead:
    return await ReportService(db).update(report_id, payload, user.id, request.client.host if request.client else None)

@router.delete("/{report_id}", response_model=Message, summary="Delete a report")
async def delete_report(report_id: str, request: Request, db: DBSession, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER))) -> Message:
    await ReportService(db).delete(report_id, user.id, request.client.host if request.client else None)
    return Message(message="Report deleted")
