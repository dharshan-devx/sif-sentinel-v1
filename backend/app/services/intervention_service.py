"""Deterministic, advisory intervention recommendation engine (Phase K)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import InterventionActionType, InterventionCategory, InterventionReviewStatus
from app.core.exceptions import AppError, NotFoundError
from app.models.intervention_recommendation import InterventionRecommendation
from app.models.precursor_pattern import PrecursorPattern
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.schemas.intervention import InterventionRead, InterventionReviewRequest, InterventionSummary
from app.services.audit_service import record_audit

logger = structlog.get_logger(__name__)
ENGINE_VERSION = "v1"


class InterventionService:
    """Creates evidence-backed recommendations; it never executes an action."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _control_state(status: str | None, failure: str | None) -> str:
        value = " ".join(str(part) for part in (status, failure) if part).casefold().replace("_", " ")
        if "bypass" in value:
            return "bypassed"
        if "not verified" in value or "unverified" in value:
            return "not_verified"
        if "ineffective" in value:
            return "ineffective"
        if "missing" in value:
            return "missing"
        if "failed" in value:
            return "failed"
        if "effective" in value or "verified" in value:
            return "verified"
        return "unknown"

    @staticmethod
    def _priority(risk_priority: str | None, state: str, recurring: bool = False) -> str:
        if risk_priority == "CRITICAL" or state == "bypassed":
            return "CRITICAL"
        if risk_priority == "HIGH" or state in {"missing", "failed", "ineffective"}:
            return "HIGH"
        if recurring or risk_priority == "MEDIUM":
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _mapping(state: str, lsr: str | None, barrier: str | None) -> tuple[str, str, str, str, str]:
        barrier_label = barrier or "identified control"
        lsr_value = (lsr or "").casefold()
        if "energy isolation" in lsr_value and state in {"not_verified", "unknown", "bypassed"}:
            return ("energy-isolation-verify", InterventionCategory.ISOLATION_VERIFY,
                    "Verify energy isolation", "Verify isolation before maintenance or related work continues.",
                    InterventionActionType.VERIFICATION)
        if "permit" in lsr_value and state in {"missing", "not_verified", "unknown"}:
            return ("permit-verify", InterventionCategory.PERMIT_VERIFY,
                    "Verify permit authorization", "Verify the required permit or authorization before the task continues.",
                    InterventionActionType.VERIFICATION)
        if "guard" in barrier_label.casefold() and state in {"missing", "failed", "bypassed", "ineffective"}:
            return ("machine-guarding", InterventionCategory.ENGINEERING_CONTROL,
                    "Restore effective machine guarding", "Consider restoring or improving the identified machine guarding.",
                    InterventionActionType.CORRECTIVE)
        mappings = {
            "missing": ("control-restore", InterventionCategory.CONTROL_RESTORE, "Restore identified control", f"Consider restoring the {barrier_label} control.", InterventionActionType.CORRECTIVE),
            "not_verified": ("barrier-verify", InterventionCategory.BARRIER_VERIFY, "Verify identified barrier", f"Verify the {barrier_label} barrier before relying on it.", InterventionActionType.VERIFICATION),
            "failed": ("barrier-restore", InterventionCategory.BARRIER_RESTORE, "Restore failed barrier", f"Consider restoring the failed {barrier_label} barrier.", InterventionActionType.CORRECTIVE),
            "bypassed": ("control-restore-review", InterventionCategory.CONTROL_RESTORE, "Restore bypassed control and review", f"Review and restore the bypassed {barrier_label} control.", InterventionActionType.IMMEDIATE_REVIEW),
            "ineffective": ("control-strengthen", InterventionCategory.CONTROL_STRENGTHEN, "Strengthen identified control", f"Consider strengthening the ineffective {barrier_label} control.", InterventionActionType.CORRECTIVE),
            "unknown": ("barrier-verify-unknown", InterventionCategory.BARRIER_VERIFY, "Verify control condition", f"Evidence is insufficient to confirm the {barrier_label} control condition; verify it in the field.", InterventionActionType.VERIFICATION),
        }
        return mappings[state]

    @staticmethod
    def _evidence(analysis: ReportAnalysis, risk_priority: str | None, precursor_priority: str | None) -> dict[str, Any]:
        return {
            "activity": analysis.activity,
            "hazard": analysis.hazard,
            "barrier": analysis.barrier,
            "barrier_status": getattr(analysis.barrier_status, "value", analysis.barrier_status),
            "barrier_failure": analysis.barrier_failure,
            "life_saving_rule": analysis.life_saving_rule,
            "sif_level": getattr(analysis.sif_level, "value", analysis.sif_level),
            "risk_priority": risk_priority,
            "precursor_priority": precursor_priority,
        }

    async def generate_for_report(
        self, report: Report, analysis: ReportAnalysis, precursor_priority: str | None = None
    ) -> list[InterventionRecommendation]:
        """Persist idempotent report recommendations from authoritative analysis fields."""
        risk_priority = analysis.risk_priority
        state = self._control_state(
            getattr(analysis.barrier_status, "value", analysis.barrier_status),
            analysis.barrier_failure,
        )
        if state == "verified":
            return []
        rule_id, category, title, description, action_type = self._mapping(state, analysis.life_saving_rule, analysis.barrier)
        priority = self._priority(risk_priority, state)
        review_required = state in {"bypassed", "unknown"} or priority == "CRITICAL"
        evidence = self._evidence(analysis, risk_priority, precursor_priority)
        rationale = (
            f"Recommended because the {analysis.barrier or 'identified'} control is {state.replace('_', ' ')}. "
            f"Risk priority is {risk_priority or 'not available'}"
            + (f" and the observation maps to {analysis.life_saving_rule}." if analysis.life_saving_rule else ".")
        )
        key = f"report:{report.id}:{rule_id}:{ENGINE_VERSION}"
        existing = await self.db.scalar(select(InterventionRecommendation).where(InterventionRecommendation.idempotency_key == key))
        if existing:
            return [existing]
        recommendation = InterventionRecommendation(
            report_id=report.id, idempotency_key=key, intervention_rule_id=rule_id,
            category=category, title=title, description=description, rationale=rationale,
            priority=priority, action_type=action_type, review_required=review_required,
            evidence_snapshot=evidence,
            source_rule=f"control_state:{state}", engine_version=ENGINE_VERSION,
            risk_priority=risk_priority, life_saving_rule=analysis.life_saving_rule,
        )
        self.db.add(recommendation)
        await self.db.flush()
        logger.info("intervention_recommendation_generated", rule_id=rule_id, priority=priority, source_type="report", engine_version=ENGINE_VERSION)
        return [recommendation]

    async def generate_for_pattern(self, pattern: PrecursorPattern) -> InterventionRecommendation | None:
        """Create one advisory preventive recommendation for a recurring pattern."""
        if pattern.occurrence_count < 3:
            return None
        key = f"pattern:{pattern.id}:recurring-control-review:{ENGINE_VERSION}"
        existing = await self.db.scalar(select(InterventionRecommendation).where(InterventionRecommendation.idempotency_key == key))
        if existing:
            return existing
        priority = "HIGH" if pattern.priority in {"CRITICAL", "HIGH"} else "MEDIUM"
        action_type = InterventionActionType.ESCALATION if pattern.trend == "INCREASING" else InterventionActionType.PREVENTIVE
        recommendation = InterventionRecommendation(
            precursor_pattern_id=pattern.id, idempotency_key=key, intervention_rule_id="recurring-control-review",
            category=InterventionCategory.SUPERVISORY_VERIFICATION,
            title="Review recurring control weakness",
            description="Consider targeted supervisory verification and field inspection for the recurring control weakness.",
            rationale=f"Recommended to address {pattern.occurrence_count} recurring observations with a {pattern.trend.lower()} trend.",
            priority=priority, action_type=action_type,
            review_required=pattern.trend == "INCREASING" or priority == "HIGH",
            evidence_snapshot={"activity": pattern.activity, "hazard": pattern.hazard, "barrier": pattern.barrier, "failure_type": pattern.failure_type, "occurrence_count": pattern.occurrence_count, "trend": pattern.trend, "pattern_priority": pattern.priority},
            source_rule="precursor:recurring-control-review", engine_version=ENGINE_VERSION,
            risk_priority=pattern.priority,
        )
        self.db.add(recommendation)
        await self.db.flush()
        return recommendation

    async def list(self, report_human_id: str | None = None, priority: str | None = None) -> list[InterventionRead]:
        query = select(InterventionRecommendation)
        if report_human_id:
            query = query.join(Report).where(Report.report_id == report_human_id)
        if priority:
            query = query.where(InterventionRecommendation.priority == priority.upper())
        rows = (await self.db.scalars(query.order_by(InterventionRecommendation.created_at.desc(), InterventionRecommendation.id))).all()
        return [InterventionRead.model_validate(row) for row in rows]

    async def get(self, recommendation_id: UUID) -> InterventionRecommendation:
        item = await self.db.get(InterventionRecommendation, recommendation_id)
        if not item:
            raise NotFoundError("intervention recommendation")
        return item

    async def review(self, recommendation_id: UUID, payload: InterventionReviewRequest, actor_id: UUID, ip: str | None) -> InterventionRead:
        item = await self.get(recommendation_id)
        if item.review_status != InterventionReviewStatus.PENDING:
            raise AppError("INTERVENTION_ALREADY_REVIEWED", "Recommendation has already been reviewed", 409)
        if payload.decision == InterventionReviewStatus.PENDING:
            raise AppError("INVALID_INTERVENTION_DECISION", "A final intervention review decision is required", 422)
        modifications = [payload.reviewer_title, payload.reviewer_description, payload.reviewer_rationale]
        if payload.decision == InterventionReviewStatus.MODIFIED and not any(modifications):
            raise AppError("MODIFICATION_REQUIRED", "MODIFIED requires revised recommendation wording", 422)
        item.review_status = payload.decision
        item.reviewed_by = actor_id
        item.reviewed_at = datetime.now(UTC)
        item.reviewer_comments = payload.reviewer_comments
        item.reviewer_title = payload.reviewer_title
        item.reviewer_description = payload.reviewer_description
        item.reviewer_rationale = payload.reviewer_rationale
        await record_audit(self.db, user_id=actor_id, action=f"INTERVENTION_{payload.decision}", entity_type="intervention_recommendation", entity_id=item.id, details={"rule_id": item.intervention_rule_id}, ip_address=ip)
        await self.db.commit()
        await self.db.refresh(item)
        return InterventionRead.model_validate(item)

    async def summary(self) -> InterventionSummary:
        rows = (await self.db.execute(select(InterventionRecommendation.category, func.count()).group_by(InterventionRecommendation.category))).all()
        total = await self.db.scalar(select(func.count()).select_from(InterventionRecommendation)) or 0
        critical = await self.db.scalar(select(func.count()).select_from(InterventionRecommendation).where(InterventionRecommendation.priority == "CRITICAL")) or 0
        pending = await self.db.scalar(select(func.count()).select_from(InterventionRecommendation).where(InterventionRecommendation.review_status == InterventionReviewStatus.PENDING)) or 0
        return InterventionSummary(total=total, critical=critical, pending=pending, by_category={category: count for category, count in rows})
