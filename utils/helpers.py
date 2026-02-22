"""
Helper utilities for Vishleshak AI v1
Includes error handling and UI helpers
"""

import streamlit as st
import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_error(error: Exception, context: str = "") -> None:
    """
    Display user-friendly error messages
    
    Args:
        error: Exception object
        context: Context where error occurred
    """
    
    error_messages = {
        "APIError": "🔑 API Error: Please check your Groq API key in .env file",
        "ConnectionError": "🌐 Connection Error: Please check your internet connection",
        "FileNotFoundError": "📁 File Error: Could not find the specified file",
        "PermissionError": "🔒 Permission Error: Cannot access file or directory",
        "MemoryError": "💾 Memory Error: Dataset too large, try a smaller file",
        "OutOfMemoryError": "💾 Memory Error: Dataset too large, try a smaller file",
    }
    
    error_type = type(error).__name__
    
    if error_type in error_messages:
        st.error(error_messages[error_type])
    else:
        st.error(f"❌ {context}: {str(error)}" if context else f"❌ Error: {str(error)}")
    
    # Log detailed error
    logger.error(f"Error in {context}: {error}", exc_info=True)
    
    # Show expandable details for debugging
    with st.expander("🔍 Error Details (for debugging)"):
        st.code(str(error))
        if hasattr(error, '__traceback__'):
            import traceback
            st.code(''.join(traceback.format_tb(error.__traceback__)))


def print_startup_summary(session_id: str) -> None:
    """
    Print clean startup summary to console
    
    Args:
        session_id: Current session ID
    """
    print("\n" + "="*60)
    print("🤖 Vishleshak AI v1 - Startup Summary")
    print("="*60)
    
    # Vector store stats
    try:
        from rag.vector_store import get_vector_store
        vs = get_vector_store()
        stats = vs.get_all_stats()
        total = sum(s.get('count', 0) for s in stats.values())
        print(f"✅ RAG System: {total} items in vector store")
    except Exception as e:
        print(f"⚠️  RAG System: Not initialized ({str(e)})")
    
    # Tools
    try:
        from tools import get_tool_registry
        tr = get_tool_registry()
        tools = tr.get_all_tools()
        print(f"✅ Tools: {len(tools)} tools ready")
    except Exception as e:
        print(f"⚠️  Tools: Not initialized ({str(e)})")
    
    print(f"✅ Session ID: {session_id[:8]}...")
    print("="*60 + "\n")


def clean_dataframe_display(df, num_rows: int = 10):
    """
    Display DataFrame with proper formatting
    
    Args:
        df: DataFrame to display
        num_rows: Number of rows to show
    """
    st.dataframe(
        df.head(num_rows),
        use_container_width=True,
        height=300,
        hide_index=True
    )
