"""Seed a development database with clearly synthetic SIH demo data."""
import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

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
USERS = [
    ("admin@sif.demo", "Demo Administrator", UserRole.ADMIN),
    ("analyst@sif.demo", "Demo HSE Analyst", UserRole.HSE_ANALYST),
    ("reviewer@sif.demo", "Demo Reviewer", UserRole.REVIEWER),
]
SITES = [
    ("Duliajan Field", "DUL", "Duliajan, Assam", "Assam"),
    ("Moran Field", "MOR", "Moran, Assam", "Assam"),
    ("Digboi Refinery", "DIG", "Digboi, Assam", "Assam"),
]
DEMO_REPORTS = [
    ("DEMO-ENERGY-001", "DUL", "Technician started maintenance before energy isolation was verified.", "Maintenance"),
    ("DEMO-ENERGY-002", "MOR", "Technician started maintenance before energy isolation was verified.", "Maintenance"),
    ("DEMO-CONFINED-001", "DIG", "Worker entered confined space without gas testing.", "Inspection"),
    ("DEMO-LIFT-001", "DUL", "Worker stood below a suspended load during crane lifting.", "Lifting"),
]

# Canonical knowledge file — same data the NLP pipeline uses for LSR mapping.
_LSR_JSON = Path(__file__).parents[1] / "app" / "knowledge" / "life_saving_rules.json"


async def seed() -> None:
    # A3 FIX: Load LSR knowledge from the canonical JSON file so /rules endpoint
    # returns complete keywords, hazards, and barriers — not empty arrays.
    lsr_data: list[dict] = json.loads(_LSR_JSON.read_text(encoding="utf-8"))

    async with SessionLocal() as db:
        # --- Users ---
        for email, full_name, role in USERS:
            if not await db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, full_name=full_name, role=role, password_hash=hash_password(DEMO_PASSWORD)))

        # --- Sites ---
        for name, code, location, region in SITES:
            if not await db.scalar(select(Site).where(Site.code == code)):
                db.add(Site(name=name, code=code, location=location, region=region, description="Synthetic demonstration site."))

        # --- Life-Saving Rules (from knowledge JSON) ---
        for rule in lsr_data:
            if not await db.scalar(select(LifeSavingRule).where(LifeSavingRule.code == rule["code"])):
                db.add(LifeSavingRule(
                    code=rule["code"],
                    name=rule["name"],
                    description=rule["description"],
                    keywords=rule.get("keywords", []),
                    hazards=rule.get("hazards", []),
                    barriers=rule.get("barriers", []),
                ))

        await db.commit()

        # --- Demo Reports ---
        admin = await db.scalar(select(User).where(User.email == "admin@sif.demo"))
        sites = {site.code: site for site in (await db.scalars(select(Site))).all()}
        reports_to_analyze: list[str] = []
        for offset, (report_id, site_code, report_text, activity) in enumerate(DEMO_REPORTS):
            if not await db.scalar(select(Report).where(Report.report_id == report_id)):
                db.add(Report(
                    report_id=report_id,
                    report_type=ReportType.NEAR_MISS,
                    report_text=report_text,
                    site_id=sites[site_code].id,
                    location="Synthetic demonstration area",
                    department="Operations",
                    activity=activity,
                    reported_at=datetime.now(UTC) - timedelta(days=offset * 4),
                    source_type=SourceType.SYNTHETIC,
                    created_by=admin.id,
                ))
                reports_to_analyze.append(report_id)
        await db.commit()

        # --- Analyse demo reports ---
        service = AnalysisService(db)
        for report_id in reports_to_analyze:
            await service.analyze_report(report_id, admin.id, None)

    print("Seed complete: synthetic demo users, sites, rules, reports, analyses, and precursor patterns.")
    print(f"Demo password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
