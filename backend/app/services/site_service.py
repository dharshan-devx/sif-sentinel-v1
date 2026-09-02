from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate


class SiteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: SiteCreate) -> Site:
        if await self.db.scalar(select(Site).where(Site.code == payload.code.upper())):
            raise AppError("SITE_CODE_EXISTS", "A site with that code already exists", 409)
        site = Site(**payload.model_dump(exclude={"code"}), code=payload.code.upper())
        self.db.add(site)
        await self.db.commit()
        await self.db.refresh(site)
        return site

    async def get(self, site_id: UUID) -> Site:
        site = await self.db.get(Site, site_id)
        if not site:
            raise NotFoundError("site")
        return site

    async def list(self) -> list[Site]:
        return list(await self.db.scalars(select(Site).order_by(Site.name)))

    async def update(self, site_id: UUID, payload: SiteUpdate) -> Site:
        site = await self.get(site_id)
        for name, value in payload.model_dump(exclude_unset=True).items():
            setattr(site, name, value)
        await self.db.commit()
        await self.db.refresh(site)
        return site
