from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select

from app.api.deps import DBSession, require_roles
from app.core.constants import UserRole
from app.core.exceptions import NotFoundError
from app.models.life_saving_rule import LifeSavingRule
from app.models.report_analysis import ReportAnalysis
from app.models.user import User

router = APIRouter(prefix="/rules", tags=["Life-Saving Rules"])
_roles = (UserRole.ADMIN, UserRole.HSE_MANAGER, UserRole.HSE_ANALYST, UserRole.REVIEWER, UserRole.VIEWER)

@router.get("")
async def rules(db: DBSession, _: User = Depends(require_roles(*_roles))):
    return list(await db.scalars(select(LifeSavingRule).where(LifeSavingRule.is_active.is_(True)).order_by(LifeSavingRule.code)))

@router.get("/{rule_id}")
async def rule(rule_id: str, db: DBSession, _: User = Depends(require_roles(*_roles))):
    item = await db.scalar(select(LifeSavingRule).where((LifeSavingRule.id == rule_id) | (LifeSavingRule.code == rule_id)))
    if not item:
        raise NotFoundError("rule")
    return item

@router.get("/{rule_id}/analytics")
async def rule_analytics(rule_id: str, db: DBSession, _: User = Depends(require_roles(*_roles))):
    item = await db.scalar(select(LifeSavingRule).where((LifeSavingRule.id == rule_id) | (LifeSavingRule.code == rule_id)))
    if not item:
        raise NotFoundError("rule")
    total, sif = (await db.execute(select(func.count(), func.coalesce(func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)), 0)).where(ReportAnalysis.life_saving_rule == item.name))).one()
    return {"life_saving_rule": item.name, "total_reports": int(total), "sif_reports": int(sif), "sif_density": round(int(sif)/int(total),3) if total else 0.0}
