from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.precursor_candidate import PrecursorCandidate
from app.models.precursor_pattern import PrecursorPattern
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.site import Site
from app.schemas.precursor import (
    GraphEdge,
    GraphNode,
    PrecursorDetail,
    PrecursorGraph,
    PrecursorSummary,
    RepresentativeReport,
)
from app.services.precursor_engine.pattern_aggregator import (
    PatternMetrics,
    aggregate_patterns,
    latest_analysis_subquery,
)


class PrecursorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def rebuild(self, *, commit: bool = False) -> int:
        metrics = await aggregate_patterns(self.db)
        keys = {item.key for item in metrics}
        existing = {pattern.pattern_key: pattern for pattern in (await self.db.scalars(select(PrecursorPattern))).all()}
        
        for item in metrics:
            pattern = existing.get(item.key)
            values = {
                "category": item.category,
                "activity": item.activity,
                "hazard": item.hazard,
                "barrier": item.barrier,
                "failure_type": item.failure_type,
                "occurrence_count": item.occurrence_count,
                "sif_count": item.sif_count,
                "sif_density": item.sif_density,
                "recent_count": item.recent_count,
                "site_count": item.site_count,
                "department_count": item.department_count,
                "trend": item.trend,
                "risk_score": item.risk_score,
                "priority": item.priority,
                "first_seen": item.first_seen,
                "last_seen": item.last_seen
            }
            if pattern:
                for field, value in values.items():
                    setattr(pattern, field, value)
            else:
                self.db.add(PrecursorPattern(pattern_key=item.key, **values))
                
        if existing:
            await self.db.execute(delete(PrecursorPattern).where(PrecursorPattern.pattern_key.not_in(keys) if keys else True))
            
        await self.db.flush()
        # A recurring pattern may warrant one preventive advisory recommendation.
        # Import locally to keep precursor aggregation independent of the API layer.
        from app.services.intervention_service import InterventionService
        intervention_service = InterventionService(self.db)
        for pattern in (await self.db.scalars(select(PrecursorPattern))).all():
            await intervention_service.generate_for_pattern(pattern)
        if commit:
            await self.db.commit()
        return len(metrics)

    async def list(self, *, site_id: UUID | None = None, activity: str | None = None, hazard: str | None = None, barrier: str | None = None, priority: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None, limit: int = 50, sort: str = "risk_score") -> list[PrecursorSummary]:
        if (date_from or date_to) and not site_id:
            metrics = await aggregate_patterns(self.db, date_from, date_to)
            ids = {item.pattern_key: item.id for item in (await self.db.scalars(select(PrecursorPattern).where(PrecursorPattern.pattern_key.in_([metric.key for metric in metrics])))).all()}
            filtered = [metric for metric in metrics if metric.key in ids and (not activity or metric.activity == activity.casefold()) and (not hazard or metric.hazard == hazard.casefold()) and (not barrier or metric.barrier == barrier.casefold()) and (not priority or metric.priority == priority.upper())]
            ordered = sorted(filtered, key=lambda metric: metric.last_seen if sort == "recent" else metric.risk_score, reverse=True)
            return [self._summary_from_metrics(ids[metric.key], metric) for metric in ordered[:limit]]
            
        filters = []
        for field, value in ((PrecursorPattern.activity, activity), (PrecursorPattern.hazard, hazard), (PrecursorPattern.barrier, barrier), (PrecursorPattern.priority, priority)):
            if value:
                filters.append(field == value.casefold())
        if date_from:
            filters.append(PrecursorPattern.last_seen >= date_from)
        if date_to:
            filters.append(PrecursorPattern.first_seen <= date_to)
            
        if site_id:
            site_match = and_(
                Report.site_id == site_id,
                PrecursorCandidate.report_id == Report.id,
                PrecursorCandidate.category == PrecursorPattern.category,
                func_lower(PrecursorCandidate.activity) == PrecursorPattern.activity,
                func_lower(PrecursorCandidate.hazard) == PrecursorPattern.hazard,
                func_lower(PrecursorCandidate.barrier) == PrecursorPattern.barrier,
                func_lower(PrecursorCandidate.failure_type) == PrecursorPattern.failure_type,
            )
            filters.append(exists(select(1).select_from(Report).join(PrecursorCandidate).where(site_match)))
            
        order = PrecursorPattern.last_seen.desc() if sort == "recent" else PrecursorPattern.risk_score.desc()
        patterns = (await self.db.scalars(select(PrecursorPattern).where(*filters).order_by(order).limit(limit))).all()
        return [self._summary(pattern) for pattern in patterns]

    async def detail(self, precursor_id: UUID) -> PrecursorDetail:
        pattern = await self.db.get(PrecursorPattern, precursor_id)
        if not pattern:
            raise NotFoundError("precursor")
            
        match = and_(
            PrecursorCandidate.category == pattern.category,
            func_lower(PrecursorCandidate.activity) == pattern.activity, 
            func_lower(PrecursorCandidate.hazard) == pattern.hazard, 
            func_lower(PrecursorCandidate.barrier) == pattern.barrier, 
            func_lower(PrecursorCandidate.failure_type) == pattern.failure_type
        )
        
        latest = latest_analysis_subquery()
        base = select(Report, ReportAnalysis, Site.name.label("site_name")).join(PrecursorCandidate, PrecursorCandidate.report_id == Report.id).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).join(Site, Site.id == Report.site_id).where(match)
        rows = (await self.db.execute(base.order_by(Report.reported_at.desc()).limit(5))).all()
        
        reports = [RepresentativeReport(report_id=report.report_id, reported_at=report.reported_at, site_name=site_name, department=report.department, sif_level=analysis.sif_level.value if analysis.sif_level else None) for report, analysis, site_name in rows]
        all_rows = (await self.db.execute(select(Site.name, Report.department).select_from(Report).join(PrecursorCandidate, PrecursorCandidate.report_id == Report.id).join(Site, Site.id == Report.site_id).where(match).distinct())).all()
        
        return PrecursorDetail(**self._summary(pattern).model_dump(), sites=sorted({row[0] for row in all_rows}), departments=sorted({row[1] for row in all_rows}), representative_reports=reports)

    async def graph(self, precursor_id: UUID) -> PrecursorGraph:
        pattern = await self.db.get(PrecursorPattern, precursor_id)
        if not pattern:
            raise NotFoundError("precursor")
        nodes = [GraphNode(id="activity", label=pattern.activity, type="activity", statistics={"occurrences": pattern.occurrence_count}), GraphNode(id="hazard", label=pattern.hazard, type="hazard", statistics={"sif_density": pattern.sif_density}), GraphNode(id="barrier", label=pattern.barrier, type="barrier", statistics={"risk_score": pattern.risk_score}), GraphNode(id="failure", label=pattern.failure_type, type="failure", statistics={"recent_count": pattern.recent_count}), GraphNode(id="sif", label="SIF potential", type="sif", statistics={"sif_count": pattern.sif_count})]
        edges = [GraphEdge(source="activity", target="hazard", label="exposes"), GraphEdge(source="hazard", target="barrier", label="controlled by"), GraphEdge(source="barrier", target="failure", label="failure"), GraphEdge(source="failure", target="sif", label="risk signal")]
        return PrecursorGraph(nodes=nodes, edges=edges)

    @staticmethod
    def _summary(pattern: PrecursorPattern) -> PrecursorSummary:
        why = PrecursorService._why(pattern.category, pattern.occurrence_count, pattern.sif_count, pattern.sif_density, pattern.recent_count, pattern.trend)
        return PrecursorSummary.model_validate({**{column.name: getattr(pattern, column.name) for column in PrecursorPattern.__table__.columns}, "why_it_matters": why})

    @staticmethod
    def _summary_from_metrics(pattern_id: UUID, metric: PatternMetrics) -> PrecursorSummary:
        return PrecursorSummary(id=pattern_id, category=metric.category, activity=metric.activity, hazard=metric.hazard, barrier=metric.barrier, failure_type=metric.failure_type, occurrence_count=metric.occurrence_count, sif_count=metric.sif_count, sif_density=metric.sif_density, recent_count=metric.recent_count, site_count=metric.site_count, department_count=metric.department_count, trend=metric.trend, risk_score=metric.risk_score, priority=metric.priority, first_seen=metric.first_seen, last_seen=metric.last_seen, why_it_matters=PrecursorService._why(metric.category, metric.occurrence_count, metric.sif_count, metric.sif_density, metric.recent_count, metric.trend))

    @staticmethod
    def _why(category: str, occurrence_count: int, sif_count: int, sif_density: float, recent_count: int, trend: str) -> str:
        cat_desc = category.replace("_", " ").title()
        return f"Precursor pattern ({cat_desc}): {occurrence_count} recurring observations, {sif_count} SIF-associated ({sif_density:.0%}), {recent_count} in the last 30 days, with a {trend.replace('_', ' ').lower()} trend."

def func_lower(column):
    return func.lower(func.trim(column))
