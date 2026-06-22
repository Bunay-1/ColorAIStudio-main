"""
Performance Optimization Module for ICAP
=======================================
"""

import logging
import psutil
import time
from typing import Dict, Any, List, Optional
from functools import wraps
import asyncio

logger = logging.getLogger("PerformanceOptimizer")

class PerformanceMonitor:
    """Monitor system and application performance."""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "disk_total_gb": disk.total / (1024**3)
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """Check system health and return status."""
        metrics = PerformanceMonitor.get_system_metrics()
        
        health_status = {
            "status": "healthy",
            "warnings": [],
            "critical_issues": []
        }
        
        # CPU check
        if metrics.get("cpu_percent", 0) > 90:
            health_status["status"] = "critical"
            health_status["critical_issues"].append("CPU usage > 90%")
        elif metrics.get("cpu_percent", 0) > 70:
            health_status["status"] = "warning"
            health_status["warnings"].append("CPU usage > 70%")
        
        # Memory check
        if metrics.get("memory_percent", 0) > 90:
            health_status["status"] = "critical"
            health_status["critical_issues"].append("Memory usage > 90%")
        elif metrics.get("memory_percent", 0) > 80:
            health_status["status"] = "warning"
            health_status["warnings"].append("Memory usage > 80%")
        
        # Disk check
        if metrics.get("disk_percent", 0) > 95:
            health_status["status"] = "critical"
            health_status["critical_issues"].append("Disk usage > 95%")
        elif metrics.get("disk_percent", 0) > 85:
            health_status["status"] = "warning"
            health_status["warnings"].append("Disk usage > 85%")
        
        return health_status

class PerformanceOptimizer:
    """Performance optimization recommendations and utilities."""
    
    @staticmethod
    def get_optimization_recommendations() -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Database optimization
        recommendations.append("Database: Enable connection pooling for better performance")
        recommendations.append("Database: Use prepared statements for repeated queries")
        recommendations.append("Database: Add indexes for frequently queried columns")
        recommendations.append("Database: Implement query result caching")
        
        # API optimization
        recommendations.append("API: Implement response compression (gzip)")
        recommendations.append("API: Use async/await for I/O operations")
        recommendations.append("API: Implement request batching for bulk operations")
        recommendations.append("API: Add CDN for static assets")
        
        # Caching
        recommendations.append("Caching: Implement Redis for session storage")
        recommendations.append("Caching: Cache frequently accessed data")
        recommendations.append("Caching: Use memoization for expensive computations")
        
        # Memory optimization
        recommendations.append("Memory: Implement lazy loading for large datasets")
        recommendations.append("Memory: Use generators instead of lists for large data processing")
        recommendations.append("Memory: Implement object pooling for frequently created objects")
        
        # Concurrency
        recommendations.append("Concurrency: Use thread pools for CPU-bound tasks")
        recommendations.append("Concurrency: Use async I/O for network operations")
        recommendations.append("Concurrency: Implement request queuing for heavy operations")
        
        # Monitoring
        recommendations.append("Monitoring: Implement application performance monitoring (APM)")
        recommendations.append("Monitoring: Add distributed tracing for microservices")
        recommendations.append("Monitoring: Set up alerting for performance thresholds")
        
        return recommendations
    
    @staticmethod
    def optimize_database_queries() -> Dict[str, Any]:
        """Database query optimization recommendations."""
        return {
            "connection_pooling": "Use connection pooling to reduce connection overhead",
            "query_caching": "Cache frequently executed queries",
            "index_optimization": "Add indexes for columns used in WHERE, JOIN, and ORDER BY clauses",
            "query_optimization": "Use EXPLAIN QUERY PLAN to analyze query performance",
            "batch_operations": "Use batch INSERT/UPDATE for multiple records",
            "avoid_n_plus_one": "Use JOIN or eager loading to avoid N+1 query problem"
        }
    
    @staticmethod
    def optimize_api_responses() -> Dict[str, Any]:
        """API response optimization recommendations."""
        return {
            "compression": "Enable gzip compression for responses",
            "pagination": "Implement pagination for large result sets",
            "field_selection": "Allow clients to select specific fields",
            "response_caching": "Cache GET requests with appropriate TTL",
            "async_operations": "Use async/await for I/O operations",
            "rate_limiting": "Implement rate limiting to prevent abuse"
        }
    
    @staticmethod
    def optimize_memory_usage() -> Dict[str, Any]:
        """Memory usage optimization recommendations."""
        return {
            "lazy_loading": "Implement lazy loading for large objects",
            "generators": "Use generators instead of lists for large datasets",
            "memory_profiling": "Profile memory usage to identify leaks",
            "garbage_collection": "Tune garbage collection parameters",
            "object_pooling": "Use object pooling for frequently created objects",
            "data_structures": "Use appropriate data structures (e.g., sets for lookups)"
        }

def measure_performance(func):
    """Decorator to measure function performance."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
        
        if execution_time > 1.0:
            logger.warning(f"{func.__name__} took {execution_time:.3f}s - consider optimization")
        
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
        
        if execution_time > 1.0:
            logger.warning(f"{func.__name__} took {execution_time:.3f}s - consider optimization")
        
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class CacheManager:
    """Simple in-memory cache manager."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.ttl:
            self.remove(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.remove(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def remove(self, key: str):
        """Remove value from cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "utilization": len(self.cache) / self.max_size * 100
        }

# Global cache instance
cache_manager = CacheManager()

def cached(ttl: int = 300, max_size: int = 1000):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class QueryOptimizer:
    """Database query optimization utilities."""
    
    @staticmethod
    def optimize_query(query: str) -> str:
        """Basic query optimization."""
        optimized = query.strip()
        
        # Add LIMIT if not present for SELECT queries
        if optimized.upper().startswith("SELECT") and "LIMIT" not in optimized.upper():
            optimized += " LIMIT 1000"
        
        return optimized
    
    @staticmethod
    def analyze_query_performance(query: str, execution_time: float) -> Dict[str, Any]:
        """Analyze query performance."""
        analysis = {
            "query": query,
            "execution_time": execution_time,
            "status": "good",
            "recommendations": []
        }
        
        if execution_time > 1.0:
            analysis["status"] = "slow"
            analysis["recommendations"].append("Consider adding indexes")
            analysis["recommendations"].append("Review query structure")
        
        if execution_time > 5.0:
            analysis["status"] = "critical"
            analysis["recommendations"].append("Query is too slow - immediate optimization required")
            analysis["recommendations"].append("Consider query caching")
        
        return analysis

def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        "system_metrics": PerformanceMonitor.get_system_metrics(),
        "system_health": PerformanceMonitor.check_system_health(),
        "cache_stats": cache_manager.get_stats(),
        "recommendations": PerformanceOptimizer.get_optimization_recommendations()
    }
