import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


def _build_engine():
    """Create the SQLAlchemy async engine with environment-appropriate pooling.

    In test runs (TESTING=1 or TEST_DATABASE_URL set), NullPool is used to
    prevent asyncpg connections from being shared across pytest-asyncio event
    loops — which would cause "Future attached to a different loop" errors.

    In production, a QueuePool with conservative settings is used.
    """
    settings = get_settings()
    is_test = os.environ.get("TESTING") == "1" or "TEST_DATABASE_URL" in os.environ

    kwargs: dict = {"pool_pre_ping": True}
    if is_test:
        kwargs["poolclass"] = NullPool
        # pool_pre_ping is irrelevant with NullPool (each call opens a fresh
        # connection), but keeping it explicit makes intent clear.
        kwargs.pop("pool_pre_ping", None)
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_recycle"] = 3600

    return create_async_engine(settings.database_url, **kwargs)


engine = _build_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with SessionLocal() as session:
        yield session
