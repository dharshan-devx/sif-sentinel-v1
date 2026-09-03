from datetime import UTC, datetime

from app.core.config import get_settings
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
from app.services.risk_engine.calculator import calculate_risk
from app.services.precursor_engine.precursor_service import PrecursorService
from app.services.report_service import ReportService
from app.services.llm.assistance_service import LLMAssistanceService


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
            # We first extract text to get candidates, ignoring precursor priority for now
            result = analyze_text(report.report_text)
        except RuntimeError as exc:
            raise AppError("MODEL_UNAVAILABLE", "Safety classifier is unavailable", 503) from exc

        # Check if the extracted candidates match any active precursor patterns
        precursor_priority = None
        if result.precursor_candidates:
            from app.services.precursor_engine.pattern_builder import build_pattern_key
            from sqlalchemy import select
            keys = [
                build_pattern_key(c.activity, c.hazard, c.barrier, c.failure_type).key 
                for c in result.precursor_candidates
            ]
            statement = select(PrecursorPattern.priority).where(
                PrecursorPattern.pattern_key.in_(keys),
                PrecursorPattern.priority.in_(["CRITICAL", "HIGH", "MEDIUM"]) # Only care about elevated risk
            )
            rows = (await self.db.execute(statement)).scalars().all()
            if rows:
                if "CRITICAL" in rows:
                    precursor_priority = "CRITICAL"
                elif "HIGH" in rows:
                    precursor_priority = "HIGH"
                else:
                    precursor_priority = "MEDIUM"
        
        # Recalculate risk with precursor intelligence
        import dataclasses
        risk_data = calculate_risk(
            sif_level=result.sif_level,
            sif_potential=result.sif_potential,
            barrier_status=result.barrier_status,
            has_lsr=bool(result.life_saving_rule),
            precursor_priority=precursor_priority
        )
        result = dataclasses.replace(result, risk=risk_data)

        try:
            analysis = ReportAnalysis(
                report_id=report.id,
                sif_potential=result.sif_potential,
                sif_level=result.sif_level,
                model_probability=result.sif_probability,
                risk_score=result.risk["score"],
                risk_priority=result.risk["priority"],
                risk_components=result.risk["components"],
                risk_version=result.risk["version"],
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
            
            # Phase J: Request optional LLM Assistance
            # Context explicitly bound to structured authoritative results to prevent injection overrides
            llm_context = {
                "structured_evidence": {
                    "activity": result.activity,
                    "hazard": result.hazard,
                    "barrier": result.barrier,
                    "barrier_status": result.barrier_status,
                    "barrier_failure": result.barrier_failure,
                    "life_saving_rule": result.life_saving_rule,
                },
                "authoritative_results": {
                    "sif_level": result.sif_level.value if result.sif_level else None,
                    "risk_score": risk_data["score"],
                    "risk_priority": risk_data["priority"],
                    "precursor_priority": precursor_priority,
                }
            }
            llm_res = await LLMAssistanceService.request_reviewer_summary(
                report_text=report.report_text,
                structured_evidence=llm_context["structured_evidence"],
                authoritative_results=llm_context["authoritative_results"]
            )
            
            # llm_attempted = True iff LLM was enabled (we made an attempt).
            # llm_used = True iff that attempt produced a usable summary.
            # This distinction allows dashboards to show:
            #   enabled + attempted + failed  vs.  disabled (no attempt).
            _llm_was_enabled = get_settings().llm_enabled
            analysis.llm_attempted = _llm_was_enabled
            analysis.llm_used = llm_res.success
            analysis.llm_provider = llm_res.provider if _llm_was_enabled else None
            analysis.llm_model_used = llm_res.model if _llm_was_enabled else None
            analysis.llm_timestamp = llm_res.timestamp if _llm_was_enabled else None
            analysis.reviewer_summary = llm_res.summary
            analysis.llm_error_code = llm_res.error_code
            
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

        return self._response(result, human_id, analysis.id, analysis_db_obj=analysis)

    @staticmethod
    def _response(
        result, report_id: str | None = None, analysis_id: UUID | None = None,
        analysis_db_obj: ReportAnalysis | None = None
    ) -> AnalysisResponse:
        resp = AnalysisResponse(
            report_id=report_id,
            analysis_id=analysis_id,
            sif_potential=result.sif_potential,
            sif_level=result.sif_level,
            model_probability=result.sif_probability,
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
            risk=result.risk,
        )
        if analysis_db_obj:
            resp.reviewer_summary = analysis_db_obj.reviewer_summary
            resp.llm_attempted = analysis_db_obj.llm_attempted
            resp.llm_used = analysis_db_obj.llm_used
            resp.llm_provider = analysis_db_obj.llm_provider
            resp.llm_model_used = analysis_db_obj.llm_model_used
            resp.llm_timestamp = analysis_db_obj.llm_timestamp
            resp.llm_error_code = analysis_db_obj.llm_error_code
            
        return resp
