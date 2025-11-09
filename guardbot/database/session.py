"""Async SQLAlchemy engine and session factory."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .models import Base
import asyncio

_engine = None
_SessionLocal = None


async def init_db(db_url: str):
    global _engine, _SessionLocal
    _engine = create_async_engine(db_url, echo=False)
    _SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    # Create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session():
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db first.")
    return _SessionLocal()
