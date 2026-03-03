"""
Database Manager for Vishleshak AI
Manages SQLite connection, table creation, and session factory
"""

import os
import socket
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session as DBSession
from sqlalchemy.pool import StaticPool

from .models import Base

# Load .env before reading any env vars (local dev only)
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).resolve().parent.parent
    _env_file = _project_root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
except ImportError:
    pass  # Not available on Streamlit Cloud; env vars set via Secrets

# Inject Streamlit secrets → os.environ so DATABASE_URL is always reachable via os.getenv()
try:
    import streamlit as st
    _SECRET_KEYS = ["DATABASE_URL", "GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    for _k in _SECRET_KEYS:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

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

        os.makedirs(_DB_DIR, exist_ok=True)

        # Try configured DATABASE_URL first; fall back to local SQLite on failure
        self._db_url = DATABASE_URL

        # Connection test — fallback to SQLite if remote DB unreachable or driver missing
        if not self._db_url.startswith("sqlite"):
            try:
                self.engine = self._create_engine(self._db_url)
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✅ Connected to remote database")
            except Exception as exc:
                logger.warning(
                    "⚠️ Remote database unreachable (%s: %s). Falling back to local SQLite.",
                    exc.__class__.__name__, exc,
                )
                self._db_url = _LOCAL_DB_URL
                self.engine = self._create_engine(self._db_url)
        else:
            self.engine = self._create_engine(self._db_url)

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        self._create_tables()
        logger.info("✅ Database initialised at %s", self._db_url)
        # Mark initialized only after full successful setup
        self._initialized = True

    @staticmethod
    def _ipv4_url(url: str) -> str:
        """
        Resolve the hostname in a PostgreSQL URL to its first IPv4 address.
        Streamlit Cloud's network may only route IPv6 for some hosts, while
        Supabase's direct endpoint does not accept IPv6 — this forces IPv4.
        Falls back to the original URL if IPv4 resolution fails.
        """
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 5432
            ipv4_results = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            if ipv4_results:
                ipv4_addr = ipv4_results[0][4][0]
                # Rebuild netloc replacing hostname with IPv4 literal
                new_netloc = parsed.netloc.replace(host, ipv4_addr, 1)
                return urlunparse(parsed._replace(netloc=new_netloc))
        except Exception:
            pass
        return url

    def _create_engine(self, url: str):
        """Create a SQLAlchemy engine for the given URL."""
        connect_args: dict = {}
        kwargs: dict = {}

        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            kwargs["poolclass"] = StaticPool
        else:
            # Force IPv4 so Streamlit Cloud (IPv6-only egress) can reach Supabase
            url = self._ipv4_url(url)
            connect_args = {
                "sslmode": "require",
                "connect_timeout": 10,
            }
            # pre-ping recycles stale connections transparently
            kwargs["pool_pre_ping"] = True
            kwargs["pool_recycle"] = 1800
            kwargs["pool_size"] = 5
            kwargs["max_overflow"] = 10

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
