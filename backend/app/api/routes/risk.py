from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.models.user import User
from app.schemas.risk import BarrierRiskItem, RiskItem, SiteRiskItem
from app.services.risk_engine.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk intelligence"])


@router.get("/sites", response_model=list[SiteRiskItem], summary="Rank sites by actual analyzed report risk signals")
async def site_risk(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), date_from: datetime | None = None, date_to: datetime | None = None, limit: int = Query(50, ge=1, le=200)) -> list[SiteRiskItem]:
    return await RiskService(db).sites(date_from, date_to, limit)


@router.get("/activities", response_model=list[RiskItem], summary="Rank activities by SIF and barrier-failure signals")
async def activity_risk(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), date_from: datetime | None = None, date_to: datetime | None = None, limit: int = Query(50, ge=1, le=200)) -> list[RiskItem]:
    return await RiskService(db).dimensions("activity", date_from, date_to, limit)


@router.get("/hazards", response_model=list[RiskItem], summary="Rank hazards by SIF and barrier-failure signals")
async def hazard_risk(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), date_from: datetime | None = None, date_to: datetime | None = None, limit: int = Query(50, ge=1, le=200)) -> list[RiskItem]:
    return await RiskService(db).dimensions("hazard", date_from, date_to, limit)


@router.get("/barriers", response_model=list[BarrierRiskItem], summary="Rank barrier control weaknesses")
async def barrier_risk(db: DBSession, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)), date_from: datetime | None = None, date_to: datetime | None = None, limit: int = Query(50, ge=1, le=200)) -> list[BarrierRiskItem]:
    return await RiskService(db).barriers(date_from, date_to, limit)
