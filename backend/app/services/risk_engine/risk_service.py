from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SIFLevel
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.site import Site
from app.schemas.risk import BarrierRiskItem, RiskItem, SiteRiskItem
from app.services.precursor_engine.pattern_aggregator import latest_analysis_subquery
from app.services.risk_engine.scoring import aggregate_risk_level, aggregate_risk_score


class RiskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base(self):
        latest = latest_analysis_subquery()
        return select(Report, ReportAnalysis).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at))

    async def sites(self, date_from: datetime | None, date_to: datetime | None, limit: int) -> list[SiteRiskItem]:
        now = datetime.now(UTC)
        recent = now - timedelta(days=30)
        filters = self._date_filters(date_from, date_to)
        latest = latest_analysis_subquery()
        key = (func.coalesce(ReportAnalysis.activity, "unknown") + "|" + func.coalesce(ReportAnalysis.hazard, "unknown") + "|" + func.coalesce(ReportAnalysis.barrier, "unknown") + "|" + func.coalesce(ReportAnalysis.barrier_failure, "unknown"))
        statement = select(Site.id, Site.name, func.count(Report.id).label("total"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif"), func.coalesce(func.sum(case((ReportAnalysis.sif_level.in_([SIFLevel.HIGH, SIFLevel.MEDIUM]), 1), else_=0)), 0).label("high"), func.coalesce(func.sum(case((ReportAnalysis.barrier_failure.is_not(None), 1), else_=0)), 0).label("failed"), func.coalesce(func.sum(case((Report.reported_at >= recent, 1), else_=0)), 0).label("recent"), func.count(func.distinct(case((ReportAnalysis.barrier_failure.is_not(None), key)))).label("patterns")).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).join(Site, Site.id == Report.site_id).where(*filters).group_by(Site.id, Site.name)
        items = []
        for row in (await self.db.execute(statement)).mappings():
            total, sif, failed = int(row["total"]), int(row["sif"]), int(row["failed"])
            density = sif / total if total else 0.0
            score = aggregate_risk_score(sif_density=density, occurrence_count=total, barrier_failure_rate=failed / total if total else 0.0, age_days=0 if row["recent"] else 90, trend="STABLE", site_count=1)
            items.append(SiteRiskItem(name=row["name"], site_id=row["id"], report_count=total, sif_count=sif, sif_density=round(density, 3), barrier_failure_count=failed, risk_score=score, risk_level=aggregate_risk_level(score), explanation=f"Risk signal based on {sif} SIF-associated reports out of {total}, with {failed} reported barrier failures.", total_reports=total, sif_reports=sif, sif_rate=round(density, 3), high_risk_reports=int(row["high"]), active_precursor_patterns=int(row["patterns"]), recent_reports=int(row["recent"])))
        return sorted(items, key=lambda item: item.risk_score, reverse=True)[:limit]

    async def dimensions(self, field: str, date_from: datetime | None, date_to: datetime | None, limit: int) -> list[RiskItem]:
        column = {"activity": ReportAnalysis.activity, "hazard": ReportAnalysis.hazard}[field]
        now = datetime.now(UTC)
        latest = latest_analysis_subquery()
        statement = select(column.label("name"), func.count(Report.id).label("total"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif"), func.coalesce(func.sum(case((ReportAnalysis.barrier_failure.is_not(None), 1), else_=0)), 0).label("failed"), func.max(Report.reported_at).label("last_seen")).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).where(column.is_not(None), *self._date_filters(date_from, date_to)).group_by(column)
        items = []
        for row in (await self.db.execute(statement)).mappings():
            total, sif, failed = int(row["total"]), int(row["sif"]), int(row["failed"])
            density = sif / total if total else 0.0
            last_seen = row["last_seen"]
            if last_seen and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=UTC)
            age = (now - last_seen).days if last_seen else 365
            score = aggregate_risk_score(sif_density=density, occurrence_count=total, barrier_failure_rate=failed / total if total else 0.0, age_days=age, trend="STABLE", site_count=1)
            items.append(RiskItem(name=row["name"], report_count=total, sif_count=sif, sif_density=round(density, 3), barrier_failure_count=failed, risk_score=score, risk_level=aggregate_risk_level(score), explanation=f"Risk signal based on {sif} SIF-associated reports out of {total}, including {failed} barrier failures."))
        return sorted(items, key=lambda item: item.risk_score, reverse=True)[:limit]

    async def barriers(self, date_from: datetime | None, date_to: datetime | None, limit: int) -> list[BarrierRiskItem]:
        latest = latest_analysis_subquery()
        statement = select(ReportAnalysis.barrier.label("barrier"), func.count(Report.id).label("total"), func.coalesce(func.sum(case((ReportAnalysis.barrier_failure.is_not(None), 1), else_=0)), 0).label("failed"), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif"), func.max(Report.reported_at).label("last_seen")).select_from(Report).join(ReportAnalysis, ReportAnalysis.report_id == Report.id).join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at)).where(ReportAnalysis.barrier.is_not(None), *self._date_filters(date_from, date_to)).group_by(ReportAnalysis.barrier)
        now = datetime.now(UTC)
        items = []
        for row in (await self.db.execute(statement)).mappings():
            total, failed, sif = int(row["total"]), int(row["failed"]), int(row["sif"])
            rate = failed / total if total else 0.0
            seen = row["last_seen"]
            if seen and seen.tzinfo is None:
                seen = seen.replace(tzinfo=UTC)
            score = aggregate_risk_score(sif_density=sif / total if total else 0.0, occurrence_count=total, barrier_failure_rate=rate, age_days=(now - seen).days if seen else 365, trend="STABLE", site_count=1)
            items.append(BarrierRiskItem(barrier=row["barrier"], total_occurrences=total, failed_count=failed, failure_rate=round(rate, 3), associated_sif_count=sif, risk_score=score, risk_level=aggregate_risk_level(score), explanation=f"Control weakness signal: {failed} failures across {total} occurrences, with {sif} SIF-associated reports."))
        return sorted(items, key=lambda item: item.risk_score, reverse=True)[:limit]

    @staticmethod
    def _date_filters(date_from: datetime | None, date_to: datetime | None) -> list:
        filters = []
        if date_from:
            filters.append(Report.reported_at >= date_from)
        if date_to:
            filters.append(Report.reported_at <= date_to)
        return filters
