"""
User Repository — CRUD operations for the users table
"""

import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from .db_manager import get_db
from .models import User, UserPreferences

logger = logging.getLogger(__name__)


class UserExistsError(Exception):
    """Raised when email or username already taken."""


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""


class UserRepository:
    """All user-related database operations."""

    # ── Create ─────────────────────────────────────────────────────────────
    def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        full_name: str = "",
    ) -> User:
        """Create a new user and their default preferences."""
        with get_db() as db:
            try:
                user = User(
                    email=email.lower().strip(),
                    username=username.strip(),
                    password_hash=password_hash,
                    full_name=full_name.strip() if full_name else "",
                )
                db.add(user)
                db.flush()  # get the id before commit

                prefs = UserPreferences(user_id=user.id)
                db.add(prefs)
                db.commit()
                db.refresh(user)
                logger.info("✅ User created: %s", user.username)
                return user
            except IntegrityError as exc:
                raise UserExistsError(
                    "Email or username already registered."
                ) from exc

    # ── Read ────────────────────────────────────────────────────────────────
    def get_user_by_id(self, user_id: int) -> User:
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                raise UserNotFoundError(f"No user with id={user_id}")
            return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        with get_db() as db:
            return (
                db.query(User)
                .filter(User.email == email.lower().strip())
                .first()
            )

    def get_user_by_username(self, username: str) -> Optional[User]:
        with get_db() as db:
            return (
                db.query(User)
                .filter(User.username == username.strip())
                .first()
            )

    # ── Update ──────────────────────────────────────────────────────────────
    def update_user(self, user_id: int, **fields) -> User:
        """Update arbitrary user fields. Pass only the fields to change."""
        allowed = {"email", "username", "full_name", "profile_pic", "is_active", "is_admin"}
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                raise UserNotFoundError(f"No user with id={user_id}")
            for key, val in fields.items():
                if key in allowed:
                    setattr(user, key, val)
            db.commit()
            db.refresh(user)
            return user

    def update_last_login(self, user_id: int) -> None:
        from datetime import datetime, timezone
        with get_db() as db:
            user = db.get(User, user_id)
            if user:
                user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()

    def update_password(self, user_id: int, new_password_hash: str) -> None:
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                raise UserNotFoundError(f"No user with id={user_id}")
            user.password_hash = new_password_hash
            db.commit()

    # ── Delete ──────────────────────────────────────────────────────────────
    def delete_user(self, user_id: int) -> None:
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                raise UserNotFoundError(f"No user with id={user_id}")
            db.delete(user)
            db.commit()
            logger.info("🗑️ User deleted: id=%s", user_id)

    # ── Preferences ─────────────────────────────────────────────────────────
    def get_preferences(self, user_id: int) -> Optional[UserPreferences]:
        with get_db() as db:
            return (
                db.query(UserPreferences)
                .filter(UserPreferences.user_id == user_id)
                .first()
            )

    def update_preferences(self, user_id: int, **fields) -> UserPreferences:
        allowed = {
            "theme", "show_thinking", "show_quality_scores",
            "default_analysis_mode", "notifications_enabled", "preferences_json",
        }
        with get_db() as db:
            prefs = (
                db.query(UserPreferences)
                .filter(UserPreferences.user_id == user_id)
                .first()
            )
            if not prefs:
                prefs = UserPreferences(user_id=user_id)
                db.add(prefs)
            for key, val in fields.items():
                if key in allowed:
                    setattr(prefs, key, val)
            db.commit()
            db.refresh(prefs)
            return prefs
