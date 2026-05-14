"""
Semantic caching using simple embedding similarity.
Falls back to simple hash cache if embeddings unavailable.
"""

import hashlib
import time
import os
import pickle
from typing import Optional, Any

EMBEDDINGS_AVAILABLE = True # Assume available, check inside methods

from app.models import CompressionLevel


# Cache configuration
MAX_CACHE_SIZE = 1000
DEFAULT_TTL_SECONDS = 86400 * 7 # 7 days for persistent demo
SIMILARITY_THRESHOLD = 0.92
CACHE_DIR = ".cache"
INDEX_PATH = os.path.join(CACHE_DIR, "faiss_index.bin")
DATA_PATH = os.path.join(CACHE_DIR, "cache_data.pkl")

SAFETY_SENSITIVE_TERMS = {
    "doctor", "hospital", "medicine", "dosage", "dose", "pregnant", "bleeding",
    "chest pain", "suicide", "self harm", "loan", "credit", "password", "otp",
    "pin", "account number", "aadhaar", "pan card", "bank", "upi", "tax",
}


class SemanticCache:
    """
    In-memory cache with high-performance FAISS similarity matching.
    Falls back to disk-persistent store on restarts.
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

        # Model placeholder (Lazy Loading)
        self._embedder = None
        
        # Load index foundation even if model isn't ready
        # Note: We avoid calling faiss here unless it's already on disk
        if EMBEDDINGS_AVAILABLE:
            try:
                if not os.path.exists(CACHE_DIR):
                    os.makedirs(CACHE_DIR)
                
                if os.path.exists(INDEX_PATH) and os.path.exists(DATA_PATH):
                    self._load_from_disk()
                else:
                    # Delay index creation until first use or model load
                    pass
            except Exception as e:
                print(f"Warning during cache init: {e}")

    def _ensure_model_loaded(self) -> None:
        """Lazy load the embedding model and FAISS only when needed."""
        global EMBEDDINGS_AVAILABLE
        if self._embedder is None and EMBEDDINGS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                import faiss
                print("Loading semantic embedding model (First time only)...")
                start = time.time()
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                
                if self._index is None:
                    self._index = faiss.IndexFlatIP(self._embedding_dim)
                
                print(f"Model loaded in {time.time() - start:.2f} seconds.")
            except ImportError:
                print("Warning: ML libraries not installed. Semantic cache disabled.")
                EMBEDDINGS_AVAILABLE = False

    def _get_text_hash(self, text: str) -> str:
        return hashlib.sha256(text.lower().encode()).hexdigest()[:16]

    def should_cache(self, text: str) -> bool:
        """Avoid reusing answers for highly personal, medical, or financial prompts."""
        lowered = text.lower()
        return not any(term in lowered for term in SAFETY_SENSITIVE_TERMS)

    def _get_embedding(self, text: str) -> Any:
        self._ensure_model_loaded()
        if self._embedder is None:
            return None
        try:
            import faiss
            embedding = self._embedder.encode(text, convert_to_numpy=True)
            # Normalize for cosine similarity via inner product
            faiss.normalize_L2(embedding.reshape(1, -1))
            return embedding.reshape(1, -1).astype('float32')
        except Exception:
            return None

    def _is_expired(self, key: str) -> bool:
        meta = self._cache_metadata.get(key)
        if not meta:
            return True
        return time.time() - meta['created_at'] > self._ttl

    def _save_to_disk(self) -> None:
        """Persist cache and index to disk."""
        if not EMBEDDINGS_AVAILABLE:
            return
        try:
            import faiss
            # 1. Save FAISS index
            if self._index:
                faiss.write_index(self._index, INDEX_PATH)
            
            # 2. Save metadata and keys
            with open(DATA_PATH, 'wb') as f:
                pickle.dump({
                    'values': self._cache_values,
                    'metadata': self._cache_metadata,
                    'keys': self._keys_in_index
                }, f)
        except Exception as e:
            print(f"Error saving cache to disk: {e}")

    def _load_from_disk(self) -> None:
        """Load cache and index from disk."""
        try:
            import faiss
            # 1. Load FAISS index
            if os.path.exists(INDEX_PATH):
                self._index = faiss.read_index(INDEX_PATH)
            
            # 2. Load metadata and keys
            if os.path.exists(DATA_PATH):
                with open(DATA_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self._cache_values = data['values']
                    self._cache_metadata = data['metadata']
                    self._keys_in_index = data['keys']
        except Exception as e:
            print(f"Error loading cache from disk: {e}")

    def get(self, text: str, compression: CompressionLevel) -> Optional[str]:
        """Get cached response using FAISS semantic search."""
        text_lower = text.lower()

        if not self.should_cache(text_lower):
            self._misses += 1
            return None

        hash_key = self._get_text_hash(text_lower)

        # 1. Try exact match first (O(1))
        if hash_key in self._cache_values and not self._is_expired(hash_key):
            self._hits += 1
            return self._cache_values[hash_key]

        # 2. Try semantic match
        if self._index and self._index.ntotal > 0:
            query_emb = self._get_embedding(text_lower)
            if query_emb is not None:
                # Search top 1
                D, I = self._index.search(query_emb, 1)
                
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
        if not self.should_cache(text):
            return

        hash_key = self._get_text_hash(text)
        
        if len(self._cache_values) >= MAX_CACHE_SIZE:
            self.clear()

        embedding = self._get_embedding(text)
        
        if embedding is not None and self._index is not None:
            self._index.add(embedding)
            self._keys_in_index.append(hash_key)

        self._cache_values[hash_key] = response
        self._cache_metadata[hash_key] = {
            'created_at': time.time(),
            'original_text': text[:50]
        }
        
        # Save to disk after each put
        self._save_to_disk()

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            "entries": len(self._cache_values),
            "faiss_index_size": self._index.ntotal if self._index else 0,
            "engine": "FAISS (Persistent)" if self._index else "Hash-only"
        }

    def clear(self) -> None:
        self._cache_values.clear()
        self._cache_metadata.clear()
        self._keys_in_index = []
        if self._index:
            self._index.reset()
        self._hits = 0
        self._misses = 0
        
        # Clear disk files too
        if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
        if os.path.exists(DATA_PATH): os.remove(DATA_PATH)



# Global cache instance
semantic_cache = SemanticCache()
