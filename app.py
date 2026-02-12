"""
FINBOT - AI Financial Assistant
Main Streamlit Application

Features:
1. Upload and analyze CSV/Excel files
2. Get AI-powered financial insights
3. Interactive Q&A chatbot with conversation memory
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT, UPLOADS_DIR
from src.core.data_processor import process_file_for_rag, DataProcessor
from src.agents.analysis_agent import analysis_orchestrator
from src.agents.chatbot_agent import get_chatbot
from src.utils.helpers import (
    validate_file, 
    create_data_summary_text,
    get_insights_from_dataframe,
    clean_dataframe
)
from dotenv import load_dotenv
load_dotenv()
# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin-top: 2rem;
    }
    .metric-card {
        background: #f3f4f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #dbeafe;
        margin-left: 2rem;
    }
    .assistant-message {
        background: #f3f4f6;
        margin-right: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "data_processor" not in st.session_state:
        st.session_state.data_processor = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = "default"
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "analysis"  # or "chatbot"


def display_header():
    """Display application header"""
    st.markdown('<p class="main-header">💰 FINBOT - AI Financial Assistant</p>', unsafe_allow_html=True)
    st.markdown("Analyze your financial data and get intelligent insights with AI-powered assistance.")
    st.markdown("---")


def handle_file_upload():
    """Handle file upload and processing"""
    uploaded_file = st.file_uploader(
        "Upload your financial data (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV or Excel file containing your financial data"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        file_path = UPLOADS_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Validate file
        is_valid, error_msg = validate_file(str(file_path))
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return None
        
        # Process file
        with st.spinner("Processing file..."):
            try:
                processor = process_file_for_rag(str(file_path))
                st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
                return processor
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                return None
    
    return None


def display_data_overview(processor: DataProcessor):
    """Display overview of the uploaded data"""
    st.markdown('<p class="sub-header">📊 Data Overview</p>', unsafe_allow_html=True)
    
    metadata = processor.get_metadata()
    df = processor.get_dataframe()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rows", f"{metadata['shape']['rows']:,}")
    with col2:
        st.metric("Total Columns", metadata['shape']['columns'])
    with col3:
        st.metric("Numeric Columns", len(metadata['numeric_columns']))
    with col4:
        missing_pct = round((sum(metadata['missing_values'].values()) / 
                           (metadata['shape']['rows'] * metadata['shape']['columns'])) * 100, 1)
        st.metric("Data Completeness", f"{100 - missing_pct}%")
    
    # Show sample data
    with st.expander("📋 View Sample Data", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)
    
    # Show column information
    with st.expander("📑 Column Information", expanded=False):
        col_info = []
        for col in metadata['columns']:
            info = processor.get_column_info(col)
            col_info.append({
                "Column": col,
                "Type": info.get("dtype", "Unknown"),
                "Missing": info.get("missing", 0),
                "Unique": info.get("unique_values", 0)
            })
        st.dataframe(pd.DataFrame(col_info), use_container_width=True)


def run_analysis(processor: DataProcessor):
    """Run financial analysis on the data"""
    st.markdown('<p class="sub-header">🔍 AI Analysis</p>', unsafe_allow_html=True)
    
    if st.button("🚀 Analyze Data", type="primary"):
        with st.spinner("Analyzing your data with AI..."):
            try:
                # Get data summary
                data_summary = create_data_summary_text(processor.get_dataframe())
                
                # Run analysis
                result = analysis_orchestrator.run_analysis(
                    data_summary=data_summary,
                    df=processor.get_dataframe()
                )
                
                st.session_state.analysis_result = result
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                return
    
    # Display analysis results
    if st.session_state.analysis_result:
        display_analysis_results(st.session_state.analysis_result)


def display_analysis_results(result: dict):
    """Display the analysis results"""
    
    # Health Score and Risk Level
    col1, col2 = st.columns(2)
    with col1:
        health_score = result.get("health_score", 0)
        st.metric(
            "💚 Financial Health Score",
            f"{health_score}/100",
            delta="Good" if health_score >= 70 else "Needs Attention"
        )
    with col2:
        risk_level = result.get("risk_level", "Unknown")
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "⚪")
        st.metric("⚠️ Risk Level", f"{risk_emoji} {risk_level}")
    
    # Summary
    st.markdown("### 📝 Summary")
    st.info(result.get("summary", "No summary available"))
    
    # Key Insights
    if "key_insights" in result and result["key_insights"]:
        st.markdown("### 💡 Key Insights")
        for insight in result["key_insights"]:
            st.markdown(f"- {insight}")
    
    # Trends
    if "trends" in result and result["trends"]:
        st.markdown("### 📈 Identified Trends")
        for trend in result["trends"]:
            st.markdown(f"- {trend}")
    
    # Concerns
    if "concerns" in result and result["concerns"]:
        st.markdown("### ⚠️ Concerns")
        for concern in result["concerns"]:
            st.warning(concern)
    
    # Recommendations
    if "recommendations" in result and result["recommendations"]:
        st.markdown("### 🎯 Recommendations")
        for rec in result["recommendations"]:
            st.success(rec)


def run_chatbot(processor: DataProcessor):
    """OPTIMIZED: Run the interactive chatbot with proper data context"""
    st.markdown('<p class="sub-header">💬 Ask Questions About Your Data</p>', unsafe_allow_html=True)
    
    # Get chatbot instance
    chatbot = get_chatbot(st.session_state.session_id)
    
    # Set data context WITH processor reference
    if processor:
        data_summary = create_data_summary_text(processor.get_dataframe(), max_rows=3)
        chatbot.chatbot.set_data_context(data_summary, processor)  # Pass processor!
    
    # Display chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your financial data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # OPTIMIZED: Pass data_processor for direct data access
                    response_data = chatbot.process_message(
                        prompt, 
                        data_summary=data_summary if processor else None,
                        data_processor=processor  # Pass the processor!
                    )
                    response = response_data.get("response", "I couldn't process that request.")
                    
                    st.markdown(response)
                    
                    # Add suggestions if available
                    if "suggestions" in response_data:
                        st.markdown("**Suggested questions:**")
                        for suggestion in response_data["suggestions"]:
                            st.markdown(f"- {suggestion}")
                    
                    # Add to message history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Clear conversation button
    if st.session_state.messages:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                chatbot.clear_conversation()
                st.rerun()

def main():
    """Main application logic"""
    initialize_session_state()
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Control Panel")
        
        # Mode selection
        mode = st.radio(
            "Choose Mode:",
            ["📊 Analysis", "💬 Chatbot Q&A"],
            index=0 if st.session_state.current_mode == "analysis" else 1
        )
        
        st.session_state.current_mode = "analysis" if "Analysis" in mode else "chatbot"
        
        st.markdown("---")
        st.markdown("### 📁 File Upload")
    
    # File upload
    processor = handle_file_upload()
    
    if processor:
        st.session_state.data_processor = processor
    
    # Main content area
    if st.session_state.data_processor:
        # Display data overview
        display_data_overview(st.session_state.data_processor)
        
        st.markdown("---")
        
        # Mode-specific content
        if st.session_state.current_mode == "analysis":
            run_analysis(st.session_state.data_processor)
        else:
            run_chatbot(st.session_state.data_processor)
    
    else:
        st.info("👆 Please upload a CSV or Excel file to get started!")
        
        # Show example
        with st.expander("ℹ️ How to use FINBOT", expanded=True):
            st.markdown("""
            ### Getting Started
            
            1. **Upload Your Data**: Click 'Browse files' and select a CSV or Excel file
            2. **Choose Your Mode**:
               - **📊 Analysis Mode**: Get comprehensive AI analysis of your financial data
               - **💬 Chatbot Mode**: Ask questions and get answers about your data
            
            ### What FINBOT Can Do
            
            **Analysis Mode:**
            - Calculate financial health scores
            - Identify trends and patterns
            - Assess risk levels
            - Provide actionable recommendations
            
            **Chatbot Mode:**
            - Answer questions about your data
            - Explain specific metrics
            - Compare different aspects of your finances
            - Remember conversation context
            
            ### Tips for Best Results
            
            - Ensure your data has clear column names
            - Include date columns for trend analysis
            - Numeric values should be properly formatted
            - Remove any sensitive personal information before upload
            """)


if __name__ == "__main__":
    main()
