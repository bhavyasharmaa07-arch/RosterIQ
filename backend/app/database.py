"""SQLite engine and session management."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "rosteriq.db"

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + DEFAULT_DB_PATH.as_posix()


def init_db() -> None:
    """Create the engine from the current DATABASE_URL and ensure tables exist."""
    global engine, SessionLocal
    url = database_url()
    if url.startswith("sqlite:///"):
        path_part = url.replace("sqlite:///", "", 1)
        if path_part and path_part != ":memory:" and not path_part.startswith("file:"):
            Path(path_part).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# Initialize on import so SessionLocal is always callable
init_db()


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        init_db()
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
