"""Seed a development database with clearly synthetic SIH demo data."""
import asyncio

from sqlalchemy import select

from app.core.constants import UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.life_saving_rule import LifeSavingRule
from app.models.site import Site
from app.models.user import User

DEMO_PASSWORD = "Demo-Only-Password-2026!"
USERS = [("admin@sif.demo", "Demo Administrator", UserRole.ADMIN), ("analyst@sif.demo", "Demo HSE Analyst", UserRole.HSE_ANALYST), ("reviewer@sif.demo", "Demo Reviewer", UserRole.REVIEWER)]
SITES = [("Duliajan Field", "DUL", "Duliajan, Assam", "Assam"), ("Moran Field", "MOR", "Moran, Assam", "Assam"), ("Digboi Refinery", "DIG", "Digboi, Assam", "Assam")]
RULES = ["Confined Space", "Energy Isolation", "Working at Height", "Line of Fire", "Hot Work", "Driving", "Safe Mechanical Lifting", "Work Authorisation", "Bypassing Safety Controls"]


async def seed() -> None:
    async with SessionLocal() as db:
        for email, full_name, role in USERS:
            if not await db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, full_name=full_name, role=role, password_hash=hash_password(DEMO_PASSWORD)))
        for name, code, location, region in SITES:
            if not await db.scalar(select(Site).where(Site.code == code)):
                db.add(Site(name=name, code=code, location=location, region=region, description="Synthetic demonstration site."))
        for index, name in enumerate(RULES, 1):
            code = f"LSR-{index:02d}"
            if not await db.scalar(select(LifeSavingRule).where(LifeSavingRule.code == code)):
                db.add(LifeSavingRule(code=code, name=name, description=f"Synthetic starter rule: {name}. Validate against local policy before use.", keywords=[], hazards=[], barriers=[]))
        await db.commit()
    print("Seed complete. Demo password for all seed users: Demo-Only-Password-2026!")


if __name__ == "__main__":
    asyncio.run(seed())
