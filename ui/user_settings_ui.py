"""
User Settings Panel — REDESIGNED with Vibrant Colors & Smooth Hover Effects
Professional, formal, production-ready design
"""

from __future__ import annotations

import json
import streamlit as st


def _inject_settings_css() -> None:
    """Inject professional settings UI CSS with vibrant colors and hover effects"""
    dark_mode = st.session_state.get("dark_mode", True)
    
    if dark_mode:
        # VIBRANT DARK THEME
        bg_primary = "#0A0E1A"
        bg_secondary = "#131824"
        bg_tertiary = "#1C2333"
        bg_hover = "#252D42"
        accent = "#6366F1"
        accent2 = "#06B6D4"
        accent3 = "#10B981"
        accent_danger = "#EF4444"
        text_primary = "#FFFFFF"
        text_secondary = "#94A3B8"
        text_muted = "#64748B"
        border = "#2D3548"
        border_hover = "#4A5568"
        glow_primary = "rgba(99, 102, 241, 0.4)"
        glow_secondary = "rgba(6, 182, 212, 0.3)"
        gradient_accent = "linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)"
        gradient_hover = "linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%)"
    else:
        # VIBRANT LIGHT THEME
        bg_primary = "#FFFFFF"
        bg_secondary = "#F8FAFC"
        bg_tertiary = "#F1F5F9"
        bg_hover = "#E2E8F0"
        accent = "#4F46E5"
        accent2 = "#0891B2"
        accent3 = "#059669"
        accent_danger = "#DC2626"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "#64748B"
        border = "#CBD5E1"
        border_hover = "#94A3B8"
        glow_primary = "rgba(79, 70, 229, 0.25)"
        glow_secondary = "rgba(8, 145, 178, 0.2)"
        gradient_accent = "linear-gradient(135deg, #4F46E5 0%, #0891B2 100%)"
        gradient_hover = "linear-gradient(135deg, #6366F1 0%, #06B6D4 100%)"
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    /* ═══════════════════════════════════════════════════════
       SETTINGS CONTAINER
    ═══════════════════════════════════════════════════════ */
    .settings-container {{
        background: {bg_secondary};
        border: 2px solid {border};
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* ═══════════════════════════════════════════════════════
       TITLE WITH VIBRANT GRADIENT
    ═══════════════════════════════════════════════════════ */
    .settings-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        background: {gradient_accent};
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 1.5rem 0;
        letter-spacing: -0.03em;
        animation: gradient-shift 3s ease infinite;
        filter: drop-shadow(0 0 20px {glow_primary});
    }}
    
    @keyframes gradient-shift {{
        0%, 100% {{ background-position: 0% center; }}
        50% {{ background-position: 100% center; }}
    }}
    
    /* ═══════════════════════════════════════════════════════
       TABS WITH VIBRANT HOVER EFFECTS
    ═══════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {{
        background: {bg_tertiary} !important;
        border-radius: 1rem !important;
        padding: 0.5rem !important;
        gap: 0.5rem !important;
        border: 2px solid {border} !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 0.75rem !important;
        color: {text_secondary} !important;
        background: transparent !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        padding: 0.875rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    
    /* Tab hover effect */
    .stTabs [data-baseweb="tab"]:hover {{
        color: {accent} !important;
        background: {bg_hover} !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
    }}
    
    /* Active tab with vibrant gradient */
    .stTabs [aria-selected="true"] {{
        background: {gradient_accent} !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 24px {glow_primary} !important;
        transform: scale(1.02) !important;
    }}
    
    /* Shimmer effect on active tab */
    .stTabs [aria-selected="true"]::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 2s infinite;
    }}
    
    @keyframes shimmer {{
        to {{ left: 100%; }}
    }}
    
    /* Tab panel */
    .stTabs [data-baseweb="tab-panel"] {{
        background: {bg_secondary} !important;
        border: 2px solid {border} !important;
        border-radius: 1rem !important;
        padding: 2rem !important;
        margin-top: 1rem !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.12) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       INPUT FIELDS WITH VIBRANT FOCUS
    ═══════════════════════════════════════════════════════ */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {{
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: {text_primary} !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        background: {bg_tertiary} !important;
        border: 2px solid {border} !important;
        border-radius: 0.875rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 1rem 1.25rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        color: {text_primary} !important;
    }}
    
    /* Hover effect on inputs */
    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:hover,
    .stSelectbox > div > div:hover {{
        border-color: {border_hover} !important;
        background: {bg_hover} !important;
        transform: scale(1.01) !important;
    }}
    
    /* Focus effect with vibrant glow */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 4px {glow_primary}, 0 4px 16px {glow_secondary} !important;
        background: {bg_secondary} !important;
        transform: scale(1.02) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       BUTTONS WITH VIBRANT HOVER
    ═══════════════════════════════════════════════════════ */
    .stButton > button,
    .stFormSubmitButton > button {{
        background: {gradient_accent} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 1rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 6px 24px {glow_primary} !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    
    /* Button shimmer effect */
    .stButton > button::before,
    .stFormSubmitButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.6s;
    }}
    
    .stButton > button:hover::before,
    .stFormSubmitButton > button:hover::before {{
        left: 100%;
    }}
    
    /* Button hover effect */
    .stButton > button:hover,
    .stFormSubmitButton > button:hover {{
        background: {gradient_hover} !important;
        transform: translateY(-3px) scale(1.04) !important;
        box-shadow: 0 12px 40px {glow_primary} !important;
    }}
    
    /* Button active state */
    .stButton > button:active,
    .stFormSubmitButton > button:active {{
        transform: translateY(-1px) scale(1.01) !important;
    }}
    
    /* Close button styling */
    .stButton > button:has(*):not(:has(svg)) {{
        background: {gradient_accent} !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       FORMS WITH VIBRANT BORDER
    ═══════════════════════════════════════════════════════ */
    .stForm {{
        background: {bg_tertiary} !important;
        border: 2px solid {border} !important;
        border-radius: 1rem !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }}
    
    .stForm:hover {{
        border-color: {border_hover} !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15) !important;
        transform: translateY(-2px) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       CHECKBOXES WITH VIBRANT ACCENT
    ═══════════════════════════════════════════════════════ */
    .stCheckbox {{
        font-family: 'Inter', sans-serif !important;
        font-size: 1.05rem !important;
        transition: all 0.2s ease !important;
    }}
    
    .stCheckbox:hover {{
        transform: translateX(3px) !important;
    }}
    
    .stCheckbox > label > div {{
        background: {bg_tertiary} !important;
        border: 2px solid {border} !important;
        transition: all 0.2s ease !important;
    }}
    
    .stCheckbox > label > div:hover {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px {glow_primary} !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       ALERTS WITH VIBRANT COLORS
    ═══════════════════════════════════════════════════════ */
    .stSuccess {{
        background: linear-gradient(135deg, {accent3}18, {accent3}08) !important;
        border-left: 4px solid {accent3} !important;
        border-radius: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15) !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, {accent_danger}18, {accent_danger}08) !important;
        border-left: 4px solid {accent_danger} !important;
        border-radius: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.15) !important;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, #F59E0B18, #F59E0B08) !important;
        border-left: 4px solid #F59E0B !important;
        border-radius: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.15) !important;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, {accent2}18, {accent2}08) !important;
        border-left: 4px solid {accent2} !important;
        border-radius: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.15) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       MARKDOWN STYLING
    ═══════════════════════════════════════════════════════ */
    .stMarkdown {{
        font-family: 'Inter', sans-serif !important;
        color: {text_primary} !important;
        line-height: 1.6 !important;
    }}
    
    .stMarkdown strong {{
        background: {gradient_accent};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }}
    
    .stMarkdown h4 {{
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        color: {text_primary} !important;
        margin: 1.5rem 0 1rem !important;
        font-size: 1.5rem !important;
    }}
    
    .stMarkdown code {{
        background: {bg_tertiary} !important;
        color: {accent} !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 0.375rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        border: 1px solid {border} !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       DOWNLOAD BUTTON SPECIAL STYLING
    ═══════════════════════════════════════════════════════ */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {accent3} 0%, {accent2} 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 1rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 6px 24px rgba(16, 185, 129, 0.3) !important;
        transition: all 0.3s ease !important;
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-3px) scale(1.04) !important;
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.4) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       DIVIDERS
    ═══════════════════════════════════════════════════════ */
    hr {{
        border: none !important;
        border-top: 2px solid {border} !important;
        margin: 2rem 0 !important;
        opacity: 0.6 !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       SELECTBOX DROPDOWN
    ═══════════════════════════════════════════════════════ */
    .stSelectbox > div > div {{
        background: {bg_tertiary} !important;
        border: 2px solid {border} !important;
        transition: all 0.3s ease !important;
    }}
    
    .stSelectbox > div > div:hover {{
        border-color: {border_hover} !important;
        background: {bg_hover} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_user_settings() -> None:
    """
    Render the user settings panel with vibrant, professional design
    ✅ Bold colors
    ✅ Smooth hover effects
    ✅ Professional appearance
    """
    from auth.auth_manager import AuthManager, AuthError
    from database.user_repository import UserRepository
    from database.chat_repository import ChatRepository

    user = st.session_state.get("auth_user")
    token = st.session_state.get("auth_token")
    if not user:
        return

    _inject_settings_css()

    auth = AuthManager()
    user_repo = UserRepository()
    chat_repo = ChatRepository()

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

        st.markdown("#### ✏️ Edit Profile")
        with st.form("profile_form"):
            new_name = st.text_input("Full Name", value=user.full_name or "", key="prof_name")
            submitted = st.form_submit_button("💾 Save Changes", width='stretch')
        if submitted:
            try:
                user_repo.update_user(user.id, full_name=new_name)
                user.full_name = new_name
                st.session_state.auth_user = user
                st.success("✅ Profile updated successfully!")
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

    # ── SECURITY TAB ─────────────────────────────────────────────────────────
    with tab_security:
        st.markdown("#### 🔐 Change Password")
        with st.form("password_form"):
            old_pass = st.text_input("Current Password", type="password", key="old_pw")
            new_pass = st.text_input(
                "New Password",
                type="password",
                help="Min 8 chars, upper+lower+digit+symbol",
                key="new_pw"
            )
            conf_pass = st.text_input("Confirm New Password", type="password", key="conf_pw")
            submitted = st.form_submit_button("🔄 Update Password", width='stretch')

        if submitted:
            if not all([old_pass, new_pass, conf_pass]):
                st.error("⚠️ Please fill in all fields.")
            elif new_pass != conf_pass:
                st.error("❌ New passwords don't match.")
            else:
                try:
                    auth.change_password(user.id, old_pass, new_pass)
                    st.success("✅ Password changed! Please log in again.")
                    st.session_state.auth_user = None
                    st.session_state.auth_token = None
                    st.rerun()
                except AuthError as e:
                    st.error(f"❌ {str(e)}")

        st.markdown("---")
        st.markdown("#### ☠️ Delete Account")
        st.warning("⚠️ This will permanently delete your account and all data. This action cannot be undone.")
        with st.form("delete_account_form"):
            confirm_pass = st.text_input("Confirm Password to Delete", type="password", key="del_pw")
            submitted = st.form_submit_button("🗑️ Permanently Delete My Account", width='stretch')

        if submitted:
            try:
                auth.delete_account(user.id, confirm_pass)
                st.session_state.auth_user = None
                st.session_state.auth_token = None
                st.success("✅ Account deleted successfully.")
                st.rerun()
            except AuthError as e:
                st.error(f"❌ {str(e)}")

    # ── PREFERENCES TAB ──────────────────────────────────────────────────────
    with tab_prefs:
        prefs = user_repo.get_preferences(user.id)
        if not prefs:
            st.info("ℹ️ Preferences not found. They will be created on save.")

        current_theme = getattr(prefs, "theme", "dark") if prefs else "dark"
        current_thinking = getattr(prefs, "show_thinking", False) if prefs else False
        current_quality = getattr(prefs, "show_quality_scores", True) if prefs else True

        with st.form("prefs_form"):
            theme = "dark"  # Only dark theme supported
            show_thinking = st.checkbox(
                "👁️ Show Agent Thinking Process",
                value=current_thinking,
                key="thinking_check"
            )
            submitted = st.form_submit_button("💾 Save Preferences", width='stretch')

        if submitted:
            try:
                user_repo.update_preferences(
                    user.id,
                    theme=theme,
                    show_thinking=show_thinking,
                    show_quality_scores=False,
                )
                # Apply theme immediately
                st.session_state.dark_mode = True
                st.session_state.show_agent_thinking = show_thinking
                st.success("✅ Preferences saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Save failed: {e}")

    # ── DATA TAB ─────────────────────────────────────────────────────────────
    with tab_data:
        st.markdown("#### 📥 Export My Conversations")
        convs = chat_repo.get_user_conversations(user.id, limit=200)
        st.markdown(f"You have **{len(convs)}** conversation(s) on record.")

        if st.button(" Download All as JSON", width='stretch', key="download_json"):
            if convs:
                all_data = []
                for conv in convs:
                    all_data.append(chat_repo.export_conversation_json(conv.id))
                json_str = json.dumps(all_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="⬇️ Download conversations.json",
                    data=json_str,
                    file_name="vishleshak_conversations.json",
                    mime="application/json",
                    width='stretch',
                    key="download_btn"
                )
            else:
                st.info("ℹ️ No conversations to export.")