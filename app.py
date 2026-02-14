"""
FINBOT v4 - Advanced Data Intelligence Platform
Main Streamlit Application

Author: FINBOT Team
Version: 4.0.0 (Phase 1: RAG & Tools)
"""

# Force torch to load first (fixes Windows DLL initialization with Streamlit)
import torch

import streamlit as st
import pandas as pd
import os
import logging
from config import settings
from utils.data_loader import DataLoader
from utils.helpers import handle_error, print_startup_summary, clean_dataframe_display
from analyzers.insight_generator import InsightGenerator
from chatbot.qa_chain import EnhancedQAChain, DataContextManager
# ============================================================================
# SUPPRESS NOISY WARNINGS
# ============================================================================

import warnings

# Suppress specific warnings
warnings.filterwarnings('ignore', message='.*torch.classes.*')
warnings.filterwarnings('ignore', message='.*Arrow table.*')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='streamlit')

# Reduce httpx logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

# Set environment variables to reduce noise
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Custom logging format for cleaner output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'  # Just show time, not full date
)

# Create console handler with color (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter with clean output
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(formatter)

# Get root logger and update
logger = logging.getLogger(__name__)


def initialize_app():
    """Initialize application on first run"""
    if 'initialized' not in st.session_state:
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 Initializing FINBOT v4...")
        progress_bar.progress(20)
        
        # Initialize knowledge base
        try:
            status_text.text("📚 Loading knowledge base...")
            kb_manager = get_knowledge_base_manager()
            if rag_config.AUTO_LOAD_KNOWLEDGE:
                kb_manager.create_default_knowledge()
                results = kb_manager.load_all_knowledge()
            progress_bar.progress(60)
        except Exception as e:
            logger.warning(f"Could not load knowledge base: {e}")
        
        # Initialize tools
        try:
            status_text.text("🛠️ Loading tools...")
            tool_registry = get_tool_registry()
            tools_list = tool_registry.list_tools()
            progress_bar.progress(80)
        except Exception as e:
            logger.warning(f"Could not load tools: {e}")
        
        status_text.text("✅ Ready!")
        progress_bar.progress(100)
        
        # Clear progress indicators
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        st.session_state.initialized = True
        logger.info("✅ FINBOT v4 initialized")


# Page configuration
st.set_page_config(
    page_title="FINBOT v4 - AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .insight-box {
        background: #eff6ff;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #3b82f6;
        margin: 1rem 0;
    }
    .rag-source-box {
        background: #f0fdf4;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bbf7d0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .chat-message {
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        line-height: 1.6;
    }
    .user-message {
        background: #f1f5f9;
        border-left: 4px solid #64748b;
    }
    .bot-message {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border-radius: 0.5rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'mode' not in st.session_state:
    st.session_state.mode = "Analysis"
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'initialized' not in st.session_state:
    # Print startup summary to console
    print_startup_summary(st.session_state.session_id)
    st.session_state.initialized = True

# Header
st.markdown('<h1 class="main-header">🤖 FINBOT v4</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Data Intelligence with RAG & Tools</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your data file for analysis"
    )
    
    if uploaded_file:
        # Save uploaded file
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_FOLDER, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Load data
        df, error = DataLoader.load_file(file_path)
        
        if error:
            st.error(f"❌ {error}")
        else:
            # Clean DataFrame to avoid Arrow warnings
            df = DataLoader.clean_dataframe_for_streamlit(df)
            
            if st.session_state.data is None or not df.equals(st.session_state.data):
                st.session_state.data = df
                # Reset QA chain when new data is loaded
                st.session_state.qa_chain = None
                st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
            
            # Show basic info
            st.info(f"📊 Shape: {df.shape}")
    
    # Mode selector
    st.markdown("---")
    st.markdown("### 🎯 Select Mode")
    
    mode = st.radio(
        "Choose operation mode:",
        ["📊 Comprehensive Analysis", "💬 RAG Chatbot"],
        label_visibility="collapsed"
    )
    
    st.session_state.mode = "Analysis" if "Analysis" in mode else "Q&A"
    
    # Settings
    st.markdown("---")
    st.markdown("### ⚙️ Actions")
    
    if st.button("🗑️ Clear Session"):
        st.session_state.data = None
        st.session_state.analysis_result = None
        st.session_state.qa_chain = None
        st.session_state.chat_history = []
        st.rerun()
    
    # About
    st.markdown("---")
    st.markdown("""
    ### ℹ️ New in v4
    - 📚 **RAG Knowledge Base**: Uses historical analyses and domain knowledge
    - 🛠️ **Smart Tools**: Python REPL, Chart Generator, Calendar
    - 🧠 **Context Awareness**: Remembers conversation history
    """)

# Main content area
if st.session_state.data is None:
    # Welcome screen
    st.markdown("""
    <div class="insight-box">
        <h2>👋 Welcome to FINBOT v4!</h2>
        <p>This version introduces Retrieval Augmented Generation (RAG) and Agentic Tools.</p>
        <p><strong>Upload your data to get started with:</strong></p>
        <ul>
            <li><strong>📊 Analysis Mode:</strong> Deep deep statistical insights and pattern detection</li>
            <li><strong>💬 RAG Chatbot:</strong> data-aware Q&A with access to domain knowledge and specialized tools</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # RAG Status
    with st.expander("📚 RAG System Status"):
        st.write("Checking knowledge base components...")
        try:
            from rag.retriever import get_retriever
            st.success("✅ Smart Retriever: Active")
            st.success("✅ Knowledge Base: Connected")
            st.success("✅ Tool Registry: Ready")
        except ImportError:
            st.error("❌ RAG components not found. Please run setup.")

else:
    # Data is loaded
    
    if st.session_state.mode == "Analysis":
        # ANALYSIS MODE
        st.markdown("## 📊 Comprehensive Analysis")
        
        # Show data preview
        with st.expander("👁️ Preview Data", expanded=False):
            clean_dataframe_display(st.session_state.data)
        
        # Analyze button
        if st.button("🚀 Analyze Data", type="primary", use_container_width=True):
            with st.spinner("🔍 Running Insight Generator... (This usually takes 10-20 seconds)"):
                try:
                    # Generate insights using the existing analyzer
                    generator = InsightGenerator(st.session_state.data)
                    result = generator.generate_comprehensive_insights()
                    st.session_state.analysis_result = result
                    st.success("✅ Analysis complete!" )
                    st.info("💡 Tip: Switch to RAG Chatbot mode to ask questions about this analysis")
                except Exception as e:
                    handle_error(e, "Data Analysis")
        
        # Display results
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            # Executive Summary
            st.markdown(f"""
            <div class="metric-card">
                <h3>📋 Executive Summary</h3>
                <p>{result.get('executive_summary', 'No summary generated.')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tabs for details
            tab1, tab2, tab3 = st.tabs(["💡 AI Insights", "📊 Statistics", "🔍 Patterns"])
            
            with tab1:
                st.markdown(result.get('ai_insights', 'No insights generated.'))
            
            with tab2:
                stats = result.get('statistical_analysis', {})
                if stats:
                    st.json(stats.get('basic_info', {}))
            
            with tab3:
                patterns = result.get('pattern_analysis', {})
                if patterns:
                    for p_type, p_list in patterns.items():
                        if p_list:
                            st.subheader(p_type.replace('_', ' ').title())
                            for p in p_list:
                                st.write(f"- {p.get('interpretation', str(p))}")

    else:
        # Q&A MODE (RAG Enabled)
        st.markdown("## 💬 AI Data Assistant (RAG Enabled)")
        
        # Initialize QA chain
        if st.session_state.qa_chain is None:
            with st.status("Initializing RAG System...", expanded=True) as status:
                try:
                    status.write("📚 Loading knowledge base...")
                    status.write("🛠️ Initializing tools...")
                    status.write("🧠 Setting up AI assistant...")
                    
                    st.session_state.qa_chain = EnhancedQAChain(
                        df=st.session_state.data,
                        session_id=st.session_state.session_id
                    )
                    
                    status.update(label="✅ Assistant Ready!", state="complete")
                except Exception as e:
                    status.update(label="❌ Initialization Failed", state="error")
                    handle_error(e, "QA Chain Initialization")
        
        # Chat interface
        chat_container = st.container()
        
        # Display chat history from session state
        with chat_container:
            for role, content in st.session_state.chat_history:
                css_class = "user-message" if role == "user" else "bot-message"
                name = "👤 You" if role == "user" else "🤖 FINBOT"
                
                st.markdown(f"""
                <div class="chat-message {css_class}">
                    <strong>{name}:</strong><br>
                    {content}
                </div>
                """, unsafe_allow_html=True)
        
        # Input area
        with st.form(key="chat_form"):
            col1, col2 = st.columns([6, 1])
            with col1:
                user_input = st.text_input(
                    "Ask about your data...",
                    placeholder="e.g., 'Analyze the trend of sales over time' or 'What best practices apply here?'",
                    label_visibility="collapsed"
                )
            with col2:
                submit_button = st.form_submit_button("Send 🚀", type="primary", use_container_width=True)
        
        if submit_button and user_input:
            # Add user message
            st.session_state.chat_history.append(("user", user_input))
            
            # Better loading indicators
            with st.status("Processing your question...", expanded=False) as status:
                try:
                    status.write("🔍 Analyzing your question...")
                    status.write("📚 Searching knowledge base...")
                    status.write("🧠 Generating insights...")
                    
                    # Get response from RAG chain
                    response = st.session_state.qa_chain.ask(user_input)
                    
                    status.update(label="✅ Response generated", state="complete")
                    
                    # Add bot message
                    st.session_state.chat_history.append(("bot", response))
                    
                    # Rerender to show new messages
                    st.rerun()
                    
                except Exception as e:
                    status.update(label="❌ Error occurred", state="error")
                    handle_error(e, "Question Processing")
        
        # RAG Context Debugger
        with st.expander("🕵️ Debug: View Retrieved Context"):
            if st.session_state.qa_chain and hasattr(st.session_state.qa_chain, 'last_context'):
                 st.write(st.session_state.qa_chain.last_context)
            else:
                st.info("Ask a question to see retrieved RAG context.")


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.8rem;">
    FINBOT v4.0.0 | Phase 1: RAG Infrastructure & Agentic Tools
</div>
""", unsafe_allow_html=True)

