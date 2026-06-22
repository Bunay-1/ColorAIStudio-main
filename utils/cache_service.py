"""
Caching Service for ICAP Enterprise
==================================
Performance optimization through intelligent caching of API responses and database queries.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import os

logger = logging.getLogger("Cache_Service")

class CacheStrategy(str, Enum):
    """Cache eviction strategies."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"

class CacheLevel(str, Enum):
    """Cache levels."""
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

@dataclass
class CacheEntry:
    """Cache entry data structure."""
    key: str
    value: Any
    ttl: int
    created_at: str
    expires_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_accessed is None:
            self.last_accessed = self.created_at

class CacheService:
    """Main caching service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None, max_memory_entries: int = 1000):
        """Initialize cache service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self.max_memory_entries = max_memory_entries
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.strategy = CacheStrategy.LRU
        self._init_database()
    
    def _init_database(self):
        """Initialize cache database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    ttl INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    size_bytes INTEGER DEFAULT 0
                )
            ''')
            
            # Cache statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    evictions INTEGER DEFAULT 0,
                    total_entries INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Cache database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from prefix and parameters."""
        key_data = f"{prefix}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        return json.dumps(value)
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage."""
        return json.loads(value)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return datetime.fromisoformat(entry.expires_at) < datetime.now()
    
    def _evict_lru(self):
        """Evict least recently used entries from memory cache."""
        if len(self.memory_cache) <= self.max_memory_entries:
            return
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Evict oldest entries
        to_evict = len(self.memory_cache) - self.max_memory_entries
        for key, _ in sorted_entries[:to_evict]:
            del self.memory_cache[key]
            self._increment_evictions()
    
    def _increment_hits(self):
        """Increment cache hit counter."""
        self._update_statistics(hits=1)
    
    def _increment_misses(self):
        """Increment cache miss counter."""
        self._update_statistics(misses=1)
    
    def _increment_evictions(self):
        """Increment eviction counter."""
        self._update_statistics(evictions=1)
    
    def _update_statistics(self, hits: int = 0, misses: int = 0, evictions: int = 0):
        """Update cache statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current statistics
            cursor.execute('SELECT cache_hits, cache_misses, evictions FROM cache_statistics ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            
            if row:
                new_hits = row[0] + hits
                new_misses = row[1] + misses
                new_evictions = row[2] + evictions
            else:
                new_hits = hits
                new_misses = misses
                new_evictions = evictions
            
            # Update statistics
            cursor.execute('''
                INSERT INTO cache_statistics (cache_hits, cache_misses, evictions, total_entries, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (new_hits, new_misses, new_evictions, len(self.memory_cache), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
    
    def get(self, key: str, level: CacheLevel = CacheLevel.MEMORY) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            level: Cache level to use
        
        Returns:
            Cached value or None if not found/expired
        """
        try:
            # Check memory cache first
            if level == CacheLevel.MEMORY and key in self.memory_cache:
                entry = self.memory_cache[key]
                
                if self._is_expired(entry):
                    del self.memory_cache[key]
                    self._increment_misses()
                    return None
                
                # Update access statistics
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
                
                self._increment_hits()
                return entry.value
            
            # Check disk cache
            if level == CacheLevel.DISK:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT value, expires_at, access_count, last_accessed
                    FROM cache_entries
                    WHERE key = ?
                ''', (key,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    expires_at = datetime.fromisoformat(row[1])
                    if expires_at < datetime.now():
                        self._increment_misses()
                        return None
                    
                    # Update access statistics
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE cache_entries
                        SET access_count = access_count + 1, last_accessed = ?
                        WHERE key = ?
                    ''', (datetime.now().isoformat(), key))
                    conn.commit()
                    conn.close()
                    
                    self._increment_hits()
                    return self._deserialize_value(row[0])
            
            self._increment_misses()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            self._increment_misses()
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        level: CacheLevel = CacheLevel.MEMORY
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600)
            level: Cache level to use
        
        Returns:
            True if set successfully
        """
        try:
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value.encode())
            
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                created_at=created_at.isoformat(),
                expires_at=expires_at.isoformat(),
                size_bytes=size_bytes
            )
            
            if level == CacheLevel.MEMORY:
                self.memory_cache[key] = entry
                self._evict_lru()
            elif level == CacheLevel.DISK:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_entries
                    (key, value, ttl, created_at, expires_at, access_count, last_accessed, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    serialized_value,
                    ttl,
                    entry.created_at,
                    entry.expires_at,
                    entry.access_count,
                    entry.last_accessed,
                    entry.size_bytes
                ))
                
                conn.commit()
                conn.close()
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    def delete(self, key: str, level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            level: Cache level to use
        
        Returns:
            True if deleted successfully
        """
        try:
            if level == CacheLevel.MEMORY and key in self.memory_cache:
                del self.memory_cache[key]
            elif level == CacheLevel.DISK:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                
                conn.commit()
                conn.close()
            
            logger.debug(f"Cache deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False
    
    def clear(self, level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """
        Clear all cache entries.
        
        Args:
            level: Cache level to clear
        
        Returns:
            True if cleared successfully
        """
        try:
            if level == CacheLevel.MEMORY:
                self.memory_cache.clear()
            elif level == CacheLevel.DISK:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache_entries')
                
                conn.commit()
                conn.close()
            
            logger.info(f"Cache cleared: {level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cache_hits, cache_misses, evictions, total_entries, updated_at
                FROM cache_statistics
                ORDER BY id DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                total_requests = row[0] + row[1]
                hit_rate = (row[0] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    "cache_hits": row[0],
                    "cache_misses": row[1],
                    "evictions": row[2],
                    "total_entries": row[3],
                    "hit_rate": round(hit_rate, 2),
                    "memory_entries": len(self.memory_cache),
                    "updated_at": row[4]
                }
            
            return {
                "cache_hits": 0,
                "cache_misses": 0,
                "evictions": 0,
                "total_entries": 0,
                "hit_rate": 0.0,
                "memory_entries": len(self.memory_cache),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def cache_api_response(
        self,
        endpoint: str,
        params: Dict[str, Any],
        response: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Cache an API response.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            response: Response data
            ttl: Time to live in seconds
        
        Returns:
            True if cached successfully
        """
        key = self._generate_key(f"api:{endpoint}", params)
        return self.set(key, response, ttl, CacheLevel.MEMORY)
    
    def get_cached_api_response(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get cached API response.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
        
        Returns:
            Cached response or None
        """
        key = self._generate_key(f"api:{endpoint}", params)
        return self.get(key, CacheLevel.MEMORY)
    
    def cache_database_query(
        self,
        query: str,
        params: Dict[str, Any],
        result: Any,
        ttl: int = 1800
    ) -> bool:
        """
        Cache a database query result.
        
        Args:
            query: SQL query
            params: Query parameters
            result: Query result
            ttl: Time to live in seconds
        
        Returns:
            True if cached successfully
        """
        key = self._generate_key(f"db:{query}", params)
        return self.set(key, result, ttl, CacheLevel.MEMORY)
    
    def get_cached_database_query(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get cached database query result.
        
        Args:
            query: SQL query
            params: Query parameters
        
        Returns:
            Cached result or None
        """
        key = self._generate_key(f"db:{query}", params)
        return self.get(key, CacheLevel.MEMORY)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Key pattern to match
        
        Returns:
            Number of entries invalidated
        """
        try:
            count = 0
            
            # Invalidate from memory cache
            keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.memory_cache[key]
                count += 1
            
            # Invalidate from disk cache
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache_entries WHERE key LIKE ?', (f'%{pattern}%',))
            count += cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate pattern: {e}")
            return 0

# Global cache service instance
cache_service = CacheService()
