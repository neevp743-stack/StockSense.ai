"""
StockSense AI — In-Memory TTL Cache Manager
Provides fast, thread-safe, in-memory caching with Time-To-Live (TTL) expiration.
Eliminates redundant database queries and repeated pandas computation.
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple

class TTLCacheManager:
    def __init__(self, default_ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            expiry, val = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + ttl
        with self._lock:
            self._cache[key] = (expiry, value)

    def invalidate(self, key_prefix: Optional[str] = None) -> None:
        with self._lock:
            if key_prefix is None:
                self._cache.clear()
            else:
                keys_to_del = [k for k in self._cache if k.startswith(key_prefix)]
                for k in keys_to_del:
                    del self._cache[k]

# Global singleton cache instances
history_cache = TTLCacheManager(default_ttl_seconds=300)     # 5 minutes for historical OHLCV
indicators_cache = TTLCacheManager(default_ttl_seconds=120)  # 2 minutes for technical indicators
prediction_cache = TTLCacheManager(default_ttl_seconds=60)   # 1 minute for AI predictions
quote_cache = TTLCacheManager(default_ttl_seconds=30)         # 30 seconds for market quotes
