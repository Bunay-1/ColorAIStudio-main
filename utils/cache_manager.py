"""
Cache Manager for Expensive Calculations
========================================
LRU Cache implementation for caching expensive operations like SPC calculations,
Delta E computations, and other resource-intensive operations.
"""

import time
import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Any, Optional
from collections import OrderedDict

logger = logging.getLogger("CacheManager")

class LRUCache:
    """Simple LRU Cache implementation with TTL support."""
    
    def __init__(self, max_size: int = 128, ttl: int = 3600):
        """
        Args:
            max_size: Maximum number of items to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key from function arguments."""
        key_data = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{func_name}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl:
            self._remove(key)
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        # Remove if exists
        if key in self.cache:
            self._remove(key)
        
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.timestamps.pop(next(reversed(self.cache)))
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def _remove(self, key: str):
        """Remove item from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "utilization": len(self.cache) / self.max_size * 100
        }

# Global cache instances
spc_cache = LRUCache(max_size=256, ttl=1800)  # 30 minutes for SPC
delta_e_cache = LRUCache(max_size=512, ttl=3600)  # 1 hour for Delta E
ral_cache = LRUCache(max_size=128, ttl=7200)  # 2 hours for RAL lookups

def cached(cache_instance: LRUCache):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_instance._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_value = cache_instance.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache_instance.set(key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator

def clear_all_caches():
    """Clear all global caches."""
    spc_cache.clear()
    delta_e_cache.clear()
    ral_cache.clear()
    logger.info("All caches cleared")

def get_cache_stats() -> dict:
    """Get statistics for all caches."""
    return {
        "spc_cache": spc_cache.get_stats(),
        "delta_e_cache": delta_e_cache.get_stats(),
        "ral_cache": ral_cache.get_stats()
    }
