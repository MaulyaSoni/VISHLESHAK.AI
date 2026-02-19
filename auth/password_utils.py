"""
Secure password utilities using bcrypt
"""

import re
import secrets
import string
from typing import List, Tuple

import bcrypt


# ── Hashing ──────────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with bcrypt (12 rounds)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── Token generation ─────────────────────────────────────────────────────────

def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ── Validation ────────────────────────────────────────────────────────────────

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength.

    Returns:
        (is_valid: bool, issues: list[str])
    """
    issues: List[str] = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        issues.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        issues.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        issues.append("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        issues.append("Password must contain at least one special character.")

    return len(issues) == 0, issues


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Returns:
        (is_valid: bool, error_message: str)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(username) > 30:
        return False, "Username must be at most 30 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain letters, numbers, and underscores."
    return True, ""
