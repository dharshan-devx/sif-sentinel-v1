"""Rules service — Life-Saving Rule retrieval and analytics.

Responsibility: LSR database access and analytics aggregation.
Routes delegate all DB operations to this service.
"""
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.life_saving_rule import LifeSavingRule
from app.models.report_analysis import ReportAnalysis


class RulesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self) -> list[LifeSavingRule]:
        """Return all active Life-Saving Rules ordered by code."""
        return list(
            await self.db.scalars(
                select(LifeSavingRule)
                .where(LifeSavingRule.is_active.is_(True))
                .order_by(LifeSavingRule.code)
            )
        )

    async def get(self, rule_id: str) -> LifeSavingRule:
        """Get a single rule by UUID or code string. Raises NotFoundError if missing."""
        item = await self.db.scalar(
            select(LifeSavingRule).where(
                or_(LifeSavingRule.id == rule_id, LifeSavingRule.code == rule_id)
            )
        )
        if not item:
            raise NotFoundError("rule")
        return item

    async def analytics(self, rule_id: str) -> dict:
        """Return SIF density analytics for a Life-Saving Rule.

        Looks up the rule first (raises NotFoundError if not found), then
        aggregates ReportAnalysis rows matching the rule's name.
        """
        item = await self.get(rule_id)
        total, sif = (
            await self.db.execute(
                select(
                    func.count(),
                    func.coalesce(
                        func.sum(case((ReportAnalysis.sif_potential.is_(True), 1), else_=0)),
                        0,
                    ),
                ).where(ReportAnalysis.life_saving_rule == item.name)
            )
        ).one()
        total, sif = int(total), int(sif)
        return {
            "life_saving_rule": item.name,
            "total_reports": total,
            "sif_reports": sif,
            "sif_density": round(sif / total, 3) if total else 0.0,
        }
