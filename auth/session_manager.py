"""
Session Manager — JWT-based session creation and validation
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt

from database.db_manager import get_db
from database.models import Session as DBSession, User

logger = logging.getLogger(__name__)

_SECRET_KEY = os.getenv("SECRET_KEY", "vishleshak-secret-change-in-production-2026")
_ALGORITHM  = "HS256"
_SESSION_DAYS = int(os.getenv("SESSION_DAYS", "7"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SessionManager:
    """Manage JWT sessions stored in the database."""

    # ── Create ─────────────────────────────────────────────────────────────
    def create_session(
        self,
        user_id: int,
        device_info: Optional[dict] = None,
    ) -> str:
        """Create a new session. Returns the JWT token string."""
        expires_at = _utcnow() + timedelta(days=_SESSION_DAYS)

        payload = {
            "user_id":  user_id,
            "exp":      int(expires_at.timestamp()),
            "iat":      int(_utcnow().timestamp()),
        }
        token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)

        with get_db() as db:
            sess = DBSession(
                user_id=user_id,
                session_token=token,
                expires_at=expires_at,
                is_active=True,
                device_info=json.dumps(device_info or {}),
            )
            db.add(sess)
            db.commit()

        logger.info("🔑 Session created for user_id=%s", user_id)
        return token

    # ── Read ────────────────────────────────────────────────────────────────
    def get_active_session(self, token: str) -> Optional[DBSession]:
        """Return the Session row if token is valid and not expired."""
        with get_db() as db:
            sess = (
                db.query(DBSession)
                .filter(
                    DBSession.session_token == token,
                    DBSession.is_active == True,  # noqa: E712
                    DBSession.expires_at > _utcnow(),
                )
                .first()
            )
            return sess

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode a JWT token. Returns payload dict or None on failure."""
        try:
            return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Invalid token")
            return None

    def get_user_sessions(self, user_id: int) -> List[DBSession]:
        with get_db() as db:
            return (
                db.query(DBSession)
                .filter(
                    DBSession.user_id == user_id,
                    DBSession.is_active == True,  # noqa: E712
                )
                .order_by(DBSession.created_at.desc())
                .all()
            )

    # ── Invalidate ──────────────────────────────────────────────────────────
    def invalidate_session(self, token: str) -> bool:
        with get_db() as db:
            sess = (
                db.query(DBSession)
                .filter(DBSession.session_token == token)
                .first()
            )
            if sess:
                sess.is_active = False
                db.commit()
                return True
            return False

    def invalidate_all_user_sessions(self, user_id: int) -> None:
        with get_db() as db:
            db.query(DBSession).filter(
                DBSession.user_id == user_id,
                DBSession.is_active == True,  # noqa: E712
            ).update({"is_active": False})
            db.commit()

    # ── Refresh ─────────────────────────────────────────────────────────────
    def refresh_session(self, old_token: str) -> Optional[str]:
        """Invalidate old token and return a new one (same user)."""
        sess = self.get_active_session(old_token)
        if not sess:
            return None
        user_id = sess.user_id
        self.invalidate_session(old_token)
        return self.create_session(user_id)

    # ── Cleanup ─────────────────────────────────────────────────────────────
    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions. Returns count deleted."""
        with get_db() as db:
            deleted = (
                db.query(DBSession)
                .filter(DBSession.expires_at <= _utcnow())
                .delete()
            )
            db.commit()
            logger.info("🧹 Expired sessions cleaned: %d", deleted)
            return deleted
