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
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from app.models import CompressionLevel


# Cache configuration
MAX_CACHE_SIZE = 1000
DEFAULT_TTL_SECONDS = 3600  # 1 hour
SIMILARITY_THRESHOLD = 0.92


class CacheEntry:
    def __init__(self, key: str, value: str, embedding: Optional[list] = None):
        self.key = key
        self.value = value
        self.embedding = embedding
        self.created_at = time.time()
        self.hit_count = 0


class SemanticCache:
    """
    In-memory cache with optional semantic similarity matching.
    Uses LRU eviction when full.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

        # Initialize embedding model if available
        self._embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                print("Warning: Could not load embedding model, using hash-based cache")
                self._embedder = None

    def _get_text_hash(self, text: str) -> str:
        """Get hash key for text."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _get_embedding(self, text: str) -> Optional[list]:
        """Get embedding for text."""
        if self._embedder is None:
            return None
        try:
            embedding = self._embedder.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception:
            return None

    def _cosine_similarity(self, a: list, b: list) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b:
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return time.time() - entry.created_at > self._ttl

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self._cache[key]

    def _evict_lru_if_needed(self) -> None:
        """Evict least recently used entry if cache is full."""
        if len(self._cache) >= MAX_CACHE_SIZE:
            # Remove oldest (first) item
            self._cache.popitem(last=False)

    def get(self, text: str, compression: CompressionLevel) -> Optional[str]:
        """
        Get cached response for text.
        Returns cached value if found, None otherwise.
        """
        self._evict_expired()

        text_lower = text.lower()

        # Try exact hash match first
        hash_key = self._get_text_hash(text_lower)
        for entry in self._cache.values():
            if entry.key == hash_key and not self._is_expired(entry):
                self._hits += 1
                entry.hit_count += 1
                # Move to end (most recently used)
                self._cache.move_to_end(entry.key)
                return entry.value

        # Try semantic similarity if embedder available
        if self._embedder:
            query_embedding = self._get_embedding(text_lower)
            if query_embedding:
                for key, entry in self._cache.items():
                    if entry.embedding and not self._is_expired(entry):
                        similarity = self._cosine_similarity(query_embedding, entry.embedding)
                        if similarity >= SIMILARITY_THRESHOLD:
                            self._hits += 1
                            entry.hit_count += 1
                            self._cache.move_to_end(key)
                            return entry.value

        self._misses += 1
        return None

    def put(self, text: str, response: str) -> None:
        """Store text -> response mapping."""
        self._evict_lru_if_needed()

        hash_key = self._get_text_hash(text.lower())
        embedding = self._get_embedding(text) if self._embedder else None

        entry = CacheEntry(hash_key, response, embedding)
        self._cache[hash_key] = entry

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        total_entries = len(self._cache)

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
            "entries": total_entries,
            "max_entries": MAX_CACHE_SIZE,
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# Global cache instance
semantic_cache = SemanticCache()