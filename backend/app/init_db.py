"""Initialize database: create all tables and seed demo data."""
import asyncio

from app.infrastructure.database import engine, Base
from app.models import *  # noqa: F401, F403 — register all models on Base.metadata


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] All tables created")


if __name__ == "__main__":
    asyncio.run(init())
