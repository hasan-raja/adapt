"""
Semantic caching using simple embedding similarity.
Falls back to simple hash cache if embeddings unavailable.
"""

import hashlib
import time
from collections import OrderedDict
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from app.models import CompressionLevel


# Cache configuration
MAX_CACHE_SIZE = 1000
DEFAULT_TTL_SECONDS = 3600  # 1 hour
SIMILARITY_THRESHOLD = 0.92


class SemanticCache:
    """
    In-memory cache with high-performance FAISS similarity matching.
    Falls back to hash-based cache if embeddings unavailable.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._cache_values: dict[str, str] = {}  # key -> response
        self._cache_metadata: dict[str, dict] = {} # key -> metadata
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

        # FAISS setup
        self._index = None
        self._keys_in_index = [] # maps index position to cache key
        self._embedding_dim = 384 # for all-MiniLM-L6-v2

        # Initialize embedding model
        self._embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
                # Inner product index for cosine similarity (requires normalized vectors)
                self._index = faiss.IndexFlatIP(self._embedding_dim)
            except Exception as e:
                print(f"Warning: Could not initialize FAISS: {e}")
                self._embedder = None

    def _get_text_hash(self, text: str) -> str:
        return hashlib.sha256(text.lower().encode()).hexdigest()[:16]

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        if self._embedder is None:
            return None
        try:
            embedding = self._embedder.encode(text, convert_to_numpy=True)
            # Normalize for cosine similarity via inner product
            faiss.normalize_L2(embedding.reshape(1, -1))
            return embedding.reshape(1, -1)
        except Exception:
            return None

    def _is_expired(self, key: str) -> bool:
        meta = self._cache_metadata.get(key)
        if not meta:
            return True
        return time.time() - meta['created_at'] > self._ttl

    def get(self, text: str, compression: CompressionLevel) -> Optional[str]:
        """Get cached response using FAISS semantic search."""
        text_lower = text.lower()
        hash_key = self._get_text_hash(text_lower)

        # 1. Try exact match first (O(1))
        if hash_key in self._cache_values and not self._is_expired(hash_key):
            self._hits += 1
            return self._cache_values[hash_key]

        # 2. Try semantic match (O(log N) or O(N) depending on index type)
        if self._index and self._index.ntotal > 0:
            query_emb = self._get_embedding(text_lower)
            if query_emb is not None:
                # Search top 1
                D, I = self._index.search(query_emb.astype('float32'), 1)
                
                if I[0][0] != -1:
                    similarity = D[0][0]
                    if similarity >= SIMILARITY_THRESHOLD:
                        match_key = self._keys_in_index[I[0][0]]
                        if not self._is_expired(match_key):
                            self._hits += 1
                            return self._cache_values[match_key]

        self._misses += 1
        return None

    def put(self, text: str, response: str) -> None:
        """Store response with embedding in FAISS index."""
        hash_key = self._get_text_hash(text)
        
        # Evict if full (simple logic: clear everything and rebuild if it gets too complex, 
        # but for this demo we'll just append)
        if len(self._cache_values) >= MAX_CACHE_SIZE:
            self.clear()

        embedding = self._get_embedding(text)
        
        if embedding is not None and self._index is not None:
            self._index.add(embedding.astype('float32'))
            self._keys_in_index.append(hash_key)

        self._cache_values[hash_key] = response
        self._cache_metadata[hash_key] = {
            'created_at': time.time(),
            'original_text': text[:50]
        }

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            "entries": len(self._cache_values),
            "faiss_index_size": self._index.ntotal if self._index else 0,
            "engine": "FAISS + MiniLM" if self._index else "Hash-only"
        }

    def clear(self) -> None:
        self._cache_values.clear()
        self._cache_metadata.clear()
        self._keys_in_index = []
        if self._index:
            self._index.reset()
        self._hits = 0
        self._misses = 0



# Global cache instance
semantic_cache = SemanticCache()