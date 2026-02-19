"""
Authentication UI — Login / Register page for Vishleshak AI
Matches the existing dark/light theme system.
"""

import streamlit as st


def _get_theme():
    dark_mode = st.session_state.get("dark_mode", True)
    if dark_mode:
        return dict(
            bg="#0F1117", surface="#1A1D27", surface2="#22263A",
            border="#2D3148", text="#E8EAF6", muted="#8892B0",
            accent="#7C3AED", accent2="#06B6D4",
        )
    return dict(
        bg="#F8FAFF", surface="#FFFFFF", surface2="#F1F5FF",
        border="#E2E8F4", text="#1A1A2E", muted="#64748B",
        accent="#4F46E5", accent2="#0891B2",
    )


def _auth_css() -> None:
    T = _get_theme()
    st.markdown(f"""
    <style>
    .auth-container {{
        max-width: 460px;
        margin: 2rem auto;
        background: {T['surface']};
        border: 1px solid {T['border']};
        border-radius: 1.25rem;
        padding: 2.5rem 2.5rem 2rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.18);
    }}
    .auth-logo {{
        text-align: center;
        font-size: 3rem;
        margin-bottom: 0.25rem;
        filter: drop-shadow(0 0 20px {T['accent']}88);
    }}
    .auth-title {{
        text-align: center;
        font-size: 1.7rem;
        font-weight: 700;
        background: linear-gradient(135deg, {T['accent']}, {T['accent2']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }}
    .auth-subtitle {{
        text-align: center;
        color: {T['muted']};
        font-size: 0.88rem;
        margin-bottom: 1.75rem;
    }}
    .auth-divider {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1.5rem 0;
        color: {T['muted']};
        font-size: 0.82rem;
    }}
    .auth-divider::before, .auth-divider::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: {T['border']};
    }}
    .auth-tab-active {{
        border-bottom: 2px solid {T['accent']};
        color: {T['accent']};
        font-weight: 600;
    }}
    .auth-welcome {{
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, {T['accent']}18, {T['accent2']}18);
        border: 1px solid {T['accent']}44;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
    }}
    </style>
    """, unsafe_allow_html=True)


def show_auth_page() -> bool:
    """
    Render the login / register page.

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
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
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
                         type="primary" if st.session_state.auth_tab == "Login" else "secondary"):
                st.session_state.auth_tab = "Login"
                st.rerun()
        with col_reg:
            if st.button("📝 Register", use_container_width=True,
                         type="primary" if st.session_state.auth_tab == "Register" else "secondary"):
                st.session_state.auth_tab = "Register"
                st.rerun()

        st.markdown("---")

        auth = AuthManager()

        # ── LOGIN FORM ──────────────────────────────────────────────────────
        if st.session_state.auth_tab == "Login":
            with st.form("login_form", clear_on_submit=False):
                email    = st.text_input("📧 Email",    placeholder="you@example.com")
                password = st.text_input("🔒 Password", placeholder="Your password", type="password")
                submitted = st.form_submit_button("Login →", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        with st.spinner("Verifying…"):
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
                full_name = st.text_input("👤 Full Name",  placeholder="John Doe")
                username  = st.text_input("🏷️ Username",   placeholder="john_doe")
                email     = st.text_input("📧 Email",      placeholder="you@example.com")
                password  = st.text_input("🔒 Password",   placeholder="Min 8 chars, upper+lower+digit+symbol",
                                          type="password")
                confirm   = st.text_input("🔒 Confirm",    placeholder="Repeat password", type="password")
                submitted = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted:
                if not all([full_name, username, email, password, confirm]):
                    st.error("Please fill in all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        with st.spinner("Creating account…"):
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

        st.markdown("")
        # theme toggle on auth page
        dark_label = "☀️ Light Mode" if st.session_state.get("dark_mode", True) else "🌙 Dark Mode"
        if st.button(dark_label, use_container_width=True):
            st.session_state.dark_mode = not st.session_state.get("dark_mode", True)
            st.rerun()

    return False
