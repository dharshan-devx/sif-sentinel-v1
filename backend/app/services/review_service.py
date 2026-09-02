from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReviewDecision, ReportStatus
from app.core.exceptions import AppError, NotFoundError
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.review import Review
from app.schemas.review import ReviewDecisionRequest, ReviewQueueItem
from app.services.audit_service import record_audit
from app.services.precursor_engine.precursor_service import PrecursorService


class ReviewService:
    def __init__(self, db: AsyncSession) -> None: self.db = db

    async def list(self, page: int, page_size: int) -> tuple[list[ReviewQueueItem], int]:
        query = select(Review, Report, ReportAnalysis).join(Report, Report.id == Review.report_id).outerjoin(ReportAnalysis, ReportAnalysis.id == Review.analysis_id).where(Review.decision == ReviewDecision.PENDING).order_by(Review.created_at)
        total = await self.db.scalar(select(func.count()).select_from(Review).where(Review.decision == ReviewDecision.PENDING)) or 0
        rows = (await self.db.execute(query.offset((page-1)*page_size).limit(page_size))).all()
        return [ReviewQueueItem(id=r.id, report_id=report.report_id, decision=r.decision, reviewer_id=r.reviewer_id, reviewed_at=r.reviewed_at, report_text=report.report_text, evidence_span=analysis.evidence_span if analysis else None, overall_confidence=analysis.overall_confidence if analysis else None, explanation=analysis.explanation if analysis else None) for r, report, analysis in rows], total

    async def get(self, review_id: UUID) -> ReviewQueueItem:
        row = (await self.db.execute(select(Review, Report, ReportAnalysis).join(Report, Report.id == Review.report_id).outerjoin(ReportAnalysis, ReportAnalysis.id == Review.analysis_id).where(Review.id == review_id))).first()
        if not row:
            raise NotFoundError("review")
        review, report, analysis = row
        return ReviewQueueItem(id=review.id, report_id=report.report_id, decision=review.decision, reviewer_id=review.reviewer_id, reviewed_at=review.reviewed_at, report_text=report.report_text, evidence_span=analysis.evidence_span if analysis else None, overall_confidence=analysis.overall_confidence if analysis else None, explanation=analysis.explanation if analysis else None)

    async def decide(self, review_id: UUID, payload: ReviewDecisionRequest, actor_id: UUID, ip: str | None) -> Review:
        review = await self.db.get(Review, review_id)
        if not review:
            raise NotFoundError("review")
        if review.decision != ReviewDecision.PENDING:
            raise AppError("REVIEW_ALREADY_DECIDED", "Review has already been decided", 409)
        if payload.decision == ReviewDecision.PENDING:
            raise AppError("INVALID_REVIEW_DECISION", "A final review decision is required", 422)
        corrected = payload.model_dump(exclude={"decision", "reviewer_comment"}, exclude_none=True)
        if payload.decision == ReviewDecision.MODIFY and not any(corrected.values()):
            raise AppError("MODIFICATION_REQUIRED", "MODIFY requires at least one correction", 422)
        review.reviewer_id, review.decision, review.reviewed_at = actor_id, payload.decision, datetime.now(UTC)
        for key, value in payload.model_dump(exclude={"decision"}, exclude_none=True).items():
            setattr(review, key, value)
        analysis = await self.db.get(ReportAnalysis, review.analysis_id) if review.analysis_id else None
        if analysis and payload.decision == ReviewDecision.MODIFY:
            mapping = {"corrected_sif_level":"sif_level", "corrected_activity":"activity", "corrected_hazard":"hazard", "corrected_barrier":"barrier", "corrected_barrier_status":"barrier_status", "corrected_barrier_failure":"barrier_failure", "corrected_life_saving_rule":"life_saving_rule"}
            for source, target in mapping.items():
                value = getattr(review, source)
                if value is not None:
                    setattr(analysis, target, value)
        # A1 FIX: Transition report status to REVIEWED so dashboard counters reflect reality.
        report = await self.db.get(Report, review.report_id)
        if report and report.status == ReportStatus.REVIEW_REQUIRED:
            report.status = ReportStatus.REVIEWED
        await record_audit(self.db, user_id=actor_id, action=f"REVIEW_{payload.decision.value}D" if payload.decision != ReviewDecision.MODIFY else "REVIEW_MODIFIED", entity_type="review", entity_id=review.id, details={"report_id": str(review.report_id)}, ip_address=ip)
        await PrecursorService(self.db).rebuild()
        await self.db.commit()
        await self.db.refresh(review)
        return review
