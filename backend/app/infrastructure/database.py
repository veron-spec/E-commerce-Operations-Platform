from sqlalchemy import create_engine
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _make_async_url(url: str) -> str:
    """Normalize provider URLs for SQLAlchemy's asyncpg dialect."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parsed = urlsplit(url)
    query = []
    for key, value in parse_qsl(parsed.query):
        if key == "channel_binding":
            continue
        if key == "sslmode":
            if value in {"require", "verify-ca", "verify-full"}:
                query.append(("ssl", "require"))
            continue
        query.append((key, value))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


engine = create_async_engine(_make_async_url(settings.database_url), echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _make_sync_url(url: str) -> str:
    """Derive a sync database URL from an async URL."""
    url = url.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")
    return url


_sync_engine = None
_sync_session = None


def get_sync_session() -> sessionmaker:
    """Create the legacy synchronous session factory only for background jobs."""
    global _sync_engine, _sync_session
    if _sync_session is None:
        _sync_engine = create_engine(_make_sync_url(settings.database_url), echo=settings.debug)
        _sync_session = sessionmaker(_sync_engine, class_=Session, expire_on_commit=False)
    return _sync_session


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
from sqlalchemy import create_engine
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _make_async_url(url: str) -> str:
    """Normalize provider URLs for SQLAlchemy's asyncpg dialect."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parsed = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query) if key != "channel_binding"]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


engine = create_async_engine(_make_async_url(settings.database_url), echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _make_sync_url(url: str) -> str:
    """Derive a sync database URL from an async URL."""
    url = url.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")
    return url


_sync_engine = None
_sync_session = None


def get_sync_session() -> sessionmaker:
    """Create the legacy synchronous session factory only for background jobs."""
    global _sync_engine, _sync_session
    if _sync_session is None:
        _sync_engine = create_engine(_make_sync_url(settings.database_url), echo=settings.debug)
        _sync_session = sessionmaker(_sync_engine, class_=Session, expire_on_commit=False)
    return _sync_session


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
