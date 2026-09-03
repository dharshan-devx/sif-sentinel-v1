from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BarrierStatus, ReportStatus, ReviewDecision
from app.core.exceptions import AppError
from app.models.model_prediction import ModelPrediction
from app.models.report_analysis import ReportAnalysis
from app.models.precursor_candidate import PrecursorCandidate
from app.models.precursor_pattern import PrecursorPattern
from app.models.review import Review
from app.schemas.analysis import AnalysisResponse
from app.services.audit_service import record_audit
from app.services.nlp.analysis_pipeline import analyze_text
from app.services.precursor_engine.precursor_service import PrecursorService
from app.services.report_service import ReportService


class AnalysisService:
    def __init__(self, db: AsyncSession | None) -> None:
        self.db = db

    def analyze_direct(self, text: str) -> AnalysisResponse:
        try:
            result = analyze_text(text)
        except RuntimeError as exc:
            raise AppError("MODEL_UNAVAILABLE", "Safety classifier is unavailable", 503) from exc
        return self._response(result)

    async def analyze_report(
        self, human_id: str, actor_id: UUID, ip_address: str | None
    ) -> AnalysisResponse:
        if self.db is None:
            raise AppError("NO_DB_SESSION", "Database session is required for report analysis", 500)

        report = await ReportService(self.db).get(human_id)

        try:
            result = analyze_text(report.report_text)
        except RuntimeError as exc:
            raise AppError("MODEL_UNAVAILABLE", "Safety classifier is unavailable", 503) from exc

        try:
            analysis = ReportAnalysis(
                report_id=report.id,
                sif_potential=result.sif_potential,
                sif_level=result.sif_level,
                sif_probability=result.sif_probability,
                activity=result.activity,
                hazard=result.hazard,
                barrier=result.barrier,
                barrier_status=BarrierStatus(result.barrier_status),
                barrier_failure=result.barrier_failure,
                life_saving_rule=result.life_saving_rule,
                rule_confidence=result.rule_confidence,
                evidence_span=result.evidence_span,
                explanation=result.explanation,
                overall_confidence=result.overall_confidence,
                model_version=result.model_version,
                analysis_status="REVIEW_REQUIRED" if result.review_required else "COMPLETE",
            )
            self.db.add(analysis)
            await self.db.flush()

            self.db.add(ModelPrediction(
                report_id=report.id,
                model_name=result.model_name,
                model_version=result.model_version,
                predicted_label="SIF" if result.sif_potential else "NON_SIF",
                probability=result.sif_probability,
                prediction_json={
                    "sif_level": result.sif_level.value,
                    "entities": {
                        "activity": result.activity,
                        "hazard": result.hazard,
                        "barrier": result.barrier,
                        "barrier_status": result.barrier_status,
                        "barrier_failure": result.barrier_failure,
                    },
                    "evidence_terms": result.evidence_terms,
                    "overall_confidence": result.overall_confidence,
                },
            ))

            for candidate in result.precursor_candidates:
                self.db.add(PrecursorCandidate(
                    report_id=report.id,
                    category=candidate.category,
                    activity=candidate.activity,
                    hazard=candidate.hazard,
                    barrier=candidate.barrier,
                    failure_type=candidate.failure_type,
                    evidence_text=candidate.evidence_text,
                ))

            report.status = (
                ReportStatus.REVIEW_REQUIRED if result.review_required else ReportStatus.ANALYZED
            )

            if result.review_required:
                self.db.add(Review(
                    report_id=report.id,
                    analysis_id=analysis.id,
                    reviewer_id=actor_id,
                    decision=ReviewDecision.PENDING,
                    reviewer_comment=(
                        "Automatically queued because the analysis confidence requires human review."
                    ),
                    reviewed_at=datetime.now(UTC),
                ))

            await PrecursorService(self.db).rebuild()
            await record_audit(
                self.db,
                user_id=actor_id,
                action="REPORT_ANALYZED",
                entity_type="report",
                entity_id=report.id,
                details={"model_version": result.model_version, "review_required": result.review_required},
                ip_address=ip_address,
            )
            await self.db.commit()
            await self.db.refresh(analysis)

        except Exception:
            await self.db.rollback()
            raise

        return self._response(result, human_id, analysis.id)

    @staticmethod
    def _response(
        result, report_id: str | None = None, analysis_id: UUID | None = None
    ) -> AnalysisResponse:
        return AnalysisResponse(
            report_id=report_id,
            analysis_id=analysis_id,
            sif_potential=result.sif_potential,
            sif_level=result.sif_level,
            sif_probability=result.sif_probability,
            activity=result.activity,
            hazard=result.hazard,
            barrier=result.barrier,
            barrier_status=BarrierStatus(result.barrier_status),
            barrier_failure=result.barrier_failure,
            life_saving_rule=result.life_saving_rule,
            rule_confidence=result.rule_confidence,
            evidence_span=result.evidence_span,
            evidence_sentences=result.evidence_sentences,
            evidence_terms=result.evidence_terms,
            overall_confidence=result.overall_confidence,
            review_required=result.review_required,
            model_version=result.model_version,
            explanation=result.explanation,
        )
