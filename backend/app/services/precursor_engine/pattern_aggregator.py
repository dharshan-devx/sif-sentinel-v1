from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.precursor_candidate import PrecursorCandidate
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.services.precursor_engine.pattern_builder import build_pattern_key
from app.services.precursor_engine.trend_analyzer import determine_trend
from app.services.risk_engine.scoring import aggregate_risk_level, aggregate_risk_score


@dataclass(frozen=True)
class PatternMetrics:
    key: str
    category: str
    activity: str
    hazard: str
    barrier: str
    failure_type: str
    occurrence_count: int
    sif_count: int
    sif_density: float
    recent_count: int
    site_count: int
    department_count: int
    first_seen: datetime | None
    last_seen: datetime | None
    trend: str
    risk_score: float
    priority: str


def latest_analysis_subquery():
    return select(ReportAnalysis.report_id, func.max(ReportAnalysis.created_at).label("latest_created")).group_by(ReportAnalysis.report_id).subquery()


async def aggregate_patterns(db: AsyncSession, date_from: datetime | None = None, date_to: datetime | None = None) -> list[PatternMetrics]:
    now = datetime.now(UTC)
    settings = get_settings()
    lookback_days = settings.precursor_lookback_days
    min_occurrences = settings.precursor_min_occurrences
    
    cutoff_start = now - timedelta(days=lookback_days)
    recent_start = now - timedelta(days=lookback_days // 3)  # Recent period is last third
    previous_start = cutoff_start
    
    latest = latest_analysis_subquery()
    
    category = PrecursorCandidate.category
    activity = func.lower(func.trim(PrecursorCandidate.activity)).label("activity")
    hazard = func.lower(func.trim(PrecursorCandidate.hazard)).label("hazard")
    barrier = func.lower(func.trim(PrecursorCandidate.barrier)).label("barrier")
    failure = func.lower(func.trim(PrecursorCandidate.failure_type)).label("failure_type")
    
    filters = [Report.reported_at >= cutoff_start]
    if date_from:
        filters.append(Report.reported_at >= date_from)
    if date_to:
        filters.append(Report.reported_at <= date_to)
        
    statement = (
        select(
            category,
            activity,
            hazard,
            barrier,
            failure,
            func.count(PrecursorCandidate.id).label("occurrence_count"),
            func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0).label("sif_count"),
            func.coalesce(func.sum(case((Report.reported_at >= recent_start, 1), else_=0)), 0).label("recent_count"),
            func.coalesce(func.sum(case((Report.reported_at.between(previous_start, recent_start), 1), else_=0)), 0).label("previous_count"),
            func.count(func.distinct(Report.site_id)).label("site_count"),
            func.count(func.distinct(Report.department)).label("department_count"),
            func.min(Report.reported_at).label("first_seen"),
            func.max(Report.reported_at).label("last_seen"),
        )
        .select_from(PrecursorCandidate)
        .join(Report, Report.id == PrecursorCandidate.report_id)
        .join(ReportAnalysis, ReportAnalysis.report_id == Report.id)
        .join(latest, (latest.c.report_id == ReportAnalysis.report_id) & (latest.c.latest_created == ReportAnalysis.created_at))
        .where(*filters)
        .group_by(category, activity, hazard, barrier, failure)
        .having(func.count(PrecursorCandidate.id) >= min_occurrences)
    )
    
    rows = (await db.execute(statement)).mappings().all()
    result: list[PatternMetrics] = []
    
    for row in rows:
        pattern = build_pattern_key(row["activity"], row["hazard"], row["barrier"], row["failure_type"])
        occurrence, sif_count = int(row["occurrence_count"]), int(row["sif_count"])
        density = round(sif_count / occurrence, 3) if occurrence else 0.0
        trend = determine_trend(int(row["recent_count"]), int(row["previous_count"]), occurrence).value
        
        last_seen = row["last_seen"]
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=UTC)
            
        age_days = (now - last_seen).total_seconds() / 86400 if last_seen else 365.0
        score = aggregate_risk_score(
            sif_density=density, 
            occurrence_count=occurrence, 
            barrier_failure_rate=1.0, 
            age_days=age_days, 
            trend=trend, 
            site_count=int(row["site_count"])
        )
        
        result.append(PatternMetrics(
            key=pattern.key,
            category=row["category"],
            activity=pattern.activity,
            hazard=pattern.hazard,
            barrier=pattern.barrier,
            failure_type=pattern.failure_type,
            occurrence_count=occurrence,
            sif_count=sif_count,
            sif_density=density,
            recent_count=int(row["recent_count"]),
            site_count=int(row["site_count"]),
            department_count=int(row["department_count"]),
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            trend=trend,
            risk_score=score,
            priority=aggregate_risk_level(score)
        ))
        
    return result
