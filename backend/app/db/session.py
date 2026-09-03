from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    # Use QueuePool for connection reuse, but avoid cross-loop issues in tests
    # by ensuring connections aren't aggressively held if we use a global engine.
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with SessionLocal() as session:
        yield session
