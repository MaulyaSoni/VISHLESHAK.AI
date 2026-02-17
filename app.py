"""
Vishleshak AI — The Analyser of Your Financial Data
Integrated with Next-Level RAG Intelligence Chatbot
Version: 1.0.0
"""

# ── silence torch before anything else ──────────────────────────────────────
try:
    import torch
except Exception:
    pass

import streamlit as st
import pandas as pd
import os
import uuid
import logging
import warnings

# ── suppress noise ───────────────────────────────────────────────────────────
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*Arrow table.*")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── project imports ───────────────────────────────────────────────────────────
from config import settings
from utils.data_loader import DataLoader
from utils.helpers import handle_error, print_startup_summary, clean_dataframe_display
from analyzers.insight_generator import InsightGenerator
from chatbot.qa_chain import EnhancedQAChain, DataContextManager
from utils.dashboard_visualizer import DashboardVisualizer

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vishleshak AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
defaults = dict(
    data=None,
    analysis_result=None,
    show_visuals=False,
    mode="Analysis",
    qa_chain=None,
    session_id=str(uuid.uuid4()),
    chat_history=[],
    all_sessions=[],          # list of {id, title, history}
    dark_mode=False,
    initialized=False,
)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# THEME TOKENS
# ─────────────────────────────────────────────────────────────────────────────
DARK = dict(
    bg="#0F1117", surface="#1A1D27", surface2="#22263A",
    border="#2D3148", text="#E8EAF6", muted="#8892B0",
    accent="#7C3AED", accent2="#06B6D4",
    card_bg="#1A1D27", card_border="#2D3148",
    user_msg="#1E2235", bot_msg="#1A2744",
    user_border="#4F46E5", bot_border="#06B6D4",
    btn_text="#FFFFFF",
)
LIGHT = dict(
    bg="#F8FAFF", surface="#FFFFFF", surface2="#F1F5FF",
    border="#E2E8F4", text="#1A1A2E", muted="#64748B",
    accent="#4F46E5", accent2="#0891B2",
    card_bg="#FFFFFF", card_border="#E2E8F4",
    user_msg="#F1F5FF", bot_msg="#EFF6FF",
    user_border="#6366F1", bot_border="#0891B2",
    btn_text="#FFFFFF",
)

T = DARK if st.session_state.dark_mode else LIGHT

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── CSS variables (theme tokens) ──────────────────────── */
:root {{
    --bg:         {T['bg']};
    --surface:    {T['surface']};
    --surface2:   {T['surface2']};
    --border:     {T['border']};
    --text:       {T['text']};
    --muted:      {T['muted']};
    --accent:     {T['accent']};
    --accent2:    {T['accent2']};
    --card:       {T['card_bg']};
    --card-b:     {T['card_border']};
    --user-msg:   {T['user_msg']};
    --bot-msg:    {T['bot_msg']};
    --user-b:     {T['user_border']};
    --bot-b:      {T['bot_border']};
    --radius:     0.875rem;
    --shadow:     0 4px 24px rgba(0,0,0,0.12);
    --shadow-lg:  0 8px 40px rgba(0,0,0,0.18);
    --transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}}

/* ── Global reset ─────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}

body, .stApp {{
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', system-ui, sans-serif !important;
}}

/* ── Hide default Streamlit chrome ─────────────────────── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding: 1.5rem 2.5rem 2rem !important;
    max-width: 100% !important;
}}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 1rem;
}}
[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}

/* ── HERO header ───────────────────────────────────────── */
.hero-wrap {{
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    position: relative;
}}
.hero-logo {{
    font-size: 3.6rem;
    filter: drop-shadow(0 0 24px {T['accent']}66);
    animation: pulse-logo 3s ease-in-out infinite;
}}
@keyframes pulse-logo {{
    0%,100% {{ transform: scale(1); filter: drop-shadow(0 0 24px {T['accent']}66); }}
    50%      {{ transform: scale(1.06); filter: drop-shadow(0 0 36px {T['accent']}99); }}
}}
.hero-title {{
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, {T['accent']} 0%, {T['accent2']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.25rem 0 0;
    line-height: 1.1;
}}
.hero-sub {{
    font-size: 1.05rem;
    color: var(--muted);
    margin-top: 0.5rem;
    font-weight: 400;
    letter-spacing: 0.01em;
}}
.hero-badges {{
    display: flex;
    justify-content: center;
    gap: 0.6rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}}
.badge {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 2rem;
    padding: 0.25rem 0.85rem;
    font-size: 0.78rem;
    color: var(--muted);
    font-weight: 500;
    transition: var(--transition);
}}
.badge:hover {{
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-2px);
}}

/* ── Upload zone ───────────────────────────────────────── */
.upload-zone {{
    background: var(--surface);
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2.5rem 2rem;
    text-align: center;
    transition: var(--transition);
    cursor: pointer;
    margin: 1.5rem auto;
    max-width: 680px;
}}
.upload-zone:hover {{
    border-color: var(--accent);
    background: var(--surface2);
    transform: translateY(-3px);
    box-shadow: var(--shadow);
}}
.upload-icon {{ font-size: 3rem; margin-bottom: 0.75rem; }}
.upload-title {{ font-size: 1.15rem; font-weight: 600; color: var(--text); }}
.upload-sub {{ font-size: 0.88rem; color: var(--muted); margin-top: 0.3rem; }}

/* ── Mode selector cards ───────────────────────────────── */
.mode-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    max-width: 680px;
    margin: 1.5rem auto 0;
}}
.mode-card {{
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    cursor: pointer;
    transition: var(--transition);
    text-align: center;
}}
.mode-card:hover {{
    border-color: var(--accent);
    transform: translateY(-4px) scale(1.02);
    box-shadow: var(--shadow);
}}
.mode-card.active {{
    border-color: var(--accent);
    background: var(--surface2);
    box-shadow: 0 0 0 3px {T['accent']}33;
}}
.mode-icon {{ font-size: 2rem; }}
.mode-label {{ font-size: 0.95rem; font-weight: 600; margin-top: 0.4rem; color: var(--text); }}
.mode-desc {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.2rem; }}

/* ── Cards ─────────────────────────────────────────────── */
.vcard {{
    background: var(--card);
    border: 1px solid var(--card-b);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: var(--shadow);
    transition: var(--transition);
}}
.vcard:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-2px); }}
.vcard h3 {{ margin: 0 0 0.75rem; font-size: 1.05rem; font-weight: 600; color: var(--text); }}

.accent-card {{
    background: linear-gradient(135deg, {T['accent']}18 0%, {T['accent2']}18 100%);
    border: 1px solid {T['accent']}44;
    border-radius: var(--radius);
    padding: 1.5rem;
    margin: 1rem 0;
}}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {{
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 0.6rem !important;
    padding: 0.65rem 1.75rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em !important;
    transition: var(--transition) !important;
    box-shadow: 0 2px 12px {T['accent']}44 !important;
    position: relative;
    overflow: hidden;
}}
.stButton > button::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(255,255,255,0);
    transition: var(--transition);
}}
.stButton > button:hover {{
    transform: translateY(-3px) scale(1.03) !important;
    box-shadow: 0 6px 24px {T['accent']}66 !important;
}}
.stButton > button:hover::after {{
    background: rgba(255,255,255,0.08);
}}
.stButton > button:active {{
    transform: translateY(-1px) scale(0.99) !important;
}}

/* Secondary buttons */
[data-testid="baseButton-secondary"] > button,
button[kind="secondary"] {{
    background: var(--surface2) !important;
    color: var(--accent) !important;
    border: 1.5px solid var(--accent) !important;
    box-shadow: none !important;
}}
[data-testid="baseButton-secondary"] > button:hover,
button[kind="secondary"]:hover {{
    background: {T['accent']}18 !important;
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 4px 16px {T['accent']}33 !important;
}}

/* ── Inputs ─────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 0.6rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: var(--transition) !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px {T['accent']}22 !important;
    outline: none !important;
}}

/* ── Chat messages ──────────────────────────────────────── */
.chat-wrap {{
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.5rem 0;
}}
.chat-msg {{
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    line-height: 1.65;
    font-size: 0.95rem;
    animation: slide-up 0.3s ease-out;
    max-width: 88%;
    position: relative;
}}
@keyframes slide-up {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.chat-msg.user {{
    background: var(--user-msg);
    border-left: 3px solid var(--user-b);
    margin-left: auto;
    border-radius: var(--radius) var(--radius) 0.25rem var(--radius);
}}
.chat-msg.bot {{
    background: var(--bot-msg);
    border-left: 3px solid var(--bot-b);
    margin-right: auto;
    border-radius: var(--radius) var(--radius) var(--radius) 0.25rem;
}}
.msg-label {{
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.35rem;
}}
.quality-pill {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 2rem;
    font-size: 0.7rem;
    font-weight: 700;
    margin-left: 0.5rem;
}}
.grade-A {{ background:#10B98122; color:#10B981; border:1px solid #10B98155; }}
.grade-B {{ background:#3B82F622; color:#3B82F6; border:1px solid #3B82F655; }}
.grade-C {{ background:#F59E0B22; color:#F59E0B; border:1px solid #F59E0B55; }}
.grade-D {{ background:#EF444422; color:#EF4444; border:1px solid #EF444455; }}
.grade-F {{ background:#99182222; color:#991822; border:1px solid #99182255; }}

/* ── Loading skeleton ──────────────────────────────────── */
.skeleton {{
    background: linear-gradient(90deg, var(--surface) 25%, var(--surface2) 50%, var(--surface) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 0.4rem;
    height: 1rem;
    margin: 0.4rem 0;
}}
@keyframes shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ── Progress bar ─────────────────────────────────────── */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
    border-radius: 2rem !important;
}}

/* ── Metric ─────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.25rem !important;
    transition: var(--transition) !important;
}}
[data-testid="metric-container"]:hover {{
    border-color: var(--accent) !important;
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}}
[data-testid="metric-container"] label {{
    color: var(--muted) !important;
    font-size: 0.8rem !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: var(--text) !important;
    font-weight: 700 !important;
}}

/* ── Tabs ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: var(--surface) !important;
    border-radius: 0.6rem !important;
    padding: 0.25rem !important;
    gap: 0.25rem !important;
    border: 1px solid var(--border) !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 0.4rem !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: var(--transition) !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.5rem !important;
    margin-top: 0.5rem !important;
}}

/* ── Expander ───────────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0.6rem !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
}}
.streamlit-expanderHeader:hover {{
    border-color: var(--accent) !important;
    background: var(--surface2) !important;
}}
.streamlit-expanderContent {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 0.6rem 0.6rem !important;
}}

/* ── File uploader ──────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    transition: var(--transition) !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: var(--accent) !important;
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}}

/* ── Sidebar chat history items ─────────────────────────── */
.hist-item {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 0.6rem 0.85rem;
    margin: 0.35rem 0;
    font-size: 0.82rem;
    color: var(--text);
    cursor: pointer;
    transition: var(--transition);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.hist-item:hover {{
    border-color: var(--accent);
    background: {T['accent']}18;
    transform: translateX(4px);
}}

/* ── Spinner override ───────────────────────────────────── */
.stSpinner > div {{
    border-top-color: var(--accent) !important;
}}

/* ── Divider ────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}}

/* ── Radio ──────────────────────────────────────────────── */
[data-testid="stRadio"] label {{
    color: var(--text) !important;
}}

/* ── Select box ─────────────────────────────────────────── */
[data-testid="stSelectbox"] > div {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 0.5rem !important;
}}

/* ── Status boxes ───────────────────────────────────────── */
.stSuccess, .stInfo, .stWarning, .stError {{
    border-radius: 0.6rem !important;
}}

/* ── Scrollbar ──────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{
    background: var(--border);
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{ background: var(--accent); }}

/* ── Data frame ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}}

/* ── Sidebar logo area ──────────────────────────────────── */
.sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem 0.5rem 1.25rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}}
.sidebar-brand-icon {{ font-size: 1.6rem; }}
.sidebar-brand-name {{
    font-size: 1.05rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.sidebar-section {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 0.75rem 0 0.35rem;
}}

/* ── Loading animation bar ──────────────────────────────── */
.loading-bar {{
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2), var(--accent));
    background-size: 200% 100%;
    border-radius: 2px;
    animation: loading-sweep 1.5s linear infinite;
    margin: 0.5rem 0;
}}
@keyframes loading-sweep {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ── Welcome feature cards ─────────────────────────────── */
.feat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}}
.feat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    text-align: center;
    transition: var(--transition);
}}
.feat-card:hover {{
    border-color: var(--accent);
    transform: translateY(-5px) scale(1.02);
    box-shadow: var(--shadow-lg);
}}
.feat-icon {{ font-size: 2rem; margin-bottom: 0.5rem; }}
.feat-title {{ font-size: 0.9rem; font-weight: 600; color: var(--text); }}
.feat-desc {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.3rem; }}

/* ── Footer ─────────────────────────────────────────────── */
.app-footer {{
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    color: var(--muted);
    font-size: 0.8rem;
    border-top: 1px solid var(--border);
    margin-top: 3rem;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🔬</span>
        <span class="sidebar-brand-name">Vishleshak AI</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Theme toggle ────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Appearance</div>', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns([2, 3])
    with col_t1:
        st.markdown("**Theme**", help="Switch between dark and light mode")
    with col_t2:
        dark_label = "☀️ Light" if st.session_state.dark_mode else "🌙 Dark"
        if st.button(dark_label, use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    # ── Mode selector ────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Mode</div>', unsafe_allow_html=True)
    mode_choice = st.radio(
        "mode",
        ["📊 Comprehensive Analysis", "💬 RAG Chatbot"],
        label_visibility="collapsed",
        index=0 if st.session_state.mode == "Analysis" else 1,
    )
    st.session_state.mode = "Analysis" if "Analysis" in mode_choice else "Q&A"

    # ── Chat History ─────────────────────────────────────────
    if st.session_state.mode == "Q&A":
        st.markdown('<div class="sidebar-section">Chat History</div>', unsafe_allow_html=True)

        # Save current session if has messages
        if st.session_state.chat_history:
            # Check if already saved
            current_ids = [s["id"] for s in st.session_state.all_sessions]
            if st.session_state.session_id not in current_ids:
                first_msg = next(
                    (m[1][:45] for m in st.session_state.chat_history if m[0] == "user"),
                    "Untitled chat"
                )
                st.session_state.all_sessions.append({
                    "id": st.session_state.session_id,
                    "title": first_msg + "…",
                    "history": st.session_state.chat_history.copy(),
                })

        if st.session_state.all_sessions:
            for i, sess in enumerate(reversed(st.session_state.all_sessions[-8:])):
                short = sess["title"][:40]
                is_current = sess["id"] == st.session_state.session_id
                icon = "💬" if is_current else "🕐"
                st.markdown(
                    f'<div class="hist-item" title="{sess["title"]}">{icon} {short}</div>',
                    unsafe_allow_html=True,
                )

            if st.button("➕ New Chat", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.chat_history = []
                st.session_state.qa_chain = None
                st.rerun()
        else:
            st.markdown(
                '<div style="color:var(--muted);font-size:0.8rem;padding:0.5rem;">No chat history yet.</div>',
                unsafe_allow_html=True,
            )

    # ── Quality metrics (Q&A only) ───────────────────────────
    if st.session_state.mode == "Q&A" and st.session_state.qa_chain:
        st.markdown('<div class="sidebar-section">Session Quality</div>', unsafe_allow_html=True)
        try:
            qm = st.session_state.qa_chain.get_quality_metrics()
            if qm.get("total_cycles", 0) > 0:
                c1, c2 = st.columns(2)
                c1.metric("Responses", qm["total_cycles"])
                avg_q = qm.get("avg_quality_all_time", 0)
                c2.metric("Avg Quality", f"{avg_q:.0f}/100")
                trend = qm.get("trend_direction", "unknown")
                trend_map = {
                    "improving": "📈 Improving",
                    "stable": "➡️ Stable",
                    "declining": "📉 Declining",
                }
                st.caption(f"Trend: {trend_map.get(trend, '⏳ Learning…')}")
        except Exception:
            pass

    # ── System status ────────────────────────────────────────
    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    try:
        from rag.vector_store import get_vector_store
        vs = get_vector_store()
        stats = vs.get_all_stats()
        total_items = sum(s.get("count", 0) for s in stats.values())
        st.markdown(f"<small style='color:var(--muted)'>📚 RAG items: **{total_items}**</small>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<small style='color:var(--muted)'>📚 RAG: Active</small>", unsafe_allow_html=True)

    try:
        from tools import get_tool_registry
        tools = get_tool_registry().get_all_tools()
        st.markdown(f"<small style='color:var(--muted)'>🛠️ Tools: **{len(tools)} ready**</small>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<small style='color:var(--muted)'>🛠️ Tools: Active</small>", unsafe_allow_html=True)

    sess_short = st.session_state.session_id[:8]
    st.markdown(f"<small style='color:var(--muted)'>🔑 Session: `{sess_short}…`</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP  (silent — no progress bar spam on every rerun)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.initialized:
    print_startup_summary(st.session_state.session_id)
    st.session_state.initialized = True


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-logo">🔬</div>
    <div class="hero-title">Vishleshak AI</div>
    <div class="hero-sub">The Analyser of Your Financial Data — Powered by Next-Level RAG Intelligence</div>
    <div class="hero-badges">
        <span class="badge">🧠 Memory</span>
        <span class="badge">🔗 RAG</span>
        <span class="badge">⛓️ Chain-of-Thought</span>
        <span class="badge">📈 Quality Scoring</span>
        <span class="badge">🛠️ Agentic Tools</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA NOT LOADED → WELCOME + UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.data is None:

    # Feature showcase
    st.markdown("""
    <div class="feat-grid">
        <div class="feat-card">
            <div class="feat-icon">📊</div>
            <div class="feat-title">Deep Analysis</div>
            <div class="feat-desc">Statistical insights, pattern detection & AI summaries</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">💬</div>
            <div class="feat-title">RAG Chatbot</div>
            <div class="feat-desc">Data-aware Q&A with knowledge base & tools</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">📈</div>
            <div class="feat-title">Smart Charts</div>
            <div class="feat-desc">Intelligent visualisations chosen for your data</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">🧠</div>
            <div class="feat-title">Memory System</div>
            <div class="feat-desc">LSTM-like multi-tiered conversation memory</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">🎯</div>
            <div class="feat-title">Quality Scoring</div>
            <div class="feat-desc">8-dimension response evaluation & learning</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">⚡</div>
            <div class="feat-title">Agentic Tools</div>
            <div class="feat-desc">Python REPL, calculator, export & more</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload section — centered
    _, ucol, _ = st.columns([1, 2.5, 1])
    with ucol:
        st.markdown("""
        <div class="upload-zone">
            <div class="upload-icon">📂</div>
            <div class="upload-title">Upload Your Dataset</div>
            <div class="upload-sub">CSV · XLSX · XLS &nbsp;•&nbsp; Up to 200 MB</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload file",
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
            help="Supports CSV and Excel files up to 200 MB",
        )

        if uploaded_file:
            with st.spinner("📥 Loading your data…"):
                os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(settings.UPLOAD_FOLDER, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                df, error = DataLoader.load_file(file_path)

            if error:
                st.error(f"❌ {error}")
            else:
                df = DataLoader.clean_dataframe_for_streamlit(df)
                st.session_state.data = df
                st.session_state.qa_chain = None
                st.session_state.analysis_result = None
                st.session_state.show_visuals = False
                st.success(f"✅ Loaded **{len(df):,} rows × {len(df.columns)} columns** from `{uploaded_file.name}`")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADED
# ─────────────────────────────────────────────────────────────────────────────
else:
    df = st.session_state.data

    # ── Data loaded banner ───────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows",     f"{len(df):,}")
    c2.metric("Columns",  len(df.columns))
    num_count = len(df.select_dtypes(include="number").columns)
    cat_count = len(df.select_dtypes(include=["object","category"]).columns)
    c3.metric("Numeric",  num_count)
    c4.metric("Categorical", cat_count)
    missing_pct = round(df.isnull().sum().sum() / max(1, df.shape[0]*df.shape[1]) * 100, 1)
    c5.metric("Missing %", f"{missing_pct}%")

    # Upload new file (inline, small)
    with st.expander("📂 Upload a different file"):
        new_file = st.file_uploader("Replace dataset", type=["csv","xlsx","xls"], label_visibility="collapsed")
        if new_file:
            os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
            fp = os.path.join(settings.UPLOAD_FOLDER, new_file.name)
            with open(fp, "wb") as f:
                f.write(new_file.getbuffer())
            df2, err = DataLoader.load_file(fp)
            if err:
                st.error(err)
            else:
                st.session_state.data = DataLoader.clean_dataframe_for_streamlit(df2)
                st.session_state.qa_chain = None
                st.session_state.analysis_result = None
                st.session_state.show_visuals = False
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # ANALYSIS MODE
    # ════════════════════════════════════════════════════════
    if st.session_state.mode == "Analysis":

        st.markdown("## 📊 Comprehensive Analysis")

        with st.expander("👁️ Preview Data", expanded=False):
            clean_dataframe_display(df)

        # ── Buttons ──────────────────────────────────────────
        if st.session_state.analysis_result is None:
            if st.button("🚀 Analyse Data", type="primary", use_container_width=False):
                prog = st.progress(0, text="🔄 Initialising analysis engine…")
                try:
                    prog.progress(20, text="📐 Computing statistics…")
                    generator = InsightGenerator(df)
                    prog.progress(55, text="🤖 Generating AI insights…")
                    result = generator.generate_comprehensive_insights()
                    prog.progress(90, text="✅ Finalising…")
                    st.session_state.analysis_result = result
                    st.session_state.show_visuals = False
                    prog.progress(100, text="✅ Analysis complete!")
                    import time; time.sleep(0.4)
                    prog.empty()
                    st.rerun()
                except Exception as e:
                    prog.empty()
                    handle_error(e, "Data Analysis")
        else:
            btn1, btn2, btn3 = st.columns([2, 2, 6])
            with btn1:
                if st.button("🔄 Re-Analyse", use_container_width=True):
                    prog = st.progress(0, text="🔄 Re-running…")
                    try:
                        prog.progress(30, text="📐 Computing…")
                        generator = InsightGenerator(df)
                        prog.progress(65, text="🤖 AI thinking…")
                        result = generator.generate_comprehensive_insights()
                        prog.progress(100, text="✅ Done!")
                        st.session_state.analysis_result = result
                        st.session_state.show_visuals = False
                        import time; time.sleep(0.3)
                        prog.empty()
                        st.rerun()
                    except Exception as e:
                        prog.empty()
                        handle_error(e, "Re-Analysis")
            with btn2:
                vis_label = "🙈 Hide Charts" if st.session_state.show_visuals else "📊 Generate Visuals"
                if st.button(vis_label, use_container_width=True):
                    st.session_state.show_visuals = not st.session_state.show_visuals
                    st.rerun()

        # ── Results ──────────────────────────────────────────
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result

            st.markdown(f"""
            <div class="accent-card">
                <h3 style="margin:0 0 0.5rem;font-size:1rem;">📋 Executive Summary</h3>
                <p style="margin:0;line-height:1.7;color:var(--text);">{result.get('executive_summary','No summary generated.')}</p>
            </div>
            """, unsafe_allow_html=True)

            # ── Visualisations ───────────────────────────────
            if st.session_state.show_visuals:
                st.markdown("## 📈 Interactive Analytics Dashboard")
                st.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)

                try:
                    dashboard = DashboardVisualizer(df)
                    with st.spinner("🎨 Building intelligent visualisations…"):
                        named_charts = dashboard.create_overview_dashboard()

                    if not named_charts:
                        st.info("📊 No charts generated — dataset may lack numeric/categorical columns.")
                    else:
                        # Group into tab categories
                        cat_map = {
                            "🔍 Quality":       [],
                            "📊 Distributions": [],
                            "🔗 Correlations":  [],
                            "🏷️ Categories":    [],
                            "📦 Comparisons":   [],
                            "📈 Trends":        [],
                            "🔭 Advanced":      [],
                        }
                        for label, fig in named_charts:
                            if any(k in label for k in ["Completeness","Quality","🔍"]):
                                cat_map["🔍 Quality"].append((label, fig))
                            elif any(k in label for k in ["Distribution","📊"]):
                                cat_map["📊 Distributions"].append((label, fig))
                            elif any(k in label for k in ["Correlation","↔️","🔗"]):
                                cat_map["🔗 Correlations"].append((label, fig))
                            elif any(k in label for k in ["Categories","🏷️","Breakdown"]):
                                cat_map["🏷️ Categories"].append((label, fig))
                            elif any(k in label for k in ["Box","📦","Mean","Comparison","Violin"]):
                                cat_map["📦 Comparisons"].append((label, fig))
                            elif any(k in label for k in ["Time","📈","Series","Trend"]):
                                cat_map["📈 Trends"].append((label, fig))
                            else:
                                cat_map["🔭 Advanced"].append((label, fig))

                        active = {k: v for k, v in cat_map.items() if v}
                        tab_objs = st.tabs(list(active.keys()))
                        for tab_obj, (tab_name, tab_charts) in zip(tab_objs, active.items()):
                            with tab_obj:
                                for label, fig in tab_charts:
                                    st.markdown(f"#### {label}")
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.markdown("")

                        st.caption(f"ℹ️ {len(named_charts)} intelligent charts generated. "
                                   "Use the 📷 icon on any chart to save as PNG.")
                except Exception as e:
                    st.error(f"❌ Dashboard error: {e}")
                    logger.error(f"Dashboard error: {e}", exc_info=True)

            # ── Detailed analysis tabs ───────────────────────
            st.markdown("## 🔍 Detailed Analysis")
            tab1, tab2, tab3 = st.tabs(["💡 AI Insights", "📊 Statistics", "🔍 Patterns"])

            with tab1:
                st.markdown(result.get("ai_insights", "No insights generated."))

            with tab2:
                stats = result.get("statistical_analysis", {})
                if stats:
                    basic = stats.get("basic_info", {})
                    if basic:
                        b1, b2, b3, b4 = st.columns(4)
                        b1.metric("Rows", f"{basic.get('total_rows',0):,}")
                        b2.metric("Columns", basic.get("total_columns", 0))
                        b3.metric("Numeric", basic.get("numeric_columns", 0))
                        b4.metric("Categorical", basic.get("categorical_columns", 0))
                    num_analysis = stats.get("numeric_analysis", {})
                    if num_analysis:
                        st.markdown("#### Numeric Summary")
                        try:
                            st.dataframe(
                                pd.DataFrame(num_analysis).T.round(3),
                                use_container_width=True
                            )
                        except Exception:
                            st.json(num_analysis)

            with tab3:
                patterns = result.get("pattern_analysis", {})
                if patterns:
                    for p_type, p_list in patterns.items():
                        if p_list:
                            st.subheader(p_type.replace("_", " ").title())
                            for p in p_list:
                                st.markdown(f"- {p.get('interpretation', str(p))}")
                else:
                    st.info("No patterns detected.")

    # ════════════════════════════════════════════════════════
    # Q&A / RAG CHATBOT MODE
    # ════════════════════════════════════════════════════════
    else:
        st.markdown("## 💬 Vishleshak RAG Assistant")

        # ── Initialise QA chain ──────────────────────────────
        if st.session_state.qa_chain is None:
            init_placeholder = st.empty()
            with init_placeholder.container():
                prog = st.progress(0)
                steps = [
                    (25,  "🔗 Connecting to knowledge base…"),
                    (50,  "🛠️ Loading agentic tools…"),
                    (75,  "🧠 Warming up AI reasoning engine…"),
                    (95,  "🎯 Calibrating quality scorer…"),
                    (100, "✅ Vishleshak AI is ready!"),
                ]
                status_txt = st.empty()
                import time
                for pct, msg in steps:
                    prog.progress(pct, text=msg)
                    status_txt.markdown(
                        f"<div class='loading-bar'></div>"
                        f"<small style='color:var(--muted)'>{msg}</small>",
                        unsafe_allow_html=True,
                    )
                    time.sleep(0.25)

                try:
                    st.session_state.qa_chain = EnhancedQAChain(
                        df=df,
                        session_id=st.session_state.session_id,
                    )
                    prog.progress(100, text="✅ All systems operational!")
                    time.sleep(0.4)
                    init_placeholder.empty()
                except Exception as e:
                    prog.empty()
                    status_txt.empty()
                    st.error(f"❌ Initialisation failed: {e}")
                    logger.error(f"QA init error: {e}", exc_info=True)

        # ── Chat history display ──────────────────────────────
        st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
        for idx, msg in enumerate(st.session_state.chat_history):
            role    = msg[0]
            content = msg[1]
            meta    = msg[2] if len(msg) > 2 else None

            if role == "user":
                st.markdown(f"""
                <div class="chat-msg user">
                    <div class="msg-label">👤 You</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                grade     = meta.get("quality_grade","") if meta else ""
                score     = meta.get("quality_score", 0) if meta else 0
                grade_cls = f"grade-{grade}" if grade else ""
                pill      = (f'<span class="quality-pill {grade_cls}">Grade {grade} · {score:.0f}/100</span>'
                             if grade else "")

                st.markdown(f"""
                <div class="chat-msg bot">
                    <div class="msg-label">🔬 Vishleshak AI {pill}</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)

                # Feedback buttons
                if meta and "quality_score" in meta:
                    message_id = meta.get("message_id", idx)
                    fb1, fb2, fb3 = st.columns([1, 1, 10])
                    with fb1:
                        if st.button("👍", key=f"up_{idx}", help="Good response"):
                            try:
                                st.session_state.qa_chain.provide_feedback("thumbs_up", message_id=message_id)
                                st.toast("Thanks for the positive feedback! 🎉")
                            except Exception:
                                pass
                    with fb2:
                        if st.button("👎", key=f"dn_{idx}", help="Needs improvement"):
                            try:
                                st.session_state.qa_chain.provide_feedback("thumbs_down", message_id=message_id)
                                st.toast("Noted — I'll improve! 📝")
                            except Exception:
                                pass

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Empty state ───────────────────────────────────────
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="accent-card" style="text-align:center;padding:2rem;">
                <div style="font-size:2.5rem;margin-bottom:0.75rem;">💬</div>
                <div style="font-size:1.05rem;font-weight:600;margin-bottom:0.5rem;">Start a Conversation</div>
                <div style="color:var(--muted);font-size:0.9rem;">
                    Ask anything about your data — trends, patterns, comparisons, predictions.
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Quick-start suggestions
            st.markdown("**💡 Try asking:**")
            suggestions = [
                "📈 Analyse the overall trends in this dataset",
                "🔍 What are the key patterns and anomalies?",
                "📊 Give me a statistical summary",
                "🎯 What insights can you generate from this data?",
                "⚠️ Which columns have data quality issues?",
                "🔗 What correlations exist between variables?",
            ]
            cols = st.columns(3)
            for i, sug in enumerate(suggestions):
                with cols[i % 3]:
                    if st.button(sug, use_container_width=True, key=f"sug_{i}"):
                        st.session_state._quick_question = sug
                        st.rerun()

        # ── Handle quick question ─────────────────────────────
        quick_q = getattr(st.session_state, "_quick_question", None)
        if quick_q:
            del st.session_state._quick_question
            user_input = quick_q
            process_question = True
        else:
            # ── Input form ────────────────────────────────────
            with st.form(key="chat_form", clear_on_submit=True):
                icol1, icol2 = st.columns([7, 1])
                with icol1:
                    user_input = st.text_input(
                        "message",
                        placeholder="Ask anything about your data…",
                        label_visibility="collapsed",
                    )
                with icol2:
                    process_question = st.form_submit_button(
                        "Send 🚀", type="primary", use_container_width=True
                    )

        # ── Process question ──────────────────────────────────
        if process_question and user_input and st.session_state.qa_chain:
            st.session_state.chat_history.append(("user", user_input))

            prog2 = st.progress(0, text="🔍 Understanding your question…")
            try:
                import time
                prog2.progress(20, text="📚 Searching knowledge base…")
                time.sleep(0.15)
                prog2.progress(45, text="🧠 Reasoning through the data…")
                time.sleep(0.15)
                prog2.progress(70, text="✍️ Composing answer…")

                result = st.session_state.qa_chain.ask(user_input, return_dict=True)

                prog2.progress(90, text="📊 Evaluating quality…")
                time.sleep(0.1)

                response    = result["formatted_response"]
                quality_obj = result["quality_score"]
                msg_id      = result.get("cycle_number", len(st.session_state.chat_history))
                grade       = quality_obj.get_grade()
                score       = quality_obj.overall_score

                prog2.progress(100, text=f"✅ Done — Grade {grade} ({score:.0f}/100)")
                time.sleep(0.3)
                prog2.empty()

                st.session_state.chat_history.append((
                    "bot",
                    response,
                    {"quality_score": score, "quality_grade": grade, "message_id": msg_id},
                ))
                st.rerun()

            except Exception as e:
                prog2.empty()
                handle_error(e, "Question Processing")

        # ── Debug expander ────────────────────────────────────
        with st.expander("🕵️ Debug: Retrieved RAG Context"):
            if st.session_state.qa_chain and hasattr(st.session_state.qa_chain, "last_context"):
                st.write(st.session_state.qa_chain.last_context)
            else:
                st.info("Ask a question to see the retrieved RAG context.")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    🔬 <strong>Vishleshak AI v1.0</strong> &nbsp;·&nbsp;
    Memory ✓ &nbsp;·&nbsp; Reasoning ✓ &nbsp;·&nbsp; Learning ✓ &nbsp;·&nbsp; RAG ✓
    &nbsp;·&nbsp; Built with ♥ using LangChain · ChromaDB · Groq LLaMA
</div>
""", unsafe_allow_html=True)