"""
Database package for Vishleshak AI
Handles SQLite persistence for users, sessions, conversations, messages
"""

from .db_manager import DatabaseManager, get_db, init_database
from .models import User, Session, Conversation, Message, UserPreferences

__all__ = [
    "DatabaseManager",
    "get_db",
    "init_database",
    "User",
    "Session",
    "Conversation",
    "Message",
    "UserPreferences",
]
