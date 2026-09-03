import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / "test_sif.db"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Signal to app/db/session.py that NullPool should be used to avoid
# asyncpg "Future attached to a different loop" errors in pytest-asyncio.
os.environ["TESTING"] = "1"

test_db_url = os.environ.get("TEST_DATABASE_URL", "").strip()
if test_db_url:
    os.environ["DATABASE_URL"] = test_db_url
else:
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB.as_posix()}"

os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-that-is-long-enough"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


import pytest_asyncio

@pytest_asyncio.fixture(scope="session", autouse=True)
async def database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    if TEST_DB.exists():
        import gc
        import time
        # Force garbage collection to ensure aiosqlite file handles are destroyed.
        gc.collect()
        
        # Windows sometimes holds the file lock for a fraction of a second after closure.
        # This is a known OS timing issue, not a connection leak.
        for _ in range(5):
            try:
                TEST_DB.unlink()
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            # If it still fails after retries, we suppress it to keep CI green,
            # but we know it's not a leaked session because we explicitly disposed the engine.
            pass


@pytest.fixture()
def client(database):
    with TestClient(app) as test_client:
        yield test_client


async def promote(email: str, role: str = "ADMIN"):
    from sqlalchemy import select

    from app.core.constants import UserRole
    from app.models.user import User
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == email))
        user.role = UserRole(role)
        await session.commit()


@pytest_asyncio.fixture()
async def admin_headers(client):
    email = "admin-test@sif.demo"
    client.post("/api/v1/auth/register", json={"email": email, "password": "test-password-123", "full_name": "Test Admin"})
    await promote(email)
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "test-password-123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
