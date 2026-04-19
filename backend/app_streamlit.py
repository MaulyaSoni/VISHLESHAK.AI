"""
Vishleshak AI — The Analyser of Your Financial Data
Integrated with Next-Level RAG Intelligence Chatbot
Version: 1.0.0
"""

# Ensure legacy app modules are importable (config/, utils/, tools/, etc.)
import sys
from pathlib import Path
_backend_dir = Path(__file__).resolve().parent
_app_modules_dir = _backend_dir / "app_modules"
if _app_modules_dir.exists():
    sys.path.insert(0, str(_app_modules_dir))

# ── load .env FIRST before anything else ────────────────────────────────────
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    # Repo root (where .env typically lives)
    _project_root = Path(__file__).resolve().parent.parent
    load_dotenv(_project_root / ".env", override=True)
    
    # Langsmith explicit observability check
    if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
        os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "Vishleshak_AI")
except Exception:
    pass  # Streamlit Cloud: secrets come from st.secrets, .env not needed

# ── Streamlit Cloud: push st.secrets into os.environ ────────────────────────
try:
    import streamlit as _st
    for _k, _v in _st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

# ── silence torch before anything else ──────────────────────────────────────
try:
    import torch
except Exception:
    pass

import streamlit as st
import pandas as pd
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

# ── auth & persistence imports ─────────────────────────────────────────────────
try:
    from database.db_manager import init_database
    from ui.auth_ui import show_auth_page
    from ui.chat_history_ui import render_chat_history_sidebar
    from ui.user_settings_ui import render_user_settings
    from ui.claude_loaders import show_claude_loader
    from database.chat_repository import ChatRepository
    AUTH_AVAILABLE = True
    init_database()
except Exception as _auth_err:
    AUTH_AVAILABLE = False
    logger.warning(f"Auth system not available: {_auth_err}")

# ── agentic imports ────────────────────────────────────────────────────────────
AGENTIC_AVAILABLE = False
SUPERVISOR_AVAILABLE = False

try:
    from agentic_core import create_vishleshak_agent
    AGENTIC_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Agentic features not available: {e}")

try:
    from agentic_core.supervisor_graph import invoke_supervisor, get_supervisor_graph
    from agentic_core.proactive_engine import ProactiveEngine
    from tools.specialized import (
        StatisticalAnalyzerTool,
        CorrelationFinderTool,
        AnomalyDetectorTool,
        ChartGeneratorTool,
        TrendAnalyzerTool,
        ForecasterTool,
        PythonSandboxTool,
        ReportGeneratorTool,
    )
    SUPERVISOR_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ Supervisor graph not available: {e}")
    SUPERVISOR_AVAILABLE = False

# Use supervisor if available, otherwise fall back to AGENTIC
AGENTIC_AVAILABLE = AGENTIC_AVAILABLE or SUPERVISOR_AVAILABLE

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
    agent=None,
    use_agent_mode=False,
    show_agent_thinking=True,
    session_id=str(uuid.uuid4()),
    chat_history=[],
    all_sessions=[],          # list of {id, title, history}
    dark_mode=True,           # Enable dark mode by default for Claude theme
    initialized=False,
    generating_visuals=False,  # NEW: track visual generation state
    charts_cache=None,         # NEW: cache generated charts
    # auth
    auth_user=None,
    auth_token=None,
    current_conv_id=None,
    show_settings=False,
    # Data Agent
    agent_status="idle",
    agent_report=None,
    agent_steps=[],
    agent_error=None,
)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE  — show login page if not authenticated
# ─────────────────────────────────────────────────────────────────────────────
if AUTH_AVAILABLE and st.session_state.auth_user is None:
    authenticated = show_auth_page()
    if not authenticated:
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# THEME TOKENS — Claude-inspired professional colors for light/dark modes
# ─────────────────────────────────────────────────────────────────────────────
DARK = dict(
    bg="#0D0F1C",           # Deep midnight
    surface="#161B2E",      # Elevated surface
    surface2="#1F2638",     # Secondary surface
    border="#2D3548",       # Subtle borders
    text="#F8FAFC",         # High contrast text
    muted="#94A3B8",        # Muted text
    accent="#6366F1",       # Indigo - primary accent
    accent2="#06B6D4",      # Cyan - secondary accent
    accent3="#10B981",      # Green - success/tertiary
    card_bg="#161B2E",      
    card_border="#2D3548",
    user_msg="#1E2638",     # User message background
    bot_msg="#1A1F2E",      # Bot message background
    user_border="#6366F1",  # Indigo border for user
    bot_border="#10B981",   # Green border for bot
    btn_text="#FFFFFF",
    gradient_accent="linear-gradient(135deg, #6366F1, #06B6D4)",
    gradient_title="linear-gradient(135deg, #6366F1 0%, #06B6D4 50%, #10B981 100%)",
)
LIGHT = dict(
    bg="#FFFFFF",           # Pure white
    surface="#F8FAFC",      # Elevated surface
    surface2="#F1F5F9",     # Secondary surface
    border="#E2E8F0",       # Subtle borders
    text="#0F172A",         # High contrast text
    muted="#475569",        # Muted text
    accent="#4F46E5",       # Deeper indigo - primary
    accent2="#0891B2",      # Deeper cyan - secondary
    accent3="#059669",      # Deeper green - success
    card_bg="#F8FAFC",
    card_border="#E2E8F0",
    user_msg="#EEF2FF",     # Light indigo tint
    bot_msg="#ECFDF5",      # Light green tint
    user_border="#4F46E5",  # Indigo border
    bot_border="#059669",   # Green border
    btn_text="#FFFFFF",
    gradient_accent="linear-gradient(135deg, #4F46E5, #0891B2)",
    gradient_title="linear-gradient(135deg, #4F46E5 0%, #0891B2 50%, #059669 100%)",
)

T = DARK if st.session_state.dark_mode else LIGHT

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Claude-inspired design with Space Grotesk & Inter
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

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
    --accent3:    {T['accent3']};
    --card:       {T['card_bg']};
    --card-b:     {T['card_border']};
    --user-msg:   {T['user_msg']};
    --bot-msg:    {T['bot_msg']};
    --user-b:     {T['user_border']};
    --bot-b:      {T['bot_border']};
    --radius:     1rem;
    --radius-lg:  1.5rem;
    --shadow:     0 10px 40px rgba(0,0,0,0.15);
    --shadow-lg:  0 20px 60px rgba(0,0,0,0.25);
    --transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    
    /* Gradients */
    --gradient-accent: {T['gradient_accent']};
    --gradient-title:  {T['gradient_title']};
}}

/* ── Global reset ─────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}

body, .stApp {{
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}}

/* ── Hide default Streamlit chrome ─────────────────────── */
#MainMenu, footer {{ visibility: hidden; }}

/* ── Header: blend with background ────────────────────────── */
header[data-testid="stHeader"] {{
    background: {T['bg']} !important;
    border: none !important;
}}

/* Hide specific chrome — do NOT hide stToolbar (contains sidebar toggle in 1.54+) */
[data-testid="stDecoration"]          {{ display: none !important; }}
[data-testid="stStatusWidget"]        {{ display: none !important; }}
/* Hide only the Deploy/Share buttons inside the toolbar, not the whole toolbar */
[data-testid="stToolbar"] [data-testid="stToolbarActionButton"] {{ display: none !important; }}
[data-testid="stAppDeployButton"]     {{ display: none !important; }}
button[title="Deploy this app"]       {{ display: none !important; }}
button[title="Manage app"]            {{ display: none !important; }}

/* ── Sidebar toggle: cover ALL known Streamlit versions ──── */
/* Streamlit <1.33 */
[data-testid="stSidebarCollapsedControl"],
/* Streamlit 1.33+ */
[data-testid="collapsedControl"],
/* Generic fallback */
button[aria-label="Open sidebar navigation menu"],
button[aria-label="Expand sidebar"] {{
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    pointer-events: all !important;
    z-index: 999999 !important;
}}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {{
    background: {T['surface']} !important;
    border: 2px solid {T['accent']} !important;
    color: {T['accent']} !important;
    cursor: pointer !important;
}}

/* ── Sidebar close/collapse button ───────────────────────── */
[data-testid="stSidebarCollapseButton"],
button[aria-label="Collapse sidebar"],
button[aria-label="Close sidebar navigation menu"] {{
    visibility: visible !important;
    display: flex !important;
    pointer-events: all !important;
    opacity: 1 !important;
}}

.block-container {{
    padding: 1.5rem 2.5rem 2rem !important;
    max-width: 100% !important;
}}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 3px solid var(--border) !important;
    padding-top: 1rem;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
}}
[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    font-size: 1.1rem !important;
}}

/* ── HERO header ───────────────────────────────────────── */
.hero-wrap {{
    text-align: center;
    padding: 3rem 1rem 2rem;
    position: relative;
}}
.hero-logo {{
    font-size: 4.5rem;
    filter: drop-shadow(0 0 30px var(--accent)) drop-shadow(0 0 60px var(--accent2));
    animation: pulse-logo 4s ease-in-out infinite;
}}
@keyframes pulse-logo {{
    0%,100% {{ transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 30px var(--accent)); }}
    50%      {{ transform: scale(1.08) rotate(2deg); filter: drop-shadow(0 0 50px var(--accent2)); }}
}}
.hero-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    background: var(--gradient-title);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 5s ease infinite, title-glow 3s ease-in-out infinite;
    margin: 0.5rem 0 0;
    line-height: 1.05;
    text-shadow: 0 0 40px var(--accent);
}}
@keyframes gradient-shift {{
    0%, 100% {{ background-position: 0% center; }}
    50% {{ background-position: 100% center; }}
}}
@keyframes title-glow {{
    0%, 100% {{ filter: drop-shadow(0 0 20px var(--accent)) brightness(1); }}
    50% {{ filter: drop-shadow(0 0 40px var(--accent2)) brightness(1.2); }}
}}
.hero-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    color: var(--muted);
    margin-top: 0.75rem;
    font-weight: 400;
    letter-spacing: 0.02em;
}}
.hero-badges {{
    display: flex;
    justify-content: center;
    gap: 0.8rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}}
.badge {{
    background: var(--surface2);
    border: 2px solid var(--border);
    border-radius: 2rem;
    padding: 0.4rem 1rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.85rem;
    color: var(--text);
    font-weight: 600;
    transition: var(--transition);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}
.badge:hover {{
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-3px) scale(1.05);
    box-shadow: 0 8px 25px var(--accent);
}}

/* ── Upload zone ───────────────────────────────────────── */
.upload-zone {{
    background: var(--surface);
    border: 3px dashed var(--border);
    border-radius: var(--radius-lg);
    padding: 3.5rem 2.5rem;
    text-align: center;
    transition: var(--transition);
    cursor: pointer;
    margin: 2rem auto;
    max-width: 700px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow);
}}
.upload-zone::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: var(--gradient-accent);
    opacity: 0;
    transition: var(--transition);
    animation: rotate-bg 20s linear infinite;
}}
.upload-zone:hover {{
    border-color: var(--accent);
    background: var(--surface2);
    transform: translateY(-5px) scale(1.02);
    box-shadow: var(--shadow-lg);
}}
.upload-zone:hover::before {{
    opacity: 0.08;
}}
.upload-icon {{ 
    font-size: 4.5rem; 
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 20px var(--accent));
    animation: float 3s ease-in-out infinite;
}}
@keyframes float {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-10px); }}
}}
.upload-title {{ 
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem; 
    font-weight: 800; 
    color: var(--text);
    background: var(--gradient-accent);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}}
.upload-sub {{ 
    font-family: 'Inter', sans-serif;
    font-size: 1rem; 
    color: var(--muted); 
    margin-top: 0.5rem;
}}

/* ── Mode selector cards ───────────────────────────────── */
.mode-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    max-width: 700px;
    margin: 2rem auto 0;
}}
.mode-card {{
    background: var(--surface);
    border: 3px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 2rem 2rem;
    cursor: pointer;
    transition: var(--transition);
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow);
}}
.mode-card::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: var(--gradient-accent);
    opacity: 0;
    transition: var(--transition);
}}
.mode-card:hover {{
    border-color: var(--accent);
    transform: translateY(-6px) scale(1.04);
    box-shadow: var(--shadow-lg);
}}
.mode-card:hover::before {{
    opacity: 0.1;
}}
.mode-card.active {{
    border-color: var(--accent);
    background: var(--gradient-accent);
    color: #FFFFFF;
    box-shadow: 0 0 0 4px var(--accent), var(--shadow-lg);
}}
.mode-card.active .mode-label,
.mode-card.active .mode-desc {{
    color: #FFFFFF;
}}
.mode-icon {{ 
    font-size: 3rem;
    filter: drop-shadow(0 0 15px var(--accent));
    margin-bottom: 0.75rem;
}}
.mode-label {{ 
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem; 
    font-weight: 700; 
    margin-top: 0.75rem; 
    color: var(--text);
}}
.mode-desc {{ 
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem; 
    color: var(--muted); 
    margin-top: 0.5rem;
}}

/* ── Cards ─────────────────────────────────────────────── */
.vcard {{
    background: var(--card);
    border: 2px solid var(--card-b);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: var(--shadow);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}}
.vcard::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--gradient-accent);
    transform: scaleY(0);
    transition: var(--transition);
}}
.vcard:hover {{ 
    box-shadow: var(--shadow-lg); 
    transform: translateY(-4px);
    border-color: var(--accent);
}}
.vcard:hover::before {{
    transform: scaleY(1);
}}
.vcard h3 {{ 
    margin: 0 0 1rem; 
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem; 
    font-weight: 700; 
    background: var(--gradient-accent);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.accent-card {{
    background: var(--gradient-accent);
    border: 3px solid var(--accent);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin: 1.5rem 0;
    color: #FFFFFF;
    box-shadow: 0 10px 40px var(--accent);
    position: relative;
    overflow: hidden;
}}
.accent-card::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
    animation: shine 3s ease-in-out infinite;
}}
@keyframes shine {{
    0%, 100% {{ transform: translateX(-100%); }}
    50% {{ transform: translateX(100%); }}
}}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {{
    background: var(--gradient-accent) !important;
    color: var(--btn-text) !important;
    border: none !important;
    border-radius: 1.5rem !important;
    padding: 0.85rem 2rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    letter-spacing: 0.02em !important;
    transition: var(--transition) !important;
    box-shadow: 0 8px 30px var(--accent) !important;
    position: relative;
    overflow: hidden;
    text-transform: none !important;
}}
.stButton > button::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0));
    opacity: 0;
    transition: var(--transition);
}}
.stButton > button:hover {{
    transform: translateY(-4px) scale(1.05) !important;
    box-shadow: 0 12px 45px var(--accent) !important;
}}
.stButton > button:hover::before {{
    opacity: 1;
}}
.stButton > button:active {{
    transform: translateY(-2px) scale(1.02) !important;
}}

/* Secondary buttons */
[data-testid="baseButton-secondary"] > button,
button[kind="secondary"] {{
    background: transparent !important;
    color: var(--accent) !important;
    border: 2px solid var(--accent) !important;
    box-shadow: 0 4px 15px var(--accent) !important;
    font-size: 1.1rem !important;
}}
[data-testid="baseButton-secondary"] > button:hover,
button[kind="secondary"]:hover {{
    background: var(--accent) !important;
    color: var(--btn-text) !important;
    transform: translateY(-3px) scale(1.04) !important;
    box-shadow: 0 8px 30px var(--accent) !important;
}}

/* ── Inputs ─────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
    border-radius: 1rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.85rem 1.2rem !important;
    transition: var(--transition) !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px var(--accent) !important;
    outline: none !important;
    transform: scale(1.02);
}}

/* ── Chat messages ──────────────────────────────────────── */
.chat-wrap {{
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 0;
}}
.chat-msg {{
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    line-height: 1.7;
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    animation: slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    max-width: 85%;
    position: relative;
    box-shadow: var(--shadow);
}}
@keyframes slide-up {{
    from {{ opacity: 0; transform: translateY(20px) scale(0.95); }}
    to   {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.chat-msg.user {{
    background: var(--user-msg);
    border-left: 4px solid var(--user-b);
    margin-left: auto;
    border-radius: var(--radius-lg) var(--radius-lg) 0.5rem var(--radius-lg);
    box-shadow: 0 8px 25px var(--user-b);
}}
.chat-msg.bot {{
    background: var(--bot-msg);
    border-left: 4px solid var(--bot-b);
    margin-right: auto;
    border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 0.5rem;
    box-shadow: 0 8px 25px var(--bot-b);
}}
.msg-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.msg-icon {{
    font-size: 1.15rem;
    line-height: 1;
    flex-shrink: 0;
}}
.quality-pill {{
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 2rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    margin-left: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}}
.grade-A {{ background:#10B98133; color:#10B981; border:2px solid #10B981; }}
.grade-B {{ background:#3B82F633; color:#3B82F6; border:2px solid #3B82F6; }}
.grade-C {{ background:#F59E0B33; color:#F59E0B; border:2px solid #F59E0B; }}
.grade-D {{ background:#EF444433; color:#EF4444; border:2px solid #EF4444; }}
.grade-F {{ background:#99182233; color:#991822; border:2px solid #991822; }}

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
.sidebar-section {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    padding: 0.75rem 0;
    margin-top: 1rem;
    border-bottom: 2px solid var(--accent);
    background: var(--gradient-accent);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hist-item {{
    background: var(--surface2);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    color: var(--text);
    cursor: pointer;
    transition: var(--transition);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}
.hist-item:hover {{
    border-color: var(--accent);
    background: var(--accent);
    color: var(--btn-text);
    transform: translateX(6px) scale(1.03);
    box-shadow: 0 6px 20px var(--accent);
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

/* ── Agent reasoning styles ─────────────────────────────── */
.agent-step {{
    background: var(--surface);
    border-left: 3px solid var(--accent);
    padding: 0.75rem;
    margin: 0.5rem 0;
    border-radius: 0.4rem;
    transition: var(--transition);
}}
.agent-step:hover {{
    background: var(--surface2);
    transform: translateX(3px);
}}
.agent-thought {{
    color: var(--text);
    font-weight: 500;
    margin-bottom: 0.4rem;
}}
.agent-action {{
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
}}
.agent-observation {{
    color: var(--muted);
    font-size: 0.85rem;
    line-height: 1.5;
    margin-top: 0.4rem;
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
    # Brand + user info
    user_label = ""
    if AUTH_AVAILABLE and st.session_state.auth_user:
        u = st.session_state.auth_user
        user_label = f"<span style='font-size:0.75rem;color:var(--muted)'>👤 {u.username}</span>"

    st.markdown(f"""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🔬</span>
        <span class="sidebar-brand-name">Vishleshak AI</span>
        {user_label}
    </div>
    """, unsafe_allow_html=True)

    # Logout button
    if AUTH_AVAILABLE and st.session_state.auth_user:
        col_set, col_out = st.columns(2)
        with col_set:
            if st.button("⚙️ Settings", width='stretch', key="sidebar_settings_btn"):
                st.session_state.show_settings = not st.session_state.get("show_settings", False)
                st.rerun()
        with col_out:
            if st.button("🚪 Logout", width='stretch', key="sidebar_logout_btn"):
                try:
                    from auth.auth_manager import AuthManager
                    AuthManager().logout_user(st.session_state.auth_token or "")
                except Exception:
                    pass
                for k in ["auth_user", "auth_token", "current_conv_id", "chat_history",
                          "qa_chain", "agent", "analysis_result", "data"]:
                    st.session_state[k] = None
                st.session_state.chat_history = []
                st.session_state._sidebar_opened = False  # re-trigger open on next login
                st.rerun()

    # ── Theme toggle (disabled — dark mode only) ────────────
    # st.markdown('<div class="sidebar-section">Appearance</div>', unsafe_allow_html=True)
    # col_t1, col_t2 = st.columns([2, 3])
    # with col_t1:
        st.markdown("**Theme**", help="Switch between dark and light mode")
    # with col_t2:
        dark_label = "☀️ Light" if st.session_state.dark_mode else "🌙 Dark"
        if st.button(dark_label, use_container_width=True, key="theme_toggle_btn"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    st.session_state.dark_mode = True  # Always dark

    # ── Mode selector ────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Mode</div>', unsafe_allow_html=True)
    mode_choice = st.radio(
        "mode",
        ["📊 Comprehensive Analysis", "💬 RAG Chatbot", "🤖 Data Agent"],
        label_visibility="collapsed",
        index=0 if st.session_state.mode == "Analysis" else (1 if st.session_state.mode == "Q&A" else 2),
    )
    if "Analysis" in mode_choice:
        st.session_state.mode = "Analysis"
    elif "Chatbot" in mode_choice:
        st.session_state.mode = "Q&A"
    else:
        st.session_state.mode = "DataAgent"
    
    # ── Agent mode toggle (Analysis mode) ─────────────────────────
    if st.session_state.mode == "Analysis" and SUPERVISOR_AVAILABLE:
        st.markdown('<div class="sidebar-section">AI Engine</div>', unsafe_allow_html=True)
        agent_mode = st.checkbox(
            "🤖 Use Multi-Agent Supervisor (v2)",
            value=st.session_state.get("use_agent_mode", False),
            help="Use LangGraph multi-agent system with specialized agents"
        )
        if agent_mode != st.session_state.get("use_agent_mode", False):
            st.session_state.use_agent_mode = agent_mode
            st.session_state.analysis_result = None  # Reset analysis
            st.rerun()
        
        if st.session_state.use_agent_mode:
            domain = st.selectbox(
                "🎯 Domain",
                ["general", "finance", "insurance", "ecommerce"],
                index=0,
                help="Select domain for specialized insights"
            )
            if domain != st.session_state.get("selected_domain", "general"):
                st.session_state.selected_domain = domain
                st.rerun()
    
    # ── Chat History (DB-backed or in-memory fallback) ──────
    if st.session_state.mode == "Q&A":
        if AUTH_AVAILABLE and st.session_state.auth_user:
            render_chat_history_sidebar(st.session_state.auth_user.id)
        else:
            # fallback: in-memory history (unauthenticated)
            st.markdown('<div class="sidebar-section">Chat History</div>', unsafe_allow_html=True)

            if st.session_state.chat_history:
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

                if st.button("➕ New Chat", width='stretch', key="new_chat_btn"):
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.chat_history = []
                    st.session_state.qa_chain = None
                    st.rerun()
            else:
                st.markdown(
                    '<div style="color:var(--muted);font-size:0.8rem;padding:0.5rem;">No chat history yet.</div>',
                    unsafe_allow_html=True,
                )

    # ── Data Agent Status ─────────────────────────────────────
    if st.session_state.get("agent_status") == "error":
        st.error("❌ Agent failed.")
        err = st.session_state.get("agent_error","Unknown")
        with st.expander("📋 Error Details"):
            st.code(err)
        if st.button("🔄 Retry", key="retry_btn"):
            st.session_state.agent_status = "idle"
            st.rerun()
    
    # ── Analysis History ──────────────────────────────────────
    if AUTH_AVAILABLE and st.session_state.auth_user:
        st.markdown('<div class="sidebar-section">📊 Analysis History</div>', unsafe_allow_html=True)
        
        try:
            from database.analysis_repository import analysis_repository
            
            # Get user's analysis reports
            reports = analysis_repository.get_user_reports(
                user_id=st.session_state.auth_user.id,
                limit=10,
                include_completed_only=True
            )
            
            if reports:
                for report in reports:
                    # Format timestamp
                    created = report.created_at.strftime("%b %d, %H:%M") if report.created_at else "Unknown"
                    
                    # Create clickable history item
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f'<div style="padding:8px;border-left:3px solid #4fc3f7;margin:4px 0;'
                            f'background:rgba(79,195,247,0.1);border-radius:0 4px 4px 0;cursor:pointer;'
                            f'title="{report.instruction}">'
                            f'<div style="font-size:0.85rem;color:#fff;">{report.title[:30]}...</div>'
                            f'<div style="font-size:0.7rem;color:#888;">{created} • {report.mode}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with col2:
                        if st.button("📂", key=f"load_analysis_{report.id}", help="Load this analysis"):
                            # Load the full report
                            full_data = analysis_repository.get_full_report_data(report.id)
                            if full_data:
                                st.session_state.agent_report = full_data
                                st.session_state.agent_status = "done"
                                st.session_state.agent_instruction = report.instruction
                                st.session_state.agent_selected_mode = report.mode
                                st.rerun()
                
                if len(reports) == 10:
                    st.caption("Showing last 10 analyses...")
            else:
                st.markdown(
                    '<div style="color:var(--muted);font-size:0.8rem;padding:0.5rem;">No analysis history yet.</div>',
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.caption("Analysis history unavailable")


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP  (silent — no progress bar spam on every rerun)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.initialized:
    print_startup_summary(st.session_state.session_id)
    st.session_state.initialized = True


# ─────────────────────────────────────────────────────────────────────────────
# USER SETTINGS PANEL (shown when toggled)
# ─────────────────────────────────────────────────────────────────────────────
if AUTH_AVAILABLE and st.session_state.get("show_settings") and st.session_state.auth_user:
    with st.expander("⚙️ Account Settings", expanded=True):
        render_user_settings()
        if st.button("✕ Close Settings", key="close_settings_btn"):
            st.session_state.show_settings = False
            st.rerun()


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
        <span class="badge">🤖 ReAct Agent</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA NOT LOADED → WELCOME + UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.data is None and st.session_state.mode != "DataAgent":

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
                
                # Compute dataset_hash for proactive engine
                import hashlib
                col_hash = hashlib.md5(",".join(sorted(df.columns.tolist())).encode()).hexdigest()[:12]
                
                st.session_state.data = df
                st.session_state.dataset_hash = col_hash
                st.session_state.qa_chain = None
                st.session_state.analysis_result = None
                st.session_state.show_visuals = False
                st.session_state.charts_cache = None
                st.session_state.generating_visuals = False
                
                # Trigger proactive engine (fire and forget)
                try:
                    user_id = st.session_state.auth_user.username if st.session_state.get("auth_user") else "default"
                    if "proactive_engine" not in st.session_state:
                        st.session_state.proactive_engine = ProactiveEngine(
                            user_id=user_id,
                            session_id=st.session_state.session_id,
                        )
                    st.session_state.proactive_engine.run_async(
                        df=df,
                        dataset_hash=col_hash,
                        dataset_name=uploaded_file.name,
                        domain=st.session_state.get("selected_domain", "general"),
                    )
                except Exception as e:
                    logger.warning(f"Proactive engine error: {e}")
                
                st.success(f"✅ Loaded **{len(df):,} rows × {len(df.columns)} columns** from `{uploaded_file.name}`")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADED OR DATA AGENT MODE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.mode == "DataAgent":
    df = None
elif st.session_state.data is None:
    df = None
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

    # ── Poll proactive flags ──────────────────────────────────
    if "proactive_engine" in st.session_state:
        try:
            flags = st.session_state.proactive_engine.poll_flags()
            for flag in flags:
                st.toast(f"{flag['icon']} {flag['message']}", icon=None)
        except Exception as e:
            logger.warning(f"Proactive poll error: {e}")

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
                df2 = DataLoader.clean_dataframe_for_streamlit(df2)
                
                # Compute dataset_hash for proactive engine
                import hashlib
                col_hash = hashlib.md5(",".join(sorted(df2.columns.tolist())).encode()).hexdigest()[:12]
                
                st.session_state.data = df2
                st.session_state.dataset_hash = col_hash
                st.session_state.qa_chain = None
                st.session_state.analysis_result = None
                st.session_state.show_visuals = False
                st.session_state.charts_cache = None
                st.session_state.generating_visuals = False
                
                # Trigger proactive engine on replace
                try:
                    user_id = st.session_state.auth_user.username if st.session_state.get("auth_user") else "default"
                    if "proactive_engine" not in st.session_state:
                        st.session_state.proactive_engine = ProactiveEngine(
                            user_id=user_id,
                            session_id=st.session_state.session_id,
                        )
                    st.session_state.proactive_engine.run_async(
                        df=df2,
                        dataset_hash=col_hash,
                        dataset_name=new_file.name,
                        domain=st.session_state.get("selected_domain", "general"),
                    )
                except Exception as e:
                    logger.warning(f"Proactive engine error: {e}")
                
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # ANALYSIS MODE
    # ════════════════════════════════════════════════════════
    if st.session_state.mode == "Analysis" and df is not None:

        st.markdown("## 📊 Comprehensive Analysis")

        with st.expander("👁️ Preview Data", expanded=False):
            clean_dataframe_display(df)

        # ── Buttons ──────────────────────────────────────────
        if st.session_state.analysis_result is None:
            if st.button("🚀 Analyse Data", type="primary", width='content', key="analyse_data_btn"):
                prog = st.progress(0, text="🔄 Initialising analysis engine…")
                try:
                    # Check if supervisor graph should be used (v2 mode)
                    use_supervisor = SUPERVISOR_AVAILABLE and st.session_state.get("use_agent_mode", False)
                    
                    prog.progress(10, text="🧠 Starting agentic supervisor…")
                    
                    if use_supervisor:
                        # ═══════════════════════════════════════════════
                        # V2 MODE: Use Multi-Agent Supervisor (LangGraph)
                        # ═══════════════════════════════════════════════
                        from config.domain_config import detect_domain_from_columns
                        domain = detect_domain_from_columns(df.columns.tolist())
                        
                        prog.progress(20, text="🧠 Running agentic supervisor (v2)…")
                        result_supervisor = invoke_supervisor(
                            user_query="Comprehensive data analysis",
                            dataset=df,
                            user_id=st.session_state.auth_user.username if st.session_state.get("auth_user") else "default",
                            session_id=st.session_state.session_id,
                            domain=domain
                        )
                        
                        # Build v2 result with supervisor output
                        stats = result_supervisor.get("dataset_meta", {})
                        profile = stats.get("profile", {})
                        column_stats = stats.get("statistics", {})
                        
                        v2_stats = {
                            "basic_info": {
                                "total_rows": profile.get("rows", 0),
                                "total_columns": profile.get("columns", 0),
                                "numeric_columns": profile.get("numeric_count", 0),
                                "categorical_columns": profile.get("categorical_count", 0)
                            },
                            "numeric_analysis": column_stats
                        }
                        
                        st.session_state.analysis_result = {
                            "executive_summary": result_supervisor.get("insights_text", "Analysis completed"),
                            "profile": profile,
                            "statistics": column_stats,
                            "supervisor_result": result_supervisor,
                            "ai_insights": result_supervisor.get("insights_text", "No insights generated."),
                            "statistical_analysis": v2_stats,
                            "pattern_analysis": result_supervisor.get("proactive_flags", []) or [],
                            "is_v2": True  # Mark as v2 result
                        }
                        
                        # Convert supervisor PNG charts to Plotly figures for display
                        prog.progress(80, text="📊 Converting charts for display...")
                        supervisor_charts = result_supervisor.get("charts", [])
                        named_charts = []
                        
                        for chart_path in supervisor_charts:
                            if os.path.exists(chart_path):
                                try:
                                    import plotly.graph_objects as go
                                    from PIL import Image
                                    import numpy as np
                                    
                                    img = Image.open(chart_path)
                                    fig = go.Figure()
                                    fig.add_trace(go.Image(z=np.array(img)))
                                    fig.update_layout(
                                        title=os.path.basename(chart_path).replace("chart_", "").replace(".png", ""),
                                        template="plotly_white",
                                        margin=dict(l=10, r=10, t=40, b=10)
                                    )
                                    named_charts.append((os.path.basename(chart_path), fig))
                                except Exception as e:
                                    logger.warning(f"Failed to convert chart {chart_path}: {e}")
                        
                        st.session_state.charts_cache = named_charts
                        prog.progress(100, text="✅ V2 Analysis complete!")
                    else:
                        # ═══════════════════════════════════════════════
                        # V1 MODE: Use original InsightGenerator
                        # ═══════════════════════════════════════════════
                        prog.progress(20, text="📐 Computing statistics…")
                        generator = InsightGenerator(df)
                        prog.progress(55, text="🤖 Generating AI insights…")
                        result = generator.generate_comprehensive_insights()
                        prog.progress(90, text="✅ Finalising…")
                        result["is_v2"] = False  # Mark as v1 result
                        st.session_state.analysis_result = result
                        
                        # Generate charts using DashboardVisualizer
                        dashboard = DashboardVisualizer(df)
                        named_charts = dashboard.create_overview_dashboard()
                        st.session_state.charts_cache = named_charts
                        prog.progress(100, text="✅ V1 Analysis complete!")
                    
                    st.session_state.show_visuals = False
                    st.session_state.generating_visuals = False
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
                if st.button("🔄 Re-Analyse", width='stretch', key="re_analyse_btn"):
                    prog = st.progress(0, text="🔄 Re-running…")
                    try:
                        use_supervisor = SUPERVISOR_AVAILABLE and st.session_state.get("use_agent_mode", False)
                        
                        if use_supervisor:
                            # ═══════════════════════════════════════════════
                            # V2 MODE: Re-run with Multi-Agent Supervisor
                            # ═══════════════════════════════════════════════
                            prog.progress(20, text="🧠 Running agentic supervisor (v2)…")
                            domain = st.session_state.get("selected_domain", "general")
                            result_supervisor = invoke_supervisor(
                                user_query="Comprehensive data analysis",
                                dataset=df,
                                user_id=st.session_state.auth_user.username if st.session_state.get("auth_user") else "default",
                                session_id=st.session_state.session_id,
                                domain=domain
                            )
                            
                            # Build v2 result
                            stats = result_supervisor.get("dataset_meta", {})
                            profile = stats.get("profile", {})
                            column_stats = stats.get("statistics", {})
                            
                            v2_stats = {
                                "basic_info": {
                                    "total_rows": profile.get("rows", 0),
                                    "total_columns": profile.get("columns", 0),
                                    "numeric_columns": profile.get("numeric_count", 0),
                                    "categorical_columns": profile.get("categorical_count", 0)
                                },
                                "numeric_analysis": column_stats
                            }
                            
                            st.session_state.analysis_result = {
                                "executive_summary": result_supervisor.get("insights_text", "Analysis completed"),
                                "profile": profile,
                                "statistics": column_stats,
                                "supervisor_result": result_supervisor,
                                "ai_insights": result_supervisor.get("insights_text", "No insights generated."),
                                "statistical_analysis": v2_stats,
                                "pattern_analysis": result_supervisor.get("proactive_flags", []) or [],
                                "is_v2": True
                            }
                            
                            # Convert supervisor PNG charts
                            prog.progress(80, text="📊 Converting charts for display...")
                            supervisor_charts = result_supervisor.get("charts", [])
                            named_charts = []
                            
                            for chart_path in supervisor_charts:
                                if os.path.exists(chart_path):
                                    try:
                                        import plotly.graph_objects as go
                                        from PIL import Image
                                        import numpy as np
                                        
                                        img = Image.open(chart_path)
                                        fig = go.Figure()
                                        fig.add_trace(go.Image(z=np.array(img)))
                                        fig.update_layout(
                                            title=os.path.basename(chart_path).replace("chart_", "").replace(".png", ""),
                                            template="plotly_white",
                                            margin=dict(l=10, r=10, t=40, b=10)
                                        )
                                        named_charts.append((os.path.basename(chart_path), fig))
                                    except Exception as e:
                                        logger.warning(f"Failed to convert chart {chart_path}: {e}")
                            
                            st.session_state.charts_cache = named_charts
                        else:
                            # ═══════════════════════════════════════════════
                            # V1 MODE: Re-run with InsightGenerator
                            # ═══════════════════════════════════════════════
                            prog.progress(30, text="📐 Computing…")
                            generator = InsightGenerator(df)
                            prog.progress(65, text="🤖 AI thinking…")
                            result = generator.generate_comprehensive_insights()
                            result["is_v2"] = False
                            st.session_state.analysis_result = result
                            
                            # Generate charts
                            dashboard = DashboardVisualizer(df)
                            named_charts = dashboard.create_overview_dashboard()
                            st.session_state.charts_cache = named_charts
                        st.session_state.show_visuals = False
                        st.session_state.generating_visuals = False
                        import time; time.sleep(0.3)
                        prog.empty()
                        st.rerun()
                    except Exception as e:
                        prog.empty()
                        handle_error(e, "Re-Analysis")
            with btn2:
                vis_label = "🔒 Hide Charts" if st.session_state.show_visuals else "📊 Generate Visuals"
                if st.button(vis_label, width='stretch', key="toggle_visuals_btn"):
                    if not st.session_state.show_visuals:
                        # Trigger visual generation
                        st.session_state.generating_visuals = True
                        st.session_state.show_visuals = True
                        st.session_state.charts_cache = None  # Clear cache
                    else:
                        # Hide charts
                        st.session_state.show_visuals = False
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

            # ── PDF Download (v2 mode) ─────────────────────────────
            supervisor_result = result.get("supervisor_result", {})
            if supervisor_result and supervisor_result.get("pdf_path"):
                pdf_path = supervisor_result["pdf_path"]
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        key="download_pdf_btn"
                    )

            # ── Visualisations ───────────────────────────────
            if st.session_state.show_visuals:
                st.markdown("## 📈 Interactive Analytics Dashboard")
                
                # Check if we need to generate charts
                if st.session_state.charts_cache is None or st.session_state.generating_visuals:
                    # Check if we're in v2 mode with supervisor
                    use_supervisor = SUPERVISOR_AVAILABLE and st.session_state.get("use_agent_mode", False)
                    supervisor_result = result.get("supervisor_result", {}) if result.get("supervisor_result") else {}
                    
                    # In v2 mode, always use DashboardVisualizer for proper plotly charts
                    if use_supervisor and supervisor_result:
                        # Generate charts using DashboardVisualizer for v2 mode
                        prog_vis = st.progress(0, text="🎨 Initializing dashboard builder…")
                        st.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)
                    
                        try:
                            import time
                            prog_vis.progress(10, text="📊 Analyzing dataset structure…")
                            time.sleep(0.2)
                            
                            dashboard = DashboardVisualizer(df)
                            
                            prog_vis.progress(25, text="🔍 Identifying data quality patterns…")
                            time.sleep(0.2)
                            
                            prog_vis.progress(40, text="📈 Generating distribution charts…")
                            time.sleep(0.2)
                            
                            prog_vis.progress(55, text="🔗 Computing correlations…")
                            time.sleep(0.2)
                            
                            prog_vis.progress(70, text="🏷️ Creating categorical breakdowns…")
                            time.sleep(0.2)
                            
                            prog_vis.progress(85, text="✨ Finalizing visualizations…")
                            named_charts = dashboard.create_overview_dashboard()
                            
                            prog_vis.progress(100, text="✅ Dashboard ready!")
                            time.sleep(0.4)
                            prog_vis.empty()
                            
                            # Cache the charts
                            st.session_state.charts_cache = named_charts
                            st.session_state.generating_visuals = False
                            logger.info(f"V2 mode: Generated {len(named_charts)} charts via DashboardVisualizer")
                        except Exception as e:
                            prog_vis.empty()
                            st.error(f"❌ Dashboard generation error: {e}")
                            logger.error(f"Dashboard error: {e}", exc_info=True)
                            st.session_state.generating_visuals = False
                            st.session_state.charts_cache = []
                            named_charts = []
                    else:
                        # Original v1 behavior - check for existing charts first
                        existing_charts = supervisor_result.get("charts", []) if supervisor_result else []
                        
                        if existing_charts and len(existing_charts) > 0:
                            # Use supervisor-generated charts (file paths)
                            named_charts = []
                            for chart_path in existing_charts:
                                if os.path.exists(chart_path):
                                    try:
                                        import plotly.io as pio
                                        import plotly.graph_objects as go
                                        from PIL import Image
                                        import numpy as np
                                        
                                        img = Image.open(chart_path)
                                        fig = go.Figure()
                                        fig.add_trace(go.Image(z=np.array(img)))
                                        fig.update_layout(
                                            title=os.path.basename(chart_path).replace("chart_", "").replace(".png", ""),
                                            template="plotly_white",
                                            margin=dict(l=10, r=10, t=40, b=10)
                                        )
                                        named_charts.append((os.path.basename(chart_path), fig))
                                    except Exception as e:
                                        logger.warning(f"Failed to load chart {chart_path}: {e}")
                            st.session_state.charts_cache = named_charts
                            st.session_state.generating_visuals = False
                            logger.info(f"Using supervisor charts: {len(named_charts)}")
                            
                            # Jump to display if we have charts
                            if named_charts:
                                named_charts = st.session_state.charts_cache
                            else:
                                # Fall back to DashboardVisualizer
                                raise Exception("No valid charts from supervisor")
                        else:
                            # Generate charts using DashboardVisualizer for v1 mode
                            prog_vis = st.progress(0, text="🎨 Initializing dashboard builder…")
                            st.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)
                    
                            try:
                                import time
                                prog_vis.progress(10, text="📊 Analyzing dataset structure…")
                                time.sleep(0.2)
                                
                                dashboard = DashboardVisualizer(df)
                                
                                prog_vis.progress(25, text="🔍 Identifying data quality patterns…")
                                time.sleep(0.2)
                                
                                prog_vis.progress(40, text="📈 Generating distribution charts…")
                                time.sleep(0.2)
                                
                                prog_vis.progress(55, text="🔗 Computing correlations…")
                                time.sleep(0.2)
                                
                                prog_vis.progress(70, text="🏷️ Creating categorical breakdowns…")
                                time.sleep(0.2)
                                
                                prog_vis.progress(85, text="✨ Finalizing visualizations…")
                                named_charts = dashboard.create_overview_dashboard()
                                
                                prog_vis.progress(100, text="✅ Dashboard ready!")
                                time.sleep(0.4)
                                prog_vis.empty()
                                
                                # Cache the charts
                                st.session_state.charts_cache = named_charts
                                st.session_state.generating_visuals = False
                            except Exception as e:
                                prog_vis.empty()
                                st.error(f"❌ Dashboard generation error: {e}")
                                logger.error(f"Dashboard error: {e}", exc_info=True)
                                st.session_state.generating_visuals = False
                                st.session_state.charts_cache = []
                                named_charts = []
                else:
                    # Use cached charts
                    named_charts = st.session_state.charts_cache
                    st.success("✅ Dashboard loaded from cache")

                # Display charts
                if not named_charts:
                    st.info("📊 No charts generated — dataset may lack numeric/categorical columns.")
                else:
                    try:
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
                        
                        # Categorize charts with progress
                        chart_progress = st.empty()
                        chart_progress.markdown(f"<small style='color:var(--muted)'>📊 Organizing {len(named_charts)} charts...</small>", unsafe_allow_html=True)
                        
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
                        
                        chart_progress.empty()
                        
                        active = {k: v for k, v in cat_map.items() if v}
                        
                        # Show chart count summary
                        st.markdown(f"""
                        <div style="background:var(--surface2);padding:0.75rem;border-radius:0.5rem;margin:1rem 0;">
                            <small>
                            📊 <b>{len(named_charts)} charts</b> organized into <b>{len(active)} categories</b>
                            &nbsp;·&nbsp; Use the 📷 icon on any chart to save as PNG
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        tab_objs = st.tabs(list(active.keys()))
                        for tab_obj, (tab_name, tab_charts) in zip(tab_objs, active.items()):
                            with tab_obj:
                                for i, (label, fig) in enumerate(tab_charts, 1):
                                    st.markdown(f"#### {label}")
                                    st.plotly_chart(fig, width='stretch')
                                    if i < len(tab_charts):
                                        st.markdown("---")
                    except Exception as e:
                        st.error(f"❌ Chart display error: {e}")
                        logger.error(f"Chart display error: {e}", exc_info=True)

            # ── Detailed analysis tabs ───────────────────────
            st.markdown("## 🔍 Detailed Analysis")
            tab1, tab2, tab3 = st.tabs(["💡 AI Insights", "📊 Statistics", "🔍 Patterns"])

            with tab1:
                st.markdown(result.get("ai_insights", "No insights generated."))

            with tab2:
                stats = result.get("statistical_analysis", {})
                if stats:
                    if "basic_info" in stats:
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
                                    width='stretch'
                                )
                            except Exception:
                                st.json(num_analysis)
                    else:
                        profile = stats.get("profile", {})
                        if profile:
                            b1, b2, b3, b4 = st.columns(4)
                            b1.metric("Rows", f"{profile.get('rows', 0):,}")
                            b2.metric("Columns", profile.get("columns", 0))
                            b3.metric("Numeric", len(profile.get("numeric_columns", [])))
                            b4.metric("Categorical", len(profile.get("categorical_columns", [])))
                        col_stats = stats.get("statistics", {})
                        if col_stats:
                            st.markdown("#### Numeric Summary")
                            try:
                                stats_df = pd.DataFrame(col_stats).T
                                stats_df = stats_df[['mean', 'median', 'std', 'min', 'max']].round(3)
                                st.dataframe(stats_df, width='stretch')
                            except Exception:
                                st.json(col_stats)

            with tab3:
                patterns = result.get("pattern_analysis", {})
                if patterns:
                    if isinstance(patterns, dict):
                        for p_type, p_list in patterns.items():
                            if p_list:
                                st.subheader(p_type.replace("_", " ").title())
                                for p in p_list:
                                    st.markdown(f"- {p.get('interpretation', str(p))}")
                    elif isinstance(patterns, list):
                        if patterns:
                            st.subheader("Key Findings & Anomalies")
                            for p in patterns:
                                st.markdown(f"- {p}")
                    else:
                        st.info("No patterns detected.")
                else:
                    st.info("No patterns detected.")

    # ════════════════════════════════════════════════════════
    # Q&A / RAG CHATBOT MODE
    # ════════════════════════════════════════════════════════
    if st.session_state.mode == "Q&A" and df is not None:
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
        for idx, msg in enumerate(st.session_state.chat_history):
            role    = msg[0]
            content = msg[1]
            meta    = msg[2] if len(msg) > 2 else None

            if role == "user":
                _uname = getattr(st.session_state.get("auth_user"), "username", None) or "You"
                st.markdown(f"""
                <div class="chat-msg user">
                    <div class="msg-label"><span class="msg-icon">👤</span> {_uname}</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-msg bot">
                    <div class="msg-label"><span class="msg-icon">🔬</span> Vishleshak AI</div>
                    {content}
                </div>
                """, unsafe_allow_html=True)

                # ── Agent reasoning trace (if agent mode) ──────────────────
                if meta and meta.get("is_agent") and st.session_state.show_agent_thinking:
                    reasoning = meta.get("reasoning_trace", [])
                    tools_used = meta.get("tools_used", [])
                    confidence = meta.get("confidence", 0)
                    
                    with st.expander(f"🧠 Agent Reasoning ({len(reasoning)} steps, {len(tools_used)} tools)", expanded=False):
                        st.markdown(f"""
                        <div style="background:var(--surface2);padding:0.75rem;border-radius:0.5rem;margin-bottom:1rem;">
                            <small>
                            🎯 <b>Confidence:</b> {confidence:.1%} &nbsp;|
                            🛠️ <b>Tools:</b> {', '.join(tools_used) if tools_used else 'None'} &nbsp;|
                            🔁 <b>Iterations:</b> {len(reasoning)}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, step in enumerate(reasoning, 1):
                            thought = step.get("thought", "")
                            action = step.get("action", "")
                            observation = step.get("observation", "")[:300] + "..."
                            
                            st.markdown(f"""
                            <div style="background:var(--surface);border-left:3px solid var(--accent);padding:0.75rem;margin:0.5rem 0;border-radius:0.4rem;">
                                <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.3rem;">STEP {i}</div>
                                {f'<div style="margin-bottom:0.5rem;"><b>💡 Thought:</b> {thought}</div>' if thought else ''}
                                <div style="margin-bottom:0.5rem;"><b>🔧 Action:</b> <code>{action}</code></div>
                                <div style="font-size:0.85rem;color:var(--muted);"><b>👁️ Observation:</b> {observation}</div>
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
                    if st.button(sug, width='stretch', key=f"sug_{i}"):
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
                        "Send 🚀", type="primary", width='stretch'
                    )

        # ── Process question ──────────────────────────────────
        if process_question and user_input:
            # Check which mode to use
            use_agent = st.session_state.use_agent_mode and st.session_state.agent is not None
            use_qa = st.session_state.qa_chain is not None

            # ── Ensure DB conversation exists ─────────────────
            def _ensure_db_conversation():
                if not (AUTH_AVAILABLE and st.session_state.auth_user):
                    return
                if st.session_state.get("current_conv_id"):
                    return
                try:
                    chat_repo = ChatRepository()
                    df_info = None
                    if st.session_state.data is not None:
                        _df = st.session_state.data
                        df_info = {"name": "dataset", "rows": len(_df), "cols": len(_df.columns)}
                    conv = chat_repo.create_conversation(
                        user_id=st.session_state.auth_user.id,
                        title=user_input[:80],
                        dataset_info=df_info,
                    )
                    st.session_state.current_conv_id = conv.id
                except Exception as _e:
                    logger.warning("Could not create DB conversation: %s", _e)

            def _save_to_db(role: str, content: str, metadata: dict | None = None):
                if not (AUTH_AVAILABLE and st.session_state.auth_user):
                    return
                cid = st.session_state.get("current_conv_id")
                if not cid:
                    return
                try:
                    chat_repo = ChatRepository()
                    chat_repo.save_message(cid, role, content, metadata or {})
                except Exception as _e:
                    logger.warning("Could not save message to DB: %s", _e)

            if not use_agent and not use_qa:
                st.error("❌ No AI system initialized. Please refresh the page.")
            else:
                _ensure_db_conversation()
                st.session_state.chat_history.append(("user", user_input))
                _save_to_db("user", user_input)

                prog2 = st.progress(0, text="🔍 Understanding your question…")
                try:
                    import time
                    
                    if use_agent:
                        # ══════════════════════════════════════════════════════
                        # AGENT MODE
                        # ══════════════════════════════════════════════════════
                        prog2.empty()  # Clear the basic progress bar
                        
                        from langchain_community.callbacks import StreamlitCallbackHandler
                        
                        agent_placeholder = st.empty()
                        with agent_placeholder.container():
                            st_callback = StreamlitCallbackHandler(
                                st.container(),
                                expand_new_thoughts=True,
                                collapse_completed_thoughts=True
                            )
                            agent_result = st.session_state.agent.run(
                                user_input,
                                callbacks=[st_callback]
                            )
                        
                        agent_placeholder.empty() # Clear live thoughts when done
                        
                        response = agent_result["answer"]
                        confidence = agent_result.get("confidence", 1.0)
                        reasoning_trace = agent_result.get("reasoning_trace", [])
                        tools_used = agent_result.get("tools_used", [])
                        
                        # Convert confidence to grade
                        if confidence >= 0.9:
                            grade, score = "A", confidence * 100
                        elif confidence >= 0.7:
                            grade, score = "B", confidence * 100
                        elif confidence >= 0.5:
                            grade, score = "C", confidence * 100
                        else:
                            grade, score = "D", confidence * 100
                        
                        prog2.progress(100, text=f"✅ Done — Confidence {confidence:.0%}")
                        time.sleep(0.3)
                        prog2.empty()
                        
                        _meta_agent = {
                            "quality_score": score,
                            "quality_grade": grade,
                            "message_id": len(st.session_state.chat_history),
                            "is_agent": True,
                            "confidence": confidence,
                            "reasoning_trace": reasoning_trace,
                            "tools_used": tools_used,
                        }
                        st.session_state.chat_history.append((
                            "bot", response, _meta_agent,
                        ))
                        _save_to_db("assistant", response, _meta_agent)
                        st.rerun()
                    
                    else:
                        # ══════════════════════════════════════════════════════
                        # REGULAR QA MODE
                        # ══════════════════════════════════════════════════════
                        prog2.progress(20, text="📚 Searching knowledge base…")
                        time.sleep(0.15)
                        prog2.progress(45, text="🧠 Reasoning through the data…")
                        time.sleep(0.15)
                        prog2.progress(70, text="✍️ Composing answer…")

                        stream_box = st.empty()
                        streamed_parts = []

                        def _on_stream(chunk: str):
                            streamed_parts.append(chunk)
                            stream_box.markdown(f"""
                            <div class="chat-msg bot">
                                <div class="msg-label"><span class="msg-icon">🔬</span> Vishleshak AI</div>
                                <div class="markdown-body">{''.join(streamed_parts)}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        result = st.session_state.qa_chain.ask(
                            user_input,
                            return_dict=True,
                            stream_callback=_on_stream,
                        )

                        # Wait for quality evaluation while keeping stream visible
                        prog2.progress(90, text="📊 Evaluating quality…")
                        
                        response    = result.get("formatted_response", "I apologize, but I couldn't generate a response.")
                        quality_obj = result.get("quality_score")
                        msg_id      = result.get("cycle_number", len(st.session_state.chat_history))
                        
                        # Handle None quality_obj
                        if quality_obj:
                            grade = quality_obj.get_grade()
                            score = quality_obj.overall_score
                        else:
                            grade = "C"
                            score = 50

                        prog2.progress(100, text=f"✅ Done — Grade {grade} ({score:.0f}/100)")
                        time.sleep(0.3)
                        prog2.empty()
                        stream_box.empty()

                        _meta_qa = {"quality_score": score, "quality_grade": grade, "message_id": msg_id}
                        st.session_state.chat_history.append((
                            "bot", response, _meta_qa,
                        ))
                        _save_to_db("assistant", response, _meta_qa)
                        st.rerun()

                except Exception as e:
                    prog2.empty()
                    logger.error(f"Error in Question Processing: {e}", exc_info=True)
                    
                    # Display user-friendly error message
                    error_response = f"❌ I encountered an error processing your question: {str(e)[:200]}"
                    
                    # Check for common errors
                    if "Connection error" in str(e) or "timeout" in str(e).lower():
                        error_response = "⚠️ Connection timeout. The AI service is experiencing high traffic. Please try again in a moment."
                    elif "NoneType" in str(e):
                        error_response = "⚠️ The response was incomplete. Please try rephrasing your question or try again."
                    elif "API" in str(e) or "rate limit" in str(e).lower():
                        error_response = "⚠️ API rate limit reached. Please wait a few seconds and try again."
                    
                    st.session_state.chat_history.append((
                        "bot",
                        error_response,
                        {"quality_score": 0, "quality_grade": "F", "message_id": len(st.session_state.chat_history), "error": True},
                    ))
                    st.rerun()

        # ── Debug expander ────────────────────────────────────
        with st.expander("🕵️ Debug: Retrieved RAG Context"):
            if st.session_state.qa_chain and hasattr(st.session_state.qa_chain, "last_context"):
                st.write(st.session_state.qa_chain.last_context)
            else:
                st.info("Ask a question to see the retrieved RAG context.")



if st.session_state.mode == "DataAgent":
    st.markdown("## 🤖 Data Agent")

    # Left panel - Input
    col_left, col_right = st.columns([35, 65])
    
    with col_left:
        st.markdown("### 📝 Input")
        
        agent_instruction = st.text_area(
            "What do you want to analyze?",
            placeholder="analyze Insurance.csv and find trends / train a model to predict Amount / download https://... and summarize",
            height=120,
            label_visibility="collapsed",
        )
        
        agent_mode = st.radio(
            "Mode",
            ["Analysis Only", "Analysis + ML Model", "Analysis + ML + Notebook"],
            index=1,
        )
        
        uploaded_file = st.file_uploader(
            "Upload CSV (optional)",
            type=["csv"],
            label_visibility="collapsed",
            key="data_agent_uploader_2",
        )
        
        uploaded_path = None
        if uploaded_file:
            os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
            uploaded_path = os.path.join(settings.UPLOAD_FOLDER, uploaded_file.name)
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        with st.expander("⚙️ Advanced", expanded=False):
            step_delay = st.slider("Step Delay (seconds)", 1, 5, 2)
            max_loop_steps = st.slider("Max Loop Steps", 10, 25, 15)
        
        run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True, key="data_agent_run_btn")
    
    with col_right:
        st.markdown("### 📊 Output")
        
        # Initialize session state for agent
        if "agent_report" not in st.session_state:
            st.session_state.agent_report = None
        if "agent_steps" not in st.session_state:
            st.session_state.agent_steps = []
        
        # Empty state - show instructions
        if not st.session_state.agent_steps and not st.session_state.agent_report:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:0.8rem;padding:2rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:1rem;">🤖</div>
                <div style="color:var(--muted);font-size:0.9rem;">
                    Enter an instruction and click <b>Run Agent</b> to start analysis.<br>
                    Example: "analyze Insurance.csv and find trends"
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Run agent on button click
        if run_button:
            if not agent_instruction:
                st.error("Please enter an instruction")
            else:
                try:
                    from data_agent_3 import run_agent
                    
                    # Prepare instruction with file path and mode
                    final_instruction = agent_instruction
                    if uploaded_path:
                        final_instruction = f"{uploaded_path} - {agent_instruction}"
                    
                    # Add mode-specific keywords to ensure agent runs correct pipeline
                    if agent_mode == "Analysis + ML Model":
                        if "train" not in final_instruction.lower() and "model" not in final_instruction.lower():
                            final_instruction += " Train a machine learning model."
                    elif agent_mode == "Analysis + ML + Notebook":
                        if "notebook" not in final_instruction.lower():
                            final_instruction += " Train a machine learning model and generate a jupyter notebook."
                    elif agent_mode == "Analysis Only":
                        # Ensure no ML keywords are present
                        final_instruction += " Analysis only, no machine learning."
                    
                    # Store selected mode for UI reference
                    st.session_state.agent_selected_mode = agent_mode
                    
                    # Map UI mode to agent task type
                    mode_to_task = {
                        "Analysis Only": "analysis_only",
                        "Analysis + ML Model": "analysis_ml",
                        "Analysis + ML + Notebook": "analysis_ml_notebook"
                    }
                    force_task_type = mode_to_task.get(agent_mode, "analysis_only")
                    
                    st.session_state.agent_status = "running"
                    st.session_state.agent_steps = []
                    st.session_state.agent_report = None
                    
                    # Run agent in a thread with file-based progress tracking
                    import threading
                    import json
                    import os
                    
                    # Progress file path for thread communication
                    os.makedirs("storage", exist_ok=True)
                    progress_file = f"storage/agent_progress_{st.session_state.session_id}.json"
                    
                    def run_agent_thread():
                        try:
                            import data_agent_3 as da3
                            from data_agent_3 import run_agent
                            
                            # Initialize progress file
                            with open(progress_file, 'w') as f:
                                json.dump({"steps": [], "status": "running"}, f)
                            
                            # Set up progress callback that writes to file
                            def progress_callback(update):
                                try:
                                    step = update.get("step", "")
                                    status = update.get("status", "")
                                    # Read current progress
                                    if os.path.exists(progress_file):
                                        with open(progress_file, 'r') as f:
                                            data = json.load(f)
                                    else:
                                        data = {"steps": [], "status": "running"}
                                    
                                    # Update steps list
                                    existing = False
                                    for i, s in enumerate(data["steps"]):
                                        if s["step"] == step:
                                            data["steps"][i]["status"] = status
                                            existing = True
                                            break
                                    if not existing:
                                        data["steps"].append({"step": step, "status": status})
                                    
                                    # Write back
                                    with open(progress_file, 'w') as f:
                                        json.dump(data, f)
                                except Exception:
                                    pass
                            
                            da3.set_progress_callback(progress_callback)
                            
                            # Run agent with forced task type from UI mode
                            report = run_agent(final_instruction, force_task_type=force_task_type)
                            
                            # Update progress file with completion
                            with open(progress_file, 'w') as f:
                                json.dump({"steps": [], "status": "done", "report": report}, f)
                                
                        except Exception as e:
                            # Update progress file with error
                            with open(progress_file, 'w') as f:
                                json.dump({"steps": [], "status": "error", "error": str(e)}, f)
                    
                    thread = threading.Thread(target=run_agent_thread, daemon=True)
                    thread.start()
                    
                    # Small delay to let thread start
                    import time
                    time.sleep(0.5)
                    
                    st.rerun()
                    
                except ImportError as e:
                    st.error(f"❌ Could not import data_agent_3: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Show progress during run
        if st.session_state.get("agent_status") == "running":
            st.markdown("#### 🔄 Agent Running...")
            
            # Read progress from file
            import json
            import os
            progress_file = f"storage/agent_progress_{st.session_state.session_id}.json"
            progress_data = {"steps": [], "status": "running"}
            
            try:
                if os.path.exists(progress_file):
                    with open(progress_file, 'r') as f:
                        progress_data = json.load(f)
            except Exception:
                pass
            
            # Check if agent completed
            if progress_data.get("status") == "done":
                st.session_state.agent_report = progress_data.get("report")
                st.session_state.agent_status = "done"
                # Clean up progress file
                try:
                    os.remove(progress_file)
                except Exception:
                    pass
                st.rerun()
            elif progress_data.get("status") == "error":
                st.session_state.agent_error = progress_data.get("error", "Unknown error")
                st.session_state.agent_status = "error"
                try:
                    os.remove(progress_file)
                except Exception:
                    pass
                st.rerun()
            
            # Progress bar
            agent_steps = progress_data.get("steps", [])
            total_steps = 10  # Total expected steps
            current_step = len([s for s in agent_steps if s.get("status") == "done"])
            progress = min(current_step / total_steps, 0.95)
            st.progress(progress, text=f"Step {current_step}/{total_steps}: Processing...")
            
            # Show captured steps with visual indicators
            st.markdown("**Progress Steps:**")
            if agent_steps:
                for step_info in agent_steps:
                    status = step_info.get("status", "")
                    step_name = step_info.get("step", "")
                    if status == "done":
                        st.success(f"✅ {step_name}")
                    elif status == "running":
                        st.info(f"🔄 {step_name}...")
                    else:
                        st.text(f"⏳ {step_name}")
            else:
                st.text("⏳ Initializing...")
            
            # Manual refresh button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🔄 Refresh Now", key="refresh_agent_status"):
                    st.rerun()
            with col2:
                if st.button("⏹ Stop Agent", key="stop_agent_btn"):
                    try:
                        import data_agent_3 as da3
                        da3.cancel_agent()
                        st.session_state.agent_status = "idle"
                        st.warning("Agent stop requested")
                    except Exception:
                        pass
                    st.rerun()
            
            st.caption("⏱️ Page auto-refreshes every 3 seconds...")
            
            # Auto-rerun after delay for live updates
            import time
            time.sleep(3)
            st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
        
        # Show results after run
        if st.session_state.get("agent_status") == "done" and st.session_state.agent_report:
            report = st.session_state.agent_report
            
            # Save analysis to database (only once)
            if "analysis_saved" not in st.session_state:
                try:
                    from database.analysis_repository import analysis_repository
                    
                    # Get user ID if authenticated
                    user_id = None
                    if st.session_state.get("auth_user"):
                        user_id = st.session_state.auth_user.id
                    
                    if user_id:
                        # Extract dataset info
                        metadata = report.get("metadata", {})
                        dataset_name = metadata.get("source", "").split("/")[-1] if metadata.get("source") else None
                        
                        # Create title from instruction
                        instruction = st.session_state.get("agent_instruction", "Data Analysis")
                        title = instruction[:100] if len(instruction) > 100 else instruction
                        
                        # Save report
                        analysis_repo = analysis_repository
                        saved_report = analysis_repo.create_report(
                            user_id=user_id,
                            session_id=st.session_state.session_id,
                            title=title,
                            instruction=instruction,
                            dataset_name=dataset_name,
                            dataset_rows=metadata.get("rows"),
                            dataset_cols=metadata.get("cols"),
                            mode=st.session_state.get("agent_selected_mode", "Analysis Only"),
                            report_data=report,
                            status="completed",
                        )
                        st.session_state.analysis_saved = True
                        st.session_state.analysis_report_id = saved_report.id
                        logger.info(f"Analysis report {saved_report.id} saved to database")
                except Exception as e:
                    logger.error(f"Failed to save analysis to database: {e}")
            
            # Result tabs
            sub_tabs = st.tabs(["📋 Summary", "📈 Charts", "🤖 ML Results", "📓 Notebook", "📄 Raw JSON"])
            
            with sub_tabs[0]:
                # Summary tab
                st.markdown("#### 📋 Analysis Summary")
                
                # Metric cards
                metadata = report.get("metadata", {})
                m_rows = metadata.get("rows", report.get("rows", "N/A"))
                m_cols = metadata.get("cols", report.get("columns", "N/A"))
                m_charts = len(report.get("charts", []))
                ml_results = report.get("ml_results", {})
                m_model = ml_results.get("metrics", {}).get("r2_score") or ml_results.get("metrics", {}).get("accuracy") or "N/A"
                
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("📊 Rows", m_rows)
                mc2.metric("📋 Columns", m_cols)
                mc3.metric("📈 Charts", m_charts)
                mc4.metric("🎯 Model Score", f"{m_model:.3f}" if isinstance(m_model, float) else m_model)
                
                st.markdown("---")
                
                # Insights section
                insights = report.get("insights", {})
                
                # Executive summary
                exec_summary = insights.get("executive_summary", report.get("executive_summary", "No summary available"))
                if exec_summary and exec_summary != "No summary available":
                    st.markdown("### 📝 Executive Summary")
                    st.info(exec_summary)
                
                # Two columns for findings and recommendations
                col_findings, col_recs = st.columns(2)
                
                with col_findings:
                    # Key findings
                    findings = insights.get("key_findings", report.get("key_findings", []))
                    if findings:
                        st.markdown("### 🔍 Key Findings")
                        for finding in findings:
                            st.markdown(f"✓ {finding}")
                
                with col_recs:
                    # Recommendations
                    recommendations = insights.get("recommendations", report.get("recommendations", []))
                    if recommendations:
                        st.markdown("### 💡 Recommendations")
                        for rec in recommendations:
                            st.markdown(f"→ {rec}")
                
                # Anomalies and risks
                anomalies = insights.get("anomalies_or_risks", report.get("anomalies_or_risks", []))
                if anomalies:
                    with st.expander("⚠️ Anomalies & Risks", expanded=True):
                        for anomaly in anomalies:
                            st.warning(anomaly)
                
                # Data quality note
                quality_note = insights.get("data_quality_note", "")
                if quality_note:
                    with st.expander("📊 Data Quality Note"):
                        st.markdown(quality_note)
                
                # Chart interpretations
                chart_interps = insights.get("chart_interpretations", insights.get("chart_interpretation", {}))
                if chart_interps:
                    with st.expander("📈 Chart Interpretations"):
                        for chart_title, interp in chart_interps.items():
                            st.markdown(f"**{chart_title}:** {interp}")
                
                st.markdown("---")
                
                # Preprocessing steps
                with st.expander("🔧 Preprocessing Steps"):
                    steps = report.get("preprocessing", report.get("preprocessing", []))
                    if steps:
                        for i, step in enumerate(steps, 1):
                            st.markdown(f"{i}. {step}")
                    else:
                        st.info("No preprocessing steps recorded")
                
                # Errors and warnings
                errors = report.get("errors", [])
                warnings_list = report.get("warnings", [])
                
                if errors:
                    with st.expander("❌ Errors During Processing"):
                        for error in errors:
                            st.error(error)
                
                if warnings_list:
                    with st.expander("⚡ Warnings"):
                        for warning in warnings_list:
                            st.warning(warning)
            
            with sub_tabs[1]:
                # Charts tab
                st.markdown("#### 📈 Generated Charts")
                charts = report.get("charts", [])
                if charts:
                    st.success(f"✅ {len(charts)} chart(s) generated successfully")
                    
                    for i, chart in enumerate(charts):
                        html_path = chart.get("html_path")
                        png_path = chart.get("png_path")
                        title = chart.get("title", f"Chart {i+1}")
                        chart_type = chart.get("type", "unknown")
                        
                        with st.container():
                            st.markdown(f"**{title}** (*{chart_type}*)")
                            
                            if html_path and os.path.exists(html_path):
                                try:
                                    with open(html_path, "r", encoding="utf-8") as f:
                                        html_content = f.read()
                                    st.components.v1.html(html_content, height=500)
                                    
                                    # Interpretation
                                    interp = chart.get("interpretation", "")
                                    if interp:
                                        st.markdown(f"💡 *{interp}*")
                                    
                                    # Download buttons row
                                    dl_col1, dl_col2 = st.columns([1, 3])
                                    with dl_col1:
                                        # Download PNG
                                        if png_path and os.path.exists(png_path):
                                            with open(png_path, "rb") as f:
                                                png_bytes = f.read()
                                            st.download_button(
                                                label="⬇️ PNG",
                                                data=png_bytes,
                                                file_name=os.path.basename(png_path),
                                                mime="image/png",
                                                key=f"dl_png_{i}"
                                            )
                                    with dl_col2:
                                        # Download HTML
                                        if html_path and os.path.exists(html_path):
                                            with open(html_path, "rb") as f:
                                                html_bytes = f.read()
                                            st.download_button(
                                                label="⬇️ HTML (Interactive)",
                                                data=html_bytes,
                                                file_name=os.path.basename(html_path),
                                                mime="text/html",
                                                key=f"dl_html_{i}"
                                            )
                                    st.markdown("---")
                                except Exception as e:
                                    st.error(f"❌ Error loading chart '{title}': {e}")
                            else:
                                st.warning(f"⚠️ Chart file not found: {html_path}")
                else:
                    st.info("ℹ️ No charts were generated for this analysis")
            
            with sub_tabs[2]:
                # ML Results tab
                st.markdown("#### 🤖 ML Results")
                ml_results = report.get("ml_results", {})
                
                if ml_results:
                    metrics = ml_results.get("metrics", {})
                    task_type = ml_results.get("task_type", "N/A")
                    target_col = ml_results.get("target_col", "N/A")
                    feat_cols = ml_results.get("feature_cols", [])
                    
                    st.markdown(f"**Task:** {task_type} | **Target:** {target_col}")
                    
                    # Metrics cards
                    if task_type == "regression":
                        rmse = metrics.get("rmse", "N/A")
                        r2 = metrics.get("r2_score", "N/A")
                        mm1, mm2 = st.columns(2)
                        mm1.metric("RMSE", rmse)
                        mm2.metric("R² Score", r2)
                    else:
                        acc = metrics.get("accuracy", "N/A")
                        st.metric("Accuracy", acc)
                    
                    # SHAP chart
                    shap_importance = ml_results.get("shap_importance", {})
                    if shap_importance:
                        st.markdown("##### SHAP Feature Importance")
                        shap_df = pd.DataFrame(list(shap_importance.items()), columns=["Feature", "Importance"])
                        shap_df = shap_df.sort_values("Importance", ascending=True)
                        st.bar_chart(shap_df.set_index("Feature"))
                    
                    # Feature importance
                    feat_imp = ml_results.get("feature_importance", {})
                    if feat_imp:
                        st.markdown("##### Feature Importance")
                        fi_df = pd.DataFrame(list(feat_imp.items()), columns=["Feature", "Importance"])
                        fi_df = fi_df.sort_values("Importance", ascending=False).head(10)
                        st.dataframe(fi_df, hide_index=True)
                    
                    # Train/test split info
                    n_train = ml_results.get("n_train", "N/A")
                    n_test = ml_results.get("n_test", "N/A")
                    st.markdown(f"**Train size:** {n_train} | **Test size:** {n_test}")
                else:
                    st.info("No ML results - run with Analysis + ML Model mode")
            
            with sub_tabs[3]:
                # Notebook tab
                st.markdown("#### 📓 Generated Notebook")
                nb_path = report.get("notebook_path")
                
                if nb_path and os.path.exists(nb_path):
                    st.success(f"✅ Notebook generated: `{os.path.basename(nb_path)}`")
                    
                    # Get file size
                    file_size = os.path.getsize(nb_path) / 1024  # KB
                    st.caption(f"📁 File size: {file_size:.1f} KB")
                    
                    # Download button with better styling
                    with open(nb_path, "rb") as f:
                        nb_bytes = f.read()
                    
                    col_dl, col_open = st.columns([1, 2])
                    with col_dl:
                        st.download_button(
                            label="⬇️ Download .ipynb",
                            data=nb_bytes,
                            file_name=os.path.basename(nb_path),
                            mime="application/x-ipynb+json",
                            key="dl_notebook_main"
                        )
                    with col_open:
                        st.markdown("💡 *Open in Jupyter Notebook or Google Colab*")
                    
                    # Preview notebook cells
                    st.markdown("---")
                    st.markdown("**📋 Notebook Preview (First 10 cells):**")
                    
                    try:
                        import nbformat
                        nb = nbformat.read(os.path.abspath(nb_path), as_version=4)
                        
                        for i, cell in enumerate(nb.cells[:10]):
                            with st.container():
                                if cell.cell_type == "code":
                                    with st.expander(f"🐍 Code Cell {i+1}", expanded=i < 3):
                                        st.code(cell.source, language="python")
                                        # Show output if available
                                        if cell.outputs:
                                            for output in cell.outputs[:2]:  # Limit outputs
                                                if output.output_type == "stream":
                                                    st.text(output.text[:500])  # Limit text
                                                elif output.output_type == "execute_result":
                                                    if hasattr(output, 'data') and 'text/plain' in output.data:
                                                        st.text(output.data['text/plain'][:500])
                                else:
                                    with st.expander(f"📝 Markdown Cell {i+1}", expanded=i < 3):
                                        st.markdown(cell.source)
                                st.markdown("---")
                        
                        if len(nb.cells) > 10:
                            st.info(f"📌 ... and {len(nb.cells) - 10} more cells. Download the notebook to see all.")
                            
                    except ImportError:
                        st.warning("⚠️ Install `nbformat` to preview notebook: `pip install nbformat`")
                    except Exception as e:
                        st.error(f"❌ Could not preview notebook: {e}")
                else:
                    st.info("ℹ️ No notebook generated - run with 'Analysis + ML + Notebook' mode to generate one")
            
            with sub_tabs[4]:
                # Raw JSON tab
                st.markdown("#### 📄 Raw JSON")
                st.json(report)
        
        # Error display
        if st.session_state.get("agent_status") == "error":
            error_msg = st.session_state.get("agent_error", "Unknown error")
            st.error(f"❌ Agent failed: {error_msg}")
            
            # Show traceback in expander
            with st.expander("📋 Full Error Details"):
                st.code(error_msg)


