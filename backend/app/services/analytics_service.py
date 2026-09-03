from datetime import UTC, datetime, timedelta

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReportStatus, SIFLevel
from app.models.precursor_pattern import PrecursorPattern
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.site import Site
from app.schemas.dashboard import (
    BarrierFailurePoint,
    DashboardSummary,
    DistributionItem,
    TimeSeriesPoint,
)
from app.services.precursor_engine.pattern_aggregator import latest_analysis_subquery


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def summary(self) -> DashboardSummary:
        latest = latest_analysis_subquery()
        metrics = (await self.db.execute(select(func.count(Report.id), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0), func.coalesce(func.sum(case((ReportAnalysis.sif_level == SIFLevel.HIGH, 1), else_=0)), 0), func.coalesce(func.sum(case((Report.status == ReportStatus.REVIEW_REQUIRED, 1), else_=0)), 0), func.count(func.distinct(Report.site_id))).select_from(Report).outerjoin(latest, latest.c.report_id == Report.id).outerjoin(ReportAnalysis, (ReportAnalysis.report_id == latest.c.report_id) & (ReportAnalysis.created_at == latest.c.latest_created)))).one()
        total, sif, high, review, sites = (int(value or 0) for value in metrics)
        active = await self.db.scalar(select(func.count()).select_from(PrecursorPattern)) or 0
        return DashboardSummary(total_reports=total, total_sif_reports=sif, high_risk_reports=high, review_required=review, active_precursors=active, sites_monitored=sites, sif_rate=round(sif / total, 3) if total else 0.0, high_risk_rate=round(high / total, 3) if total else 0.0)

    async def sif_trend(self, window: str) -> list[TimeSeriesPoint]:
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[window]
        start = datetime.now(UTC) - timedelta(days=days)
        latest = latest_analysis_subquery()
        dialect = self.db.bind.dialect.name
        day = func.date(Report.reported_at).label("day") if dialect == "sqlite" else cast(Report.reported_at, Date).label("day")
        statement = select(day, func.count(Report.id).label("total"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif"), func.coalesce(func.sum(case((ReportAnalysis.sif_level == SIFLevel.HIGH, 1), else_=0)), 0).label("high")).select_from(Report).outerjoin(latest, latest.c.report_id == Report.id).outerjoin(ReportAnalysis, (ReportAnalysis.report_id == latest.c.report_id) & (ReportAnalysis.created_at == latest.c.latest_created)).where(Report.reported_at >= start).group_by(day).order_by(day)
        return [TimeSeriesPoint(date=str(row.day), total_reports=int(row.total), sif_reports=int(row.sif), high_sif_reports=int(row.high), sif_rate=round(int(row.sif) / int(row.total), 3) if row.total else 0.0) for row in (await self.db.execute(statement)).all()]

    async def distribution(self, field: str) -> list[DistributionItem]:
        column = {"activity": ReportAnalysis.activity, "hazard": ReportAnalysis.hazard, "lsr": ReportAnalysis.life_saving_rule}[field]
        latest = latest_analysis_subquery()
        total = await self.db.scalar(select(func.count(Report.id))) or 0
        statement = select(column.label("name"), func.count(Report.id).label("count"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif")).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).where(column.is_not(None)).group_by(column).order_by(func.count(Report.id).desc())
        return [DistributionItem(name=row.name, count=int(row.count), sif_count=int(row.sif), sif_density=round(int(row.sif) / int(row.count), 3) if row.count else 0.0, percentage=round(int(row.count) / total, 3) if total else 0.0) for row in (await self.db.execute(statement)).all()]

    async def site_comparison(self) -> list[DistributionItem]:
        latest = latest_analysis_subquery()
        total = await self.db.scalar(select(func.count(Report.id))) or 0
        statement = select(Site.name.label("name"), func.count(Report.id).label("count"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif")).select_from(Report).join(Site, Site.id == Report.site_id).outerjoin(latest, latest.c.report_id == Report.id).outerjoin(ReportAnalysis, (ReportAnalysis.report_id == latest.c.report_id) & (ReportAnalysis.created_at == latest.c.latest_created)).group_by(Site.name).order_by(func.count(Report.id).desc())
        return [DistributionItem(name=row.name, count=int(row.count), sif_count=int(row.sif), sif_density=round(int(row.sif) / int(row.count), 3) if row.count else 0.0, percentage=round(int(row.count) / total, 3) if total else 0.0) for row in (await self.db.execute(statement)).all()]

    async def barrier_failures(self, window: str) -> list[BarrierFailurePoint]:
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[window]
        latest = latest_analysis_subquery()
        dialect = self.db.bind.dialect.name
        day = func.date(Report.reported_at).label("day") if dialect == "sqlite" else cast(Report.reported_at, Date).label("day")
        statement = select(day, func.count(Report.id).label("failed")).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).where(Report.reported_at >= datetime.now(UTC) - timedelta(days=days), ReportAnalysis.barrier_failure.is_not(None)).group_by(day).order_by(day)
        return [BarrierFailurePoint(date=str(row.day), failed_count=int(row.failed)) for row in (await self.db.execute(statement)).all()]
