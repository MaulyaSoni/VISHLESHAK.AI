"""
Authentication UI — FINAL PRODUCTION VERSION
✅ No empty block at top
✅ Single clean borders
✅ Text perfectly centered in inputs
✅ Professional spacing
"""

import streamlit as st


def _get_theme():
    """Get theme colors"""
    dark_mode = st.session_state.get("dark_mode", True)
    if dark_mode:
        return dict(
            bg_primary="#0D0F1C",
            bg_secondary="#1A1F2E",
            bg_input="#262B3D",
            accent_primary="#6366F1",
            accent_secondary="#06B6D4",
            text_primary="#F8FAFC",
            text_secondary="#94A3B8",
            text_placeholder="#64748B",
            border="#3A4158",
            glow="rgba(99, 102, 241, 0.3)",
        )
    return dict(
        bg_primary="#F8FAFC",
        bg_secondary="#FFFFFF",
        bg_input="#FFFFFF",
        accent_primary="#4F46E5",
        accent_secondary="#0891B2",
        text_primary="#0F172A",
        text_secondary="#64748B",
        text_placeholder="#94A3B8",
        border="#D1D5DB",
        glow="rgba(79, 70, 229, 0.15)",
    )


def _auth_css() -> None:
    """Professional auth CSS - FINAL VERSION"""
    T = _get_theme()
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    /* ═══════════════════════════════════════════════════════
       FULL PAGE SETUP
    ═══════════════════════════════════════════════════════ */
    [data-testid="stAppViewContainer"] {{
        background: 
            radial-gradient(circle at 20% 20%, {T['accent_primary']}10 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, {T['accent_secondary']}08 0%, transparent 50%),
            {T['bg_primary']};
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }}
    
    /* Hide everything we don't need */
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {{
        display: none !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       CENTERED CONTAINER (480px card)
    ═══════════════════════════════════════════════════════ */
    .block-container {{
        max-width: 480px !important;
        width: 100% !important;
        padding: 2rem 1.5rem !important;
        margin: 0 auto !important;
    }}
    
    /* Main card wrapper */
    .auth-card {{
        background: {T['bg_secondary']};
        border: 1px solid {T['border']};
        border-radius: 1.5rem;
        padding: 2.5rem 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* ═══════════════════════════════════════════════════════
       LOGO & BRANDING
    ═══════════════════════════════════════════════════════ */
    .auth-logo {{
        font-size: 4rem;
        text-align: center;
        margin-bottom: 1rem;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 20px {T['glow']});
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-8px); }}
    }}
    
    .auth-title {{
        text-align: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, {T['accent_primary']}, {T['accent_secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }}
    
    .auth-subtitle {{
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: {T['text_secondary']};
        margin-bottom: 2rem;
    }}
    
    /* ═══════════════════════════════════════════════════════
       TAB BUTTONS (Login / Register)
    ═══════════════════════════════════════════════════════ */
    .stButton > button {{
        width: 100%;
        height: 3rem;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border-radius: 0.75rem !important;
        transition: all 0.2s ease !important;
    }}
    
    /* Unselected tab (secondary) */
    .stButton > button[data-testid="baseButton-secondary"] {{
        background: {T['bg_input']} !important;
        color: {T['text_secondary']} !important;
        border: 1px solid {T['border']} !important;
    }}
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
        border-color: {T['accent_primary']} !important;
        color: {T['accent_primary']} !important;
        background: {T['accent_primary']}08 !important;
        transform: translateY(-1px);
    }}
    
    /* Selected tab (primary) */
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, {T['accent_primary']}, {T['accent_secondary']}) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px {T['glow']} !important;
    }}
    
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px {T['glow']} !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       INPUT FIELDS - FIXED: Single border, centered text
    ═══════════════════════════════════════════════════════ */
    
    /* Label styling */
    .stTextInput > label,
    .stTextInput label {{
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: {T['text_primary']} !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }}
    
    /* Input container - REMOVE BORDER HERE */
    .stTextInput > div {{
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }}
    
    /* Actual input field - SINGLE BORDER ONLY */
    .stTextInput > div > div {{
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }}
    
    .stTextInput > div > div > input {{
        background: {T['bg_input']} !important;
        border: 1px solid {T['border']} !important; /* SINGLE BORDER */
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        color: {T['text_primary']} !important;
        padding: 0.875rem 1rem !important;
        height: 3rem !important;
        line-height: 1.5 !important; /* VERTICAL CENTER */
        transition: all 0.2s ease !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }}
    
    /* Placeholder text */
    .stTextInput > div > div > input::placeholder {{
        color: {T['text_placeholder']} !important;
        opacity: 0.7 !important;
        line-height: 1.5 !important;
    }}
    
    /* Focus state - SINGLE BORDER */
    .stTextInput > div > div > input:focus {{
        border: 1px solid {T['accent_primary']} !important; /* SINGLE BORDER */
        box-shadow: 0 0 0 3px {T['glow']} !important;
        outline: none !important;
        transform: scale(1.01);
    }}
    
    /* ═══════════════════════════════════════════════════════
       SUBMIT BUTTON - Clean gradient
    ═══════════════════════════════════════════════════════ */
    .stFormSubmitButton > button {{
        width: 100% !important;
        height: 3.5rem !important;
        background: linear-gradient(135deg, {T['accent_primary']}, {T['accent_secondary']}) !important;
        border: none !important;
        color: white !important;
        border-radius: 0.875rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 6px 24px {T['glow']} !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
    }}
    
    /* Shimmer effect */
    .stFormSubmitButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.6s;
    }}
    
    .stFormSubmitButton > button:hover::before {{
        left: 100%;
    }}
    
    .stFormSubmitButton > button:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 10px 35px {T['glow']} !important;
    }}
    
    .stFormSubmitButton > button:active {{
        transform: translateY(-1px) scale(0.98) !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       DIVIDER
    ═══════════════════════════════════════════════════════ */
    hr {{
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid {T['border']};
        opacity: 0.5;
    }}
    
    /* ═══════════════════════════════════════════════════════
       MESSAGES (Success / Error)
    ═══════════════════════════════════════════════════════ */
    .stSuccess {{
        background: linear-gradient(135deg, #10B98115, #10B98108) !important;
        border-left: 3px solid #10B981 !important;
        border-radius: 0.75rem !important;
        padding: 0.875rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #EF444415, #EF444408) !important;
        border-left: 3px solid #EF4444 !important;
        border-radius: 0.75rem !important;
        padding: 0.875rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       THEME TOGGLE BUTTON
    ═══════════════════════════════════════════════════════ */
    .theme-toggle {{
        margin-top: 1.5rem;
    }}
    
    .theme-toggle .stButton > button {{
        background: {T['bg_input']} !important;
        border: 1px solid {T['border']} !important;
        color: {T['text_primary']} !important;
        height: 2.75rem !important;
        font-size: 0.9rem !important;
    }}
    
    .theme-toggle .stButton > button:hover {{
        background: {T['accent_primary']}10 !important;
        border-color: {T['accent_primary']} !important;
        transform: translateY(-1px);
    }}
    
    /* ═══════════════════════════════════════════════════════
       LOADING SPINNER
    ═══════════════════════════════════════════════════════ */
    .stSpinner > div {{
        border-color: {T['accent_primary']} !important;
    }}
    
    /* ═══════════════════════════════════════════════════════
       FORM SPACING
    ═══════════════════════════════════════════════════════ */
    .stForm {{
        padding: 0 !important;
        border: none !important;
    }}
    
    .stTextInput {{
        margin-bottom: 1rem !important;
    }}
    
    /* Remove any extra padding/margins */
    .stTextInput > div {{
        margin: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def show_auth_page() -> bool:
    """
    FINAL production auth page
    ✅ No empty block
    ✅ Single borders
    ✅ Centered text
    ✅ Perfect spacing
    """
    from auth.auth_manager import AuthManager, AuthError

    _auth_css()

    # ── Init state ────────────────────────────────────────────────
    for key, val in [
        ("auth_tab", "Login"),
        ("auth_user", None),
        ("auth_token", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    # Already logged in
    if st.session_state.auth_user is not None:
        return True

    # ── Auth Card (NO EMPTY BLOCK) ────────────────────────────────
    # st.markdown('<div class="auth-card">Hello<div>', unsafe_allow_html=True)
    
    # Logo & Title (NO EMPTY BLOCK ABOVE)
    st.markdown('<div class="auth-logo">🔬</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Vishleshak AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-subtitle">The Analyser of Your Financial Data</div>',
        unsafe_allow_html=True,
    )

    # Tab buttons
    col_login, col_reg = st.columns(2, gap="small")
    with col_login:
        if st.button(
            "🔓 Login",
            width='stretch',
            type="primary" if st.session_state.auth_tab == "Login" else "secondary",
            key="login_tab",
        ):
            st.session_state.auth_tab = "Login"
            st.rerun()
    with col_reg:
        if st.button(
            "📝 Register",
            width='stretch',
            type="primary" if st.session_state.auth_tab == "Register" else "secondary",
            key="register_tab",
        ):
            st.session_state.auth_tab = "Register"
            st.rerun()

    st.markdown("---")

    auth = AuthManager()

    # ── LOGIN FORM ────────────────────────────────────────────────
    if st.session_state.auth_tab == "Login":
        with st.form("login_form", clear_on_submit=False):
            st.text_input(
                "📧 Email",
                placeholder="you@example.com",
                key="login_email",
            )
            st.text_input(
                "🔒 Password",
                placeholder="Your password",
                type="password",
                key="login_password",
            )
            submitted = st.form_submit_button("Login →", width='stretch')

        if submitted:
            email = st.session_state.login_email
            password = st.session_state.login_password

            if not email or not password:
                st.error("⚠️ Please fill in all fields.")
            else:
                try:
                    with st.spinner("🔐 Verifying credentials..."):
                        user, token = auth.login_user(email.strip(), password)
                    st.session_state.auth_user = user
                    st.session_state.auth_token = token
                    st.success(f"✅ Welcome back, **{user.username}**!")
                    import time
                    time.sleep(0.5)
                    st.rerun()
                except AuthError as e:
                    st.error(f"❌ {str(e)}")

    # ── REGISTER FORM ─────────────────────────────────────────────
    else:
        with st.form("register_form", clear_on_submit=False):
            st.text_input(
                "👤 Full Name",
                placeholder="John Doe",
                key="reg_fullname",
            )
            st.text_input(
                "🏷️ Username",
                placeholder="john_doe",
                key="reg_username",
            )
            st.text_input(
                "📧 Email",
                placeholder="you@example.com",
                key="reg_email",
            )
            st.text_input(
                "🔒 Password",
                placeholder="Min 8 chars, upper+lower+digit",
                type="password",
                key="reg_password",
            )
            st.text_input(
                "🔒 Confirm Password",
                placeholder="Repeat password",
                type="password",
                key="reg_confirm",
            )
            submitted = st.form_submit_button("Create Account →", width='stretch')

        if submitted:
            full_name = st.session_state.reg_fullname
            username = st.session_state.reg_username
            email = st.session_state.reg_email
            password = st.session_state.reg_password
            confirm = st.session_state.reg_confirm

            if not all([full_name, username, email, password, confirm]):
                st.error("⚠️ Please fill in all fields.")
            elif password != confirm:
                st.error("❌ Passwords do not match.")
            else:
                try:
                    with st.spinner("✨ Creating your account..."):
                        user = auth.register_user(
                            email=email.strip(),
                            username=username.strip(),
                            password=password,
                            full_name=full_name.strip(),
                        )
                        _, token = auth.login_user(email.strip(), password)
                    st.session_state.auth_user = user
                    st.session_state.auth_token = token
                    st.success(f"🎉 Account created! Welcome, **{user.username}**!")
                    import time
                    time.sleep(0.5)
                    st.rerun()
                except AuthError as e:
                    st.error(f"❌ {str(e)}")

    # Theme toggle (disabled — dark mode only)
    # st.markdown('<div class="theme-toggle">', unsafe_allow_html=True)
    # dark_label = "☀️ Light Mode" if st.session_state.get("dark_mode", True) else "🌙 Dark Mode"
    # if st.button(dark_label, use_container_width=True, key="theme_toggle"):
    #     st.session_state.dark_mode = not st.session_state.get("dark_mode", True)
    #     st.rerun()
    # st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.dark_mode = True  # Always dark
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close auth-card

    return False