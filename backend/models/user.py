"""
User model
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User model"""
    id: int
    email: str
    username: str
    domain: str = "general"
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'domain': self.domain,
            'is_active': self.is_active
        }
