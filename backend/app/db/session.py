from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

import sys
from sqlalchemy.pool import NullPool

# Determine if we are running in tests
is_test = "pytest" in sys.modules or "TEST_DATABASE_URL" in __import__("os").environ

kwargs = {}
if is_test:
    kwargs["poolclass"] = NullPool
else:
    kwargs["pool_size"] = 5
    kwargs["max_overflow"] = 10
    kwargs["pool_recycle"] = 3600

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    **kwargs
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with SessionLocal() as session:
        yield session
