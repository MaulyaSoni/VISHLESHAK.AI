"""
Claude.ai-inspired theme system for Vishleshak AI
Professional, minimal, confidence-inspiring design
"""

from typing import Dict


def get_claude_theme(dark_mode: bool = True) -> Dict[str, str]:
    """
    Get Claude-inspired theme colors based on mode.
    
    Args:
        dark_mode: True for dark theme, False for light theme
        
    Returns:
        Dictionary of theme color values
    """
    if dark_mode:
        return {
            # Backgrounds
            "bg_primary": "#0D0F1C",
            "bg_secondary": "#161B2E",
            "bg_tertiary": "#1F2638",
            "bg_overlay": "#2A3044",
            
            # Accents
            "accent_primary": "#6366F1",
            "accent_secondary": "#06B6D4",
            "accent_success": "#10B981",
            "accent_warning": "#F59E0B",
            "accent_danger": "#EF4444",
            
            # Text
            "text_primary": "#F8FAFC",
            "text_secondary": "#94A3B8",
            "text_tertiary": "#64748B",
            
            # Borders & Dividers
            "border": "#2D3548",
            "border_hover": "#3F4A62",
            
            # Special Effects
            "glow_primary": "rgba(99, 102, 241, 0.4)",
            "glow_secondary": "rgba(6, 182, 212, 0.3)",
        }
    else:
        return {
            # Backgrounds
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8FAFC",
            "bg_tertiary": "#F1F5F9",
            "bg_overlay": "#E2E8F0",
            
            # Accents
            "accent_primary": "#4F46E5",
            "accent_secondary": "#0891B2",
            "accent_success": "#059669",
            "accent_warning": "#D97706",
            "accent_danger": "#DC2626",
            
            # Text
            "text_primary": "#0F172A",
            "text_secondary": "#475569",
            "text_tertiary": "#64748B",
            
            # Borders
            "border": "#E2E8F0",
            "border_hover": "#CBD5E1",
            
            # Special Effects
            "glow_primary": "rgba(79, 70, 229, 0.15)",
            "glow_secondary": "rgba(8, 145, 178, 0.15)",
        }


def generate_claude_css(dark_mode: bool = True) -> str:
    """
    Generate complete CSS for Claude-inspired theme.
    
    Args:
        dark_mode: True for dark theme, False for light theme
        
    Returns:
        Complete CSS string ready for injection
    """
    T = get_claude_theme(dark_mode)
    
    return f"""
    <style>
    /* ═══════════════════════════════════════════════════════════════ */
    /* CLAUDE.AI-INSPIRED THEME - PROFESSIONAL & MINIMAL */
    /* ═══════════════════════════════════════════════════════════════ */
    
    /* ── Font Imports ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* ── CSS Variables ────────────────────────────────────────────── */
    :root {{
        /* Colors */
        --bg-primary: {T['bg_primary']};
        --bg-secondary: {T['bg_secondary']};
        --bg-tertiary: {T['bg_tertiary']};
        --bg-overlay: {T['bg_overlay']};
        
        --accent-primary: {T['accent_primary']};
        --accent-secondary: {T['accent_secondary']};
        --accent-success: {T['accent_success']};
        --accent-warning: {T['accent_warning']};
        --accent-danger: {T['accent_danger']};
        
        --text-primary: {T['text_primary']};
        --text-secondary: {T['text_secondary']};
        --text-tertiary: {T['text_tertiary']};
        
        --border: {T['border']};
        --border-hover: {T['border_hover']};
        
        --glow-primary: {T['glow_primary']};
        --glow-secondary: {T['glow_secondary']};
        
        /* Typography */
        --font-display: 'Space Grotesk', system-ui, -apple-system, sans-serif;
        --font-body: 'Inter', system-ui, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        
        /* Easing Functions */
        --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
        --ease-in-out-circ: cubic-bezier(0.785, 0.135, 0.15, 0.86);
        --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
        
        /* Spacing */
        --space-xs: 0.25rem;
        --space-sm: 0.5rem;
        --space-md: 1rem;
        --space-lg: 1.5rem;
        --space-xl: 2rem;
        --space-2xl: 3rem;
        
        /* Border Radius */
        --radius-sm: 0.5rem;
        --radius-md: 0.75rem;
        --radius-lg: 1rem;
        --radius-xl: 1.25rem;
        --radius-2xl: 1.5rem;
        
        /* Shadows */
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.16);
        --shadow-xl: 0 20px 60px rgba(0, 0, 0, 0.3);
    }}
    
    /* ── Global Reset ──────────────────────────────────────────────── */
    *, *::before, *::after {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    html {{
        scroll-behavior: smooth;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    
    body, .stApp {{
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    
    /* ── Hide Streamlit Chrome ─────────────────────────────────────── */
    #MainMenu, footer, header {{
        visibility: hidden;
        height: 0;
    }}
    
    .block-container {{
        padding: var(--space-lg) var(--space-xl) var(--space-xl) !important;
        max-width: 100% !important;
    }}
    
    /* ── Sidebar Styling ───────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
        padding: var(--space-lg);
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.08);
    }}
    
    [data-testid="stSidebar"] * {{
        color: var(--text-primary) !important;
    }}
    
    /* ── Sidebar Brand ────────────────────────────────────────────── */
    .sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-bottom: var(--space-lg);
        border-bottom: 1px solid var(--border);
        margin-bottom: var(--space-lg);
    }}
    
    .sidebar-logo {{
        font-size: 1.75rem;
        animation: pulse-glow 3s ease-in-out infinite;
    }}
    
    @keyframes pulse-glow {{
        0%, 100% {{ filter: drop-shadow(0 0 10px var(--glow-primary)); }}
        50% {{ filter: drop-shadow(0 0 20px var(--glow-primary)); }}
    }}
    
    .sidebar-title {{
        font-family: var(--font-display);
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* ── Sidebar Sections ──────────────────────────────────────────── */
    .sidebar-section {{
        margin: var(--space-lg) 0 var(--space-md);
        font-family: var(--font-display);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--text-tertiary);
    }}
    
    /* ── Sidebar Buttons ───────────────────────────────────────────── */
    .sidebar-button {{
        width: 100%;
        padding: 0.75rem 1rem;
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        font-family: var(--font-body);
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.2s var(--ease-out-expo);
        margin-bottom: var(--space-sm);
        display: flex;
        align-items: center;
        gap: var(--space-sm);
    }}
    
    .sidebar-button:hover {{
        background: var(--bg-overlay);
        border-color: var(--accent-primary);
        transform: translateX(4px);
    }}
    
    .sidebar-button.active {{
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.2), 
            rgba(6, 182, 212, 0.2));
        border-color: var(--accent-primary);
        box-shadow: 0 0 20px var(--glow-primary);
    }}
    
    /* ── Chat History Items ────────────────────────────────────────── */
    .chat-history-item {{
        padding: 0.75rem;
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        margin-bottom: var(--space-sm);
        cursor: pointer;
        transition: all 0.2s var(--ease-out-expo);
        font-size: 0.875rem;
        color: var(--text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .chat-history-item:hover {{
        background: var(--bg-overlay);
        border-color: var(--accent-secondary);
        transform: translateX(6px);
        color: var(--text-primary);
    }}
    
    .chat-history-item.active {{
        background: rgba(99, 102, 241, 0.15);
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        font-weight: 600;
    }}
    
    /* ── Hero Section ──────────────────────────────────────────────── */
    .dashboard-hero {{
        text-align: center;
        padding: var(--space-2xl) var(--space-xl) var(--space-2xl);
        position: relative;
    }}
    
    .hero-logo {{
        font-size: 4rem;
        margin-bottom: var(--space-md);
        animation: float 4s ease-in-out infinite;
        filter: drop-shadow(0 0 30px var(--glow-primary));
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .hero-title {{
        font-family: var(--font-display);
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, 
            var(--accent-primary) 0%, 
            var(--accent-secondary) 50%,
            var(--accent-primary) 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-x 4s ease infinite;
        margin-bottom: 0.75rem;
        line-height: 1.1;
    }}
    
    @keyframes gradient-x {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    .hero-subtitle {{
        font-family: var(--font-body);
        font-size: 1.125rem;
        color: var(--text-secondary);
        font-weight: 400;
        margin-bottom: var(--space-xl);
        line-height: 1.6;
    }}
    
    /* ── Badge Row ─────────────────────────────────────────────────── */
    .badge-row {{
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: var(--space-lg);
    }}
    
    .badge {{
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        padding: var(--space-sm) var(--space-md);
        border-radius: 2rem;
        font-family: var(--font-body);
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        transition: all 0.3s var(--ease-spring);
        cursor: pointer;
    }}
    
    .badge:hover {{
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 4px 16px var(--glow-primary);
    }}
    
    /* ── Feature Grid ──────────────────────────────────────────────── */
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: var(--space-lg);
        padding: var(--space-xl);
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    .feature-card {{
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: var(--space-xl);
        text-align: center;
        transition: all 0.4s var(--ease-out-expo);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}
    
    .feature-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    
    .feature-card:hover::before {{
        opacity: 1;
    }}
    
    .feature-card:hover {{
        transform: translateY(-8px) scale(1.02);
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-lg);
    }}
    
    .feature-icon {{
        font-size: 2.5rem;
        margin-bottom: var(--space-md);
        filter: drop-shadow(0 0 10px var(--glow-secondary));
    }}
    
    .feature-title {{
        font-family: var(--font-display);
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: var(--space-sm);
    }}
    
    .feature-desc {{
        font-family: var(--font-body);
        font-size: 0.9rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }}
    
    /* ── Buttons ───────────────────────────────────────────────────── */
    .stButton > button {{
        width: 100%;
        padding: var(--space-md);
        background: linear-gradient(135deg, 
            var(--accent-primary) 0%, 
            var(--accent-secondary) 100%);
        border: none !important;
        border-radius: var(--radius-lg) !important;
        font-family: var(--font-display) !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: white !important;
        cursor: pointer;
        transition: all 0.3s var(--ease-out-expo) !important;
        position: relative;
        overflow: hidden;
    }}
    
    .stButton > button::before {{
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
    
    .stButton > button:hover::before {{
        left: 100%;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 30px var(--glow-primary) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) scale(0.99) !important;
    }}
    
    /* ── Input Fields ──────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        width: 100%;
        padding: 0.875rem 1rem !important;
        background: var(--bg-tertiary) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-body) !important;
        font-size: 1rem !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 4px var(--glow-primary) !important;
        outline: none !important;
        background: var(--bg-secondary) !important;
    }}
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {{
        color: var(--text-tertiary) !important;
    }}
    
    /* ── Chat Messages ─────────────────────────────────────────────── */
    .chat-message {{
        padding: var(--space-md) var(--space-lg);
        margin: var(--space-md) 0;
        border-radius: var(--radius-lg);
        line-height: 1.6;
        animation: slide-in 0.3s var(--ease-out-expo);
    }}
    
    @keyframes slide-in {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .chat-message.user {{
        background: rgba(99, 102, 241, 0.1);
        border-left: 3px solid var(--accent-primary);
        margin-left: auto;
        max-width: 85%;
    }}
    
    .chat-message.assistant {{
        background: var(--bg-secondary);
        border-left: 3px solid var(--accent-secondary);
        margin-right: auto;
        max-width: 85%;
    }}
    
    .message-label {{
        font-family: var(--font-display);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: var(--space-sm);
    }}
    
    /* ── Cards ─────────────────────────────────────────────────────── */
    .claude-card {{
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: var(--space-xl);
        margin: var(--space-lg) 0;
        transition: all 0.3s var(--ease-out-expo);
    }}
    
    .claude-card:hover {{
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    
    .card-title {{
        font-family: var(--font-display);
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: var(--space-md);
    }}
    
    .card-content {{
        font-family: var(--font-body);
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }}
    
    /* ── Metrics ───────────────────────────────────────────────────── */
    [data-testid="metric-container"] {{
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: var(--space-lg) !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-testid="metric-container"]:hover {{
        border-color: var(--border-hover) !important;
        box-shadow: var(--shadow-sm) !important;
    }}
    
    [data-testid="metric-container"] label {{
        color: var(--text-tertiary) !important;
        font-family: var(--font-display) !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }}
    
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-family: var(--font-display) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }}
    
    /* ── Tabs ──────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-secondary) !important;
        border-radius: var(--radius-lg) !important;
        padding: var(--space-sm) !important;
        gap: var(--space-sm) !important;
        border: 1px solid var(--border) !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: var(--radius-md) !important;
        color: var(--text-secondary) !important;
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: var(--space-sm) var(--space-lg) !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, 
            var(--accent-primary), 
            var(--accent-secondary)) !important;
        color: white !important;
    }}
    
    .stTabs [data-baseweb="tab-panel"] {{
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: var(--space-xl) !important;
        margin-top: var(--space-md) !important;
    }}
    
    /* ── Expander ──────────────────────────────────────────────────── */
    .streamlit-expanderHeader {{
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        padding: var(--space-md) !important;
        transition: all 0.2s ease !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        border-color: var(--border-hover) !important;
        background: var(--bg-tertiary) !important;
    }}
    
    .streamlit-expanderContent {{
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
        padding: var(--space-md) !important;
    }}
    
    /* ── Progress Bar ──────────────────────────────────────────────── */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, 
            var(--accent-primary), 
            var(--accent-secondary)) !important;
        border-radius: 2rem !important;
    }}
    
    /* ── Scrollbar ─────────────────────────────────────────────────── */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg-primary);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
        transition: background 0.2s ease;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--border-hover);
    }}
    
    /* ── Divider ───────────────────────────────────────────────────── */
    hr {{
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: var(--space-xl) 0 !important;
    }}
    
    /* ── Alerts ────────────────────────────────────────────────────── */
    .stAlert {{
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--border) !important;
        padding: var(--space-md) var(--space-lg) !important;
        font-family: var(--font-body) !important;
    }}
    
    .stSuccess {{
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: var(--accent-success) !important;
        color: var(--accent-success) !important;
    }}
    
    .stInfo {{
        background: rgba(6, 182, 212, 0.1) !important;
        border-color: var(--accent-secondary) !important;
        color: var(--accent-secondary) !important;
    }}
    
    .stWarning {{
        background: rgba(245, 158, 11, 0.1) !important;
        border-color: var(--accent-warning) !important;
        color: var(--accent-warning) !important;
    }}
    
    .stError {{
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: var(--accent-danger) !important;
        color: var(--accent-danger) !important;
    }}
    
    /* ── File Uploader ─────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {{
        background: var(--bg-secondary) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-xl) !important;
        padding: var(--space-xl) !important;
        transition: all 0.3s ease !important;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: var(--accent-primary) !important;
        background: var(--bg-tertiary) !important;
        box-shadow: 0 0 20px var(--glow-primary) !important;
    }}
    
    /* ── Select Box ────────────────────────────────────────────────── */
    [data-testid="stSelectbox"] > div {{
        background: var(--bg-tertiary) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }}
    
    /* ── Dataframe ─────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        overflow: hidden;
    }}
    
    /* ── Animations for Page Load ──────────────────────────────────── */
    @keyframes fade-in-up {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .animate-fade-in {{
        animation: fade-in-up 0.6s var(--ease-out-expo) forwards;
    }}
    
    .animate-stagger-1 {{ animation-delay: 0.05s; }}
    .animate-stagger-2 {{ animation-delay: 0.1s; }}
    .animate-stagger-3 {{ animation-delay: 0.15s; }}
    .animate-stagger-4 {{ animation-delay: 0.2s; }}
    .animate-stagger-5 {{ animation-delay: 0.25s; }}
    
    </style>
    """
