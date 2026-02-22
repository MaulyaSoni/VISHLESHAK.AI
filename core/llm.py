"""
LLM Initialization for Vishleshak AI v1
Manages LLM instances for analysis and chat

Features:
- Singleton pattern for LLM instances
- Separate LLMs for analysis vs chat
- Groq integration with LLaMA models
"""

from langchain_groq import ChatGroq
from config import settings
from typing import Optional


# Global LLM instances (singleton pattern)
_analysis_llm: Optional[ChatGroq] = None
_chat_llm: Optional[ChatGroq] = None


def get_analysis_llm() -> ChatGroq:
    """
    Get or create the Analysis LLM instance
    Used for deep statistical insights and recommendations
    
    Returns:
        ChatGroq instance configured for analysis
    """
    global _analysis_llm
    
    if _analysis_llm is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. "
                "Please set it in your .env file. "
                "Get a free key at: https://console.groq.com/keys"
            )
        
        _analysis_llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
    
    return _analysis_llm


def get_chat_llm() -> ChatGroq:
    """
    Get or create the Chat LLM instance
    Used for conversational Q&A
    
    Returns:
        ChatGroq instance configured for chat
    """
    global _chat_llm
    
    if _chat_llm is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. "
                "Please set it in your .env file. "
                "Get a free key at: https://console.groq.com/keys"
            )
        
        _chat_llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.CHAT_MODEL,
            temperature=settings.CHAT_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
    
    return _chat_llm


def reset_llms():
    """
    Reset LLM instances (useful for testing or configuration changes)
    """
    global _analysis_llm, _chat_llm
    _analysis_llm = None
    _chat_llm = None


# Module-level convenience - use get_* functions for access
# These are here for backward compatibility with imports like "from core.llm import chat_llm"
# but should be called as chat_llm() not used directly
def chat_llm():
    """Convenience function - returns chat LLM instance"""
    return get_chat_llm()

def analysis_llm():
    """Convenience function - returns analysis LLM instance"""
    return get_analysis_llm()
