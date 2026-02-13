"""
FINBOT v4 - Advanced Data Intelligence Platform
Main Streamlit Application

Author: FINBOT Team
Version: 4.0.0
"""

import streamlit as st
import pandas as pd
from config import settings
from utils.data_loader import DataLoader
from analyzers.insight_generator import InsightGenerator
from chatbot.qa_chain import DataContextManager
import os

# Page configuration
st.set_page_config(
    page_title=settings.PAGE_TITLE,
    page_icon=settings.PAGE_ICON,
    layout=settings.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        background: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .insight-box {
        background: #eff6ff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fef3c7;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e0e7ff;
        margin-left: 2rem;
    }
    .bot-message {
        background: #f3f4f6;
        margin-right: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border-radius: 0.5rem;
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
if 'context_manager' not in st.session_state:
    st.session_state.context_manager = DataContextManager()
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Header
st.markdown('<h1 class="main-header">🤖 FINBOT v4</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Data Intelligence Platform with AI-Powered Analysis & Q&A</p>', unsafe_allow_html=True)

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
            st.session_state.data = df
            st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
            
            # Show basic info
            file_info = DataLoader.get_file_info(file_path)
            st.info(f"📊 File Size: {file_info['size_mb']} MB")
    
    # Mode selector
    st.markdown("---")
    st.markdown("### 🎯 Select Mode")
    
    mode = st.radio(
        "Choose operation mode:",
        ["📊 Analysis", "💬 Q&A Chatbot"],
        label_visibility="collapsed"
    )
    
    if mode == "📊 Analysis":
        st.session_state.mode = "Analysis"
    else:
        st.session_state.mode = "Q&A"
    
    # Settings
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    
    if st.button("🗑️ Clear All Data"):
        st.session_state.data = None
        st.session_state.analysis_result = None
        st.session_state.qa_chain = None
        st.rerun()
    
    # About
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **FINBOT v4** is an advanced data intelligence platform powered by:
    - 📊 Comprehensive Statistical Analysis
    - 🔍 Pattern Detection & Anomaly Identification
    - 💡 AI-Powered Insights (Claude-level)
    - 💬 Conversational Q&A with Memory
    - 🎯 Actionable Recommendations
    
    **Powered by:** Groq LLaMA 3.1 70B
    """)

# Main content area
if st.session_state.data is None:
    # Welcome screen
    st.markdown("""
    <div class="insight-box">
        <h2>👋 Welcome to FINBOT v4!</h2>
        <p>Upload your CSV or Excel file to get started with:</p>
        <ul>
            <li><strong>📊 Analysis Mode:</strong> Get comprehensive statistical analysis, pattern detection, and AI-powered insights</li>
            <li><strong>💬 Q&A Mode:</strong> Ask questions about your data and get intelligent answers with conversation memory</li>
        </ul>
        <p><strong>Supported formats:</strong> CSV, XLSX, XLS | <strong>Max size:</strong> 50 MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show example questions
    st.markdown("### 💡 Example Questions You Can Ask:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Statistical Questions:**
        - What's the average value of column X?
        - How many records have Y > 100?
        - What's the correlation between A and B?
        - Show me the distribution of categories
        """)
    
    with col2:
        st.markdown("""
        **Insight Questions:**
        - What are the main trends in this data?
        - Are there any outliers I should know about?
        - What patterns do you see?
        - What recommendations do you have?
        """)

else:
    # Data loaded - show appropriate interface based on mode
    
    if st.session_state.mode == "Analysis":
        # ANALYSIS MODE
        st.markdown("## 📊 Comprehensive Analysis")
        
        # Show data preview
        with st.expander("👁️ Preview Data", expanded=False):
            st.dataframe(st.session_state.data.head(10), use_container_width=True)
        
        # Analyze button
        if st.button("🚀 Analyze Data", type="primary", use_container_width=True):
            with st.spinner("🔍 Performing comprehensive analysis... This may take a moment."):
                try:
                    # Generate insights
                    generator = InsightGenerator(st.session_state.data)
                    result = generator.generate_comprehensive_insights()
                    st.session_state.analysis_result = result
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
        
        # Display results
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            # Executive Summary
            st.markdown(f"""
            <div class="metric-card">
                <h3>📋 Executive Summary</h3>
                <p>{result['executive_summary']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tabs for different sections
            tab1, tab2, tab3, tab4 = st.tabs([
                "💡 AI Insights",
                "📊 Statistical Analysis",
                "🔍 Pattern Detection",
                "🎯 Recommendations"
            ])
            
            with tab1:
                st.markdown("### 💡 AI-Powered Insights")
                st.markdown(result['ai_insights'])
            
            with tab2:
                st.markdown("### 📊 Statistical Analysis")
                
                # Basic Info
                basic_info = result['statistical_analysis']['basic_info']
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Rows", f"{basic_info['total_rows']:,}")
                with col2:
                    st.metric("Total Columns", basic_info['total_columns'])
                with col3:
                    st.metric("Numeric Columns", basic_info['numeric_columns'])
                with col4:
                    st.metric("Categorical Columns", basic_info['categorical_columns'])
                
                # Numeric Analysis
                if result['statistical_analysis']['numeric_analysis']:
                    st.markdown("#### Numeric Columns")
                    numeric_df = pd.DataFrame(result['statistical_analysis']['numeric_analysis']).T
                    st.dataframe(numeric_df, use_container_width=True)
                
                # Correlation Analysis
                if result['statistical_analysis']['correlation_analysis'].get('strong_correlations'):
                    st.markdown("#### Strong Correlations")
                    for corr in result['statistical_analysis']['correlation_analysis']['strong_correlations'][:10]:
                        st.markdown(f"- **{corr['variable_1']}** ↔ **{corr['variable_2']}**: {corr['correlation']:.3f} ({corr['strength']} {corr['direction']})")
            
            with tab3:
                st.markdown("### 🔍 Pattern Detection")
                
                patterns = result['pattern_analysis']
                
                # Trends
                if patterns['trend_patterns']:
                    st.markdown("#### 📈 Trend Patterns")
                    for trend in patterns['trend_patterns']:
                        st.markdown(f"- {trend['interpretation']}")
                
                # Categorical Patterns
                if patterns['categorical_patterns']:
                    st.markdown("#### 📊 Categorical Patterns")
                    for pattern in patterns['categorical_patterns']:
                        st.markdown(f"- {pattern['interpretation']}")
                
                # Anomalies
                if patterns['anomaly_patterns']:
                    st.markdown("""
                    <div class="warning-box">
                        <h4>⚠️ Anomaly Patterns</h4>
                    """, unsafe_allow_html=True)
                    for anomaly in patterns['anomaly_patterns']:
                        st.markdown(f"- {anomaly['interpretation']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Data Quality Issues
                if patterns['data_quality_patterns']:
                    st.markdown("#### 🔍 Data Quality Issues")
                    for issue in patterns['data_quality_patterns']:
                        st.markdown(f"- {issue['interpretation']}")
            
            with tab4:
                st.markdown("### 🎯 Recommendations")
                
                if result['recommendations']:
                    for i, rec in enumerate(result['recommendations'], 1):
                        st.markdown(f"{i}. {rec}")
                else:
                    st.info("No specific recommendations at this time.")
    
    else:
        # Q&A MODE
        st.markdown("## 💬 Ask Questions About Your Data")
        
        # Initialize Q&A chain if not exists
        if st.session_state.qa_chain is None:
            with st.spinner("Initializing chatbot..."):
                st.session_state.qa_chain = st.session_state.context_manager.create_context(
                    st.session_state.session_id,
                    st.session_state.data
                )
                st.success("✅ Chatbot ready!")
        
        # Show data preview
        with st.expander("👁️ Preview Data", expanded=False):
            st.dataframe(st.session_state.data.head(10), use_container_width=True)
        
        # Chat interface
        st.markdown("### 💭 Conversation")
        
        # Display chat history
        chat_history = st.session_state.qa_chain.get_chat_history()
        
        if chat_history:
            for msg in chat_history:
                if msg['type'] == 'human':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>👤 You:</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🤖 FINBOT:</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👋 Start a conversation! Ask me anything about your data.")
        
        # Question input
        col1, col2 = st.columns([5, 1])
        
        with col1:
            question = st.text_input(
                "Ask a question:",
                placeholder="e.g., What's the average attendance rate?",
                label_visibility="collapsed"
            )
        
        with col2:
            ask_button = st.button("Ask", type="primary", use_container_width=True)
        
        # Example questions
        with st.expander("💡 Example Questions"):
            example_questions = [
                "What's the summary of this dataset?",
                "How many unique values are in each column?",
                "What are the top 5 categories by frequency?",
                "Are there any missing values?",
                "What's the correlation between X and Y?",
                "Show me statistics for column X",
                "What patterns do you notice?",
                "What's the average value of X?",
                "How many rows have Y > threshold?"
            ]
            
            for eq in example_questions:
                if st.button(eq, key=f"example_{eq}"):
                    question = eq
                    ask_button = True
        
        # Process question
        if ask_button and question:
            with st.spinner("🤔 Thinking..."):
                try:
                    result = st.session_state.qa_chain.ask_with_data_analysis(question)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.qa_chain.clear_history()
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p><strong>FINBOT v4</strong> | Advanced Data Intelligence Platform | Powered by Groq LLaMA 3.1 70B</p>
    <p>Built with ❤️ using LangChain, Streamlit, and Claude-level AI insights</p>
</div>
""", unsafe_allow_html=True)
