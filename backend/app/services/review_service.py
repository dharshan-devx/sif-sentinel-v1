"""Review service — Phase C hardened implementation.

State machine (Review.decision):
    PENDING  → APPROVE  → report.status = REVIEWED
    PENDING  → REJECT   → report.status = REVIEWED
    PENDING  → MODIFY   → report.status = REVIEWED (+ corrected fields stored)

Invalid transitions (returns HTTP 409):
    APPROVE/REJECT/MODIFY → any further decision

AI provenance rule:
    APPROVE and REJECT:
        ReportAnalysis is NOT modified. The AI output is preserved exactly.
        The Review record stores the decision without touching the analysis.
    MODIFY:
        Corrections are stored in the Review.corrected_* columns ONLY.
        ReportAnalysis is NOT mutated — AI predictions are permanently auditable.
        Downstream analytics read corrections from the Review record when present.

Concurrency note:
    The PENDING guard is enforced while holding a row lock where the database
    supports it. This prevents two PostgreSQL reviewers from both observing a
    pending decision and committing conflicting final decisions.

Precursor rebuild:
    rebuild() is called on APPROVE and MODIFY decisions because:
    - APPROVE validates the AI prediction → analysis is trustworthy for patterns
    - MODIFY corrects the analysis → corrected fields update precursor signals
    REJECT is intentionally excluded because a rejected prediction is not
    trustworthy enough to influence precursor analytics.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReportStatus, ReviewDecision
from app.core.exceptions import AppError, NotFoundError
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.review import Review
from app.schemas.review import (
    DecisionResponse,
    ReviewDecisionRequest,
    ReviewQueueItem,
    ReviewStatusFilter,
)
from app.services.audit_service import record_audit
from app.services.precursor_engine.precursor_service import PrecursorService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_queue_item(review: Review, report: Report, analysis: ReportAnalysis | None, pending: bool) -> ReviewQueueItem:
    """Build ReviewQueueItem from ORM rows.

    For PENDING reviews, reviewer_id and reviewed_at are set to None so
    callers can distinguish them from completed reviews even though the DB
    columns store the initiating analyst's id/timestamp as a placeholder.
    """
    return ReviewQueueItem(
        id=review.id,
        report_id=report.report_id,
        decision=review.decision,
        reviewer_id=None if pending else review.reviewer_id,
        reviewed_at=None if pending else review.reviewed_at,
        report_text=report.report_text,
        evidence_span=analysis.evidence_span if analysis else None,
        overall_confidence=analysis.overall_confidence if analysis else None,
        explanation=analysis.explanation if analysis else None,
        reviewer_comment=review.reviewer_comment,
        corrected_sif_level=review.corrected_sif_level,
        corrected_activity=review.corrected_activity,
        corrected_hazard=review.corrected_hazard,
        corrected_barrier=review.corrected_barrier,
        corrected_barrier_status=review.corrected_barrier_status,
        corrected_barrier_failure=review.corrected_barrier_failure,
        corrected_life_saving_rule=review.corrected_life_saving_rule,
    )


def _joined_query():
    """Base SELECT that joins Review → Report → ReportAnalysis."""
    return (
        select(Review, Report, ReportAnalysis)
        .join(Report, Report.id == Review.report_id)
        .outerjoin(ReportAnalysis, ReportAnalysis.id == Review.analysis_id)
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        page: int,
        page_size: int,
        status_filter: ReviewStatusFilter = ReviewStatusFilter.PENDING,
    ) -> tuple[list[ReviewQueueItem], int]:
        """Return paginated reviews filtered by status.

        status_filter:
            PENDING  → only Review.decision == PENDING
            REVIEWED → only non-PENDING decisions (APPROVE/REJECT/MODIFY)
            ALL      → no filter
        """
        from sqlalchemy import func

        base = _joined_query()

        if status_filter == ReviewStatusFilter.PENDING:
            base = base.where(Review.decision == ReviewDecision.PENDING)
            pending_mode = True
        elif status_filter == ReviewStatusFilter.REVIEWED:
            base = base.where(Review.decision != ReviewDecision.PENDING)
            pending_mode = False
        else:  # ALL
            pending_mode = None  # handled per-row below

        base = base.order_by(Review.created_at)

        # Count query mirrors the same filter
        count_q = select(func.count()).select_from(Review)
        if status_filter == ReviewStatusFilter.PENDING:
            count_q = count_q.where(Review.decision == ReviewDecision.PENDING)
        elif status_filter == ReviewStatusFilter.REVIEWED:
            count_q = count_q.where(Review.decision != ReviewDecision.PENDING)

        total = await self.db.scalar(count_q) or 0
        rows = (
            await self.db.execute(
                base.offset((page - 1) * page_size).limit(page_size)
            )
        ).all()

        items = []
        for r, report, analysis in rows:
            is_pending = pending_mode if pending_mode is not None else (r.decision == ReviewDecision.PENDING)
            items.append(_to_queue_item(r, report, analysis, is_pending))

        return items, total

    async def get(self, review_id: UUID) -> ReviewQueueItem:
        row = (
            await self.db.execute(
                _joined_query().where(Review.id == review_id)
            )
        ).first()
        if not row:
            raise NotFoundError("review")
        review, report, analysis = row
        pending = review.decision == ReviewDecision.PENDING
        return _to_queue_item(review, report, analysis, pending)

    async def decide(
        self,
        review_id: UUID,
        payload: ReviewDecisionRequest,
        actor_id: UUID,
        ip: str | None,
    ) -> DecisionResponse:
        """Apply a final review decision.

        Validates the state machine, writes corrected fields to the Review
        record (without mutating the original ReportAnalysis), updates
        Report.status, logs the audit event, conditionally rebuilds the
        precursor graph, and commits everything in one transaction.
        """
        # --- Load ---
        review = await self.db.scalar(
            select(Review).where(Review.id == review_id).with_for_update()
        )
        if not review:
            raise NotFoundError("review")

        # --- State machine guard ---
        if review.decision != ReviewDecision.PENDING:
            raise AppError(
                "REVIEW_ALREADY_DECIDED",
                f"Review has already been decided: {review.decision.value}",
                409,
            )

        # --- Reject attempt to submit PENDING as a decision ---
        if payload.decision == ReviewDecision.PENDING:
            raise AppError(
                "INVALID_REVIEW_DECISION",
                "A final decision (APPROVE, REJECT, or MODIFY) is required",
                422,
            )

        # --- MODIFY requires at least one correction ---
        corrected_fields = payload.model_dump(
            exclude={"decision", "reviewer_comment"}, exclude_none=True
        )
        if payload.decision == ReviewDecision.MODIFY and not corrected_fields:
            raise AppError(
                "MODIFICATION_REQUIRED",
                "MODIFY decision requires at least one corrected field",
                422,
            )

        decided_at = datetime.now(UTC)

        # --- Write decision metadata to the Review record ---
        review.decision = payload.decision
        review.reviewer_id = actor_id
        review.reviewed_at = decided_at
        review.reviewer_comment = payload.reviewer_comment

        # --- Store corrected fields on the Review (NOT on ReportAnalysis) ---
        # AI provenance is preserved: ReportAnalysis is never mutated here.
        # Corrected values live in Review.corrected_* columns so the original
        # AI prediction is permanently auditable alongside the human correction.
        for field, value in payload.model_dump(
            include={
                "corrected_sif_level",
                "corrected_activity",
                "corrected_hazard",
                "corrected_barrier",
                "corrected_barrier_status",
                "corrected_barrier_failure",
                "corrected_life_saving_rule",
            },
            exclude_none=True,
        ).items():
            setattr(review, field, value)

        # --- Transition Report.status ---
        report = await self.db.get(Report, review.report_id)
        if report and report.status == ReportStatus.REVIEW_REQUIRED:
            report.status = ReportStatus.REVIEWED

        # --- Audit log ---
        action_map = {
            ReviewDecision.APPROVE: "REVIEW_APPROVED",
            ReviewDecision.REJECT: "REVIEW_REJECTED",
            ReviewDecision.MODIFY: "REVIEW_MODIFIED",
        }
        audit_details: dict = {
            "report_id": str(review.report_id),
            "decision": payload.decision.value,
        }
        if payload.decision == ReviewDecision.MODIFY and corrected_fields:
            audit_details["corrections"] = list(corrected_fields.keys())

        await record_audit(
            self.db,
            user_id=actor_id,
            action=action_map[payload.decision],
            entity_type="review",
            entity_id=review.id,
            details=audit_details,
            ip_address=ip,
        )

        # --- Precursor rebuild ---
        # Rebuild after APPROVE (AI prediction validated → trustworthy signal)
        # Rebuild after MODIFY  (corrections update precursor inputs)
        # Skip   after REJECT  (rejected prediction is unreliable for analytics)
        if payload.decision in (ReviewDecision.APPROVE, ReviewDecision.MODIFY):
            await PrecursorService(self.db).rebuild()

        # --- Commit ---
        await self.db.commit()
        await self.db.refresh(review)

        return DecisionResponse(
            review_id=review.id,
            decision=review.decision,
            report_id=report.report_id if report else str(review.report_id),
            report_status=report.status.value if report else ReportStatus.REVIEWED.value,
            reviewer_id=actor_id,
            reviewed_at=decided_at,
            message="Review completed successfully.",
        )
