"""
Chat Repository — CRUD for conversations and messages
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .db_manager import get_db
from .models import Conversation, Message

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ChatRepository:
    """All conversation/message database operations."""

    # ── Conversations ───────────────────────────────────────────────────────

    def create_conversation(
        self,
        user_id: int,
        title: str = "New Chat",
        dataset_info: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        with get_db() as db:
            conv = Conversation(
                user_id=user_id,
                title=title[:200],
                dataset_name=dataset_info.get("name") if dataset_info else None,
                dataset_rows=dataset_info.get("rows") if dataset_info else None,
                dataset_cols=dataset_info.get("cols") if dataset_info else None,
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            logger.info("💬 Conversation %s created for user %s", conv.id, user_id)
            return conv

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        with get_db() as db:
            return (
                db.query(Conversation)
                .filter(Conversation.id == conv_id)
                .first()
            )

    def get_conversation_with_messages(self, conv_id: int) -> Optional[Conversation]:
        """Return conversation and eagerly load messages."""
        from sqlalchemy.orm import joinedload
        with get_db() as db:
            return (
                db.query(Conversation)
                .options(joinedload(Conversation.messages))
                .filter(Conversation.id == conv_id)
                .first()
            )

    def get_user_conversations(
        self,
        user_id: int,
        limit: int = 50,
        include_archived: bool = False,
    ) -> List[Conversation]:
        with get_db() as db:
            q = db.query(Conversation).filter(Conversation.user_id == user_id)
            if not include_archived:
                q = q.filter(Conversation.is_archived == False)  # noqa: E712
            return (
                q.order_by(Conversation.updated_at.desc())
                .limit(limit)
                .all()
            )

    def update_conversation_title(self, conv_id: int, new_title: str) -> None:
        with get_db() as db:
            conv = db.get(Conversation, conv_id)
            if conv:
                conv.title = new_title[:200]
                conv.updated_at = _utcnow()
                db.commit()

    def archive_conversation(self, conv_id: int) -> None:
        with get_db() as db:
            conv = db.get(Conversation, conv_id)
            if conv:
                conv.is_archived = True
                db.commit()

    def delete_conversation(self, conv_id: int) -> None:
        with get_db() as db:
            conv = db.get(Conversation, conv_id)
            if conv:
                db.delete(conv)
                db.commit()
                logger.info("🗑️ Conversation %s deleted", conv_id)

    def search_conversations(
        self, user_id: int, query: str
    ) -> List[Conversation]:
        """Search conversation titles and message content."""
        with get_db() as db:
            term = f"%{query}%"
            return (
                db.query(Conversation)
                .filter(
                    Conversation.user_id == user_id,
                    Conversation.is_archived == False,  # noqa: E712
                    Conversation.title.ilike(term),
                )
                .order_by(Conversation.updated_at.desc())
                .limit(20)
                .all()
            )

    # ── Messages ────────────────────────────────────────────────────────────

    def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        meta = metadata or {}
        with get_db() as db:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                quality_score=meta.get("quality_score"),
                quality_grade=meta.get("quality_grade"),
                tools_used=json.dumps(meta["tools_used"]) if "tools_used" in meta else None,
                confidence=meta.get("confidence"),
                reasoning_trace=json.dumps(meta["reasoning_trace"]) if "reasoning_trace" in meta else None,
            )
            db.add(msg)

            # bump conversation updated_at
            conv = db.get(Conversation, conversation_id)
            if conv:
                conv.updated_at = _utcnow()

            db.commit()
            db.refresh(msg)
            return msg

    def get_messages(self, conversation_id: int) -> List[Message]:
        with get_db() as db:
            return (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )

    # ── Export helper ────────────────────────────────────────────────────────

    def export_conversation_json(self, conv_id: int) -> Dict[str, Any]:
        """Return a dict representation suitable for JSON export."""
        conv = self.get_conversation_with_messages(conv_id)
        if not conv:
            return {}
        return {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "dataset": conv.dataset_name,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "quality_score": m.quality_score,
                    "quality_grade": m.quality_grade,
                }
                for m in conv.messages
            ],
        }
