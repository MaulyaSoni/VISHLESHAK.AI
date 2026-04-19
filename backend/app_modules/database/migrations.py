"""
Database migration utilities for Vishleshak AI
"""

import logging
import shutil
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Create all tables if they don't exist."""
    from .db_manager import get_db_manager
    get_db_manager()  # constructor handles table creation


def backup_database(output_path: str | None = None) -> str:
    """
    Copy the SQLite database file to a backup location.
    Returns the path to the backup file.
    """
    import database.db_manager as _dbm
    src = Path(_dbm._DB_PATH)
    if not src.exists():
        raise FileNotFoundError(f"Database not found at {src}")

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(src.parent / f"vishleshak_backup_{ts}.db")

    shutil.copy2(src, output_path)
    logger.info("✅ Database backed up to %s", output_path)
    return output_path


def restore_database(backup_path: str) -> None:
    """Restore the SQLite database from a backup file."""
    import database.db_manager as _dbm
    src = Path(backup_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup not found at {src}")

    shutil.copy2(src, _dbm._DB_PATH)
    logger.info("✅ Database restored from %s", backup_path)


def export_to_json(output_path: str) -> None:
    """Export all data to a JSON file (for inspection / migration)."""
    from .db_manager import get_db
    from .models import User, Conversation, Message

    data: dict = {"users": [], "conversations": [], "messages": []}

    with get_db() as db:
        for u in db.query(User).all():
            data["users"].append({
                "id": u.id, "email": u.email, "username": u.username,
                "full_name": u.full_name,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            })
        for c in db.query(Conversation).all():
            data["conversations"].append({
                "id": c.id, "user_id": c.user_id, "title": c.title,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "dataset_name": c.dataset_name,
            })
        for m in db.query(Message).all():
            data["messages"].append({
                "id": m.id, "conversation_id": m.conversation_id,
                "role": m.role, "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "quality_score": m.quality_score,
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("✅ Data exported to %s", output_path)


def export_to_postgres(pg_connection_string: str) -> None:
    """
    Migrate data from SQLite to PostgreSQL.
    Requires psycopg2: pip install psycopg2-binary
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base, User, Session, Conversation, Message, UserPreferences
    from .db_manager import get_db

    logger.info("Starting migration to PostgreSQL...")
    pg_engine = create_engine(pg_connection_string, echo=False)
    Base.metadata.create_all(pg_engine)
    PGSession = sessionmaker(bind=pg_engine)
    pg_db = PGSession()

    try:
        with get_db() as sqlite_db:
            for table_cls in [User, UserPreferences, Session, Conversation, Message]:
                rows = sqlite_db.query(table_cls).all()
                for row in rows:
                    pg_db.merge(row)
        pg_db.commit()
        logger.info("✅ Migration to PostgreSQL complete!")
    except Exception as exc:
        pg_db.rollback()
        logger.error("Migration failed: %s", exc)
        raise
    finally:
        pg_db.close()
