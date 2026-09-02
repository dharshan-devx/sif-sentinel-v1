"""Seed a development database with clearly synthetic SIH demo data."""
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.constants import ReportType, SourceType, UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.life_saving_rule import LifeSavingRule
from app.models.report import Report
from app.models.site import Site
from app.models.user import User
from app.services.analysis.analysis_service import AnalysisService

DEMO_PASSWORD = "Demo-Only-Password-2026!"
USERS = [("admin@sif.demo", "Demo Administrator", UserRole.ADMIN), ("analyst@sif.demo", "Demo HSE Analyst", UserRole.HSE_ANALYST), ("reviewer@sif.demo", "Demo Reviewer", UserRole.REVIEWER)]
SITES = [("Duliajan Field", "DUL", "Duliajan, Assam", "Assam"), ("Moran Field", "MOR", "Moran, Assam", "Assam"), ("Digboi Refinery", "DIG", "Digboi, Assam", "Assam")]
RULES = ["Confined Space", "Energy Isolation", "Working at Height", "Line of Fire", "Hot Work", "Driving", "Safe Mechanical Lifting", "Work Authorisation", "Bypassing Safety Controls"]
DEMO_REPORTS = [
    ("DEMO-ENERGY-001", "DUL", "Technician started maintenance before energy isolation was verified.", "Maintenance"),
    ("DEMO-ENERGY-002", "MOR", "Technician started maintenance before energy isolation was verified.", "Maintenance"),
    ("DEMO-CONFINED-001", "DIG", "Worker entered confined space without gas testing.", "Inspection"),
    ("DEMO-LIFT-001", "DUL", "Worker stood below a suspended load during crane lifting.", "Lifting"),
]


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
        admin = await db.scalar(select(User).where(User.email == "admin@sif.demo"))
        sites = {site.code: site for site in (await db.scalars(select(Site))).all()}
        reports_to_analyze: list[str] = []
        for offset, (report_id, site_code, report_text, activity) in enumerate(DEMO_REPORTS):
            if not await db.scalar(select(Report).where(Report.report_id == report_id)):
                db.add(Report(report_id=report_id, report_type=ReportType.NEAR_MISS, report_text=report_text, site_id=sites[site_code].id, location="Synthetic demonstration area", department="Operations", activity=activity, reported_at=datetime.now(UTC) - timedelta(days=offset * 4), source_type=SourceType.SYNTHETIC, created_by=admin.id))
                reports_to_analyze.append(report_id)
        await db.commit()
        service = AnalysisService(db)
        for report_id in reports_to_analyze:
            await service.analyze_report(report_id, admin.id, None)
    print("Seed complete: synthetic demo users, sites, rules, reports, analyses, and precursor patterns. Demo password: Demo-Only-Password-2026!")


if __name__ == "__main__":
    asyncio.run(seed())
