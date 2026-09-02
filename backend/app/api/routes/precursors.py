from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.common import Message
from app.schemas.precursor import PrecursorDetail, PrecursorGraph, PrecursorSummary
from app.services.precursor_engine.precursor_service import PrecursorService

router = APIRouter(prefix="/precursors", tags=["Precursor intelligence"])


@router.get("", response_model=list[PrecursorSummary], summary="Rank recurring precursor patterns")
async def list_precursors(
    db: DBSession,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)),
    site: UUID | None = None,
    activity: str | None = None,
    hazard: str | None = None,
    barrier: str | None = None,
    risk_level: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    sort: str = Query("risk_score", pattern="^(risk_score|recent)$"),
) -> list[PrecursorSummary]:
    # Stored patterns are all-time; optional dates narrow by observed first/last activity.
    return await PrecursorService(db).list(site_id=site, activity=activity, hazard=hazard, barrier=barrier, risk_level=risk_level, limit=limit, sort=sort, date_from=date_from, date_to=date_to)


@router.get("/trends", response_model=list[PrecursorSummary], summary="List precursor trends")
async def precursor_trends(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), limit: int = Query(50, ge=1, le=200)) -> list[PrecursorSummary]:
    return await PrecursorService(db).list(limit=limit, sort="recent")


@router.post("/rebuild", response_model=Message, summary="Idempotently rebuild precursor pattern statistics")
async def rebuild_precursors(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST))) -> Message:
    count = await PrecursorService(db).rebuild()
    await db.commit()
    return Message(message=f"Rebuilt {count} precursor patterns")


@router.get("/{precursor_id}", response_model=PrecursorDetail, summary="Get precursor detail and linked report summaries")
async def get_precursor(precursor_id: UUID, db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER))) -> PrecursorDetail:
    return await PrecursorService(db).detail(precursor_id)


@router.get("/{precursor_id}/graph", response_model=PrecursorGraph, summary="Get React Flow-compatible precursor graph")
async def precursor_graph(precursor_id: UUID, db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER))) -> PrecursorGraph:
    return await PrecursorService(db).graph(precursor_id)
