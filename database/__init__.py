"""
Database package for Vishleshak AI
Handles SQLite persistence for users, sessions, conversations, messages, analysis reports
"""

from .db_manager import DatabaseManager, get_db, init_database
from .models import User, Session, Conversation, Message, UserPreferences, AnalysisReport
from .analysis_repository import AnalysisRepository, analysis_repository

__all__ = [
    "DatabaseManager",
    "get_db",
    "init_database",
    "User",
    "Session",
    "Conversation",
    "Message",
    "UserPreferences",
    "AnalysisReport",
    "AnalysisRepository",
    "analysis_repository",
]
