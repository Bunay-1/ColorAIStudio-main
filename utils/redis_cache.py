"""
Redis Cache Service for ICAP Platform v8.10.0
=============================================
High-performance caching layer for color measurements and RAG results
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta
import redis
from redis import Redis
from redis.exceptions import RedisError, ConnectionError
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ICAP_RedisCache")


class RedisCache:
    """Redis cache manager with connection pooling and error handling"""
    
    _instance: Optional['RedisCache'] = None
    _client: Optional[Redis] = None
    
    def __new__(cls) -> 'RedisCache':
        """Singleton pattern for Redis connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize Redis connection with connection pooling"""
        if self._client is not None:
            return
            
        try:
            redis_host = os.environ.get("REDIS_HOST", "localhost")
            redis_port = int(os.environ.get("REDIS_PORT", 6379))
            redis_db = int(os.environ.get("REDIS_DB", 0))
            redis_password = os.environ.get("REDIS_PASSWORD")
            
            self._client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20,
                health_check_interval=30
            )
            
            # Test connection
            self._client.ping()
            logger.info(f"Redis cache connected to {redis_host}:{redis_port}")
            
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self._client = None
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if self._client is None:
            return False
        try:
            return self._client.ping()
        except RedisError:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available:
            return None
            
        try:
            value = self._client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.is_available:
            return False
            
        try:
            # Serialize to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if ttl is None:
                return self._client.set(key, value)
            elif isinstance(ttl, timedelta):
                return self._client.setex(key, ttl, value)
            else:
                return self._client.setex(key, ttl, value)
                
        except RedisError as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available:
            return False
            
        try:
            return bool(self._client.delete(key))
        except RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_available:
            return 0
            
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis DELETE_PATTERN error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_available:
            return False
            
        try:
            return bool(self._client.exists(key))
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache (use with caution)"""
        if not self.is_available:
            return False
            
        try:
            self._client.flushdb()
            logger.warning("Redis cache cleared")
            return True
        except RedisError as e:
            logger.error(f"Redis CLEAR error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.is_available:
            return {"available": False}
            
        try:
            info = self._client.info()
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "total_keys": self._client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except RedisError as e:
            logger.error(f"Redis STATS error: {e}")
            return {"available": False, "error": str(e)}


# Global cache instance
cache = RedisCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set for {cache_key}")
            
            return result
        return wrapper
    return decorator
