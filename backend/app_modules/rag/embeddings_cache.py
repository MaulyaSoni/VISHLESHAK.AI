"""
Embeddings Cache for Vishleshak AI v1
Disk-based caching layer for embeddings using diskcache
"""

from typing import List, Optional, Any
from pathlib import Path
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class EmbeddingsCache:
    """
    Disk-based caching layer for embeddings
    
    Uses diskcache for persistent, thread-safe caching of embedding
    computations to avoid redundant model calls.
    
    Features:
    - Disk-based persistence
    - Thread-safe operations
    - Configurable size limits
    - Automatic eviction
    
    Usage:
        cache = EmbeddingsCache()
        
        # Check cache before computing
        cached = cache.get("some text")
        if cached is None:
            embedding = compute_embedding("some text")
            cache.set("some text", embedding)
    """
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        size_limit_mb: int = 500
    ):
        """
        Initialize embeddings cache
        
        Args:
            cache_dir: Directory for cache storage
            size_limit_mb: Maximum cache size in megabytes
        """
        from config import rag_config
        
        self.cache_dir = Path(cache_dir) if cache_dir else rag_config.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.size_limit = size_limit_mb * 1024 * 1024  # Convert to bytes
        
        try:
            import diskcache
            self.cache = diskcache.Cache(
                str(self.cache_dir / "diskcache"),
                size_limit=self.size_limit
            )
            self._use_diskcache = True
            logger.info(f"✅ Embeddings cache initialized (diskcache) at {self.cache_dir}")
        except ImportError:
            logger.warning(
                "diskcache not installed, using in-memory fallback. "
                "Install with: pip install diskcache"
            )
            self.cache = {}
            self._use_diskcache = False
    
    def _make_key(self, text: str) -> str:
        """Generate a cache key from text"""
        return f"emb_{hashlib.sha256(text.encode()).hexdigest()}"
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding for text
        
        Args:
            text: Text to look up
            
        Returns:
            Cached embedding or None if not found
        """
        key = self._make_key(text)
        
        try:
            if self._use_diskcache:
                result = self.cache.get(key, default=None)
            else:
                result = self.cache.get(key, None)
            
            if result is not None:
                logger.debug(f"Cache hit for key: {key[:16]}...")
            return result
            
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, text: str, embedding: List[float]) -> bool:
        """
        Cache an embedding for text
        
        Args:
            text: Text that was embedded
            embedding: The embedding vector
            
        Returns:
            True if successfully cached
        """
        key = self._make_key(text)
        
        try:
            if self._use_diskcache:
                self.cache.set(key, embedding)
            else:
                self.cache[key] = embedding
            return True
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False
    
    def get_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Get cached embeddings for multiple texts
        
        Args:
            texts: List of texts to look up
            
        Returns:
            List of embeddings (None for cache misses)
        """
        return [self.get(text) for text in texts]
    
    def set_batch(
        self, 
        texts: List[str], 
        embeddings: List[List[float]]
    ) -> int:
        """
        Cache multiple embeddings
        
        Args:
            texts: List of texts
            embeddings: Corresponding embeddings
            
        Returns:
            Number successfully cached
        """
        count = 0
        for text, embedding in zip(texts, embeddings):
            if self.set(text, embedding):
                count += 1
        return count
    
    def clear(self):
        """Clear all cached embeddings"""
        try:
            if self._use_diskcache:
                self.cache.clear()
            else:
                self.cache.clear()
            logger.info("Embeddings cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        try:
            if self._use_diskcache:
                return {
                    "type": "diskcache",
                    "size": len(self.cache),
                    "volume": self.cache.volume(),
                    "directory": str(self.cache_dir)
                }
            else:
                return {
                    "type": "in-memory",
                    "size": len(self.cache),
                    "directory": str(self.cache_dir)
                }
        except Exception as e:
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            if self._use_diskcache and hasattr(self, 'cache'):
                self.cache.close()
        except Exception:
            pass
