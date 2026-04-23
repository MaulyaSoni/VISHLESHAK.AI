"""
Authentication service - Uses AuthManager (same as Streamlit app.py)
"""
from typing import Optional, Tuple
from backend.models.user import User
from backend.core.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service wrapper around AuthManager"""
    
    def __init__(self):
        # Import here to avoid circular imports
        from auth.auth_manager import AuthManager
        self.auth_manager = AuthManager()
    
    def authenticate(self, email: str, password: str) -> Optional[Tuple[User, str]]:
        """
        Authenticate user using AuthManager (same as Streamlit)
        Returns (User, token) or None on failure
        """
        try:
            user, token = self.auth_manager.login_user(email, password)
            logger.info(f"User authenticated: {email}")
            return user, token
        except Exception as e:
            logger.warning(f"Authentication failed for {email}: {e}")
            return None
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user by token using AuthManager"""
        try:
            user = self.auth_manager.verify_session(token)
            return user
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    def logout(self, token: str) -> bool:
        """Logout user using AuthManager"""
        try:
            return self.auth_manager.logout_user(token)
        except Exception as e:
            logger.warning(f"Logout failed: {e}")
            return False


# Singleton instance
auth_service = AuthService()
