"""
Embedding Model Management for Vishleshak AI v1
Handles embedding generation using HuggingFace sentence-transformers
"""

from typing import List, Optional
import numpy as np
from pathlib import Path
import pickle
import hashlib
from sentence_transformers import SentenceTransformer
from config import rag_config
import logging

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manages embedding generation with caching
    
    Features:
    - HuggingFace sentence-transformers (free, local)
    - Disk caching for performance
    - Batch processing
    - GPU support if available
    
    Usage:
        embedder = EmbeddingManager()
        embeddings = embedder.embed_texts(["Hello world", "Another text"])
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Singleton pattern - only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize embedding model"""
        if not hasattr(self, 'initialized'):
            self.model_name = rag_config.EMBEDDING_MODEL_NAME
            self.device = rag_config.EMBEDDING_DEVICE
            self.batch_size = rag_config.EMBEDDING_BATCH_SIZE
            self.cache_enabled = rag_config.CACHE_EMBEDDINGS
            self.cache_dir = rag_config.CACHE_DIR
            
            # Load model
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Initialize cache
            if self.cache_enabled:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self._load_cache()
            
            self.initialized = True
            logger.info("✅ Embedding manager initialized")
    
    def _load_cache(self):
        """Load embedding cache from disk"""
        self.cache = {}
        cache_file = self.cache_dir / "embedding_cache.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Loaded {len(self.cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save embedding cache to disk"""
        if not self.cache_enabled:
            return
        
        cache_file = self.cache_dir / "embedding_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
            logger.debug(f"Saved {len(self.cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with caching
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        if not texts:
            return []
        
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache
        for i, text in enumerate(texts):
            if self.cache_enabled:
                cache_key = self._get_cache_key(text)
                if cache_key in self.cache:
                    embeddings.append(self.cache[cache_key])
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)
                    embeddings.append(None)  # Placeholder
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)
                embeddings.append(None)
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            logger.debug(f"Generating embeddings for {len(texts_to_embed)} texts")
            
            try:
                new_embeddings = self.model.encode(
                    texts_to_embed,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                
                # Update cache and results
                for idx, new_emb in zip(indices_to_embed, new_embeddings):
                    emb_list = new_emb.tolist()
                    embeddings[idx] = emb_list
                    
                    if self.cache_enabled:
                        cache_key = self._get_cache_key(texts[idx])
                        self.cache[cache_key] = emb_list
                
                # Save cache periodically
                if self.cache_enabled and len(texts_to_embed) > 10:
                    self._save_cache()
                
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.cache = {}
        cache_file = self.cache_dir / "embedding_cache.pkl"
        if cache_file.exists():
            cache_file.unlink()
        logger.info("Cache cleared")


# Global instance
_embedding_manager = None

def get_embeddings() -> EmbeddingManager:
    """
    Get global embedding manager instance
    
    Returns:
        EmbeddingManager: Singleton embedding manager
        
    Usage:
        embedder = get_embeddings()
        emb = embedder.embed_text("Hello world")
    """
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager
