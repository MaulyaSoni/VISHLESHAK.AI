"""
User Settings Panel — profile, password, preferences, data export, account deletion
"""

from __future__ import annotations

import json

import streamlit as st


def render_user_settings() -> None:
    """
    Render the user settings panel in an expander or modal-style area.
    Must be called when st.session_state.auth_user is set.
    """
    from auth.auth_manager import AuthManager, AuthError
    from database.user_repository import UserRepository
    from database.chat_repository import ChatRepository

    user  = st.session_state.get("auth_user")
    token = st.session_state.get("auth_token")
    if not user:
        return

    auth       = AuthManager()
    user_repo  = UserRepository()
    chat_repo  = ChatRepository()

    st.markdown("---")
    st.markdown("### ⚙️ Account Settings")

    tab_profile, tab_security, tab_prefs, tab_data = st.tabs(
        ["👤 Profile", "🔒 Security", "🎨 Preferences", "📊 My Data"]
    )

    # ── PROFILE TAB ──────────────────────────────────────────────────────────
    with tab_profile:
        st.markdown(f"**Username:** `{user.username}`")
        st.markdown(f"**Email:** `{user.email}`")
        if user.created_at:
            st.markdown(f"**Member since:** {user.created_at.strftime('%B %d, %Y')}")

        st.markdown("#### Edit Profile")
        with st.form("profile_form"):
            new_name  = st.text_input("Full Name",  value=user.full_name or "")
            submitted = st.form_submit_button("Save Changes", use_container_width=True)
        if submitted:
            try:
                user_repo.update_user(user.id, full_name=new_name)
                user.full_name = new_name
                st.session_state.auth_user = user
                st.success("✅ Profile updated!")
            except Exception as e:
                st.error(f"Update failed: {e}")

    # ── SECURITY TAB ─────────────────────────────────────────────────────────
    with tab_security:
        st.markdown("#### Change Password")
        with st.form("password_form"):
            old_pass  = st.text_input("Current Password",  type="password")
            new_pass  = st.text_input("New Password",      type="password",
                                      help="Min 8 chars, upper+lower+digit+symbol")
            conf_pass = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password", use_container_width=True)

        if submitted:
            if not all([old_pass, new_pass, conf_pass]):
                st.error("Please fill in all fields.")
            elif new_pass != conf_pass:
                st.error("New passwords don't match.")
            else:
                try:
                    auth.change_password(user.id, old_pass, new_pass)
                    st.success("✅ Password changed! Please log in again.")
                    st.session_state.auth_user  = None
                    st.session_state.auth_token = None
                    st.rerun()
                except AuthError as e:
                    st.error(str(e))

        st.markdown("---")
        st.markdown("#### ☠️ Delete Account")
        st.warning("This will permanently delete your account and all data.")
        with st.form("delete_account_form"):
            confirm_pass = st.text_input("Confirm Password", type="password")
            submitted    = st.form_submit_button("🗑️ Delete My Account", use_container_width=True)

        if submitted:
            try:
                auth.delete_account(user.id, confirm_pass)
                st.session_state.auth_user  = None
                st.session_state.auth_token = None
                st.success("Account deleted.")
                st.rerun()
            except AuthError as e:
                st.error(str(e))

    # ── PREFERENCES TAB ──────────────────────────────────────────────────────
    with tab_prefs:
        prefs = user_repo.get_preferences(user.id)
        if not prefs:
            st.info("Preferences not found. They will be created on save.")

        current_theme = getattr(prefs, "theme", "dark") if prefs else "dark"
        current_thinking = getattr(prefs, "show_thinking", False) if prefs else False
        current_quality  = getattr(prefs, "show_quality_scores", True) if prefs else True

        with st.form("prefs_form"):
            theme = st.selectbox(
                "🎨 Theme",
                options=["dark", "light"],
                index=0 if current_theme == "dark" else 1,
            )
            show_thinking = st.checkbox(
                "👁️ Show Agent Thinking Process",
                value=current_thinking,
            )
            show_quality = st.checkbox(
                "📊 Show Quality Scores",
                value=current_quality,
            )
            submitted = st.form_submit_button("Save Preferences", use_container_width=True)

        if submitted:
            try:
                user_repo.update_preferences(
                    user.id,
                    theme=theme,
                    show_thinking=show_thinking,
                    show_quality_scores=show_quality,
                )
                # Apply theme immediately
                st.session_state.dark_mode = (theme == "dark")
                st.session_state.show_agent_thinking = show_thinking
                st.success("✅ Preferences saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

    # ── DATA TAB ─────────────────────────────────────────────────────────────
    with tab_data:
        st.markdown("#### 📥 Export My Conversations")
        convs = chat_repo.get_user_conversations(user.id, limit=200)
        st.markdown(f"You have **{len(convs)}** conversation(s) on record.")

        if st.button("Download All as JSON", use_container_width=True):
            all_data = []
            for conv in convs:
                all_data.append(chat_repo.export_conversation_json(conv.id))
            json_str = json.dumps(all_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="⬇️ Download conversations.json",
                data=json_str,
                file_name="my_conversations.json",
                mime="application/json",
                use_container_width=True,
            )
