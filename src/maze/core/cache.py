"""Advanced caching for performance optimization.

Implements multi-level caching strategy:
- Grammar cache (already exists)
- Type context cache (NEW)
- Symbol cache (NEW)
- Validation result cache (NEW)

Target: >80% cache hit rate (from 70%)
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    
    value: T
    timestamp: float
    hits: int = 0
    size_bytes: int = 0


class LRUCache(Generic[T]):
    """LRU cache with size limits and hit tracking."""

    def __init__(self, capacity: int = 10000, max_size_mb: int = 100):
        """Initialize LRU cache.

        Args:
            capacity: Maximum number of entries
            max_size_mb: Maximum cache size in MB
        """
        self.capacity = capacity
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry[T]] = {}
        self.access_order: list[str] = []
        self.total_size = 0
        
        # Metrics
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[T]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Hit: update access order and metrics
            self.access_order.remove(key)
            self.access_order.append(key)
            self.cache[key].hits += 1
            self.hits += 1
            return self.cache[key].value
        else:
            # Miss
            self.misses += 1
            return None

    def put(self, key: str, value: T, size_bytes: int = 0) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            size_bytes: Size in bytes (for memory tracking)
        """
        # Remove if already exists
        if key in self.cache:
            self.total_size -= self.cache[key].size_bytes
            self.access_order.remove(key)

        # Evict if necessary
        while (
            len(self.cache) >= self.capacity
            or self.total_size + size_bytes > self.max_size_bytes
        ):
            if not self.access_order:
                break
            
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                self.total_size -= self.cache[oldest_key].size_bytes
                del self.cache[oldest_key]

        # Add new entry
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            hits=0,
            size_bytes=size_bytes,
        )
        self.access_order.append(key)
        self.total_size += size_bytes

    def hit_rate(self) -> float:
        """Get cache hit rate.

        Returns:
            Hit rate between 0.0 and 1.0
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()
        self.total_size = 0
        self.hits = 0
        self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "entries": len(self.cache),
            "capacity": self.capacity,
            "size_mb": self.total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate(),
        }


def cache_key_for_file(file_path: str, content: str) -> str:
    """Generate cache key for file content.

    Args:
        file_path: File path
        content: File content

    Returns:
        Cache key (hash)
    """
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{file_path}:{content_hash}"
