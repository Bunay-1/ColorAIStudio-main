"""
Custom Business Metrics for ICAP
==================================
Business-specific metrics for monitoring quality, performance, and efficiency.
"""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("BusinessMetrics")

class BusinessMetrics:
    """Custom business metrics collector for ICAP."""
    
    def __init__(self, max_history: int = 1000):
        """
        Args:
            max_history: Maximum number of data points to keep in memory
        """
        self.max_history = max_history
        
        # Quality metrics
        self.color_quality_pass_rate = deque(maxlen=max_history)
        self.delta_e_values = deque(maxlen=max_history)
        self.batch_failures = defaultdict(int)
        
        # Performance metrics
        self.analysis_times = defaultdict(deque)  # operation -> times
        self.vision_detection_counts = defaultdict(int)
        self.rag_query_times = deque(maxlen=max_history)
        
        # Efficiency metrics
        self.cache_hit_rates = defaultdict(list)
        self.batch_sizes = deque(maxlen=max_history)
        
        # Business KPIs
        self.scrap_rate = 0.0
        self.rework_rate = 0.0
        self.oee = 0.0  # Overall Equipment Effectiveness
        self.color_correction_time_avg = 0.0
        
        # Timestamps
        self.start_time = time.time()
        self.last_update = time.time()
    
    def record_color_analysis(self, delta_e: float, passed: bool, batch_id: str, batch_size: float):
        """
        Record color analysis metrics.
        
        Args:
            delta_e: Delta E value
            passed: Whether the color passed quality check
            batch_id: Batch identifier
            batch_size: Size of the batch in kg
        """
        self.delta_e_values.append(delta_e)
        self.batch_sizes.append(batch_size)
        
        if passed:
            self.color_quality_pass_rate.append(1)
        else:
            self.color_quality_pass_rate.append(0)
            self.batch_failures[batch_id] += 1
        
        self.last_update = time.time()
    
    def record_analysis_time(self, operation: str, duration: float):
        """
        Record analysis operation duration.
        
        Args:
            operation: Name of the operation (e.g., "color_analysis", "vision_detect")
            duration: Duration in seconds
        """
        self.analysis_times[operation].append(duration)
        # Keep only last 100 measurements per operation
        if len(self.analysis_times[operation]) > 100:
            self.analysis_times[operation].popleft()
        
        self.last_update = time.time()
    
    def record_vision_detection(self, defect_count: int, image_count: int):
        """
        Record vision detection metrics.
        
        Args:
            defect_count: Number of defects detected
            image_count: Number of images processed
        """
        self.vision_detection_counts["total_images"] += image_count
        self.vision_detection_counts["total_defects"] += defect_count
        self.vision_detection_counts["defects_per_image"] = defect_count / max(image_count, 1)
        
        self.last_update = time.time()
    
    def record_rag_query(self, query_time: float, result_count: int):
        """
        Record RAG query metrics.
        
        Args:
            query_time: Time taken for query in seconds
            result_count: Number of results returned
        """
        self.rag_query_times.append(query_time)
        self.last_update = time.time()
    
    def record_cache_hit(self, cache_name: str, hit: bool):
        """
        Record cache hit/miss.
        
        Args:
            cache_name: Name of the cache
            hit: Whether it was a cache hit
        """
        self.cache_hit_rates[cache_name].append(1 if hit else 0)
        # Keep only last 100 measurements
        if len(self.cache_hit_rates[cache_name]) > 100:
            self.cache_hit_rates[cache_name].pop(0)
        
        self.last_update = time.time()
    
    def calculate_quality_metrics(self) -> Dict:
        """Calculate quality-related metrics."""
        if not self.color_quality_pass_rate:
            return {"pass_rate": 0.0, "avg_delta_e": 0.0, "std_delta_e": 0.0}
        
        import numpy as np
        
        pass_rate = sum(self.color_quality_pass_rate) / len(self.color_quality_pass_rate) * 100
        avg_delta_e = sum(self.delta_e_values) / len(self.delta_e_values)
        std_delta_e = np.std(list(self.delta_e_values)) if len(self.delta_e_values) > 1 else 0.0
        
        return {
            "pass_rate": round(pass_rate, 2),
            "avg_delta_e": round(avg_delta_e, 4),
            "std_delta_e": round(std_delta_e, 4),
            "total_analyses": len(self.color_quality_pass_rate),
            "failed_batches": len(self.batch_failures)
        }
    
    def calculate_performance_metrics(self) -> Dict:
        """Calculate performance-related metrics."""
        metrics = {}
        
        for operation, times in self.analysis_times.items():
            if times:
                import numpy as np
                metrics[f"{operation}_avg_time"] = round(sum(times) / len(times), 4)
                metrics[f"{operation}_p50_time"] = round(np.percentile(times, 50), 4)
                metrics[f"{operation}_p95_time"] = round(np.percentile(times, 95), 4)
                metrics[f"{operation}_p99_time"] = round(np.percentile(times, 99), 4)
        
        # RAG query metrics
        if self.rag_query_times:
            import numpy as np
            metrics["rag_avg_query_time"] = round(sum(self.rag_query_times) / len(self.rag_query_times), 4)
            metrics["rag_p95_query_time"] = round(np.percentile(list(self.rag_query_times), 95), 4)
        
        return metrics
    
    def calculate_efficiency_metrics(self) -> Dict:
        """Calculate efficiency-related metrics."""
        metrics = {}
        
        # Cache hit rates
        for cache_name, hits in self.cache_hit_rates.items():
            if hits:
                hit_rate = sum(hits) / len(hits) * 100
                metrics[f"{cache_name}_hit_rate"] = round(hit_rate, 2)
        
        # Batch size statistics
        if self.batch_sizes:
            import numpy as np
            metrics["avg_batch_size"] = round(sum(self.batch_sizes) / len(self.batch_sizes), 2)
            metrics["total_processed_kg"] = round(sum(self.batch_sizes), 2)
        
        return metrics
    
    def calculate_business_kpis(self) -> Dict:
        """Calculate business KPIs."""
        quality_metrics = self.calculate_quality_metrics()
        
        # Calculate scrap rate (simplified)
        pass_rate = quality_metrics.get("pass_rate", 100)
        self.scrap_rate = max(0, 100 - pass_rate)
        
        # Calculate rework rate (simplified - based on batch failures)
        total_batches = quality_metrics.get("total_analyses", 0)
        failed_batches = quality_metrics.get("failed_batches", 0)
        self.rework_rate = (failed_batches / max(total_batches, 1)) * 100 if total_batches > 0 else 0
        
        # OEE (Overall Equipment Effectiveness) - simplified calculation
        # OEE = Availability × Performance × Quality
        # For now, we use quality as a proxy
        self.oee = pass_rate / 100
        
        return {
            "scrap_rate": round(self.scrap_rate, 2),
            "rework_rate": round(self.rework_rate, 2),
            "oee": round(self.oee, 4),
            "quality_score": round(pass_rate, 2)
        }
    
    def get_all_metrics(self) -> Dict:
        """Get all collected metrics."""
        return {
            "quality": self.calculate_quality_metrics(),
            "performance": self.calculate_performance_metrics(),
            "efficiency": self.calculate_efficiency_metrics(),
            "business_kpis": self.calculate_business_kpis(),
            "system": {
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "last_update": datetime.fromtimestamp(self.last_update).isoformat()
            }
        }
    
    def reset(self):
        """Reset all metrics."""
        self.color_quality_pass_rate.clear()
        self.delta_e_values.clear()
        self.batch_failures.clear()
        
        for operation in self.analysis_times:
            self.analysis_times[operation].clear()
        
        self.vision_detection_counts.clear()
        self.rag_query_times.clear()
        
        for cache_name in self.cache_hit_rates:
            self.cache_hit_rates[cache_name].clear()
        
        self.batch_sizes.clear()
        
        self.start_time = time.time()
        self.last_update = time.time()
        
        logger.info("Business metrics reset")

# Global metrics instance
business_metrics = BusinessMetrics()
