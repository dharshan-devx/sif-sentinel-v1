from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
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
        """Rebuild all precursor patterns from current analysis data.

        ``commit=False`` (default): flushes only — the caller is responsible
        for committing as part of a larger transaction (used by analysis and
        review services).

        ``commit=True``: commits immediately — used by the explicit
        POST /precursors/rebuild endpoint where rebuild IS the transaction.
        """
        metrics = await aggregate_patterns(self.db)
        keys = {item.key for item in metrics}
        existing = {pattern.pattern_key: pattern for pattern in (await self.db.scalars(select(PrecursorPattern))).all()}
        for item in metrics:
            pattern = existing.get(item.key)
            values = {"activity": item.activity, "hazard": item.hazard, "barrier": item.barrier, "failure_type": item.failure_type, "occurrence_count": item.occurrence_count, "sif_count": item.sif_count, "sif_density": item.sif_density, "recent_count": item.recent_count, "site_count": item.site_count, "department_count": item.department_count, "trend": item.trend, "risk_score": item.risk_score, "risk_level": item.risk_level, "first_seen": item.first_seen, "last_seen": item.last_seen}
            if pattern:
                for field, value in values.items():
                    setattr(pattern, field, value)
            else:
                self.db.add(PrecursorPattern(pattern_key=item.key, **values))
        if existing:
            await self.db.execute(delete(PrecursorPattern).where(PrecursorPattern.pattern_key.not_in(keys) if keys else True))
        await self.db.flush()
        if commit:
            await self.db.commit()
        return len(metrics)

    async def list(self, *, site_id: UUID | None = None, activity: str | None = None, hazard: str | None = None, barrier: str | None = None, risk_level: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None, limit: int = 50, sort: str = "risk_score") -> list[PrecursorSummary]:
        if (date_from or date_to) and not site_id:
            metrics = await aggregate_patterns(self.db, date_from, date_to)
            ids = {item.pattern_key: item.id for item in (await self.db.scalars(select(PrecursorPattern).where(PrecursorPattern.pattern_key.in_([metric.key for metric in metrics])))).all()}
            filtered = [metric for metric in metrics if metric.key in ids and (not activity or metric.activity == activity.casefold()) and (not hazard or metric.hazard == hazard.casefold()) and (not barrier or metric.barrier == barrier.casefold()) and (not risk_level or metric.risk_level == risk_level.upper())]
            ordered = sorted(filtered, key=lambda metric: metric.last_seen if sort == "recent" else metric.risk_score, reverse=True)
            return [self._summary_from_metrics(ids[metric.key], metric) for metric in ordered[:limit]]
        filters = []
        for field, value in ((PrecursorPattern.activity, activity), (PrecursorPattern.hazard, hazard), (PrecursorPattern.barrier, barrier), (PrecursorPattern.risk_level, risk_level)):
            if value:
                filters.append(field == value.casefold())
        if date_from:
            filters.append(PrecursorPattern.last_seen >= date_from)
        if date_to:
            filters.append(PrecursorPattern.first_seen <= date_to)
        if site_id:
            latest = latest_analysis_subquery()
            site_match = and_(
                Report.site_id == site_id,
                ReportAnalysis.report_id == Report.id,
                latest.c.report_id == ReportAnalysis.report_id,
                latest.c.latest_created == ReportAnalysis.created_at,
                func_lower(ReportAnalysis.activity) == PrecursorPattern.activity,
                func_lower(ReportAnalysis.hazard) == PrecursorPattern.hazard,
                func_lower(ReportAnalysis.barrier) == PrecursorPattern.barrier,
                func_lower(ReportAnalysis.barrier_failure) == PrecursorPattern.failure_type,
            )
            filters.append(exists(select(1).select_from(Report).join(ReportAnalysis).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).where(site_match)))
        order = PrecursorPattern.last_seen.desc() if sort == "recent" else PrecursorPattern.risk_score.desc()
        patterns = (await self.db.scalars(select(PrecursorPattern).where(*filters).order_by(order).limit(limit))).all()
        return [self._summary(pattern) for pattern in patterns]

    async def detail(self, precursor_id: UUID) -> PrecursorDetail:
        pattern = await self.db.get(PrecursorPattern, precursor_id)
        if not pattern:
            raise NotFoundError("precursor")
        latest = latest_analysis_subquery()
        match = and_(func_lower(ReportAnalysis.activity) == pattern.activity, func_lower(ReportAnalysis.hazard) == pattern.hazard, func_lower(ReportAnalysis.barrier) == pattern.barrier, func_lower(ReportAnalysis.barrier_failure) == pattern.failure_type)
        base = select(Report, ReportAnalysis, Site.name.label("site_name")).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).join(Site, Site.id == Report.site_id).where(match)
        rows = (await self.db.execute(base.order_by(Report.reported_at.desc()).limit(5))).all()
        reports = [RepresentativeReport(report_id=report.report_id, reported_at=report.reported_at, site_name=site_name, department=report.department, sif_level=analysis.sif_level.value if analysis.sif_level else None) for report, analysis, site_name in rows]
        all_rows = (await self.db.execute(select(Site.name, Report.department).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).join(Site, Site.id == Report.site_id).where(match).distinct())).all()
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
        why = PrecursorService._why(pattern.occurrence_count, pattern.sif_count, pattern.sif_density, pattern.recent_count, pattern.trend)
        return PrecursorSummary.model_validate({**{column.name: getattr(pattern, column.name) for column in PrecursorPattern.__table__.columns}, "why_it_matters": why})

    @staticmethod
    def _summary_from_metrics(pattern_id: UUID, metric: PatternMetrics) -> PrecursorSummary:
        return PrecursorSummary(id=pattern_id, activity=metric.activity, hazard=metric.hazard, barrier=metric.barrier, failure_type=metric.failure_type, occurrence_count=metric.occurrence_count, sif_count=metric.sif_count, sif_density=metric.sif_density, recent_count=metric.recent_count, site_count=metric.site_count, department_count=metric.department_count, trend=metric.trend, risk_score=metric.risk_score, risk_level=metric.risk_level, first_seen=metric.first_seen, last_seen=metric.last_seen, why_it_matters=PrecursorService._why(metric.occurrence_count, metric.sif_count, metric.sif_density, metric.recent_count, metric.trend))

    @staticmethod
    def _why(occurrence_count: int, sif_count: int, sif_density: float, recent_count: int, trend: str) -> str:
        return f"Potential precursor signal: {occurrence_count} analyzed reports, {sif_count} SIF-associated ({sif_density:.0%}), {recent_count} in the last 30 days, with a {trend.replace('_', ' ').lower()} trend."

def func_lower(column):
    """Lowercase + trim a SQLAlchemy column expression for case-insensitive matching."""
    return func.lower(func.trim(column))
