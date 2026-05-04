"""
Database engine + session wiring for the FastAPI backend.

Primary target is Postgres (the "FastAPI Postgres SQL provider"), driven by
the ``DATABASE_URL`` env var (e.g. ``postgresql+psycopg://user:pass@host/db``).
If ``DATABASE_URL`` is not set we fall back to a local SQLite file so the
server can still boot on a bare dev machine without Postgres installed.

Expose three things:
  - ``engine``        : SQLAlchemy ``Engine``
  - ``SessionLocal``  : ``sessionmaker`` bound to that engine
  - ``get_db``        : FastAPI dependency yielding a scoped ``Session``
  - ``init_db``       : creates all tables declared on ``Base.metadata``
"""
from __future__ import annotations

import os
from typing import Iterator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend_apis.models import Base


DEFAULT_SQLITE_URL = "sqlite:///./player_connections.db"


def resolve_database_url() -> str:
    """
    Pick the DB URL from the environment.

    Priority:
      1. ``DATABASE_URL`` (canonical FastAPI/Vercel env var)
      2. ``POSTGRES_URL`` (Vercel Marketplace Postgres providers often set this)
      3. ``DEFAULT_SQLITE_URL`` (local dev fallback)
    """
    return (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or DEFAULT_SQLITE_URL
    )


def build_engine(url: Optional[str] = None) -> Engine:
    db_url = url or resolve_database_url()

    connect_args: dict = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(db_url, future=True, connect_args=connect_args)


engine: Engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def ensure_sqlite_player_wallet_columns(eng: Engine) -> None:
    """
    SQLite does not apply new columns from ``create_all`` on existing tables.

    Add any columns introduced after the first deploy so local ``player_connections.db``
    (and similar) stay compatible without a full reset.
    """
    url = str(eng.url)
    if not url.startswith("sqlite"):
        return
    additions = [
        ("gems", "INTEGER NOT NULL DEFAULT 0"),
        ("total_earned_gems", "INTEGER NOT NULL DEFAULT 0"),
        ("inventory_keys", "INTEGER NOT NULL DEFAULT 0"),
        ("session_coins_earned", "INTEGER NOT NULL DEFAULT 0"),
    ]
    with eng.begin() as conn:
        raw = conn.execute(text("PRAGMA table_info(player_wallets)"))
        rows = raw.fetchall()
        if not rows:
            return
        existing = {row[1] for row in rows}
        for column_name, ddl_suffix in additions:
            if column_name in existing:
                continue
            conn.execute(text(f"ALTER TABLE player_wallets ADD COLUMN {column_name} {ddl_suffix}"))


def init_db(target_engine: Optional[Engine] = None) -> None:
    """Create all tables declared on ``Base.metadata`` if missing."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    ensure_sqlite_player_wallet_columns(eng)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
