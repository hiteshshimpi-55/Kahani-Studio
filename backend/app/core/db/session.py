from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.repository.models.base.base import Base

# Local Postgres is fast; keep a warm pool. (pool_pre_ping off — avoids extra RTT.)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=280,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


get_db = get_db_session

__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db_session", "get_db"]
