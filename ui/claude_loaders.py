"""
Claude-inspired loading animations for Vishleshak AI
Professional, smooth, confidence-inspiring loaders
"""

import streamlit as st


def show_claude_loader(loader_type: str = "orbital", text: str = "Loading...") -> None:
    """
    Display Claude-inspired loading animation.
    
    Args:
        loader_type: "orbital", "circular", or "dots"
        text: Loading message to display
    """
    dark_mode = st.session_state.get("dark_mode", True)
    
    # Theme colors
    if dark_mode:
        primary = "#6366F1"
        secondary = "#06B6D4"
        success = "#10B981"
        bg = "rgba(13, 15, 28, 0.95)"
        text_color = "#F8FAFC"
    else:
        primary = "#4F46E5"
        secondary = "#0891B2"
        success = "#059669"
        bg = "rgba(255, 255, 255, 0.95)"
        text_color = "#0F172A"
    
    if loader_type == "orbital":
        st.markdown(f"""
        <div class="loader-overlay">
            <div class="loader-container">
                <div class="orbital-spinner">
                    <div class="orbit orbit-1"></div>
                    <div class="orbit orbit-2"></div>
                    <div class="orbit orbit-3"></div>
                </div>
                <div class="loader-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loader-overlay {{
            position: fixed;
            inset: 0;
            background: {bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.2s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loader-container {{
            text-align: center;
        }}
        
        .orbital-spinner {{
            width: 80px;
            height: 80px;
            position: relative;
            margin: 0 auto 1.5rem;
        }}
        
        .orbit {{
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid transparent;
            animation: orbit 1.2s ease-in-out infinite;
        }}
        
        .orbit-1 {{
            border-top-color: {primary};
            animation-delay: 0s;
        }}
        
        .orbit-2 {{
            border-top-color: {secondary};
            animation-delay: 0.15s;
            width: 70%;
            height: 70%;
            top: 15%;
            left: 15%;
        }}
        
        .orbit-3 {{
            border-top-color: {success};
            animation-delay: 0.3s;
            width: 40%;
            height: 40%;
            top: 30%;
            left: 30%;
        }}
        
        @keyframes orbit {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loader-text {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: {text_color};
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    elif loader_type == "circular":
        st.markdown(f"""
        <div class="loader-overlay">
            <div class="loader-container">
                <div class="circular-loader"></div>
                <div class="loader-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loader-overlay {{
            position: fixed;
            inset: 0;
            background: {bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.2s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loader-container {{
            text-align: center;
        }}
        
        .circular-loader {{
            width: 80px;
            height: 80px;
            border: 4px solid rgba(99, 102, 241, 0.1);
            border-top-color: {primary};
            border-right-color: {secondary};
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
            margin: 0 auto 1.5rem;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loader-text {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: {text_color};
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    else:  # dots
        st.markdown(f"""
        <div class="loader-overlay">
            <div class="loader-container">
                <div class="dots-loader">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
                <div class="loader-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loader-overlay {{
            position: fixed;
            inset: 0;
            background: {bg};
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.2s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loader-container {{
            text-align: center;
        }}
        
        .dots-loader {{
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            margin: 0 auto 1.5rem;
        }}
        
        .dot {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: {primary};
            animation: bounce 1.4s ease-in-out infinite;
        }}
        
        .dot:nth-child(1) {{
            animation-delay: 0s;
            background: {primary};
        }}
        
        .dot:nth-child(2) {{
            animation-delay: 0.2s;
            background: {secondary};
        }}
        
        .dot:nth-child(3) {{
            animation-delay: 0.4s;
            background: {success};
        }}
        
        @keyframes bounce {{
            0%, 80%, 100% {{ 
                transform: scale(0);
                opacity: 0.5;
            }}
            40% {{ 
                transform: scale(1);
                opacity: 1;
            }}
        }}
        
        .loader-text {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: {text_color};
        }}
        </style>
        """, unsafe_allow_html=True)


def show_progress_loader(progress: int, text: str = "Processing...") -> None:
    """
    Display progress loader with percentage.
    
    Args:
        progress: Progress value (0-100)
        text: Loading message
    """
    dark_mode = st.session_state.get("dark_mode", True)
    
    if dark_mode:
        primary = "#6366F1"
        secondary = "#06B6D4"
        bg = "rgba(13, 15, 28, 0.95)"
        text_color = "#F8FAFC"
        track_color = "rgba(99, 102, 241, 0.1)"
    else:
        primary = "#4F46E5"
        secondary = "#0891B2"
        bg = "rgba(255, 255, 255, 0.95)"
        text_color = "#0F172A"
        track_color = "rgba(79, 70, 229, 0.1)"
    
    st.markdown(f"""
    <div class="loader-overlay">
        <div class="loader-container">
            <div class="progress-circle">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" fill="none" 
                            stroke="{track_color}" stroke-width="8"/>
                    <circle cx="60" cy="60" r="54" fill="none" 
                            stroke="url(#gradient)" stroke-width="8"
                            stroke-dasharray="339.292" 
                            stroke-dashoffset="{339.292 * (1 - progress/100)}"
                            stroke-linecap="round"
                            transform="rotate(-90 60 60)"
                            style="transition: stroke-dashoffset 0.3s ease;"/>
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:{primary};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:{secondary};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <text x="60" y="65" text-anchor="middle" 
                          font-family="Space Grotesk, sans-serif" 
                          font-size="24" font-weight="700" fill="{text_color}">
                        {progress}%
                    </text>
                </svg>
            </div>
            <div class="loader-text">{text}</div>
        </div>
    </div>
    
    <style>
    .loader-overlay {{
        position: fixed;
        inset: 0;
        background: {bg};
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.2s ease;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    .loader-container {{
        text-align: center;
    }}
    
    .progress-circle {{
        margin: 0 auto 1.5rem;
        filter: drop-shadow(0 0 20px {primary});
    }}
    
    .loader-text {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: {text_color};
    }}
    </style>
    """, unsafe_allow_html=True)
