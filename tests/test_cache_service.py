"""
Unit tests for Cache Service
"""

import pytest
from unittest.mock import Mock, patch
from utils.cache_service import CacheService, CacheLevel, CacheEvictionPolicy


@pytest.fixture
def cache_service():
    """Fixture for CacheService instance"""
    return CacheService()


class TestCacheService:
    """Test cases for CacheService"""

    def test_set_cache_value(self, cache_service):
        """Test setting cache value"""
        result = cache_service.set(
            key="test_key",
            value="test_value",
            ttl=3600,
            level=CacheLevel.MEMORY
        )
        
        assert result is True
        assert cache_service.exists("test_key") is True

    def test_get_cache_value(self, cache_service):
        """Test getting cache value"""
        cache_service.set("test_key", "test_value", ttl=3600)
        
        value = cache_service.get("test_key")
        
        assert value == "test_value"

    def test_get_cache_value_not_found(self, cache_service):
        """Test getting non-existent cache value"""
        value = cache_service.get("non_existent_key")
        
        assert value is None

    def test_delete_cache_value(self, cache_service):
        """Test deleting cache value"""
        cache_service.set("test_key", "test_value", ttl=3600)
        
        result = cache_service.delete("test_key")
        
        assert result is True
        assert cache_service.exists("test_key") is False

    def test_clear_cache_memory_level(self, cache_service):
        """Test clearing memory cache"""
        cache_service.set("key1", "value1", ttl=3600, level=CacheLevel.MEMORY)
        cache_service.set("key2", "value2", ttl=3600, level=CacheLevel.MEMORY)
        
        result = cache_service.clear(level=CacheLevel.MEMORY)
        
        assert result is True
        assert cache_service.exists("key1") is False
        assert cache_service.exists("key2") is False

    def test_clear_cache_disk_level(self, cache_service):
        """Test clearing disk cache"""
        cache_service.set("key1", "value1", ttl=3600, level=CacheLevel.DISK)
        
        result = cache_service.clear(level=CacheLevel.DISK)
        
        assert result is True

    def test_clear_cache_all_levels(self, cache_service):
        """Test clearing all cache levels"""
        cache_service.set("key1", "value1", ttl=3600, level=CacheLevel.MEMORY)
        cache_service.set("key2", "value2", ttl=3600, level=CacheLevel.DISK)
        
        result = cache_service.clear(level=CacheLevel.ALL)
        
        assert result is True

    def test_invalidate_cache_pattern(self, cache_service):
        """Test invalidating cache by pattern"""
        cache_service.set("user_1", "data1", ttl=3600)
        cache_service.set("user_2", "data2", ttl=3600)
        cache_service.set("product_1", "data3", ttl=3600)
        
        result = cache_service.invalidate_pattern("user_*")
        
        assert result is True
        assert cache_service.exists("user_1") is False
        assert cache_service.exists("user_2") is False
        assert cache_service.exists("product_1") is True

    def test_get_cache_statistics(self, cache_service):
        """Test getting cache statistics"""
        cache_service.set("key1", "value1", ttl=3600)
        cache_service.set("key2", "value2", ttl=3600)
        cache_service.get("key1")
        cache_service.get("key3")  # Cache miss
        
        stats = cache_service.get_statistics()
        
        assert stats["total_keys"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_ttl_expiration(self, cache_service):
        """Test cache TTL expiration"""
        cache_service.set("test_key", "test_value", ttl=1)  # 1 second TTL
        
        import time
        time.sleep(2)
        
        value = cache_service.get("test_key")
        
        assert value is None

    def test_cache_lru_eviction(self, cache_service):
        """Test LRU cache eviction"""
        cache_service.set_max_size(3)
        cache_service.set_eviction_policy(CacheEvictionPolicy.LRU)
        
        cache_service.set("key1", "value1", ttl=3600)
        cache_service.set("key2", "value2", ttl=3600)
        cache_service.set("key3", "value3", ttl=3600)
        cache_service.set("key4", "value4", ttl=3600)  # Should evict key1
        
        assert cache_service.exists("key1") is False
        assert cache_service.exists("key4") is True

    def test_cache_set_with_metadata(self, cache_service):
        """Test setting cache with metadata"""
        metadata = {"source": "api", "version": "1.0"}
        
        cache_service.set("test_key", "test_value", ttl=3600, metadata=metadata)
        
        value, retrieved_metadata = cache_service.get_with_metadata("test_key")
        
        assert value == "test_value"
        assert retrieved_metadata["source"] == "api"
        assert retrieved_metadata["version"] == "1.0"

    def test_cache_increment(self, cache_service):
        """Test incrementing cache value"""
        cache_service.set("counter", 5, ttl=3600)
        
        new_value = cache_service.increment("counter", 3)
        
        assert new_value == 8

    def test_cache_decrement(self, cache_service):
        """Test decrementing cache value"""
        cache_service.set("counter", 10, ttl=3600)
        
        new_value = cache_service.decrement("counter", 3)
        
        assert new_value == 7

    def test_cache_append_to_list(self, cache_service):
        """Test appending to list in cache"""
        cache_service.set("my_list", [1, 2, 3], ttl=3600)
        
        cache_service.append("my_list", 4)
        
        value = cache_service.get("my_list")
        
        assert value == [1, 2, 3, 4]

    def test_cache_get_multiple_keys(self, cache_service):
        """Test getting multiple cache keys"""
        cache_service.set("key1", "value1", ttl=3600)
        cache_service.set("key2", "value2", ttl=3600)
        cache_service.set("key3", "value3", ttl=3600)
        
        values = cache_service.get_multiple(["key1", "key2", "key3"])
        
        assert values["key1"] == "value1"
        assert values["key2"] == "value2"
        assert values["key3"] == "value3"

    def test_cache_set_multiple_keys(self, cache_service):
        """Test setting multiple cache keys"""
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        result = cache_service.set_multiple(data, ttl=3600)
        
        assert result is True
        assert cache_service.exists("key1") is True
        assert cache_service.exists("key2") is True
        assert cache_service.exists("key3") is True

    def test_cache_exists(self, cache_service):
        """Test checking if key exists"""
        cache_service.set("test_key", "test_value", ttl=3600)
        
        assert cache_service.exists("test_key") is True
        assert cache_service.exists("non_existent") is False

    def test_cache_expire(self, cache_service):
        """Test expiring a key"""
        cache_service.set("test_key", "test_value", ttl=3600)
        
        result = cache_service.expire("test_key", ttl=1)
        
        assert result is True
        
        import time
        time.sleep(2)
        
        assert cache_service.exists("test_key") is False

    def test_cache_persist(self, cache_service):
        """Test persisting a key (removing TTL)"""
        cache_service.set("test_key", "test_value", ttl=3600)
        
        result = cache_service.persist("test_key")
        
        assert result is True

    def test_cache_rename(self, cache_service):
        """Test renaming a key"""
        cache_service.set("old_key", "value", ttl=3600)
        
        result = cache_service.rename("old_key", "new_key")
        
        assert result is True
        assert cache_service.exists("new_key") is True
        assert cache_service.exists("old_key") is False

    def test_cache_get_size(self, cache_service):
        """Test getting cache size"""
        cache_service.set("key1", "value1", ttl=3600)
        cache_service.set("key2", "value2", ttl=3600)
        
        size = cache_service.get_size()
        
        assert size == 2

    def test_cache_flush_all(self, cache_service):
        """Test flushing all cache"""
        cache_service.set("key1", "value1", ttl=3600)
        cache_service.set("key2", "value2", ttl=3600)
        
        result = cache_service.flush_all()
        
        assert result is True
        assert cache_service.get_size() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
