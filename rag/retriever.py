"""
Smart Retriever for FINBOT v4
Implements intelligent retrieval strategies across all RAG use cases
"""

from typing import List, Dict, Any, Optional
import logging
from rag.vector_store import get_vector_store
from config import rag_config

logger = logging.getLogger(__name__)


class SmartRetriever:
    """
    Intelligent retrieval across all RAG collections
    
    Features:
    - Multi-collection search
    - Relevance filtering
    - Context window management
    - Source attribution
    
    Usage:
        retriever = SmartRetriever()
        context = retriever.get_comprehensive_context("dropout analysis question")
    """
    
    def __init__(self):
        """Initialize smart retriever"""
        self.vector_store = get_vector_store()
        self.similarity_threshold = rag_config.SIMILARITY_THRESHOLD
        logger.info("✅ Smart retriever initialized")
    
    def get_comprehensive_context(
        self, 
        query: str,
        include_analyses: bool = True,
        include_knowledge: bool = True,
        include_patterns: bool = True,
        include_documents: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive context from all RAG sources
        
        Args:
            query: User query
            include_analyses: Include historical analyses
            include_knowledge: Include domain knowledge
            include_patterns: Include similar patterns
            include_documents: Include document chunks
            
        Returns:
            Dict with context from all enabled sources
            
        Example:
            context = retriever.get_comprehensive_context(
                "How to reduce dropout rate?",
                include_analyses=True,
                include_knowledge=True
            )
        """
        context = {}
        
        # RAG Use Case 1: Historical Analyses
        if include_analyses and rag_config.ENABLE_HISTORICAL_MEMORY:
            analyses = self.vector_store.retrieve_similar_analyses(
                query, 
                k=rag_config.DEFAULT_TOP_K_ANALYSES
            )
            context["past_analyses"] = self._filter_by_similarity(analyses)
        
        # RAG Use Case 2: Domain Knowledge
        if include_knowledge and rag_config.ENABLE_KNOWLEDGE_BASE:
            knowledge = self.vector_store.query_knowledge(
                query,
                k=rag_config.DEFAULT_TOP_K_KNOWLEDGE
            )
            context["domain_knowledge"] = self._filter_by_similarity(knowledge)
        
        # RAG Use Case 3: Similar Patterns
        if include_patterns and rag_config.ENABLE_PATTERN_MATCHING:
            patterns = self.vector_store.find_similar_patterns(
                query,
                k=rag_config.DEFAULT_TOP_K_PATTERNS
            )
            context["similar_patterns"] = self._filter_by_similarity(patterns)
        
        # RAG Use Case 4: Documents
        if include_documents and rag_config.ENABLE_DOCUMENT_QA:
            documents = self.vector_store.query_documents(
                query,
                k=rag_config.DEFAULT_TOP_K_DOCUMENTS
            )
            context["documents"] = self._filter_by_similarity(documents)
        
        logger.debug(f"Retrieved context from {len(context)} sources")
        return context
    
    def _filter_by_similarity(
        self, 
        results: List[Dict]
    ) -> List[Dict]:
        """
        Filter results by similarity threshold
        
        Args:
            results: List of retrieval results
            
        Returns:
            Filtered results above threshold
        """
        return [
            r for r in results 
            if r.get("similarity", 0) >= self.similarity_threshold
        ]
    
    def format_context_for_prompt(
        self, 
        context: Dict[str, Any],
        max_length: int = None
    ) -> str:
        """
        Format retrieved context for LLM prompt
        
        Args:
            context: Context dict from get_comprehensive_context
            max_length: Maximum length in characters
            
        Returns:
            Formatted context string
        """
        if max_length is None:
            max_length = rag_config.MAX_CONTEXT_LENGTH
        
        formatted_parts = []
        current_length = 0
        
        # Add past analyses
        if "past_analyses" in context and context["past_analyses"]:
            analyses_text = "📊 RELEVANT PAST ANALYSES:\n\n"
            for i, analysis in enumerate(context["past_analyses"], 1):
                timestamp = analysis["metadata"].get("timestamp", "Unknown")
                text = analysis["text"][:500]  # Truncate long analyses
                analyses_text += f"{i}. Analysis from {timestamp}:\n{text}\n\n"
            
            if current_length + len(analyses_text) < max_length:
                formatted_parts.append(analyses_text)
                current_length += len(analyses_text)
        
        # Add domain knowledge
        if "domain_knowledge" in context and context["domain_knowledge"]:
            knowledge_text = "📚 RELEVANT KNOWLEDGE:\n\n"
            for i, knowledge in enumerate(context["domain_knowledge"], 1):
                topic = knowledge["metadata"].get("topic", "General")
                text = knowledge["text"][:400]
                knowledge_text += f"{i}. {topic}:\n{text}\n\n"
            
            if current_length + len(knowledge_text) < max_length:
                formatted_parts.append(knowledge_text)
                current_length += len(knowledge_text)
        
        # Add similar patterns
        if "similar_patterns" in context and context["similar_patterns"]:
            patterns_text = "🔍 SIMILAR PATTERNS FROM HISTORY:\n\n"
            for i, pattern in enumerate(context["similar_patterns"], 1):
                desc = pattern["description"][:300]
                outcome = pattern["metadata"].get("outcome", "Unknown")
                patterns_text += f"{i}. Pattern: {desc}\n   Outcome: {outcome}\n\n"
            
            if current_length + len(patterns_text) < max_length:
                formatted_parts.append(patterns_text)
                current_length += len(patterns_text)
        
        # Add documents
        if "documents" in context and context["documents"]:
            docs_text = "📄 RELEVANT DOCUMENTS:\n\n"
            for i, doc in enumerate(context["documents"], 1):
                source = doc["metadata"].get("filename", "Unknown")
                text = doc["text"][:400]
                docs_text += f"{i}. From {source}:\n{text}\n\n"
            
            if current_length + len(docs_text) < max_length:
                formatted_parts.append(docs_text)
                current_length += len(docs_text)
        
        return "\n".join(formatted_parts)
    
    def get_sources(self, context: Dict[str, Any]) -> List[str]:
        """
        Extract all sources from retrieved context
        
        Args:
            context: Context dict
            
        Returns:
            List of source strings
        """
        sources = []
        
        for category in context.values():
            if isinstance(category, list):
                for item in category:
                    metadata = item.get("metadata", {})
                    source = metadata.get("source") or metadata.get("filename")
                    if source and source not in sources:
                        sources.append(source)
        
        return sources


# Global instance
_retriever = None

def get_retriever() -> SmartRetriever:
    """Get global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = SmartRetriever()
    return _retriever
