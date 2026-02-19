"""
User Settings Panel — profile, password, preferences, data export, account deletion
Clean, modern UI with bold styling
"""

from __future__ import annotations

import json

import streamlit as st


def _inject_settings_css() -> None:
    """Inject Claude-inspired settings UI CSS"""
    dark_mode = st.session_state.get("dark_mode", True)
    
    if dark_mode:
        bg_primary = "#0D0F1C"
        bg_secondary = "#161B2E"
        bg_tertiary = "#1F2638"
        accent = "#6366F1"
        accent2 = "#06B6D4"
        accent3 = "#10B981"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        border = "#2D3548"
        glow = "rgba(99, 102, 241, 0.25)"
        gradient = "linear-gradient(135deg, #6366F1, #06B6D4)"
    else:
        bg_primary = "#FFFFFF"
        bg_secondary = "#F8FAFC"
        bg_tertiary = "#F1F5F9"
        accent = "#4F46E5"
        accent2 = "#0891B2"
        accent3 = "#059669"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        border = "#E2E8F0"
        glow = "rgba(79, 70, 229, 0.15)"
        gradient = "linear-gradient(135deg, #4F46E5, #0891B2)"
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Settings section title */
    .settings-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        background: {gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1.5rem 0 1rem;
        letter-spacing: -0.02em;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background: {bg_secondary} !important;
        border-radius: 0.75rem !important;
        padding: 0.35rem !important;
        gap: 0.35rem !important;
        border: 1px solid {border} !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 0.5rem !important;
        color: {text_secondary} !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.65rem 1.25rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {gradient} !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px {glow} !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: {bg_secondary} !important;
        border: 1px solid {border} !important;
        border-radius: 0.75rem !important;
        padding: 1.5rem !important;
        margin-top: 0.75rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }}
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        background: {bg_tertiary} !important;
        border: 1.5px solid {border} !important;
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 0.875rem 1rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        color: {text_primary} !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 4px {glow} !important;
        background: {bg_secondary} !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: {gradient} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 0.875rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        padding: 0.875rem 2rem !important;
        box-shadow: 0 4px 16px {glow} !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 24px {glow} !important;
    }}
    
    /* Form styling */
    .stForm {{
        background: {bg_tertiary} !important;
        border: 1px solid {border} !important;
        border-radius: 0.75rem !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
    }}
    
    /* Checkbox styling */
    .stCheckbox {{
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
    }}
    
    /* Info/warning/success boxes */
    .stAlert {{
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 1rem 1.25rem !important;
    }}
    
    /* Labels */
    label {{
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: {text_primary} !important;
    }}
    
    /* Markdown in settings */
    .stMarkdown {{
        font-family: 'Inter', sans-serif !important;
        color: {text_primary} !important;
    }}
    .stMarkdown strong {{
        color: {accent} !important;
        font-weight: 700 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_user_settings() -> None:
    """
    Render the user settings panel with modern, bold design.
    Must be called when st.session_state.auth_user is set.
    """
    from auth.auth_manager import AuthManager, AuthError
    from database.user_repository import UserRepository
    from database.chat_repository import ChatRepository

    user  = st.session_state.get("auth_user")
    token = st.session_state.get("auth_token")
    if not user:
        return

    _inject_settings_css()

    auth       = AuthManager()
    user_repo  = UserRepository()
    chat_repo  = ChatRepository()

    st.markdown("---")
    st.markdown('<div class="settings-title">⚙️ Account Settings</div>', unsafe_allow_html=True)

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
