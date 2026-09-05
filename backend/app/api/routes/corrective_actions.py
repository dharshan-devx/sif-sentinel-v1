from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionDecisionRequest,
    CorrectiveActionExportItem,
    CorrectiveActionModifyRequest,
    CorrectiveActionRead,
    CorrectiveActionVerifyRequest,
)
from app.services.corrective_action_service import CorrectiveActionService

router = APIRouter(prefix="/corrective-actions", tags=["Corrective Actions & Prevention"])

_all_roles = (
    UserRole.ADMIN,
    UserRole.HSE_MANAGER,
    UserRole.HSE_ANALYST,
    UserRole.REVIEWER,
    UserRole.VIEWER,
)
_analyst_and_above = (
    UserRole.ADMIN,
    UserRole.HSE_MANAGER,
    UserRole.HSE_ANALYST,
    UserRole.REVIEWER,
)
_reviewer_and_above = (
    UserRole.ADMIN,
    UserRole.HSE_MANAGER,
    UserRole.REVIEWER,
)
_manager_and_above = (
    UserRole.ADMIN,
    UserRole.HSE_MANAGER,
)


@router.post("", response_model=CorrectiveActionRead, summary="Create a new corrective action item")
async def create_corrective_action(
    payload: CorrectiveActionCreate,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_analyst_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).create_action(
        payload=payload,
        creator_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.get("/export", response_model=list[CorrectiveActionExportItem], summary="Export approved corrective action plans")
async def export_corrective_actions(
    db: DBSession,
    _: User = Depends(require_roles(*_all_roles)),
) -> list[CorrectiveActionExportItem]:
    return await CorrectiveActionService(db).export_approved_actions()


@router.get("", response_model=list[CorrectiveActionRead], summary="List corrective actions with filtering")
async def list_corrective_actions(
    db: DBSession,
    _: User = Depends(require_roles(*_all_roles)),
    report_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    hierarchy_level: str | None = None,
) -> list[CorrectiveActionRead]:
    actions = await CorrectiveActionService(db).list_actions(
        report_id=report_id,
        status=status,
        priority=priority,
        hierarchy_level=hierarchy_level,
    )
    return [CorrectiveActionRead.model_validate(a) for a in actions]


@router.get("/{action_id}", response_model=CorrectiveActionRead, summary="Get a corrective action by ID")
async def get_corrective_action(
    action_id: UUID,
    db: DBSession,
    _: User = Depends(require_roles(*_all_roles)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).get(action_id)
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/submit", response_model=CorrectiveActionRead, summary="Submit a draft action for HSE review")
async def submit_corrective_action(
    action_id: UUID,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_analyst_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).submit(
        action_id=action_id,
        actor_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/approve", response_model=CorrectiveActionRead, summary="Approve an action plan")
async def approve_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionDecisionRequest | None = None,
    request: Request = None,
    db: DBSession = None,
    user: User = Depends(require_roles(*_reviewer_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).approve(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request and request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/reject", response_model=CorrectiveActionRead, summary="Reject an action plan with reason")
async def reject_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionDecisionRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_reviewer_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).reject(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/cancel", response_model=CorrectiveActionRead, summary="Cancel an action plan with reason")
async def cancel_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionDecisionRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_analyst_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).cancel(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/modify", response_model=CorrectiveActionRead, summary="Modify action scope with audit trail")
async def modify_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionModifyRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_reviewer_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).modify(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/start", response_model=CorrectiveActionRead, summary="Start implementation (move to IN_PROGRESS)")
async def start_corrective_action(
    action_id: UUID,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_analyst_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).start_action(
        action_id=action_id,
        actor_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/request-verification", response_model=CorrectiveActionRead, summary="Request verification on completed field action")
async def request_action_verification(
    action_id: UUID,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_analyst_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).request_verification(
        action_id=action_id,
        actor_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/verify", response_model=CorrectiveActionRead, summary="Verify field effectiveness of restored barrier")
async def verify_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionVerifyRequest,
    request: Request,
    db: DBSession,
    user: User = Depends(require_roles(*_reviewer_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).verify(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.post("/{action_id}/close", response_model=CorrectiveActionRead, summary="Formally close verified action item")
async def close_corrective_action(
    action_id: UUID,
    payload: CorrectiveActionDecisionRequest | None = None,
    request: Request = None,
    db: DBSession = None,
    user: User = Depends(require_roles(*_manager_and_above)),
) -> CorrectiveActionRead:
    action = await CorrectiveActionService(db).close(
        action_id=action_id,
        actor_id=user.id,
        payload=payload,
        ip=request.client.host if request and request.client else None,
    )
    return CorrectiveActionRead.model_validate(action)


@router.get("/{action_id}/audit", response_model=list[dict], summary="Get complete audit trail for an action item")
async def get_action_audit_trail(
    action_id: UUID,
    db: DBSession,
    _: User = Depends(require_roles(*_all_roles)),
) -> list[dict]:
    return await CorrectiveActionService(db).get_audit_trail(action_id)
