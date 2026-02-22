"""
RAG Module for Vishleshak AI v1
Retrieval Augmented Generation system with vector stores
"""

from .document_loader import DocumentProcessor
from .retriever import SmartRetriever, get_retriever
from .knowledge_base import KnowledgeBaseManager, get_knowledge_base_manager
from .embeddings_cache import EmbeddingsCache

# Alias for backward compatibility
DocumentLoader = DocumentProcessor

__all__ = [
    'DocumentProcessor',
    'DocumentLoader',
    'SmartRetriever',
    'get_retriever',
    'KnowledgeBaseManager',
    'get_knowledge_base_manager',
    'EmbeddingsCache'
]
