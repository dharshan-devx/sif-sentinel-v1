from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.review import (
    DecisionResponse,
    ReviewDecisionRequest,
    ReviewQueueItem,
    ReviewStatusFilter,
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Human reviews"])
_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.REVIEWER)


@router.get("", response_model=list[ReviewQueueItem], summary="List reviews with optional status filter")
async def queue(
    db: DBSession,
    _: User = Depends(require_roles(*_roles)),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ReviewStatusFilter = Query(ReviewStatusFilter.PENDING, description="Filter by review status"),
) -> list[ReviewQueueItem]:
    """List reviews filtered by status.

    - **PENDING** (default): reviews awaiting human decision
    - **REVIEWED**: completed reviews (APPROVE / REJECT / MODIFY)
    - **ALL**: no filter, returns everything
    """
    items, _ = await ReviewService(db).list(page, page_size, status)
    return items


@router.get("/{review_id}", response_model=ReviewQueueItem, summary="Get a single review by ID")
async def get_review(
    review_id: UUID,
    db: DBSession,
    _: User = Depends(require_roles(*_roles)),
) -> ReviewQueueItem:
    return await ReviewService(db).get(review_id)


@router.post(
    "/{review_id}/decision",
    response_model=DecisionResponse,
    summary="Submit a final review decision (APPROVE / REJECT / MODIFY)",
)
async def decision(
    review_id: UUID,
    payload: ReviewDecisionRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_roles)),
) -> DecisionResponse:
    """Submit the human reviewer's decision on a pending AI-generated review.

    - **APPROVE**: AI prediction is confirmed as correct
    - **REJECT**: AI prediction is rejected (original is preserved for audit)
    - **MODIFY**: reviewer provides corrections; originals are preserved alongside
    """
    return await ReviewService(db).decide(
        review_id,
        payload,
        user.id,
        request.client.host if request.client else None,
    )
