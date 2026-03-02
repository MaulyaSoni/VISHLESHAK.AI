"""
Database Manager for Vishleshak AI
Manages SQLite connection, table creation, and session factory
"""

import os
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session as DBSession
from sqlalchemy.pool import StaticPool

from .models import Base

# Load .env before reading any env vars
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=True)

logger = logging.getLogger(__name__)

# ── Database path ──────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_DIR   = os.path.join(_BASE_DIR, "storage")
_DB_PATH  = os.path.join(_DB_DIR, "vishleshak.db")
_LOCAL_DB_URL = f"sqlite:///{_DB_PATH}"

# Allow override via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", _LOCAL_DB_URL)


class DatabaseManager:
    """Central database manager — singleton pattern via module-level instance."""

    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        os.makedirs(_DB_DIR, exist_ok=True)

        # Try configured DATABASE_URL first; fall back to local SQLite on failure
        self._db_url = DATABASE_URL
        self.engine = self._create_engine(self._db_url)

        # Connection test — fallback to SQLite if remote DB unreachable
        if not self._db_url.startswith("sqlite"):
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✅ Connected to remote database")
            except Exception as exc:
                logger.warning(
                    "⚠️ Remote database unreachable (%s). Falling back to local SQLite.",
                    exc.__class__.__name__,
                )
                self._db_url = _LOCAL_DB_URL
                self.engine = self._create_engine(self._db_url)

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        self._create_tables()
        logger.info("✅ Database initialised at %s", self._db_url)

    def _create_engine(self, url: str):
        """Create a SQLAlchemy engine for the given URL."""
        connect_args: dict = {}
        kwargs: dict = {}

        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            kwargs["poolclass"] = StaticPool

        engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False,
            **kwargs,
        )

        # Enable WAL mode & foreign keys for SQLite
        if url.startswith("sqlite"):
            @event.listens_for(engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _):  # noqa: ANN001
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        return engine

    # ── Table creation ──────────────────────────────────────────────────────
    def _create_tables(self) -> None:
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ All tables ready")

    # ── Session context manager ─────────────────────────────────────────────
    @contextmanager
    def session(self) -> Generator[DBSession, None, None]:
        """Yield a SQLAlchemy session with automatic commit / rollback."""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── Health check ────────────────────────────────────────────────────────
    def health_check(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Database health check failed: %s", exc)
            return False

    # ── Drop all (useful during dev / tests) ────────────────────────────────
    def drop_all_tables(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️ All tables dropped")


# ── Module-level helpers ───────────────────────────────────────────────────
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@contextmanager
def get_db() -> Generator[DBSession, None, None]:
    """Convenience shortcut: `with get_db() as db:`"""
    with get_db_manager().session() as db:
        yield db


def init_database() -> DatabaseManager:
    """Initialise the database (call once at app startup)."""
    return get_db_manager()
