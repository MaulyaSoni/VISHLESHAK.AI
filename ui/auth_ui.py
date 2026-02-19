"""
Authentication UI — Login / Register page for Vishleshak AI
Claude.ai-inspired professional design
"""

import streamlit as st


def _get_theme():
    """Get Claude-inspired theme colors"""
    dark_mode = st.session_state.get("dark_mode", True)
    if dark_mode:
        return dict(
            bg_primary="#0D0F1C",
            bg_secondary="#161B2E",
            bg_tertiary="#1F2638",
            bg_overlay="#2A3044",
            accent_primary="#6366F1",
            accent_secondary="#06B6D4",
            accent_success="#10B981",
            text_primary="#F8FAFC",
            text_secondary="#94A3B8",
            text_tertiary="#64748B",
            border="#2D3548",
            border_hover="#3F4A62",
            glow_primary="rgba(99, 102, 241, 0.25)",
            glow_secondary="rgba(6, 182, 212, 0.2)",
        )
    return dict(
        bg_primary="#FFFFFF",
        bg_secondary="#F8FAFC",
        bg_tertiary="#F1F5F9",
        bg_overlay="#E2E8F0",
        accent_primary="#4F46E5",
        accent_secondary="#0891B2",
        accent_success="#059669",
        text_primary="#0F172A",
        text_secondary="#475569",
        text_tertiary="#64748B",
        border="#E2E8F0",
        border_hover="#CBD5E1",
        glow_primary="rgba(79, 70, 229, 0.15)",
        glow_secondary="rgba(8, 145, 178, 0.12)",
    )


def _auth_css() -> None:
    """Inject Claude-inspired auth page CSS"""
    T = _get_theme()
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset & Base Styles */
    [data-testid="stAppViewContainer"] {{
        background: 
            radial-gradient(circle at 20% 20%, {T['accent_primary']}08 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, {T['accent_secondary']}06 0%, transparent 50%),
            {T['bg_primary']};
        background-attachment: fixed;
    }}
    
    /* Hide default Streamlit elements on auth page */
    [data-testid="stHeader"] {{
        background-color: transparent;
    }}
    
    /* Logo with Float Animation */
    .auth-logo {{
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 20px {T['glow_primary']});
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    /* Gradient Animated Title */
    .auth-title {{
        text-align: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, 
            {T['accent_primary']} 0%, 
            {T['accent_secondary']} 50%,
            {T['accent_primary']} 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        animation: gradient-shift 4s ease infinite;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    @keyframes gradient-shift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    /* Subtitle */
    .auth-subtitle {{
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: {T['text_secondary']};
        margin-bottom: 2rem;
        font-weight: 400;
    }}
    
    /* Input Fields - Claude Style */
    .stTextInput > div > div > input {{
        background: {T['bg_tertiary']} !important;
        border: 1.5px solid {T['border']} !important;
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        color: {T['text_primary']} !important;
        padding: 0.875rem 1rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: {T['text_tertiary']} !important;
        opacity: 0.7;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {T['accent_primary']} !important;
        box-shadow: 0 0 0 4px {T['glow_primary']} !important;
        outline: none !important;
        background: {T['bg_secondary']} !important;
    }}
    
    /* Tab Buttons */
    .stButton > button[data-testid="baseButton-secondary"] {{
        background: transparent !important;
        border: 1px solid {T['border']} !important;
        color: {T['text_secondary']} !important;
        border-radius: 0.75rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
        border-color: {T['accent_primary']} !important;
        color: {T['accent_primary']} !important;
        background: {T['bg_tertiary']} !important;
    }}
    
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, 
            {T['accent_primary']} 0%, 
            {T['accent_secondary']} 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 0.75rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 12px {T['glow_primary']} !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    
    .stButton > button[data-testid="baseButton-primary"]::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255,255,255,0.15), 
            transparent);
        transition: left 0.5s;
    }}
    
    .stButton > button[data-testid="baseButton-primary"]:hover::before {{
        left: 100%;
    }}
    
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 24px {T['glow_primary']} !important;
    }}
    
    /* Form Submit Buttons */
    .stFormSubmitButton > button {{
        width: 100% !important;
        background: linear-gradient(135deg, 
            {T['accent_primary']} 0%, 
            {T['accent_secondary']} 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 0.875rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        padding: 1rem !important;
        box-shadow: 0 6px 20px {T['glow_primary']} !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    
    .stFormSubmitButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255,255,255,0.2), 
            transparent);
        transition: left 0.5s;
    }}
    
    .stFormSubmitButton > button:hover::before {{
        left: 100%;
    }}
    
    .stFormSubmitButton > button:hover {{
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 10px 30px {T['glow_primary']} !important;
    }}
    
    .stFormSubmitButton > button:active {{
        transform: translateY(0) scale(0.99) !important;
    }}
    
    /* Divider */
    hr {{
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid {T['border']};
        opacity: 0.6;
    }}
    
    /* Success/Error Messages */
    .stSuccess {{
        background: linear-gradient(135deg, {T['accent_success']}15, {T['accent_success']}08) !important;
        border-left: 4px solid {T['accent_success']} !important;
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #EF444415, #EF444408) !important;
        border-left: 4px solid #EF4444 !important;
        border-radius: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    /* Loading Spinner */
    .stSpinner > div {{
        border-color: {T['accent_primary']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def show_auth_page() -> bool:
    """
    Render the login / register page with Claude-inspired professional design.

    Returns True once the user is authenticated (session_state populated).
    Handles all auth state internally via st.session_state.
    """
    from auth.auth_manager import AuthManager, AuthError

    _auth_css()

    # ── Initialise auth state ────────────────────────────────────────────────
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

    # ── Layout ───────────────────────────────────────────────────────────────
    st.markdown('<div class="auth-logo">🔬</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Vishleshak AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-subtitle">The Analyser of Your Financial Data</div>',
        unsafe_allow_html=True,
    )

    # Tab buttons
    col_login, col_reg = st.columns(2)
    with col_login:
        if st.button("🔓 Login", use_container_width=True,
                     type="primary" if st.session_state.auth_tab == "Login" else "secondary",
                     key="login_tab"):
            st.session_state.auth_tab = "Login"
            st.rerun()
    with col_reg:
        if st.button("📝 Register", use_container_width=True,
                     type="primary" if st.session_state.auth_tab == "Register" else "secondary",
                     key="register_tab"):
            st.session_state.auth_tab = "Register"
            st.rerun()

    st.markdown("---")

    auth = AuthManager()

    # ── LOGIN FORM ──────────────────────────────────────────────────────
    if st.session_state.auth_tab == "Login":
        with st.form("login_form", clear_on_submit=False):
            st.text_input("📧 Email", placeholder="you@example.com", key="login_email")
            st.text_input("🔒 Password", placeholder="Your password", type="password", key="login_password")
            submitted = st.form_submit_button("Login →", use_container_width=True)

        if submitted:
            email = st.session_state.login_email
            password = st.session_state.login_password
            
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                try:
                    with st.spinner("Verifying credentials..."):
                        user, token = auth.login_user(email.strip(), password)
                    st.session_state.auth_user  = user
                    st.session_state.auth_token = token
                    st.success(f"Welcome back, **{user.username}**! 👋")
                    st.rerun()
                except AuthError as e:
                    st.error(str(e))

    # ── REGISTER FORM ───────────────────────────────────────────────────
    else:
        with st.form("register_form", clear_on_submit=False):
            st.text_input("👤 Full Name", placeholder="John Doe", key="reg_fullname")
            st.text_input("🏷️ Username", placeholder="john_doe", key="reg_username")
            st.text_input("📧 Email", placeholder="you@example.com", key="reg_email")
            st.text_input("🔒 Password", placeholder="Min 8 chars, upper+lower+digit+symbol",
                         type="password", key="reg_password")
            st.text_input("🔒 Confirm Password", placeholder="Repeat password", 
                         type="password", key="reg_confirm")
            submitted = st.form_submit_button("Create Account →", use_container_width=True)

        if submitted:
            full_name = st.session_state.reg_fullname
            username = st.session_state.reg_username
            email = st.session_state.reg_email
            password = st.session_state.reg_password
            confirm = st.session_state.reg_confirm
            
            if not all([full_name, username, email, password, confirm]):
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    with st.spinner("Creating your account..."):
                        user = auth.register_user(
                            email=email.strip(),
                            username=username.strip(),
                            password=password,
                            full_name=full_name.strip(),
                        )
                        _, token = auth.login_user(email.strip(), password)
                    st.session_state.auth_user  = user
                    st.session_state.auth_token = token
                    st.success(f"Account created! Welcome, **{user.username}** 🎉")
                    st.rerun()
                except AuthError as e:
                    st.error(str(e))

    # Theme toggle
    st.markdown("")
    dark_label = "☀️ Light Mode" if st.session_state.get("dark_mode", True) else "🌙 Dark Mode"
    if st.button(dark_label, use_container_width=True, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.get("dark_mode", True)
        st.rerun()

    return False

