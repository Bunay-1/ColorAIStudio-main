# Performance Tuning Guide
=========================

## Overview
ICAP v8.9.5 Enterprise includes comprehensive performance optimization tools and monitoring capabilities. This guide covers performance tuning strategies for optimal production deployment.

## System Requirements

### Minimum Requirements
- **CPU:** 4 cores
- **Memory:** 8 GB RAM
- **Storage:** 50 GB SSD
- **Network:** 1 Gbps

### Recommended Requirements
- **CPU:** 8+ cores
- **Memory:** 16+ GB RAM
- **Storage:** 100+ GB NVMe SSD
- **Network:** 10 Gbps

### High-Performance Requirements
- **CPU:** 16+ cores
- **Memory:** 32+ GB RAM
- **Storage:** 200+ GB NVMe SSD
- **Network:** 25+ Gbps
- **GPU:** NVIDIA GPU for Vision AI (optional)

## Database Optimization

### SQLite Configuration
```python
# database.py optimizations
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")  # Balanced safety/performance
conn.execute("PRAGMA cache_size=-10000")  # 10MB cache
conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
```

### Connection Pooling
```python
# Configure connection pool
_MAX_POOL_SIZE = 10  # Increase from 5 to 10
_connection_pool = []
```

### Index Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON measurements(timestamp);
CREATE INDEX IF NOT EXISTS idx_measurements_batch_id ON measurements(batch_id);
CREATE INDEX IF NOT EXISTS idx_measurements_machine_id ON measurements(machine_id);
CREATE INDEX IF NOT EXISTS idx_measurements_client_id ON measurements(client_id);
CREATE INDEX IF NOT EXISTS idx_measurements_status ON measurements(status);
CREATE INDEX IF NOT EXISTS idx_measurements_tenant_id ON measurements(tenant_id);

-- Composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_measurements_tenant_timestamp ON measurements(tenant_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_measurements_batch_tenant ON measurements(batch_id, tenant_id);
```

### Query Optimization
```python
# Use prepared statements
cursor.execute('''
    SELECT * FROM measurements 
    WHERE batch_id = ? AND tenant_id = ?
    ORDER BY timestamp DESC 
    LIMIT ?
''', (batch_id, tenant_id, limit))

# Use specific columns instead of SELECT *
cursor.execute('''
    SELECT id, timestamp, delta_e, status 
    FROM measurements 
    WHERE batch_id = ?
''', (batch_id,))

# Use LIMIT for large result sets
cursor.execute('''
    SELECT * FROM measurements 
    ORDER BY timestamp DESC 
    LIMIT 1000
''')
```

### Data Cleanup
```python
# Regular cleanup of old data
from database import cleanup_old_data

# Clean up data older than 90 days
cleanup_old_data(days_to_keep=90)

# Clean up specific tenant data
cleanup_old_data(days_to_keep=90, tenant_id="company_a")
```

## API Performance

### Response Compression
```python
# Enable gzip compression in FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Async Operations
```python
# Use async/await for I/O operations
async def analyze_color(request: ColorAnalysisRequest):
    # Async database operations
    result = await async_db_query(query)
    
    # Async API calls
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
    
    return result
```

### Pagination
```python
# Implement pagination for large result sets
@router.get("/measurements")
async def get_measurements(
    page: int = 1,
    per_page: int = 100,
    tenant_id: str = Depends(get_current_tenant)
):
    offset = (page - 1) * per_page
    measurements = get_measurements_paginated(
        tenant_id, offset, per_page
    )
    return {
        "data": measurements,
        "page": page,
        "per_page": per_page,
        "total": total_count
    }
```

### Field Selection
```python
# Allow clients to select specific fields
@router.get("/measurements")
async def get_measurements(
    fields: str = None,  # Comma-separated field list
    tenant_id: str = Depends(get_current_tenant)
):
    if fields:
        field_list = fields.split(",")
        measurements = get_measurements_with_fields(tenant_id, field_list)
    else:
        measurements = get_all_measurements(tenant_id)
    return measurements
```

## Caching Strategy

### In-Memory Caching
```python
from utils.performance_optimizer import cached, cache_manager

# Cache expensive computations
@cached(ttl=300, max_size=1000)
async def expensive_computation(param: str):
    # Expensive operation
    result = compute_something(param)
    return result

# Manual cache usage
cache_manager.set("key", value, ttl=300)
cached_value = cache_manager.get("key")
```

### Redis Caching (Recommended for Production)
```python
import redis

# Configure Redis cache
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# Cache with Redis
def get_with_cache(key: str, ttl: int = 300):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    # Compute value
    value = compute_value()
    
    # Cache result
    redis_client.setex(key, ttl, json.dumps(value))
    return value
```

### Cache Invalidation
```python
# Invalidate cache on data changes
def update_measurement(measurement_id: str, data: dict):
    # Update database
    update_db(measurement_id, data)
    
    # Invalidate related cache
    cache_key = f"measurement_{measurement_id}"
    cache_manager.remove(cache_key)
    
    # Invalidate tenant cache
    tenant_key = f"tenant_{data['tenant_id']}_measurements"
    cache_manager.remove(tenant_key)
```

## Memory Optimization

### Lazy Loading
```python
# Load data only when needed
class MeasurementLoader:
    def __init__(self, measurement_id: str):
        self.measurement_id = measurement_id
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            self._data = load_measurement(self.measurement_id)
        return self._data
```

### Generators for Large Data
```python
# Use generators instead of lists
def get_all_measurements_generator(tenant_id: str):
    """Generator for large datasets"""
    offset = 0
    batch_size = 1000
    
    while True:
        batch = get_measurements_batch(tenant_id, offset, batch_size)
        if not batch:
            break
        
        for measurement in batch:
            yield measurement
        
        offset += batch_size
```

### Object Pooling
```python
from queue import Queue

class ObjectPool:
    def __init__(self, create_func, max_size=10):
        self.pool = Queue(maxsize=max_size)
        self.create_func = create_func
        
        # Pre-populate pool
        for _ in range(max_size):
            self.pool.put(create_func())
    
    def get(self):
        try:
            return self.pool.get_nowait()
        except:
            return self.create_func()
    
    def put(self, obj):
        try:
            self.pool.put_nowait(obj)
        except:
            pass  # Pool is full, discard object
```

## Concurrency Optimization

### Thread Pools for CPU-Bound Tasks
```python
from concurrent.futures import ThreadPoolExecutor

def process_batch_parallel(items: list, workers: int = 4):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(process_item, items))
    return results
```

### Async I/O for Network Operations
```python
import asyncio
import httpx

async def fetch_multiple_urls(urls: list):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
    return responses
```

### Request Queuing for Heavy Operations
```python
from queue import Queue
import threading

request_queue = Queue()

def worker():
    while True:
        request = request_queue.get()
        process_heavy_request(request)
        request_queue.task_done()

# Start worker threads
for _ in range(4):
    threading.Thread(target=worker, daemon=True).start()
```

## Rate Limiting Optimization

### Role-Based Rate Limits
```python
from utils.rate_limiter import configure_role_limits

# Configure role-specific limits
configure_role_limits({
    "ADMIN": 3.0,  # 3x limit for admins
    "SUPERVISOR": 2.0,
    "OPERATOR": 1.0,
    "VIEWER": 0.5
})
```

### Operation-Specific Limits
```python
from utils.rate_limiter import configure_operation_limits

# Configure operation-specific limits
configure_operation_limits({
    "light": 200,  # Increase light operation limit
    "heavy": 30,   # Increase heavy operation limit
    "auth": 20      # Increase auth limit
})
```

## Vision AI Optimization

### Model Optimization
```python
# Use TensorRT for GPU acceleration
# (Requires NVIDIA GPU and TensorRT installation)
import tensorrt as trt

# Model quantization
# Reduce model size with minimal accuracy loss
```

### Batch Processing
```python
# Process multiple images in batch
def batch_detect_defects(image_paths: list):
    results = []
    for image_path in image_paths:
        defects = vision_engine.detect_defects(image_path)
        results.append(defects)
    return results
```

### Image Optimization
```python
# Resize images to optimal size
import cv2

def optimize_image(image_path: str, max_size: int = 1920):
    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    
    if max(height, width) > max_size:
        scale = max_size / max(height, width)
        new_size = (int(width * scale), int(height * scale))
        img = cv2.resize(img, new_size)
    
    return img
```

## RAG Optimization

### Index Optimization
```python
# Use efficient embeddings
from fastembed import FastEmbed

embedding_model = FastEmbed("BAAI/bge-small-en-v1.5")

# Batch embedding
def embed_documents_batch(documents: list, batch_size: int = 100):
    embeddings = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        batch_embeddings = embedding_model.embed(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

### Query Optimization
```python
# Use hybrid search
def hybrid_search(query: str, top_k: int = 10):
    # Vector search
    vector_results = vector_search(query, top_k=top_k)
    
    # Keyword search
    keyword_results = keyword_search(query, top_k=top_k)
    
    # Combine results
    combined = combine_results(vector_results, keyword_results)
    return combined[:top_k]
```

## Monitoring and Profiling

### Performance Monitoring
```python
from utils.performance_optimizer import PerformanceMonitor, get_performance_report

# Get system metrics
metrics = PerformanceMonitor.get_system_metrics()
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_percent']}%")

# Get comprehensive report
report = get_performance_report()
```

### Function Profiling
```python
from utils.performance_optimizer import measure_performance

@measure_performance
async def slow_function():
    # Expensive operation
    await asyncio.sleep(2)
    return result
```

### Load Testing
```bash
# Run load tests
python scripts/load_test.py http://localhost:8000 10 50 5

# Arguments: base_url num_users requests_per_user concurrent_requests
```

## Kubernetes Optimization

### Resource Limits
```yaml
# k8s/icap-deployment.yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Horizontal Pod Autoscaler
```yaml
autoscaling:
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Node Affinity
```yaml
# Schedule on specific nodes
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: gpu
              operator: In
              values:
                - "true"
```

## Environment Variables

### Performance Configuration
```env
# Database Performance
ICAP_DB_POOL_SIZE=10
ICAP_DB_CACHE_SIZE=10000

# API Performance
ICAP_ASYNC_WORKERS=4
ICAP_MAX_CONCURRENT_REQUESTS=100

# Cache Configuration
ICAP_CACHE_TTL=300
ICAP_CACHE_MAX_SIZE=1000

# Rate Limiting
ICAP_RATE_LIMIT_GLOBAL=100
ICAP_RATE_LIMIT_PER_USER=50
ICAP_RATE_LIMIT_PER_TENANT=200

# Session Management
ICAP_SESSION_TIMEOUT=480
ICAP_MAX_CONCURRENT_SESSIONS=10
ICAP_MAX_CONCURRENT_OPERATIONS=5
```

## Troubleshooting

### High CPU Usage
```bash
# Check CPU usage
top -p $(pgrep -f irm_api.py)

# Profile CPU usage
python -m cProfile -s time irm_api.py

# Identify bottlenecks
python -m cProfile -s cumtime irm_api.py
```

### High Memory Usage
```bash
# Check memory usage
ps aux | grep irm_api.py

# Profile memory usage
python -m memory_profiler irm_api.py

# Check for memory leaks
python -m tracemalloc irm_api.py
```

### Slow Database Queries
```python
# Analyze query performance
from utils.performance_optimizer import QueryOptimizer

query = "SELECT * FROM measurements WHERE batch_id = ?"
optimized = QueryOptimizer.optimize_query(query)

# Execute with timing
import time
start = time.time()
cursor.execute(optimized, (batch_id,))
execution_time = time.time() - start

analysis = QueryOptimizer.analyze_query_performance(query, execution_time)
print(analysis)
```

### Slow API Responses
```bash
# Use load testing to identify slow endpoints
python scripts/load_test.py http://localhost:8000 10 50 5

# Check response times in logs
grep "executed in" logs/app.log
```

## Best Practices

### 1. Database
- Use connection pooling
- Add appropriate indexes
- Use prepared statements
- Implement query result caching
- Regularly clean up old data

### 2. API
- Enable response compression
- Implement pagination
- Use async/await for I/O
- Cache frequently accessed data
- Use field selection for large responses

### 3. Memory
- Use lazy loading
- Use generators for large datasets
- Implement object pooling
- Profile memory usage regularly
- Monitor for memory leaks

### 4. Concurrency
- Use thread pools for CPU-bound tasks
- Use async I/O for network operations
- Implement request queuing
- Monitor concurrent operations
- Set appropriate resource limits

### 5. Caching
- Cache expensive computations
- Use appropriate TTL values
- Implement cache invalidation
- Monitor cache hit rates
- Use Redis for distributed caching

## Performance Benchmarks

### Target Performance Metrics
- **API Response Time:** < 100ms (p95)
- **Database Query Time:** < 50ms (p95)
- **Vision Processing:** < 500ms per image
- **RAG Query Time:** < 1s (p95)
- **Memory Usage:** < 4GB per instance
- **CPU Usage:** < 70% under normal load

### Load Testing Results
```
Load Test Results:
Total Requests: 500
Successful: 498
Failed: 2
Success Rate: 99.6%
Duration: 30.5s
Requests/Second: 16.4

Response Times:
Average: 0.125s
Median: 0.098s
Min: 0.045s
Max: 0.890s
P95: 0.245s
P99: 0.678s
```

## Support
For performance issues:
- **Documentation:** See [Performance Tuning Guide](Docs/PERFORMANCE_TUNING.md)
- **Load Testing:** See [Load Testing Script](scripts/load_test.py)
- **Monitoring:** See [Performance Optimizer](utils/performance_optimizer.py)
- **Support:** performance@icap-enterprise.com
