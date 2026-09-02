from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.review import ReviewDecisionRequest, ReviewQueueItem
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Human reviews"])
_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.REVIEWER)

@router.get("", response_model=list[ReviewQueueItem])
async def queue(db: DBSession, _: User = Depends(require_roles(*_roles)), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> list[ReviewQueueItem]:
    return (await ReviewService(db).list(page, page_size))[0]

@router.get("/{review_id}", response_model=ReviewQueueItem)
async def get_review(review_id: UUID, db: DBSession, _: User = Depends(require_roles(*_roles))) -> ReviewQueueItem:
    return await ReviewService(db).get(review_id)

@router.post("/{review_id}/decision", response_model=ReviewQueueItem)
async def decision(review_id: UUID, payload: ReviewDecisionRequest, request: Request, db: DBSession, user: User = Depends(require_roles(*_roles))) -> ReviewQueueItem:
    review = await ReviewService(db).decide(review_id, payload, user.id, request.client.host if request.client else None)
    return await ReviewService(db).get(review.id)
