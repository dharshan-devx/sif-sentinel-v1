import asyncio
import csv
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path so we can import app modules
project_root = Path(__file__).resolve().parent.parent.parent
backend_path = project_root / "backend"
sys.path.append(str(backend_path))

from app.core.constants import ReportStatus, ReportType, SourceType, UserRole
from app.db.session import SessionLocal, engine
from app.models.report import Report
from app.models.site import Site
from app.models.user import User

async def get_or_create_dummy_user_and_site(session):
    # Check if dummy user exists
    user_email = "admin@sifsentinel.com"
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.email == user_email))
    user = result.scalars().first()
    if not user:
        user = User(
            email=user_email,
            password_hash="fakehash",
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(user)
    
    # Check if dummy site exists
    site_code = "MAIN-01"
    result = await session.execute(select(Site).where(Site.code == site_code))
    site = result.scalars().first()
    if not site:
        site = Site(
            name="Main Facility",
            code=site_code,
            location="HQ",
            region="North America",
            is_active=True
        )
        session.add(site)
    
    await session.commit()
    await session.refresh(user)
    await session.refresh(site)
    return user, site

def parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y")
    except ValueError:
        try:
            return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        except ValueError:
            return datetime.utcnow()

from app.db.init_db import create_tables

async def seed_data():
    print("Starting database seeding...")
    await create_tables()
    async with SessionLocal() as session:
        user, site = await get_or_create_dummy_user_and_site(session)
        
        reports_to_insert = []
        
        # 1. Process Synthetic Data (limit to 200)
        synthetic_path = project_root / "data" / "raw" / "safety_reports.csv"
        if synthetic_path.exists():
            print(f"Reading synthetic data from {synthetic_path}...")
            with open(synthetic_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if count >= 200:
                        break
                    try:
                        rtype_str = row.get("report_type", "INCIDENT")
                        rtype = getattr(ReportType, rtype_str, ReportType.INCIDENT)
                        
                        report = Report(
                            report_id=f"SYN-{uuid.uuid4().hex[:8]}",
                            report_type=rtype,
                            report_text=row.get("report_text", ""),
                            site_id=site.id,
                            location="Various",
                            department="Operations",
                            activity=row.get("activity") or None,
                            reported_at=datetime.utcnow(),
                            source_type=SourceType.SYNTHETIC,
                            status=ReportStatus.NEW,
                            created_by=user.id
                        )
                        reports_to_insert.append(report)
                        count += 1
                    except Exception as e:
                        print(f"Error parsing synthetic row: {e}")
        else:
            print(f"Warning: {synthetic_path} not found.")

        # 2. Process OSHA Data (limit to 300)
        osha_path = project_root / "Dump" / "OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv"
        if osha_path.exists():
            print(f"Reading OSHA data from {osha_path}...")
            with open(osha_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if count >= 300:
                        break
                    
                    text = row.get("Abstract Text", "")
                    if not text:
                        continue
                        
                    try:
                        report = Report(
                            report_id=f"OSH-{row.get('summary_nr', '')}-{uuid.uuid4().hex[:6]}",
                            report_type=ReportType.INCIDENT,
                            report_text=text,
                            site_id=site.id,
                            location="External Site",
                            department="External",
                            activity=None,
                            reported_at=parse_date(row.get("Event Date", "")),
                            source_type=SourceType.IMPORTED,
                            status=ReportStatus.NEW,
                            created_by=user.id
                        )
                        reports_to_insert.append(report)
                        count += 1
                    except Exception as e:
                        print(f"Error parsing OSHA row: {e}")
        else:
            print(f"Warning: {osha_path} not found.")

        if reports_to_insert:
            print(f"Inserting {len(reports_to_insert)} reports into the database...")
            session.add_all(reports_to_insert)
            await session.commit()
            print("Successfully seeded the database!")
        else:
            print("No reports found to insert.")

async def main():
    await seed_data()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
