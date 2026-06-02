from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _make_sync_url(url: str) -> str:
    """Derive a sync database URL from an async URL."""
    url = url.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")
    return url


sync_engine = create_engine(_make_sync_url(settings.database_url), echo=settings.debug)
sync_session = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
