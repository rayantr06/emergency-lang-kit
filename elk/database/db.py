"""
ELK Database Connection
Handles Async/Sync sessions for SQLModel.
Defaults to SQLite for development, configured for Postgres in production.
"""

import os
from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Default to SQLite for dev simplicity
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///elk_jobs.db")
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "sqlite:///elk_jobs.db")

# Async Engine (for API/Workers)
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Sync Engine (for migrations/scripts)
engine = create_engine(SYNC_DATABASE_URL, echo=False)

async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency for FastAPI sessions."""
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
