"""
Authentication Manager — register, login, logout, verify
"""

import logging
from typing import Optional, Tuple

from database.models import User
from database.user_repository import UserRepository, UserExistsError, UserNotFoundError
from .password_utils import (
    hash_password, verify_password,
    validate_password_strength, validate_email, validate_username,
)
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised for authentication / authorisation failures."""


class AuthManager:
    """Central auth facade used by the Streamlit app."""

    def __init__(self) -> None:
        self._users = UserRepository()
        self._sessions = SessionManager()

    # ── Register ────────────────────────────────────────────────────────────
    def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = "",
    ) -> User:
        """
        Register a new user.
        Raises AuthError on validation failure or duplicate.
        """
        # Validate inputs
        if not validate_email(email):
            raise AuthError("Invalid email address format.")

        ok_user, user_err = validate_username(username)
        if not ok_user:
            raise AuthError(user_err)

        ok_pass, pass_issues = validate_password_strength(password)
        if not ok_pass:
            raise AuthError(" ".join(pass_issues))

        try:
            hashed = hash_password(password)
            user = self._users.create_user(
                email=email,
                username=username,
                password_hash=hashed,
                full_name=full_name,
            )
            logger.info("✅ Registered: %s", user.email)
            return user
        except UserExistsError:
            raise AuthError("Email or username is already registered.")

    # ── Login ────────────────────────────────────────────────────────────────
    def login_user(
        self,
        email: str,
        password: str,
        device_info: Optional[dict] = None,
    ) -> Tuple[User, str]:
        """
        Verify credentials and return (User, session_token).
        Raises AuthError on failure.
        """
        user = self._users.get_user_by_email(email)
        if not user:
            raise AuthError("Incorrect email or password.")

        if not user.is_active:
            raise AuthError("This account has been deactivated.")

        if not verify_password(password, user.password_hash):
            raise AuthError("Incorrect email or password.")

        # Update last login
        self._users.update_last_login(user.id)

        # Create session
        token = self._sessions.create_session(
            user_id=user.id,
            device_info=device_info or {},
        )
        logger.info("🔓 Login: %s", user.email)
        return user, token

    # ── Logout ───────────────────────────────────────────────────────────────
    def logout_user(self, session_token: str) -> bool:
        success = self._sessions.invalidate_session(session_token)
        if success:
            logger.info("🔒 Session invalidated")
        return success

    # ── Verify session ───────────────────────────────────────────────────────
    def verify_session(self, token: str) -> Optional[User]:
        """Return the User associated with this token, or None."""
        sess = self._sessions.get_active_session(token)
        if not sess:
            return None
        try:
            return self._users.get_user_by_id(sess.user_id)
        except UserNotFoundError:
            return None

    # ── Refresh ──────────────────────────────────────────────────────────────
    def refresh_session(self, old_token: str) -> Optional[str]:
        return self._sessions.refresh_session(old_token)

    # ── Change password ───────────────────────────────────────────────────────
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:
        try:
            user = self._users.get_user_by_id(user_id)
        except UserNotFoundError:
            raise AuthError("User not found.")

        if not verify_password(old_password, user.password_hash):
            raise AuthError("Current password is incorrect.")

        ok_pass, pass_issues = validate_password_strength(new_password)
        if not ok_pass:
            raise AuthError(" ".join(pass_issues))

        new_hash = hash_password(new_password)
        self._users.update_password(user_id, new_hash)
        # Invalidate all sessions so re-login is required
        self._sessions.invalidate_all_user_sessions(user_id)
        logger.info("🔑 Password changed for user_id=%s", user_id)

    # ── Delete account ────────────────────────────────────────────────────────
    def delete_account(self, user_id: int, password: str) -> None:
        try:
            user = self._users.get_user_by_id(user_id)
        except UserNotFoundError:
            raise AuthError("User not found.")
        if not verify_password(password, user.password_hash):
            raise AuthError("Incorrect password.")
        self._sessions.invalidate_all_user_sessions(user_id)
        self._users.delete_user(user_id)
        logger.info("🗑️ Account deleted: user_id=%s", user_id)
