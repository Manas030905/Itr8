"""Database engine and session management (sync SQLAlchemy 2.0, psycopg 3)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db import registry  # noqa: F401  (register all models)

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request; services decide when to commit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
