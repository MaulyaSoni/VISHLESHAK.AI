"""
Context Manager for Enhanced Chatbot
Manages RAG context injection and formatting
"""

from typing import Dict, Any, Optional
import logging
from rag.retriever import get_retriever
from rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context retrieval and formatting for chatbot
    
    Features:
    - Retrieve relevant context from RAG
    - Format context for prompts
    - Track context sources
    - Manage context window
    
    Usage:
        context_manager = ContextManager()
        context = context_manager.get_context_for_query("dropout analysis")
    """
    
    def __init__(self):
        """Initialize context manager"""
        self.retriever = get_retriever()
        self.vector_store = get_vector_store()
        logger.info("✅ Context manager initialized")
    
    def get_context_for_query(
        self,
        query: str,
        include_analyses: bool = True,
        include_knowledge: bool = True,
        include_patterns: bool = True,
        include_documents: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for a query
        
        Args:
            query: User query
            include_analyses: Include historical analyses
            include_knowledge: Include domain knowledge
            include_patterns: Include similar patterns
            include_documents: Include documents
            
        Returns:
            Dict with context and metadata
        """
        # Retrieve context from all sources
        raw_context = self.retriever.get_comprehensive_context(
            query=query,
            include_analyses=include_analyses,
            include_knowledge=include_knowledge,
            include_patterns=include_patterns,
            include_documents=include_documents
        )
        
        # Format for prompt
        formatted_context = self.retriever.format_context_for_prompt(raw_context)
        
        # Extract sources
        sources = self.retriever.get_sources(raw_context)
        
        return {
            "raw_context": raw_context,
            "formatted_context": formatted_context,
            "sources": sources,
            "has_context": bool(formatted_context.strip())
        }
    
    def should_use_rag(self, query: str) -> bool:
        """
        Determine if RAG should be used for this query
        
        Args:
            query: User query
            
        Returns:
            True if RAG would be beneficial
        """
        # Keywords that suggest RAG would help
        rag_keywords = [
            "compare", "previous", "last", "history", "before",
            "similar", "pattern", "trend", "past", "earlier",
            "research", "study", "best practice", "recommend",
            "policy", "guideline", "standard", "benchmark"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in rag_keywords)
    
    def save_interaction_to_rag(
        self,
        query: str,
        response: str,
        metadata: Dict[str, Any]
    ):
        """
        Save important interactions to RAG for future reference
        
        Args:
            query: User query
            response: Bot response
            metadata: Additional metadata
        """
        # Determine if this interaction is worth saving
        if self._is_worth_saving(query, response):
            # Save as analysis or pattern depending on content
            if "analysis" in query.lower() or "insight" in query.lower():
                self.vector_store.save_analysis(
                    analysis_text=f"Query: {query}\n\nResponse: {response}",
                    metadata=metadata
                )
            else:
                self.vector_store.save_pattern(
                    pattern_description=f"Query: {query}\n\nResponse: {response}",
                    metadata=metadata
                )
    
    def _is_worth_saving(self, query: str, response: str) -> bool:
        """Determine if interaction should be saved to RAG"""
        # Save if response is substantial and informative
        return (
            len(response) > 200 and
            not response.startswith("Error") and
            "I don't" not in response
        )
