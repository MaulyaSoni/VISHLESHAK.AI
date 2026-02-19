"""
Chat History Sidebar — shows DB-persisted conversations for the logged-in user
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List

import streamlit as st


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _group_label(conv_created_at: datetime | None) -> str:
    if conv_created_at is None:
        return "Older"
    now = _utcnow()
    diff = now - conv_created_at
    if diff < timedelta(days=1):
        return "Today"
    if diff < timedelta(days=2):
        return "Yesterday"
    if diff < timedelta(days=7):
        return "Last 7 Days"
    return "Older"


def _css() -> None:
    T_accent = "#7C3AED" if st.session_state.get("dark_mode", True) else "#4F46E5"
    st.markdown(f"""
    <style>
    .hist-group-label {{
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: {T_accent};
        padding: 0.6rem 0 0.2rem;
    }}
    .hist-active {{
        border-color: {T_accent} !important;
        background: {T_accent}22 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_chat_history_sidebar(user_id: int) -> None:
    """
    Render the chat history section inside the Streamlit sidebar.
    Loads conversations from the database for the given user_id.
    Clicking a conversation loads it into session state.
    """
    from database.chat_repository import ChatRepository
    from database.db_manager import get_db
    from database.models import Message

    _css()
    chat_repo = ChatRepository()

    st.markdown('<div class="sidebar-section">Chat History</div>', unsafe_allow_html=True)

    # ── Search ────────────────────────────────────────────────────────────────
    search_q = st.text_input(
        "search_chats", placeholder="🔍 Search chats…",
        label_visibility="collapsed",
        key="chat_search_input",
    )

    # ── New Chat button ───────────────────────────────────────────────────────
    if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
        import uuid
        st.session_state.session_id    = str(uuid.uuid4())
        st.session_state.chat_history  = []
        st.session_state.qa_chain      = None
        st.session_state.current_conv_id = None
        st.rerun()

    # ── Load conversations ────────────────────────────────────────────────────
    try:
        if search_q:
            convs = chat_repo.search_conversations(user_id, search_q)
        else:
            convs = chat_repo.get_user_conversations(user_id, limit=30)
    except Exception:
        st.caption("⚠️ Could not load history.")
        return

    if not convs:
        st.markdown(
            '<div style="color:var(--muted);font-size:0.8rem;padding:0.5rem 0;">'
            'No conversations yet. Start chatting!</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Group by date ─────────────────────────────────────────────────────────
    groups: dict[str, list] = {}
    for c in convs:
        label = _group_label(c.created_at)
        groups.setdefault(label, []).append(c)

    current_conv_id = st.session_state.get("current_conv_id")

    for group in ["Today", "Yesterday", "Last 7 Days", "Older"]:
        if group not in groups:
            continue
        st.markdown(f'<div class="hist-group-label">{group}</div>', unsafe_allow_html=True)
        for conv in groups[group]:
            title   = (conv.title or "Untitled")[:38]
            is_curr = conv.id == current_conv_id
            icon    = "💬" if is_curr else "🕐"
            extra   = " hist-active" if is_curr else ""

            col_title, col_del = st.columns([5, 1])
            with col_title:
                st.markdown(
                    f'<div class="hist-item{extra}" title="{conv.title}">{icon} {title}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Load##{conv.id}", key=f"load_conv_{conv.id}",
                    help=conv.title or "Load conversation",
                    use_container_width=True,
                ):
                    _load_conversation(conv.id)

            with col_del:
                if st.button("🗑", key=f"del_conv_{conv.id}", help="Delete"):
                    chat_repo.delete_conversation(conv.id)
                    if current_conv_id == conv.id:
                        st.session_state.current_conv_id = None
                        st.session_state.chat_history = []
                    st.rerun()

    # ── Archive button (bottom) ───────────────────────────────────────────────
    if st.button("📦 Archive Current", use_container_width=True, key="archive_btn"):
        cid = st.session_state.get("current_conv_id")
        if cid:
            chat_repo.archive_conversation(cid)
            st.session_state.current_conv_id = None
            st.session_state.chat_history = []
            st.rerun()


def _load_conversation(conv_id: int) -> None:
    """Load a conversation from DB into session_state.chat_history."""
    from database.chat_repository import ChatRepository
    chat_repo = ChatRepository()

    conv = chat_repo.get_conversation_with_messages(conv_id)
    if not conv:
        return

    # Rebuild chat_history as list of (role_str, content) tuples
    history = []
    for msg in conv.messages:
        role = "user" if msg.role == "user" else "assistant"
        history.append((role, msg.content))

    st.session_state.chat_history    = history
    st.session_state.current_conv_id = conv_id
    st.session_state.qa_chain        = None   # reset so it re-builds with new context
    st.rerun()
