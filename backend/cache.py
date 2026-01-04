"""
Cache Module for Delhi Pollution Dashboard
============================================
Simple in-memory cache with TTL for API responses.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading

class Cache:
    """
    Thread-safe in-memory cache with TTL support.
    Used to cache API responses and reduce external API calls.
    """
    
    def __init__(self, default_ttl_minutes: int = 5):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if datetime.now() > entry["expires_at"]:
                # Entry has expired
                del self._cache[key]
                return None
            
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl_minutes: Optional custom TTL (uses default if not specified)
        """
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        expires_at = datetime.now() + ttl
        
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now()
            }
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            now = datetime.now()
            valid_entries = sum(
                1 for entry in self._cache.values()
                if entry["expires_at"] > now
            )
            
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "expired_entries": len(self._cache) - valid_entries,
                "keys": list(self._cache.keys())
            }

# Global cache instance
aqi_cache = Cache(default_ttl_minutes=5)

# Cache keys
CACHE_KEY_STATIONS = "stations_data"
CACHE_KEY_CPCB = "cpcb_data"
CACHE_KEY_AQICN = "aqicn_data"
CACHE_KEY_OPENAQ = "openaq_data"
