import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / "test_sif.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-that-is-long-enough"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import app.models  # noqa: E402,F401
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(setup())
    yield
    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    asyncio.run(teardown())
    if TEST_DB.exists():
        TEST_DB.unlink()


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


@pytest.fixture()
def admin_headers(client):
    email = "admin-test@sif.demo"
    client.post("/api/v1/auth/register", json={"email": email, "password": "test-password-123", "full_name": "Test Admin"})
    asyncio.run(promote(email))
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "test-password-123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
