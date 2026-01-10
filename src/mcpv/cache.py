"""Smart Result Caching - Reduces redundant tool calls and saves tokens.

This module implements a thread-safe LRU cache with TTL support for
caching tool execution results. It helps reduce token costs by avoiding
repeated identical tool calls.

Security considerations:
- Cache keys are generated from tool name + args hash (no sensitive data in keys)
- Cache is per-session (cleared on restart)
- TTL prevents stale data from persisting indefinitely
"""
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from threading import Lock
from collections import OrderedDict

logger = logging.getLogger("mcpv-cache")

# Configuration from environment
CACHE_TTL = float(os.environ.get("MCPV_CACHE_TTL", "300.0"))  # 5 minutes default
CACHE_MAX_SIZE = int(os.environ.get("MCPV_CACHE_MAX_SIZE", "100"))  # Max entries


@dataclass
class CacheEntry:
    """Represents a cached tool result with metadata."""
    result: str
    timestamp: float
    hit_count: int = 0
    tool_name: str = ""
    args_hash: str = ""
    
    def is_expired(self, ttl: float = CACHE_TTL) -> bool:
        """Check if this entry has exceeded its TTL."""
        return (time.time() - self.timestamp) > ttl
    
    def age_seconds(self) -> float:
        """Returns age of cache entry in seconds."""
        return time.time() - self.timestamp


class SmartCache:
    """Thread-safe LRU cache with TTL for tool results.
    
    Features:
    - LRU eviction when max size reached
    - TTL-based expiration
    - Thread-safe operations
    - Hit/miss statistics
    
    Usage:
        cache = SmartCache()
        
        # Check cache before calling tool
        key = cache.generate_key("query-docs", {"query": "nextjs"})
        cached = cache.get(key)
        if cached:
            return cached.result
        
        # After getting result from tool
        cache.set(key, result, tool_name="query-docs")
    """
    
    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: float = CACHE_TTL):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
        logger.info(f"SmartCache initialized: max_size={max_size}, ttl={ttl}s")
    
    def generate_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate a deterministic cache key from tool name and args.
        
        Uses SHA256 hash of sorted JSON args to ensure consistency
        regardless of arg order.
        """
        # Sort args for deterministic serialization
        try:
            args_json = json.dumps(args, sort_keys=True, default=str)
        except (TypeError, ValueError):
            # Fallback for non-serializable args
            args_json = str(sorted(args.items()))
        
        args_hash = hashlib.sha256(args_json.encode()).hexdigest()[:16]
        return f"{tool_name}:{args_hash}"
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve a cache entry if it exists and is not expired.
        
        Returns None if:
        - Key doesn't exist
        - Entry has expired (and removes it)
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired(self._ttl):
                # Remove expired entry
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache EXPIRED: {key}")
                return None
            
            # Cache hit - move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            logger.debug(f"Cache HIT: {key} (hits: {entry.hit_count})")
            return entry
    
    def set(self, key: str, result: str, tool_name: str = "") -> None:
        """Store a result in the cache.
        
        Implements LRU eviction: if cache is full, removes oldest entry.
        """
        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key].result = result
                self._cache[key].timestamp = time.time()
                self._cache.move_to_end(key)
                return
            
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache EVICT (LRU): {oldest_key}")
            
            # Add new entry
            self._cache[key] = CacheEntry(
                result=result,
                timestamp=time.time(),
                tool_name=tool_name,
                args_hash=key.split(":")[-1] if ":" in key else ""
            )
            logger.debug(f"Cache SET: {key}")
    
    def invalidate(self, key: str) -> bool:
        """Remove a specific entry from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache INVALIDATE: {key}")
                return True
            return False
    
    def clear(self) -> int:
        """Clear all cache entries. Returns count of cleared entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED: {count} entries removed")
            return count
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() 
                if v.is_expired(self._ttl)
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cache CLEANUP: {len(expired_keys)} expired entries removed")
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 1),
                "entries": [
                    {
                        "tool": e.tool_name,
                        "age_seconds": round(e.age_seconds(), 1),
                        "hit_count": e.hit_count
                    }
                    for e in list(self._cache.values())[:10]  # Show max 10
                ]
            }
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        entry = self.get(key)
        return entry is not None


# Singleton instance
cache = SmartCache()
