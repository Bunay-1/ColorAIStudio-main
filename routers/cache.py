"""
Cache Router for ICAP Enterprise
================================
REST API endpoints for cache management and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from utils.cache_service import (
    CacheService, CacheLevel, CacheStrategy
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/cache", tags=["Cache"])
logger = logging.getLogger("Cache_Router")

cache_service = CacheService()

@router.get("/statistics")
async def get_cache_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics."""
    try:
        # Only admins can view cache statistics
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        stats = cache_service.get_statistics()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_cache(
    level: str = Query("memory"),
    current_user: dict = Depends(get_current_user)
):
    """
    Clear cache.
    
    - **level**: Cache level to clear (memory, disk)
    """
    try:
        # Only admins can clear cache
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        cache_level = CacheLevel(level)
        success = cache_service.clear(cache_level)
        
        if success:
            return {"status": "success", "message": f"Cache cleared: {level}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
            
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cache level")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/invalidate")
async def invalidate_cache_pattern(
    pattern: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Invalidate cache entries matching a pattern.
    
    - **pattern**: Key pattern to match
    """
    try:
        # Only admins can invalidate cache
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        count = cache_service.invalidate_pattern(pattern)
        
        return {
            "status": "success",
            "message": f"Invalidated {count} cache entries matching pattern: {pattern}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_cache_config(
    current_user: dict = Depends(get_current_user)
):
    """Get cache configuration."""
    try:
        # Only admins can view cache configuration
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        config = {
            "strategy": cache_service.strategy.value,
            "max_memory_entries": cache_service.max_memory_entries,
            "memory_entries": len(cache_service.memory_cache)
        }
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_cache_config(
    config: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update cache configuration.
    
    - **strategy**: Cache eviction strategy (lru, lfu, ttl)
    - **max_memory_entries**: Maximum memory cache entries
    """
    try:
        # Only admins can update cache configuration
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        if "strategy" in config:
            cache_service.strategy = CacheStrategy(config["strategy"])
        
        if "max_memory_entries" in config:
            cache_service.max_memory_entries = config["max_memory_entries"]
            cache_service._evict_lru()
        
        return {"status": "success", "message": "Cache configuration updated"}
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid configuration value")
    except Exception as e:
        logger.error(f"Error updating cache config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
