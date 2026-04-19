"""
Authentication service
"""
import uuid
from typing import Optional, Tuple
from backend.models.user import User
from backend.core.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self._users = {}  # In-memory store for development
        self._tokens = {}
        
        # Create default user for development
        default_user = User(
            id=1,
            email="admin@vishleshak.ai",
            username="admin",
            domain="general"
        )
        self._users[1] = default_user
        self._users["admin@vishleshak.ai"] = default_user
    
    def authenticate(self, email: str, password: str) -> Optional[Tuple[User, str]]:
        """
        Authenticate user and return user + token
        For development, accepts any password for known users
        """
        user = self._users.get(email)
        if user:
            token = str(uuid.uuid4())
            self._tokens[token] = user.id
            logger.info(f"User authenticated: {email}")
            return user, token
        
        # Auto-create user for development
        user_id = len(self._users) + 1
        user = User(
            id=user_id,
            email=email,
            username=email.split('@')[0],
            domain="general"
        )
        self._users[user_id] = user
        self._users[email] = user
        
        token = str(uuid.uuid4())
        self._tokens[token] = user_id
        logger.info(f"New user created: {email}")
        return user, token
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user by token"""
        user_id = self._tokens.get(token)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def logout(self, token: str) -> bool:
        """Logout user"""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False


# Singleton instance
auth_service = AuthService()
