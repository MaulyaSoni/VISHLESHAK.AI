"""
Advanced Loading Animations for Vishleshak AI
Includes gear animations, circular progress, blur backgrounds
"""

import streamlit as st


def show_loading_animation(animation_type="gear", text="Loading...", progress=None):
    """
    Display advanced loading animation with blur background.
    
    Args:
        animation_type: "gear", "circle", "spinner"
        text: Loading text to display
        progress: Optional progress value (0-100) for circular completion
    """
    dark_mode = st.session_state.get("dark_mode", True)
    
    # Claude theme colors
    if dark_mode:
        accent = "#6366F1"  # indigo
        accent2 = "#06B6D4"  # cyan
        bg_overlay = "rgba(13, 15, 28, 0.95)"
        text_color = "#F8FAFC"
    else:
        accent = "#4F46E5"  # deeper indigo
        accent2 = "#0891B2"  # deeper cyan
        bg_overlay = "rgba(255, 255, 255, 0.95)"
        text_color = "#0F172A"
    
    # Gear animation
    if animation_type == "gear":
        st.markdown(f"""
        <div class="loading-overlay">
            <div class="loading-content">
                <div class="gear-container">
                    <div class="gear gear-large">
                        <div class="gear-inner"></div>
                    </div>
                    <div class="gear gear-small" style="animation-direction: reverse;">
                        <div class="gear-inner"></div>
                    </div>
                </div>
                <div class="loading-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: {bg_overlay};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loading-content {{
            text-align: center;
        }}
        
        .gear-container {{
            position: relative;
            width: 120px;
            height: 120px;
            margin: 0 auto 1.5rem;
        }}
        
        .gear {{
            position: absolute;
            border-radius: 50%;
            border: 4px solid {accent};
            animation: rotateGear 2s linear infinite;
        }}
        
        .gear-large {{
            width: 80px;
            height: 80px;
            top: 20px;
            left: 0;
            box-shadow: 0 0 30px {accent}66, inset 0 0 20px {accent}33;
        }}
        
        .gear-small {{
            width: 50px;
            height: 50px;
            top: 0;
            right: 0;
            box-shadow: 0 0 20px {accent}66, inset 0 0 15px {accent}33;
        }}
        
        .gear-inner {{
            position: absolute;
            width: 60%;
            height: 60%;
            border-radius: 50%;
            border: 2px solid {accent};
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: inset 0 0 10px {accent}55;
        }}
        
        .gear::before {{
            content: '';
            position: absolute;
            width: 8px;
            height: 8px;
            background: {accent};
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 10px {accent};
        }}
        
        @keyframes rotateGear {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: {text_color};
            background: linear-gradient(135deg, {accent}, #FF0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: pulse 2s ease-in-out infinite;
            text-shadow: 0 0 20px {accent}44;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Circle progress animation
    elif animation_type == "circle":
        progress_val = progress if progress is not None else 0
        st.markdown(f"""
        <div class="loading-overlay">
            <div class="loading-content">
                <div class="circle-progress">
                    <svg width="140" height="140" viewBox="0 0 140 140">
                        <circle cx="70" cy="70" r="60" class="circle-bg"/>
                        <circle cx="70" cy="70" r="60" class="circle-progress-bar"
                                style="--progress: {progress_val};"/>
                        <text x="70" y="75" class="circle-text">{progress_val}%</text>
                    </svg>
                </div>
                <div class="loading-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: {bg_overlay};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loading-content {{
            text-align: center;
        }}
        
        .circle-progress {{
            margin: 0 auto 1.5rem;
            filter: drop-shadow(0 0 20px {accent}44);
        }}
        
        .circle-bg {{
            fill: none;
            stroke: {accent}22;
            stroke-width: 8;
        }}
        
        .circle-progress-bar {{
            fill: none;
            stroke: {accent};
            stroke-width: 8;
            stroke-linecap: round;
            stroke-dasharray: 377;
            stroke-dashoffset: calc(377 - (377 * var(--progress)) / 100);
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
            animation: progressGlow 2s ease-in-out infinite;
            filter: drop-shadow(0 0 8px {accent});
        }}
        
        @keyframes progressGlow {{
            0%, 100% {{ filter: drop-shadow(0 0 8px {accent}); }}
            50% {{ filter: drop-shadow(0 0 16px {accent}); }}
        }}
        
        .circle-text {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 28px;
            font-weight: 700;
            fill: {accent};
            text-anchor: middle;
            dominant-baseline: middle;
        }}
        
        .loading-text {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: {text_color};
            background: linear-gradient(135deg, {accent}, #FF0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Simple spinner
    else:
        st.markdown(f"""
        <div class="loading-overlay">
            <div class="loading-content">
                <div class="spinner-ring">
                    <div></div><div></div><div></div><div></div>
                </div>
                <div class="loading-text">{text}</div>
            </div>
        </div>
        
        <style>
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: {bg_overlay};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .loading-content {{
            text-align: center;
        }}
        
        .spinner-ring {{
            display: inline-block;
            position: relative;
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
        }}
        
        .spinner-ring div {{
            box-sizing: border-box;
            display: block;
            position: absolute;
            width: 64px;
            height: 64px;
            margin: 8px;
            border: 4px solid {accent};
            border-radius: 50%;
            animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
            border-color: {accent} transparent transparent transparent;
            filter: drop-shadow(0 0 10px {accent}66);
        }}
        
        .spinner-ring div:nth-child(1) {{ animation-delay: -0.45s; }}
        .spinner-ring div:nth-child(2) {{ animation-delay: -0.3s; }}
        .spinner-ring div:nth-child(3) {{ animation-delay: -0.15s; }}
        
        @keyframes spinner-ring {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: {text_color};
            background: linear-gradient(135deg, {accent}, #FF0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        </style>
        """, unsafe_allow_html=True)


def inject_loader_styles():
    """Inject reusable loader styles into the page - Claude theme"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    </style>
    """, unsafe_allow_html=True)
