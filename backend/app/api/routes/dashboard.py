from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.dashboard import (
    BarrierFailurePoint,
    DashboardSummary,
    DistributionItem,
    TimeSeriesPoint,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard analytics"])

_read_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)


@router.get("/summary", response_model=DashboardSummary, summary="Organization-wide report and precursor summary")
async def summary(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> DashboardSummary:
    return await AnalyticsService(db).summary()


@router.get("/sif-trend", response_model=list[TimeSeriesPoint], summary="Daily SIF signal trend")
async def sif_trend(db: DBSession, _: User = Depends(require_roles(*_read_roles)), window: str = Query("30d", pattern="^(7d|30d|90d|1y)$")) -> list[TimeSeriesPoint]:
    return await AnalyticsService(db).sif_trend(window)


@router.get("/lsr-distribution", response_model=list[DistributionItem], summary="Life-Saving Rule distribution")
async def lsr_distribution(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> list[DistributionItem]:
    return await AnalyticsService(db).distribution("lsr")


@router.get("/site-comparison", response_model=list[DistributionItem], summary="Comparable report and SIF metrics by site")
async def site_comparison(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> list[DistributionItem]:
    return await AnalyticsService(db).site_comparison()


@router.get("/activity-distribution", response_model=list[DistributionItem], summary="Activity distribution from analyzed reports")
async def activity_distribution(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> list[DistributionItem]:
    return await AnalyticsService(db).distribution("activity")


@router.get("/hazard-distribution", response_model=list[DistributionItem], summary="Hazard distribution from analyzed reports")
async def hazard_distribution(db: DBSession, _: User = Depends(require_roles(*_read_roles))) -> list[DistributionItem]:
    return await AnalyticsService(db).distribution("hazard")


@router.get("/barrier-failures", response_model=list[BarrierFailurePoint], summary="Daily barrier-failure signals")
async def barrier_failures(db: DBSession, _: User = Depends(require_roles(*_read_roles)), window: str = Query("30d", pattern="^(7d|30d|90d|1y)$")) -> list[BarrierFailurePoint]:
    return await AnalyticsService(db).barrier_failures(window)
