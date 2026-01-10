"""Tests for SmartCache - LRU cache with TTL."""
import pytest
import time
from unittest.mock import patch


class TestCacheKeyGeneration:
    """Test suite for cache key generation."""
    
    def test_same_args_same_key(self):
        """Same tool and args should produce same key."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        key1 = cache.generate_key("query-docs", {"query": "nextjs"})
        key2 = cache.generate_key("query-docs", {"query": "nextjs"})
        
        assert key1 == key2
    
    def test_different_args_different_key(self):
        """Different args should produce different keys."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        key1 = cache.generate_key("query-docs", {"query": "nextjs"})
        key2 = cache.generate_key("query-docs", {"query": "react"})
        
        assert key1 != key2
    
    def test_arg_order_independent(self):
        """Key should be same regardless of arg order."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        key1 = cache.generate_key("tool", {"a": 1, "b": 2})
        key2 = cache.generate_key("tool", {"b": 2, "a": 1})
        
        assert key1 == key2


class TestCacheOperations:
    """Test suite for basic cache operations."""
    
    def test_set_and_get(self):
        """Should store and retrieve values."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        cache.set("test-key", "test-result", tool_name="test")
        entry = cache.get("test-key")
        
        assert entry is not None
        assert entry.result == "test-result"
    
    def test_get_nonexistent_returns_none(self):
        """Should return None for missing keys."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        entry = cache.get("nonexistent")
        
        assert entry is None
    
    def test_cache_hit_increments_count(self):
        """Each hit should increment hit_count."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        cache.set("key", "value")
        cache.get("key")
        cache.get("key")
        entry = cache.get("key")
        
        assert entry.hit_count == 3
    
    def test_invalidate_removes_entry(self):
        """Invalidate should remove specific entry."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        cache.set("key", "value")
        result = cache.invalidate("key")
        
        assert result is True
        assert cache.get("key") is None
    
    def test_clear_removes_all(self):
        """Clear should remove all entries."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        count = cache.clear()
        
        assert count == 3
        assert len(cache) == 0


class TestCacheTTL:
    """Test suite for TTL expiration."""
    
    def test_expired_entry_returns_none(self):
        """Expired entries should return None."""
        from mcpv.cache import SmartCache
        cache = SmartCache(ttl=0.1)  # 100ms TTL
        
        cache.set("key", "value")
        time.sleep(0.15)  # Wait for expiration
        
        entry = cache.get("key")
        
        assert entry is None
    
    def test_non_expired_entry_returns_value(self):
        """Non-expired entries should return value."""
        from mcpv.cache import SmartCache
        cache = SmartCache(ttl=10.0)  # 10s TTL
        
        cache.set("key", "value")
        entry = cache.get("key")
        
        assert entry is not None
        assert entry.result == "value"
    
    def test_cleanup_expired_removes_old_entries(self):
        """cleanup_expired should remove only expired entries."""
        from mcpv.cache import SmartCache
        cache = SmartCache(ttl=0.1)
        
        cache.set("old", "old_value")
        time.sleep(0.15)
        cache.set("new", "new_value")
        
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("new") is not None


class TestCacheLRU:
    """Test suite for LRU eviction."""
    
    def test_evicts_oldest_when_full(self):
        """Should evict oldest entry when at capacity."""
        from mcpv.cache import SmartCache
        cache = SmartCache(max_size=2)
        
        cache.set("first", "1")
        cache.set("second", "2")
        cache.set("third", "3")  # Should evict "first"
        
        assert cache.get("first") is None
        assert cache.get("second") is not None
        assert cache.get("third") is not None
    
    def test_access_updates_lru_order(self):
        """Accessing an entry should move it to end (most recent)."""
        from mcpv.cache import SmartCache
        cache = SmartCache(max_size=2)
        
        cache.set("first", "1")
        cache.set("second", "2")
        cache.get("first")  # Access first, making it most recent
        cache.set("third", "3")  # Should evict "second" instead
        
        assert cache.get("first") is not None
        assert cache.get("second") is None
        assert cache.get("third") is not None


class TestCacheStats:
    """Test suite for statistics."""
    
    def test_stats_track_hits_misses(self):
        """Stats should accurately track hits and misses."""
        from mcpv.cache import SmartCache
        cache = SmartCache()
        
        cache.set("key", "value")
        cache.get("key")  # hit
        cache.get("key")  # hit
        cache.get("missing")  # miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == pytest.approx(66.7, rel=0.1)
    
    def test_stats_show_size(self):
        """Stats should show current size."""
        from mcpv.cache import SmartCache
        cache = SmartCache(max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 10
