from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from promopulse.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """
    Lazily create and cache a single AsyncEngine instance for the process.
    """
    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            future=True,
            echo=False,  # toggle via env later if needed
        )

    return _engine


# Global async session factory bound to our engine
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=get_engine(),
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that provides an AsyncSession per request.
    """
    async with async_session_maker() as session:
        yield session
