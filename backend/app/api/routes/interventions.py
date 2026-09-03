from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.intervention import InterventionRead, InterventionReviewRequest, InterventionSummary
from app.services.intervention_service import InterventionService

router = APIRouter(prefix="/interventions", tags=["Intervention intelligence"])
_read_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)
_review_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.REVIEWER)


@router.get("", response_model=list[InterventionRead], summary="List advisory intervention recommendations")
async def list_interventions(
    db: DBSession,
    _: User = Depends(require_roles(*_read_roles)),
    report_id: str | None = None,
    priority: str | None = None,
) -> list[InterventionRead]:
    return await InterventionService(db).list(report_human_id=report_id, priority=priority)


@router.get("/summary", response_model=InterventionSummary, summary="Summarize intervention recommendation queue")
async def intervention_summary(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> InterventionSummary:
    return await InterventionService(db).summary()


@router.get("/{recommendation_id}", response_model=InterventionRead, summary="Get an intervention recommendation")
async def get_intervention(recommendation_id: UUID, db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> InterventionRead:
    return InterventionRead.model_validate(await InterventionService(db).get(recommendation_id))


@router.post("/{recommendation_id}/review", response_model=InterventionRead, summary="Accept, modify, or reject an advisory recommendation")
async def review_intervention(
    recommendation_id: UUID,
    payload: InterventionReviewRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_review_roles)),
) -> InterventionRead:
    return await InterventionService(db).review(
        recommendation_id, payload, user.id, request.client.host if request.client else None
    )
