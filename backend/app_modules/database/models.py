"""
SQLAlchemy ORM models for Vishleshak AI
Tables: users, sessions, conversations, messages, user_preferences
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    username      = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(200))
    created_at    = Column(DateTime, default=_utcnow)
    last_login    = Column(DateTime)
    is_active     = Column(Boolean, default=True)
    is_admin      = Column(Boolean, default=False)
    profile_pic   = Column(Text)  # base64 or URL

    sessions      = relationship("Session",       back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation",  back_populates="user", cascade="all, delete-orphan")
    preferences   = relationship("UserPreferences", back_populates="user",
                                  uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


# ─────────────────────────────────────────────────────────────────────────────
class Session(Base):
    __tablename__ = "sessions"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    created_at    = Column(DateTime, default=_utcnow)
    expires_at    = Column(DateTime, nullable=False)
    is_active     = Column(Boolean, default=True)
    device_info   = Column(Text)   # JSON: browser, OS, IP

    user = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_sessions_token", "session_token"),)

    def __repr__(self) -> str:
        return f"<Session id={self.id} user_id={self.user_id}>"


# ─────────────────────────────────────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title        = Column(String(200), default="New Chat")
    created_at   = Column(DateTime, default=_utcnow)
    updated_at   = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    is_archived  = Column(Boolean, default=False)
    dataset_name = Column(String(200))
    dataset_rows = Column(Integer)
    dataset_cols = Column(Integer)

    user     = relationship("User",    back_populates="conversations")
    messages = relationship("Message", back_populates="conversation",
                             cascade="all, delete-orphan", order_by="Message.created_at")

    __table_args__ = (
        Index("idx_conv_user_id",   "user_id"),
        Index("idx_conv_created",   "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title!r}>"


# ─────────────────────────────────────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role            = Column(String(20), nullable=False)   # 'user' | 'assistant'
    content         = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=_utcnow)

    # Agent metadata
    quality_score   = Column(Float)
    quality_grade   = Column(String(2))
    tools_used      = Column(Text)    # JSON array
    confidence      = Column(Float)
    reasoning_trace = Column(Text)    # JSON

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_msg_conv_id", "conversation_id"),
        Index("idx_msg_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role!r}>"


# ─────────────────────────────────────────────────────────────────────────────
class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id                  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme                    = Column(String(20), default="dark")
    show_thinking            = Column(Boolean, default=False)
    show_quality_scores      = Column(Boolean, default=True)
    default_analysis_mode    = Column(String(50), default="comprehensive")
    notifications_enabled    = Column(Boolean, default=True)
    preferences_json         = Column(Text)   # extra JSON settings

    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id}>"


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id        = Column(String(100), unique=True, nullable=False, index=True)
    description   = Column(Text)
    schedule      = Column(String(50), nullable=False)
    pipeline      = Column(Text)   # JSON array of pipeline steps
    source        = Column(String(50), default="last_uploaded")
    output        = Column(Text)   # JSON array of outputs
    domain        = Column(String(20), default="general")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=_utcnow)
    last_run      = Column(DateTime)
    next_run      = Column(DateTime)

    __table_args__ = (Index("idx_sched_user", "user_id"),)


class DatasetMemory(Base):
    __tablename__ = "dataset_memories"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_hash   = Column(String(50), nullable=False, index=True)
    dataset_name   = Column(String(200))
    key_findings   = Column(Text)
    anomalies      = Column(Text)   # JSON array
    column_stats   = Column(Text)   # JSON
    domain         = Column(String(20))
    memory_tier    = Column(String(10), default="warm")  # warm or cold
    created_at     = Column(DateTime, default=_utcnow)
    accessed_at    = Column(DateTime)

    __table_args__ = (
        Index("idx_dataset_mem_user", "user_id"),
        Index("idx_dataset_mem_hash", "dataset_hash"),
    )


# ─────────────────────────────────────────────────────────────────────────────
class AnalysisReport(Base):
    """Stores Data Agent analysis reports for history and retrieval."""
    __tablename__ = "analysis_reports"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id      = Column(String(100), nullable=False, index=True)
    title           = Column(String(300), default="Data Analysis")
    instruction     = Column(Text)  # User's original instruction
    dataset_name    = Column(String(200))
    dataset_rows    = Column(Integer)
    dataset_cols    = Column(Integer)
    mode            = Column(String(50))  # Analysis Only, Analysis + ML, etc.
    
    # Report content stored as JSON
    executive_summary = Column(Text)
    key_findings      = Column(Text)  # JSON array
    recommendations   = Column(Text)  # JSON array
    anomalies         = Column(Text)  # JSON array
    charts_info       = Column(Text)  # JSON array of chart metadata
    ml_metrics        = Column(Text)  # JSON object
    notebook_path     = Column(String(500))
    full_report       = Column(Text)  # Complete report JSON
    
    # Status and timestamps
    status          = Column(String(20), default="completed")  # completed, error, running
    error_message   = Column(Text)
    created_at      = Column(DateTime, default=_utcnow)
    updated_at      = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("idx_analysis_user", "user_id"),
        Index("idx_analysis_session", "session_id"),
        Index("idx_analysis_created", "created_at"),
    )
