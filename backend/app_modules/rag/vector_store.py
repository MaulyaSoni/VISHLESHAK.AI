"""
Vector Store Management for Vishleshak AI v1
Manages ChromaDB collections for RAG system
"""

from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from config import rag_config
from core.embeddings import get_embeddings
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manages all vector stores for RAG system
    
    Implements 4 RAG use cases:
    1. Historical Analysis Memory - Store and retrieve past analyses
    2. Domain Knowledge Base - Query domain-specific knowledge
    3. Similar Pattern Matching - Find similar patterns from history
    4. Document Q&A - Answer questions from documents
    
    Usage:
        vsm = VectorStoreManager()
        
        # Store analysis
        vsm.save_analysis(analysis_text, metadata)
        
        # Retrieve similar analyses
        results = vsm.retrieve_similar_analyses("dropout rate analysis")
    """
    
    def __init__(self):
        """Initialize vector store manager"""
        self.embedding_function = get_embeddings()
        self.db_path = str(rag_config.VECTOR_DB_PATH)
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at {self.db_path}")
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(**rag_config.CHROMA_SETTINGS)
        )
        
        # Initialize collections for each use case
        self.collections = {}
        self._init_collections()
        
        logger.info("✅ Vector store manager initialized")
    
    def _init_collections(self):
        """Initialize all collections"""
        for key, name in rag_config.VECTOR_DB_COLLECTIONS.items():
            try:
                collection = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"Collection for {key}"}
                )
                self.collections[key] = collection
                logger.info(f"  Initialized collection: {name}")
            except Exception as e:
                logger.error(f"Error initializing collection {name}: {e}")
                raise
    
    # ========================================================================
    # RAG USE CASE 1: Historical Analysis Memory
    # ========================================================================
    
    def save_analysis(
        self, 
        analysis_text: str, 
        metadata: Dict[str, Any],
        analysis_id: Optional[str] = None
    ) -> str:
        """
        Store analysis for future retrieval
        
        Args:
            analysis_text: Full analysis text to store
            metadata: Metadata (timestamp, dataset_name, metrics, etc.)
            analysis_id: Optional unique ID (generated if not provided)
            
        Returns:
            str: ID of stored analysis
            
        Example:
            metadata = {
                "timestamp": "2024-02-13",
                "dataset_name": "students.csv",
                "num_rows": 500,
                "avg_dropout_risk": 0.59
            }
            vsm.save_analysis(analysis_text, metadata)
        """
        if not rag_config.ENABLE_HISTORICAL_MEMORY:
            logger.warning("Historical memory disabled")
            return ""
        
        collection = self.collections["analyses"]
        
        # Generate ID if not provided
        if analysis_id is None:
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Ensure all metadata values are strings (ChromaDB requirement)
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float)):
                clean_metadata[k] = str(v)
            elif isinstance(v, (list, dict)):
                clean_metadata[k] = json.dumps(v)
            else:
                clean_metadata[k] = str(v) if v is not None else ""
        
        # Generate embedding
        embedding = self.embedding_function.embed_text(analysis_text)
        
        try:
            collection.add(
                ids=[analysis_id],
                embeddings=[embedding],
                documents=[analysis_text],
                metadatas=[clean_metadata]
            )
            logger.info(f"Saved analysis: {analysis_id}")
            return analysis_id
        
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise
    
    def retrieve_similar_analyses(
        self, 
        query: str, 
        k: int = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past analyses
        
        Args:
            query: Query text to find similar analyses
            k: Number of results (default from config)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of dicts with keys: id, text, metadata, similarity
        """
        if not rag_config.ENABLE_HISTORICAL_MEMORY:
            return []
        
        if k is None:
            k = rag_config.DEFAULT_TOP_K_ANALYSES
        
        collection = self.collections["analyses"]
        
        # Check if collection has any items
        if collection.count() == 0:
            return []
        
        # Adjust k to not exceed collection count
        k = min(k, collection.count())
        
        # Generate query embedding
        query_embedding = self.embedding_function.embed_text(query)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - distance  # Convert distance to similarity
                    })
            
            logger.debug(f"Retrieved {len(formatted_results)} similar analyses")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error retrieving analyses: {e}")
            return []
    
    # ========================================================================
    # RAG USE CASE 2: Domain Knowledge Base
    # ========================================================================
    
    def add_knowledge(
        self, 
        knowledge_text: str, 
        metadata: Dict[str, Any],
        knowledge_id: Optional[str] = None
    ) -> str:
        """
        Add knowledge to domain knowledge base
        
        Args:
            knowledge_text: Knowledge content
            metadata: Metadata (domain, source, topic, etc.)
            knowledge_id: Optional unique ID
            
        Returns:
            str: ID of stored knowledge
        """
        if not rag_config.ENABLE_KNOWLEDGE_BASE:
            return ""
        
        collection = self.collections["knowledge"]
        
        if knowledge_id is None:
            knowledge_id = f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Clean metadata for ChromaDB
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float)):
                clean_metadata[k] = str(v)
            elif isinstance(v, (list, dict)):
                clean_metadata[k] = json.dumps(v)
            else:
                clean_metadata[k] = str(v) if v is not None else ""
        
        embedding = self.embedding_function.embed_text(knowledge_text)
        
        try:
            collection.add(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[clean_metadata]
            )
            logger.info(f"Added knowledge: {knowledge_id}")
            return knowledge_id
        
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            raise
    
    def query_knowledge(
        self, 
        question: str, 
        domain: Optional[str] = None,
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Query domain-specific knowledge
        
        Args:
            question: Question to answer
            domain: Optional domain filter (education, finance, etc.)
            k: Number of results
            
        Returns:
            List of relevant knowledge pieces
        """
        if not rag_config.ENABLE_KNOWLEDGE_BASE:
            return []
        
        if k is None:
            k = rag_config.DEFAULT_TOP_K_KNOWLEDGE
        
        collection = self.collections["knowledge"]
        
        if collection.count() == 0:
            return []
        
        k = min(k, collection.count())
        
        query_embedding = self.embedding_function.embed_text(question)
        
        # Build filter
        filter_dict = {"domain": domain} if domain else None
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_dict
            )
            
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - distance
                    })
            
            logger.debug(f"Retrieved {len(formatted_results)} knowledge pieces")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            return []
    
    # ========================================================================
    # RAG USE CASE 3: Similar Pattern Matching
    # ========================================================================
    
    def save_pattern(
        self, 
        pattern_description: str, 
        metadata: Dict[str, Any],
        pattern_id: Optional[str] = None
    ) -> str:
        """
        Store detected pattern for future matching
        
        Args:
            pattern_description: Description of the pattern
            metadata: Pattern metadata (type, outcome, action_taken, etc.)
            pattern_id: Optional unique ID
            
        Returns:
            str: ID of stored pattern
        """
        if not rag_config.ENABLE_PATTERN_MATCHING:
            return ""
        
        collection = self.collections["patterns"]
        
        if pattern_id is None:
            pattern_id = f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Clean metadata
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float)):
                clean_metadata[k] = str(v)
            elif isinstance(v, (list, dict)):
                clean_metadata[k] = json.dumps(v)
            else:
                clean_metadata[k] = str(v) if v is not None else ""
        
        embedding = self.embedding_function.embed_text(pattern_description)
        
        try:
            collection.add(
                ids=[pattern_id],
                embeddings=[embedding],
                documents=[pattern_description],
                metadatas=[clean_metadata]
            )
            logger.info(f"Saved pattern: {pattern_id}")
            return pattern_id
        
        except Exception as e:
            logger.error(f"Error saving pattern: {e}")
            raise
    
    def find_similar_patterns(
        self, 
        pattern_description: str, 
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar patterns from history
        
        Args:
            pattern_description: Description of current pattern
            k: Number of results
            
        Returns:
            List of similar patterns with outcomes
        """
        if not rag_config.ENABLE_PATTERN_MATCHING:
            return []
        
        if k is None:
            k = rag_config.DEFAULT_TOP_K_PATTERNS
        
        collection = self.collections["patterns"]
        
        if collection.count() == 0:
            return []
        
        k = min(k, collection.count())
        
        query_embedding = self.embedding_function.embed_text(pattern_description)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "description": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - distance
                    })
            
            logger.debug(f"Found {len(formatted_results)} similar patterns")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error finding patterns: {e}")
            return []
    
    # ========================================================================
    # RAG USE CASE 4: Document Q&A
    # ========================================================================
    
    def add_document(
        self, 
        document_text: str, 
        metadata: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """
        Add document to document store
        
        Args:
            document_text: Document content
            metadata: Document metadata (title, source, type, etc.)
            document_id: Optional unique ID
            
        Returns:
            str: ID of stored document
        """
        if not rag_config.ENABLE_DOCUMENT_QA:
            return ""
        
        collection = self.collections["documents"]
        
        if document_id is None:
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Clean metadata
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float)):
                clean_metadata[k] = str(v)
            elif isinstance(v, (list, dict)):
                clean_metadata[k] = json.dumps(v)
            else:
                clean_metadata[k] = str(v) if v is not None else ""
        
        embedding = self.embedding_function.embed_text(document_text)
        
        try:
            collection.add(
                ids=[document_id],
                embeddings=[embedding],
                documents=[document_text],
                metadatas=[clean_metadata]
            )
            logger.info(f"Added document: {document_id}")
            return document_id
        
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def query_documents(
        self, 
        question: str, 
        k: int = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Answer questions from documents
        
        Args:
            question: Question to answer
            k: Number of document chunks to retrieve
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant document chunks
        """
        if not rag_config.ENABLE_DOCUMENT_QA:
            return []
        
        if k is None:
            k = rag_config.DEFAULT_TOP_K_DOCUMENTS
        
        collection = self.collections["documents"]
        
        if collection.count() == 0:
            return []
        
        k = min(k, collection.count())
        
        query_embedding = self.embedding_function.embed_text(question)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata
            )
            
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - distance
                    })
            
            logger.debug(f"Retrieved {len(formatted_results)} document chunks")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return []
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        collection = self.collections.get(collection_name)
        if not collection:
            return {}
        
        try:
            count = collection.count()
            return {
                "collection": collection_name,
                "count": count,
                "name": collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {}
        for name in self.collections.keys():
            stats[name] = self.get_collection_stats(name)
        return stats
    
    def clear_collection(self, collection_name: str):
        """Clear all data from a collection"""
        try:
            self.client.delete_collection(
                name=rag_config.VECTOR_DB_COLLECTIONS[collection_name]
            )
            self._init_collections()  # Recreate
            logger.info(f"Cleared collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise


# Global instance
_vector_store_manager = None

def get_vector_store() -> VectorStoreManager:
    """Get global vector store manager instance"""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager
