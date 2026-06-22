"""
Performance Optimization and Load Testing for ICAP
==================================================
"""

import asyncio
import time
import statistics
import httpx
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LoadTest")

class LoadTestConfig:
    """Configuration for load testing."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        num_users: int = 10,
        requests_per_user: int = 100,
        concurrent_requests: int = 5
    ):
        self.base_url = base_url
        self.num_users = num_users
        self.requests_per_user = requests_per_user
        self.concurrent_requests = concurrent_requests

class LoadTestResults:
    """Results from load testing."""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, success: bool, response_time: float, error: str = None):
        """Add a single request result."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
        else:
            self.failed_requests += 1
            if error:
                self.errors.append(error)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate performance statistics."""
        if not self.response_times:
            return {}
        
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "duration_seconds": duration,
            "requests_per_second": self.total_requests / duration if duration > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
            "error_count": len(self.errors),
            "error_rate": (len(self.errors) / self.total_requests * 100) if self.total_requests > 0 else 0
        }

class ICapLoadTester:
    """Load tester for ICAP API."""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = LoadTestResults()
    
    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> bool:
        """Test a single endpoint."""
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            success = response.status_code < 400
            error = f"HTTP {response.status_code}" if not success else None
            
            self.results.add_result(success, response_time, error)
            
            return success
            
        except Exception as e:
            response_time = time.time() - start_time
            error = str(e)
            self.results.add_result(False, response_time, error)
            return False
    
    async def test_health_endpoint(self):
        """Test the health endpoint."""
        logger.info("Testing health endpoint...")
        await self.test_endpoint("GET", "/health")
    
    async def test_color_analyze_endpoint(self):
        """Test the color analyze endpoint."""
        logger.info("Testing color analyze endpoint...")
        
        data = {
            "lab_sample": [50.0, 2.0, 5.0],
            "lab_standard": [50.0, 2.0, 5.0],
            "tolerance": 1.0,
            "batch_id": "test_batch",
            "operator_id": "test_operator",
            "machine_id": "test_machine",
            "client_id": "test_client",
            "method": "CIE2000",
            "illuminant": "D65",
            "batch_size": 1000
        }
        
        await self.test_endpoint("POST", "/color/analyze", data)
    
    async def test_vision_analyze_endpoint(self):
        """Test the vision analyze endpoint (requires file)."""
        logger.info("Skipping vision analyze endpoint (requires file upload)...")
        # This would require a file upload, skipping for now
    
    async def test_rag_diagnose_endpoint(self):
        """Test the RAG diagnose endpoint."""
        logger.info("Testing RAG diagnose endpoint...")
        
        data = {
            "prompt": "What is the color analysis process?",
            "use_rag": False,
            "temperature": 0.7
        }
        
        await self.test_endpoint("POST", "/rag/diagnose", data)
    
    async def test_rag_stats_endpoint(self):
        """Test the RAG stats endpoint."""
        logger.info("Testing RAG stats endpoint...")
        await self.test_endpoint("GET", "/rag/stats")
    
    async def run_user_session(self, user_id: int):
        """Simulate a user session with multiple requests."""
        logger.info(f"Starting user session {user_id}...")
        
        # Mix of different requests
        endpoints = [
            ("GET", "/health", None),
            ("POST", "/color/analyze", {"lab_sample": [50.0, 2.0, 5.0], "lab_standard": [50.0, 2.0, 5.0], "tolerance": 1.0, "batch_id": f"batch_{user_id}", "operator_id": f"operator_{user_id}", "machine_id": f"machine_{user_id}", "client_id": "test_client", "method": "CIE2000", "illuminant": "D65", "batch_size": 1000}),
            ("GET", "/rag/stats", None),
        ]
        
        for i in range(self.config.requests_per_user):
            method, endpoint, data = endpoints[i % len(endpoints)]
            await self.test_endpoint(method, endpoint, data)
    
    async def run_concurrent_load_test(self):
        """Run concurrent load test with multiple users."""
        logger.info(f"Starting concurrent load test with {self.config.num_users} users...")
        
        self.results.start_time = time.time()
        
        # Create tasks for each user session
        tasks = [
            self.run_user_session(user_id)
            for user_id in range(self.config.num_users)
        ]
        
        # Run tasks concurrently
        await asyncio.gather(*tasks)
        
        self.results.end_time = time.time()
        
        logger.info("Load test completed")
    
    def print_results(self):
        """Print load test results."""
        stats = self.results.get_statistics()
        
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        print(f"Total Requests: {stats.get('total_requests', 0)}")
        print(f"Successful: {stats.get('successful_requests', 0)}")
        print(f"Failed: {stats.get('failed_requests', 0)}")
        print(f"Success Rate: {stats.get('success_rate', 0):.2f}%")
        print(f"Duration: {stats.get('duration_seconds', 0):.2f}s")
        print(f"Requests/Second: {stats.get('requests_per_second', 0):.2f}")
        print(f"\nResponse Times:")
        print(f"  Average: {stats.get('avg_response_time', 0):.3f}s")
        print(f"  Median: {stats.get('median_response_time', 0):.3f}s")
        print(f"  Min: {stats.get('min_response_time', 0):.3f}s")
        print(f"  Max: {stats.get('max_response_time', 0):.3f}s")
        print(f"  P95: {stats.get('p95_response_time', 0):.3f}s")
        print(f"  P99: {stats.get('p99_response_time', 0):.3f}s")
        print(f"\nErrors: {stats.get('error_count', 0)}")
        print(f"Error Rate: {stats.get('error_rate', 0):.2f}%")
        
        if self.results.errors:
            print("\nSample Errors:")
            for error in self.results.errors[:5]:
                print(f"  - {error}")
        
        print("="*60 + "\n")
    
    def save_results(self, filename: str = "load_test_results.json"):
        """Save load test results to file."""
        stats = self.results.get_statistics()
        
        results_data = {
            "config": {
                "base_url": self.config.base_url,
                "num_users": self.config.num_users,
                "requests_per_user": self.config.requests_per_user,
                "concurrent_requests": self.config.concurrent_requests
            },
            "results": stats,
            "errors": self.results.errors[:10]  # Save first 10 errors
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Results saved to {filename}")

class PerformanceOptimizer:
    """Performance optimization recommendations."""
    
    @staticmethod
    def analyze_results(results: Dict[str, Any]) -> List[str]:
        """Analyze load test results and provide recommendations."""
        recommendations = []
        
        # Response time analysis
        avg_response_time = results.get('avg_response_time', 0)
        p95_response_time = results.get('p95_response_time', 0)
        
        if avg_response_time > 1.0:
            recommendations.append("⚠️  Average response time > 1s - Consider optimizing database queries or adding caching")
        
        if p95_response_time > 2.0:
            recommendations.append("⚠️  P95 response time > 2s - Consider implementing request queuing for heavy operations")
        
        # Success rate analysis
        success_rate = results.get('success_rate', 100)
        if success_rate < 99:
            recommendations.append(f"⚠️  Success rate {success_rate:.1f}% - Check error logs and implement retry logic")
        
        # Throughput analysis
        requests_per_second = results.get('requests_per_second', 0)
        if requests_per_second < 10:
            recommendations.append("⚠️  Low throughput - Consider horizontal scaling or connection pooling")
        
        # Error rate analysis
        error_rate = results.get('error_rate', 0)
        if error_rate > 1:
            recommendations.append(f"⚠️  Error rate {error_rate:.1f}% - Implement circuit breaker pattern")
        
        if not recommendations:
            recommendations.append("✅ Performance is within acceptable ranges")
        
        return recommendations

async def main():
    """Main function to run load tests."""
    import sys
    
    # Configuration
    config = LoadTestConfig(
        base_url=sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000",
        num_users=int(sys.argv[2]) if len(sys.argv) > 2 else 10,
        requests_per_user=int(sys.argv[3]) if len(sys.argv) > 3 else 50,
        concurrent_requests=int(sys.argv[4]) if len(sys.argv) > 4 else 5
    )
    
    logger.info(f"Starting load test against {config.base_url}")
    logger.info(f"Users: {config.num_users}, Requests per user: {config.requests_per_user}")
    
    # Create load tester
    tester = ICapLoadTester(config)
    
    # Run load test
    await tester.run_concurrent_load_test()
    
    # Print results
    tester.print_results()
    
    # Save results
    tester.save_results()
    
    # Analyze results and provide recommendations
    stats = tester.results.get_statistics()
    recommendations = PerformanceOptimizer.analyze_results(stats)
    
    print("\nPerformance Recommendations:")
    for rec in recommendations:
        print(f"  {rec}")

if __name__ == "__main__":
    asyncio.run(main())
