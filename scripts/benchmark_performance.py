#!/usr/bin/env python3
"""
Performance Benchmarking Suite for ICAP Enterprise
==================================================
Comprehensive performance benchmarking for ICAP v8.9.5 Enterprise.
"""

import asyncio
import time
import statistics
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    duration_ms: float
    success: bool
    status_code: int = None
    error: str = None

@dataclass
class BenchmarkStats:
    """Statistics for a benchmark."""
    name: str
    runs: int
    success_count: int
    failure_count: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    throughput_rps: float

class PerformanceBenchmark:
    """Performance benchmarking suite for ICAP."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.token = None
        self.results: List[BenchmarkResult] = []
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def authenticate(self, username: str = "admin", password: str = "admin_password"):
        """Authenticate and get token."""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def run_benchmark(
        self,
        name: str,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
        runs: int = 10
    ) -> BenchmarkStats:
        """Run a benchmark for a specific endpoint."""
        logger.info(f"Running benchmark: {name} ({runs} runs)")
        
        results = []
        
        for i in range(runs):
            start_time = time.time()
            try:
                if method == "GET":
                    response = await self.client.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        params=params
                    )
                elif method == "POST":
                    response = await self.client.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        json=data,
                        params=params
                    )
                elif method == "PUT":
                    response = await self.client.put(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers(),
                        json=data
                    )
                elif method == "DELETE":
                    response = await self.client.delete(
                        f"{self.base_url}{endpoint}",
                        headers=self.get_headers()
                    )
                
                duration_ms = (time.time() - start_time) * 1000
                success = response.status_code in [200, 201]
                
                result = BenchmarkResult(
                    name=name,
                    duration_ms=duration_ms,
                    success=success,
                    status_code=response.status_code
                )
                results.append(result)
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                result = BenchmarkResult(
                    name=name,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                )
                results.append(result)
        
        # Calculate statistics
        successful_results = [r for r in results if r.success]
        durations = [r.duration_ms for r in successful_results]
        
        if durations:
            stats = BenchmarkStats(
                name=name,
                runs=runs,
                success_count=len(successful_results),
                failure_count=len(results) - len(successful_results),
                min_ms=min(durations),
                max_ms=max(durations),
                mean_ms=statistics.mean(durations),
                median_ms=statistics.median(durations),
                p95_ms=statistics.quantiles(durations, n=100)[94] if len(durations) >= 100 else sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0,
                p99_ms=statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 0 else 0,
                std_dev_ms=statistics.stdev(durations) if len(durations) > 1 else 0,
                throughput_rps=len(successful_results) / (sum(durations) / 1000) if sum(durations) > 0 else 0
            )
        else:
            stats = BenchmarkStats(
                name=name,
                runs=runs,
                success_count=0,
                failure_count=runs,
                min_ms=0,
                max_ms=0,
                mean_ms=0,
                median_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_dev_ms=0,
                throughput_rps=0
            )
        
        self.results.extend(results)
        return stats
    
    async def benchmark_authentication(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark authentication endpoints."""
        return await self.run_benchmark(
            name="Authentication (Login)",
            method="POST",
            endpoint="/auth/login",
            data={"username": "admin", "password": "admin_password"},
            runs=runs
        )
    
    async def benchmark_color_analysis(self, runs: int = 20) -> BenchmarkStats:
        """Benchmark color analysis endpoint."""
        return await self.run_benchmark(
            name="Color Analysis",
            method="POST",
            endpoint="/color/analyze",
            data={
                "lab_sample": [50.0, 2.0, 5.0],
                "lab_standard": [50.0, 2.0, 5.0],
                "tolerance": 1.0,
                "batch_id": "benchmark_batch",
                "operator_id": "benchmark_operator",
                "machine_id": "benchmark_machine",
                "client_id": "benchmark_client",
                "method": "CIE2000",
                "illuminant": "D65",
                "batch_size": 1000
            },
            runs=runs
        )
    
    async def benchmark_vision_analysis(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark vision analysis endpoint (if available)."""
        # Note: This requires actual image files
        logger.info("Vision analysis benchmark skipped (requires image files)")
        return None
    
    async def benchmark_rag_query(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark RAG query endpoint."""
        return await self.run_benchmark(
            name="RAG Query",
            method="POST",
            endpoint="/rag/diagnose",
            data={
                "prompt": "What causes color variations?",
                "use_rag": True,
                "temperature": 0.7
            },
            runs=runs
        )
    
    async def benchmark_user_management(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark user management endpoints."""
        return await self.run_benchmark(
            name="User Management (List Users)",
            method="GET",
            endpoint="/auth/users",
            runs=runs
        )
    
    async def benchmark_tenant_management(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark tenant management endpoints."""
        return await self.run_benchmark(
            name="Tenant Management (List Tenants)",
            method="GET",
            endpoint="/auth/tenants",
            runs=runs
        )
    
    async def benchmark_audit_logs(self, runs: int = 10) -> BenchmarkStats:
        """Benchmark audit log query endpoint."""
        return await self.run_benchmark(
            name="Audit Logs Query",
            method="GET",
            endpoint="/auth/audit/logs",
            params={"limit": 10},
            runs=runs
        )
    
    async def benchmark_health_check(self, runs: int = 50) -> BenchmarkStats:
        """Benchmark health check endpoint."""
        return await self.run_benchmark(
            name="Health Check",
            method="GET",
            endpoint="/health",
            runs=runs
        )
    
    async def run_concurrent_benchmark(
        self,
        name: str,
        method: str,
        endpoint: str,
        data: dict = None,
        concurrent_requests: int = 10,
        total_requests: int = 100
    ) -> BenchmarkStats:
        """Run concurrent benchmark to test load handling."""
        logger.info(f"Running concurrent benchmark: {name} ({concurrent_requests} concurrent, {total_requests} total)")
        
        results = []
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    if method == "GET":
                        response = await self.client.get(
                            f"{self.base_url}{endpoint}",
                            headers=self.get_headers()
                        )
                    elif method == "POST":
                        response = await self.client.post(
                            f"{self.base_url}{endpoint}",
                            headers=self.get_headers(),
                            json=data
                        )
                    
                    duration_ms = (time.time() - start_time) * 1000
                    success = response.status_code in [200, 201]
                    
                    result = BenchmarkResult(
                        name=name,
                        duration_ms=duration_ms,
                        success=success,
                        status_code=response.status_code
                    )
                    results.append(result)
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    result = BenchmarkResult(
                        name=name,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(e)
                    )
                    results.append(result)
        
        # Run concurrent requests
        start_time = time.time()
        await asyncio.gather(*[make_request() for _ in range(total_requests)])
        total_duration = time.time() - start_time
        
        # Calculate statistics
        successful_results = [r for r in results if r.success]
        durations = [r.duration_ms for r in successful_results]
        
        if durations:
            stats = BenchmarkStats(
                name=name,
                runs=total_requests,
                success_count=len(successful_results),
                failure_count=len(results) - len(successful_results),
                min_ms=min(durations),
                max_ms=max(durations),
                mean_ms=statistics.mean(durations),
                median_ms=statistics.median(durations),
                p95_ms=statistics.quantiles(durations, n=100)[94] if len(durations) >= 100 else sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0,
                p99_ms=statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 0 else 0,
                std_dev_ms=statistics.stdev(durations) if len(durations) > 1 else 0,
                throughput_rps=len(successful_results) / total_duration
            )
        else:
            stats = BenchmarkStats(
                name=name,
                runs=total_requests,
                success_count=0,
                failure_count=total_requests,
                min_ms=0,
                max_ms=0,
                mean_ms=0,
                median_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_dev_ms=0,
                throughput_rps=0
            )
        
        self.results.extend(results)
        return stats
    
    async def run_full_benchmark_suite(self):
        """Run comprehensive benchmark suite."""
        logger.info("=" * 60)
        logger.info("Starting Full Benchmark Suite")
        logger.info("=" * 60)
        
        stats_list = []
        
        # Authentication
        await self.authenticate()
        
        # Sequential benchmarks
        stats_list.append(await self.benchmark_health_check(runs=50))
        stats_list.append(await self.benchmark_authentication(runs=10))
        stats_list.append(await self.benchmark_color_analysis(runs=20))
        stats_list.append(await self.benchmark_rag_query(runs=10))
        stats_list.append(await self.benchmark_user_management(runs=10))
        stats_list.append(await self.benchmark_tenant_management(runs=10))
        stats_list.append(await self.benchmark_audit_logs(runs=10))
        
        # Concurrent benchmarks
        stats_list.append(await self.run_concurrent_benchmark(
            name="Concurrent Health Check",
            method="GET",
            endpoint="/health",
            concurrent_requests=20,
            total_requests=200
        ))
        
        stats_list.append(await self.run_concurrent_benchmark(
            name="Concurrent Color Analysis",
            method="POST",
            endpoint="/color/analyze",
            data={
                "lab_sample": [50.0, 2.0, 5.0],
                "lab_standard": [50.0, 2.0, 5.0],
                "tolerance": 1.0,
                "batch_id": "concurrent_batch",
                "operator_id": "concurrent_operator",
                "machine_id": "concurrent_machine",
                "client_id": "concurrent_client",
                "method": "CIE2000",
                "illuminant": "D65",
                "batch_size": 1000
            },
            concurrent_requests=10,
            total_requests=50
        ))
        
        # Filter None results
        stats_list = [s for s in stats_list if s is not None]
        
        # Print summary
        self.print_summary(stats_list)
        
        # Save results
        self.save_results(stats_list)
        
        return stats_list
    
    def print_summary(self, stats_list: List[BenchmarkStats]):
        """Print benchmark summary."""
        logger.info("=" * 60)
        logger.info("Benchmark Summary")
        logger.info("=" * 60)
        
        for stats in stats_list:
            logger.info(f"\n{stats.name}")
            logger.info(f"  Runs: {stats.runs}")
            logger.info(f"  Success: {stats.success_count}")
            logger.info(f"  Failures: {stats.failure_count}")
            logger.info(f"  Min: {stats.min_ms:.2f} ms")
            logger.info(f"  Max: {stats.max_ms:.2f} ms")
            logger.info(f"  Mean: {stats.mean_ms:.2f} ms")
            logger.info(f"  Median: {stats.median_ms:.2f} ms")
            logger.info(f"  P95: {stats.p95_ms:.2f} ms")
            logger.info(f"  P99: {stats.p99_ms:.2f} ms")
            logger.info(f"  Std Dev: {stats.std_dev_ms:.2f} ms")
            logger.info(f"  Throughput: {stats.throughput_rps:.2f} RPS")
    
    def save_results(self, stats_list: List[BenchmarkStats]):
        """Save benchmark results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "benchmarks": [
                {
                    "name": stats.name,
                    "runs": stats.runs,
                    "success_count": stats.success_count,
                    "failure_count": stats.failure_count,
                    "min_ms": stats.min_ms,
                    "max_ms": stats.max_ms,
                    "mean_ms": stats.mean_ms,
                    "median_ms": stats.median_ms,
                    "p95_ms": stats.p95_ms,
                    "p99_ms": stats.p99_ms,
                    "std_dev_ms": stats.std_dev_ms,
                    "throughput_rps": stats.throughput_rps
                }
                for stats in stats_list
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\nResults saved to: {filename}")

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICAP Performance Benchmark Suite")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL")
    parser.add_argument("--username", type=str, default="admin", help="Username")
    parser.add_argument("--password", type=str, default="admin_password", help="Password")
    
    args = parser.parse_args()
    
    async with PerformanceBenchmark(args.url) as benchmark:
        await benchmark.authenticate(args.username, args.password)
        await benchmark.run_full_benchmark_suite()

if __name__ == "__main__":
    asyncio.run(main())
