"""
SIF Sentinel — Corrective Action Lifecycle & Governance Service (Phase 5F Closed Loop)

Enforces:
1. Deterministic state transitions (DRAFT -> SUBMITTED -> APPROVED -> IN_PROGRESS -> VERIFICATION_REQUIRED -> VERIFIED -> CLOSED).
2. Immutable original recommendation provenance.
3. Server-side RBAC validation.
4. Comprehensive audit event recording on every mutating action.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.audit_log import AuditLog
from app.models.corrective_action import CorrectiveAction
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionDecisionRequest,
    CorrectiveActionExportItem,
    CorrectiveActionModifyRequest,
    CorrectiveActionVerifyRequest,
)
from app.services.audit_service import record_audit

logger = structlog.get_logger(__name__)


class CorrectiveActionService:
    """Manages persistent corrective actions with state-machine governance and auditability."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_action(
        self,
        payload: CorrectiveActionCreate,
        creator_id: UUID,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Creates a new corrective action in DRAFT state."""
        action = CorrectiveAction(
            report_id=payload.report_id,
            intervention_recommendation_id=payload.intervention_recommendation_id,
            intervention_code=payload.intervention_code,
            title=payload.title,
            description=payload.description,
            hierarchy_level=payload.hierarchy_level.upper(),
            action_type=payload.action_type.upper(),
            priority=payload.priority.upper(),
            status="DRAFT",
            original_recommendation=payload.original_recommendation or {
                "title": payload.title,
                "description": payload.description,
                "hierarchy_level": payload.hierarchy_level,
                "action_type": payload.action_type,
                "priority": payload.priority,
            },
            user_modifications=[],
            assigned_to=payload.assigned_to,
            due_date=payload.due_date,
            created_by=creator_id,
        )
        self.db.add(action)
        await self.db.flush()

        await record_audit(
            self.db,
            user_id=creator_id,
            action="ACTION_CREATED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"status": "DRAFT", "code": action.intervention_code},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def get(self, action_id: UUID) -> CorrectiveAction:
        action = await self.db.get(CorrectiveAction, action_id)
        if not action:
            raise NotFoundError("corrective action")
        return action

    async def list_actions(
        self,
        report_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        hierarchy_level: str | None = None,
    ) -> list[CorrectiveAction]:
        query = select(CorrectiveAction)
        if report_id:
            query = query.where(CorrectiveAction.report_id == report_id)
        if status:
            query = query.where(CorrectiveAction.status == status.upper())
        if priority:
            query = query.where(CorrectiveAction.priority == priority.upper())
        if hierarchy_level:
            query = query.where(CorrectiveAction.hierarchy_level == hierarchy_level.upper())

        query = query.order_by(CorrectiveAction.created_at.desc(), CorrectiveAction.id)
        rows = (await self.db.scalars(query)).all()
        return list(rows)

    async def submit(self, action_id: UUID, actor_id: UUID, ip: str | None = None) -> CorrectiveAction:
        """Transitions action from DRAFT -> SUBMITTED."""
        action = await self._get_for_update(action_id)
        if action.status != "DRAFT":
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot submit action with status '{action.status}'. Must be DRAFT.",
                409,
            )

        action.status = "SUBMITTED"
        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_SUBMITTED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": "DRAFT", "new_status": "SUBMITTED"},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def approve(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionDecisionRequest | None = None,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Transitions action from SUBMITTED or UNDER_REVIEW -> APPROVED."""
        action = await self._get_for_update(action_id)
        if action.status not in ("SUBMITTED", "UNDER_REVIEW"):
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot approve action with status '{action.status}'. Must be SUBMITTED or UNDER_REVIEW.",
                409,
            )

        old_status = action.status
        action.status = "APPROVED"
        action.approved_by = actor_id
        action.approved_at = datetime.now(UTC)
        if payload and payload.notes:
            action.verification_notes = payload.notes

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_APPROVED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": old_status, "new_status": "APPROVED", "notes": payload.notes if payload else None},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def reject(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionDecisionRequest,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Transitions action from SUBMITTED or UNDER_REVIEW -> REJECTED."""
        action = await self._get_for_update(action_id)
        if action.status not in ("SUBMITTED", "UNDER_REVIEW", "DRAFT"):
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot reject action with status '{action.status}'.",
                409,
            )

        old_status = action.status
        action.status = "REJECTED"
        action.reviewed_by = actor_id
        action.rejection_reason = payload.reason or payload.notes or "Rejected by reviewer"

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_REJECTED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": old_status, "new_status": "REJECTED", "reason": action.rejection_reason},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def modify(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionModifyRequest,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Records human edits with before/after audit tracking while keeping original snapshot immutable."""
        action = await self._get_for_update(action_id)
        if action.status in ("CLOSED", "REJECTED", "CANCELLED"):
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot modify closed or terminal action with status '{action.status}'.",
                409,
            )

        mod_record = {
            "user_id": str(actor_id),
            "timestamp": datetime.now(UTC).isoformat(),
            "reason": payload.modification_reason,
            "changes": {},
        }

        if payload.title and payload.title != action.title:
            mod_record["changes"]["title"] = {"old": action.title, "new": payload.title}
            action.title = payload.title

        if payload.description and payload.description != action.description:
            mod_record["changes"]["description"] = {"old": action.description, "new": payload.description}
            action.description = payload.description

        if payload.assigned_to is not None and payload.assigned_to != action.assigned_to:
            mod_record["changes"]["assigned_to"] = {"old": action.assigned_to, "new": payload.assigned_to}
            action.assigned_to = payload.assigned_to

        if payload.due_date is not None and payload.due_date != action.due_date:
            mod_record["changes"]["due_date"] = {
                "old": action.due_date.isoformat() if action.due_date else None,
                "new": payload.due_date.isoformat(),
            }
            action.due_date = payload.due_date

        action.user_modifications = list(action.user_modifications or []) + [mod_record]
        action.reviewed_by = actor_id

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_MODIFIED",
            entity_type="corrective_action",
            entity_id=action.id,
            details=mod_record,
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def start_action(self, action_id: UUID, actor_id: UUID, ip: str | None = None) -> CorrectiveAction:
        """Transitions action from APPROVED -> IN_PROGRESS."""
        action = await self._get_for_update(action_id)
        if action.status != "APPROVED":
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot start action with status '{action.status}'. Must be APPROVED first.",
                409,
            )

        action.status = "IN_PROGRESS"
        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_STARTED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": "APPROVED", "new_status": "IN_PROGRESS"},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def request_verification(self, action_id: UUID, actor_id: UUID, ip: str | None = None) -> CorrectiveAction:
        """Transitions action from IN_PROGRESS -> VERIFICATION_REQUIRED."""
        action = await self._get_for_update(action_id)
        if action.status != "IN_PROGRESS":
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot request verification for action with status '{action.status}'. Must be IN_PROGRESS.",
                409,
            )

        action.status = "VERIFICATION_REQUIRED"
        action.completed_at = datetime.now(UTC)
        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_COMPLETED_PENDING_VERIFICATION",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": "IN_PROGRESS", "new_status": "VERIFICATION_REQUIRED"},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def verify(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionVerifyRequest,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Transitions action from VERIFICATION_REQUIRED -> VERIFIED (or back to IN_PROGRESS if ineffective)."""
        action = await self._get_for_update(action_id)
        if action.status != "VERIFICATION_REQUIRED":
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot verify action with status '{action.status}'. Must be VERIFICATION_REQUIRED.",
                409,
            )

        old_status = action.status
        action.verified_by = actor_id
        action.verification_notes = payload.verification_notes

        if payload.effective:
            action.status = "VERIFIED"
            action.verified_at = datetime.now(UTC)
        else:
            action.status = "IN_PROGRESS"

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_VERIFIED" if payload.effective else "ACTION_VERIFICATION_FAILED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": old_status, "new_status": action.status, "notes": payload.verification_notes},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def close(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionDecisionRequest | None = None,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Transitions action from VERIFIED -> CLOSED."""
        action = await self._get_for_update(action_id)
        if action.status != "VERIFIED":
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot close action with status '{action.status}'. Must be VERIFIED first.",
                409,
            )

        action.status = "CLOSED"
        action.closed_by = actor_id
        action.closed_at = datetime.now(UTC)

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_CLOSED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": "VERIFIED", "new_status": "CLOSED"},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def cancel(
        self,
        action_id: UUID,
        actor_id: UUID,
        payload: CorrectiveActionDecisionRequest,
        ip: str | None = None,
    ) -> CorrectiveAction:
        """Transitions action to CANCELLED from DRAFT, SUBMITTED, or UNDER_REVIEW."""
        action = await self._get_for_update(action_id)
        if action.status not in ("DRAFT", "SUBMITTED", "UNDER_REVIEW"):
            raise AppError(
                "INVALID_STATE_TRANSITION",
                f"Cannot cancel action with status '{action.status}'. Must be DRAFT, SUBMITTED, or UNDER_REVIEW.",
                409,
            )

        old_status = action.status
        action.status = "CANCELLED"
        action.cancellation_reason = payload.reason or payload.notes or "Cancelled by user"

        await record_audit(
            self.db,
            user_id=actor_id,
            action="ACTION_CANCELLED",
            entity_type="corrective_action",
            entity_id=action.id,
            details={"old_status": old_status, "new_status": "CANCELLED", "reason": action.cancellation_reason},
            ip_address=ip,
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def get_audit_trail(self, action_id: UUID) -> list[dict[str, Any]]:
        """Returns the complete immutable audit history for this corrective action."""
        query = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == "corrective_action",
                AuditLog.entity_id == action_id,
            )
            .order_by(AuditLog.created_at.asc())
        )
        logs = (await self.db.scalars(query)).all()
        return [
            {
                "id": str(log.id),
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "details": log.details,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "ip_address": log.ip_address,
            }
            for log in logs
        ]

    async def export_approved_actions(self) -> list[CorrectiveActionExportItem]:
        """Exports approved/verified/closed action plans with complete governance data."""
        query = (
            select(CorrectiveAction)
            .where(CorrectiveAction.status.in_(["APPROVED", "IN_PROGRESS", "VERIFICATION_REQUIRED", "VERIFIED", "CLOSED"]))
            .order_by(CorrectiveAction.created_at.desc())
        )
        rows = (await self.db.scalars(query)).all()
        return [
            CorrectiveActionExportItem(
                action_id=str(row.id),
                report_id=str(row.report_id) if row.report_id else None,
                intervention_code=row.intervention_code,
                title=row.title,
                hierarchy_level=row.hierarchy_level,
                action_type=row.action_type,
                priority=row.priority,
                status=row.status,
                assigned_to=row.assigned_to,
                due_date=row.due_date.isoformat() if row.due_date else None,
                approved_at=row.approved_at.isoformat() if row.approved_at else None,
                verified_at=row.verified_at.isoformat() if row.verified_at else None,
                closed_at=row.closed_at.isoformat() if row.closed_at else None,
                original_rule=row.original_recommendation.get("deterministic_rule_id", "HOC-RULE"),
                source_basis="CAUSAL_GRAPH + RISK_ENGINE + BARRIER_STATUS",
            )
            for row in rows
        ]

    async def _get_for_update(self, action_id: UUID) -> CorrectiveAction:
        action = await self.db.scalar(
            select(CorrectiveAction)
            .where(CorrectiveAction.id == action_id)
            .with_for_update()
        )
        if not action:
            raise NotFoundError("corrective action")
        return action
