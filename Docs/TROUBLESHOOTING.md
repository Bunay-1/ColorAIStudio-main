# ICAP Platform Troubleshooting Guide v8.10.0 Enterprise
=====================================================

Comprehensive troubleshooting guide for common issues and solutions

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Database Issues](#database-issues)
3. [Redis Cache Issues](#redis-cache-issues)
4. [Qdrant Vector Database Issues](#qdrant-vector-database-issues)
5. [Ollama LLM Issues](#ollama-llm-issues)
6. [Authentication Issues](#authentication-issues)
7. [Performance Issues](#performance-issues)
8. [Vision AI Issues](#vision-ai-issues)
9. [RAG System Issues](#rag-system-issues)
10. [Docker Issues](#docker-issues)
11. [Kubernetes Issues](#kubernetes-issues)
12. [Network Issues](#network-issues)
13. [Monitoring and Logging](#monitoring-and-logging)

---

## Installation Issues

### Python Dependencies Installation Failed

**Problem:** `pip install -r requirements.txt` fails with dependency conflicts.

**Solution:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If still failing, try installing individually
pip install fastapi uvicorn[standard] python-multipart
pip install numpy<2.0.0 pandas scipy scikit-learn
```

### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### CUDA/GPU Issues

**Problem:** CUDA not available or GPU not detected.

**Solution:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA toolkit if missing
# Ubuntu/Debian:
sudo apt-get install nvidia-cuda-toolkit

# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## Database Issues

### SQLite Database Locked

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:**
```bash
# Check for running processes
lsof icap.db  # Linux/Mac
# Windows: Use Process Explorer

# Kill locking processes if safe
kill -9 <PID>

# Enable WAL mode for better concurrency
python -c "import sqlite3; conn = sqlite3.connect('icap.db'); conn.execute('PRAGMA journal_mode=WAL'); conn.commit()"
```

### PostgreSQL Connection Failed

**Problem:** Cannot connect to PostgreSQL database.

**Solution:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL if not running
sudo systemctl start postgresql

# Check connection
psql -U icap_user -d icap -h localhost

# Check firewall
sudo ufw allow 5432/tcp

# Verify connection string in .env
ICAP_DATABASE_URL=postgresql://icap_user:password@localhost:5432/icap
```

### Database Migration Failed

**Problem:** Alembic migration fails.

**Solution:**
```bash
# Check current migration status
alembic current

# Reset to initial state (CAUTION: drops data)
alembic downgrade base

# Re-run migrations
alembic upgrade head

# If migration conflicts, create new migration
alembic revision --autogenerate -m "fix migration"
alembic upgrade head
```

---

## Redis Cache Issues

### Redis Connection Failed

**Problem:** Cannot connect to Redis server.

**Solution:**
```bash
# Check Redis status
redis-cli ping

# Start Redis if not running
sudo systemctl start redis
# Or using Docker
docker start icap-redis

# Check Redis logs
docker logs icap-redis

# Verify connection settings
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Redis Out of Memory

**Problem:** Redis memory usage too high.

**Solution:**
```bash
# Check Redis memory usage
redis-cli INFO memory

# Configure max memory in redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru

# Or in docker-compose.yml
command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru

# Clear cache (CAUTION)
redis-cli FLUSHDB
```

### Cache Not Working

**Problem:** Cache hits not occurring despite configuration.

**Solution:**
```python
# Check Redis availability
from utils.redis_cache import cache
print(cache.is_available)

# Check cache stats
print(cache.get_stats())

# Verify cache key generation
# Ensure cache keys are consistent
cache_key = f"delta_e:CIEDE2000:{tuple(lab_sample)}:{tuple(lab_standard)}"
print(cache_key)
```

---

## Qdrant Vector Database Issues

### Qdrant Connection Failed

**Problem:** Cannot connect to Qdrant vector database.

**Solution:**
```bash
# Check Qdrant status
docker ps | grep qdrant

# Start Qdrant if not running
docker start icap-qdrant

# Check Qdrant logs
docker logs icap-qdrant

# Verify Qdrant health
curl http://localhost:6333/health

# Check connection settings
QDRANT_URL=http://localhost:6333
```

### Qdrant Collection Not Found

**Problem:** `Collection not found` error.

**Solution:**
```python
# Create collection if not exists
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="icap_documents",
    vectors_config={
        "size": 768,  # Adjust based on your embedding model
        "distance": "Cosine"
    }
)
```

### Qdrant Slow Performance

**Problem:** Qdrant queries are slow.

**Solution:**
```bash
# Check Qdrant resources
docker stats icap-qdrant

# Increase Qdrant memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Optimize collection configuration
client.update_collection(
    collection_name="icap_documents",
    optimizer_config={
        "indexing_threshold": 20000
    }
)
```

---

## Ollama LLM Issues

### Ollama Connection Failed

**Problem:** Cannot connect to Ollama LLM service.

**Solution:**
```bash
# Check Ollama status
docker ps | grep ollama

# Start Ollama if not running
docker start icap-ollama

# Check Ollama logs
docker logs icap-ollama

# Verify Ollama health
curl http://localhost:11434/api/tags

# Check connection settings
OLLAMA_URL=http://localhost:11434/api/generate
```

### Ollama Model Not Found

**Problem:** Model not found in Ollama.

**Solution:**
```bash
# Pull the model
docker exec -it icap-ollama ollama pull irm-industrial

# Or if running locally
ollama pull irm-industrial

# List available models
docker exec -it icap-ollama ollama list
```

### Ollama Slow Response

**Problem:** Ollama responses are very slow.

**Solution:**
```bash
# Check GPU availability
docker exec -it icap-ollama ollama run irm-industrial --verbose

# Increase GPU resources in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      gpus: 1

# Use smaller model for faster response
OLLAMA_MODEL=llama2:7b
```

---

## Authentication Issues

### JWT Token Expired

**Problem:** `Token has expired` error.

**Solution:**
```python
# Refresh token using refresh endpoint
import requests

response = requests.post(
    "http://localhost:8000/auth/refresh",
    json={"refresh_token": your_refresh_token}
)

new_token = response.json()["access_token"]
```

### Invalid Credentials

**Problem:** `Invalid username or password` error.

**Solution:**
```bash
# Reset user password (ADMIN only)
# Using Python
from utils.auth import get_password_hash
from database import get_db_connection

hashed_password = get_password_hash("new_password")
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET hashed_password = ? WHERE username = ?",
        (hashed_password, "username")
    )
    conn.commit()
```

### Permission Denied

**Problem:** `Insufficient permissions` error.

**Solution:**
```bash
# Check user role
# Using API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/auth/users/username

# Update user role (ADMIN only)
curl -X PUT -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "ADMIN"}' \
  http://localhost:8000/auth/users/username
```

---

## Performance Issues

### Slow API Response Times

**Problem:** API endpoints responding slowly.

**Solution:**
```bash
# Check system resources
htop  # Linux/Mac
# Windows: Task Manager

# Check database performance
# For PostgreSQL
EXPLAIN ANALYZE SELECT * FROM measurements;

# Enable query logging in database
# Check slow queries

# Check Redis cache hit rate
redis-cli INFO stats | grep keyspace

# Enable profiling
from utils.performance_optimizer import PerformanceOptimizer
optimizer = PerformanceOptimizer()
optimizer.enable_profiling()
```

### High Memory Usage

**Problem:** Application consuming too much memory.

**Solution:**
```python
# Check memory usage
import psutil
process = psutil.Process()
print(process.memory_info().rss / 1024 / 1024)  # MB

# Clear Redis cache
from utils.redis_cache import cache
cache.clear_all()

# Restart services
docker-compose restart icap-api

# Check for memory leaks
# Use memory profiler
pip install memory_profiler
python -m memory_profiler irm_api.py
```

### High CPU Usage

**Problem:** Application consuming too much CPU.

**Solution:**
```bash
# Check CPU usage
top  # Linux/Mac
# Windows: Task Manager

# Check number of workers
# Adjust in uvicorn startup
uvicorn irm_api:app --workers 4

# Profile CPU usage
python -m cProfile -o profile.stats irm_api.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

---

## Vision AI Issues

### Model Loading Failed

**Problem:** YOLO model fails to load.

**Solution:**
```bash
# Check model file exists
ls -la yolo11n.pt

# Download model if missing
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo11n.pt

# Check model permissions
chmod 644 yolo11n.pt

# Verify model integrity
python -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); print(model)"
```

### GPU Not Available for Vision

**Problem:** Vision AI not using GPU.

**Solution:**
```python
# Check CUDA availability
import torch
print(torch.cuda.is_available())

# Set device in vision_engine.py
device = "cuda" if torch.cuda.is_available() else "cpu"

# Install CUDA PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Vision Analysis Too Slow

**Problem:** Vision analysis taking too long.

**Solution:**
```python
# Use TensorRT for inference
# Convert model to TensorRT
from ultralytics import YOLO
model = YOLO("yolo11n.pt")
model.export(format="engine", device=0)

# Reduce image resolution
# In vision_engine.py
image = cv2.resize(image, (640, 640))  # Instead of (1920, 1080)

# Enable batch processing
# Process multiple images at once
```

---

## RAG System Issues

### Document Indexing Failed

**Problem:** Document indexing fails with errors.

**Solution:**
```bash
# Check document file exists
ls -la /path/to/document.pdf

# Check file permissions
chmod 644 /path/to/document.pdf

# Check supported formats
# Supported: .pdf, .docx, .xlsx, .csv, .json, .md, .html, .xml

# Check Qdrant connection
curl http://localhost:6333/health

# Re-index document
curl -X POST http://localhost:8000/rag/index_document \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/document.pdf"}'
```

### RAG Query Returns No Results

**Problem:** RAG queries return empty results.

**Solution:**
```python
# Check collection has documents
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
collection_info = client.get_collection("icap_documents")
print(collection_info.points_count)

# Re-index documents if empty
# Check embedding model is working
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode("test query")
print(len(embeddings))
```

### RAG Slow Performance

**Problem:** RAG queries are slow.

**Solution:**
```bash
# Enable Redis caching
# Check cache is working
from utils.redis_cache import cache
print(cache.is_available)

# Optimize Qdrant collection
client.update_collection(
    collection_name="icap_documents",
    optimizer_config={"indexing_threshold": 10000}
)

# Use smaller embedding model
# In rag_system.py
model = SentenceTransformer('all-MiniLM-L6-v2')  # Smaller than large models
```

---

## Docker Issues

### Docker Build Failed

**Problem:** Docker build fails with errors.

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Check Dockerfile syntax
docker build --no-cache -t icap-v8.10.0 .

# Check base image availability
docker pull nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Check disk space
df -h  # Linux/Mac
# Windows: Check disk space in File Explorer
```

### Docker Container Won't Start

**Problem:** Docker container fails to start.

**Solution:**
```bash
# Check container logs
docker logs icap-api

# Check container status
docker ps -a

# Restart container
docker restart icap-api

# Check resource limits
docker stats icap-api

# Remove and recreate container
docker-compose down
docker-compose up -d
```

### Docker Network Issues

**Problem:** Containers cannot communicate.

**Solution:**
```bash
# Check network
docker network ls
docker network inspect icap-network

# Recreate network
docker network rm icap-network
docker-compose up -d

# Check DNS resolution
docker exec icap-api ping qdrant
docker exec icap-api ping redis
```

---

## Kubernetes Issues

### Pod Won't Start

**Problem:** Kubernetes pod stuck in Pending state.

**Solution:**
```bash
# Check pod status
kubectl get pods -n <namespace>

# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>

# Check resource requests/limits
kubectl describe deployment icap -n <namespace>

# Check node resources
kubectl describe nodes
```

### HPA Not Scaling

**Problem:** Horizontal Pod Autoscaler not scaling pods.

**Solution:**
```bash
# Check HPA status
kubectl get hpa -n <namespace>

# Check HPA metrics
kubectl describe hpa icap -n <namespace>

# Check metrics server
kubectl get apiservice | grep metrics

# Adjust HPA thresholds
kubectl edit hpa icap -n <namespace>
```

### Persistent Volume Issues

**Problem:** Persistent Volume claims not binding.

**Solution:**
```bash
# Check PVC status
kubectl get pvc -n <namespace>

# Check available PVs
kubectl get pv

# Check storage class
kubectl get storageclass

# Create PV if needed
kubectl apply -f pv-config.yaml
```

---

## Network Issues

### Port Already in Use

**Problem:** Port 8000 already in use.

**Solution:**
```bash
# Check what's using the port
lsof -i :8000  # Linux/Mac
# Windows: netstat -ano | findstr :8000

# Kill the process
kill -9 <PID>  # Linux/Mac
# Windows: taskkill /PID <PID> /F

# Or use different port
# In .env
ICAP_PORT=8001
```

### Firewall Blocking Connections

**Problem:** Firewall blocking API connections.

**Solution:**
```bash
# Check firewall status
sudo ufw status  # Linux
# Windows: Check Windows Firewall settings

# Allow port
sudo ufw allow 8000/tcp  # Linux
# Windows: Add rule in Windows Firewall

# Test connection
telnet localhost 8000
curl http://localhost:8000/health
```

### CORS Errors

**Problem:** CORS errors in browser console.

**Solution:**
```python
# Check CORS configuration in irm_api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set specific origins in production
allow_origins=["https://your-domain.com"]
```

---

## Monitoring and Logging

### Enable Debug Logging

**Problem:** Need more detailed logging for debugging.

**Solution:**
```python
# Set log level in .env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.getLogger("ICAP_API").setLevel(logging.DEBUG)

# Enable structured logging
from utils.logging_config import setup_logging
logger = setup_logging("debug")
```

### Check Application Logs

**Problem:** Need to view application logs.

**Solution:**
```bash
# Docker logs
docker logs -f icap-api

# Kubernetes logs
kubectl logs -f <pod-name> -n <namespace>

# Application logs
tail -f logs/icap.log

# Audit logs
tail -f AuditTrail/measurements_log.csv
```

### Monitor Performance Metrics

**Problem:** Need to monitor application performance.

**Solution:**
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics

# Check Grafana dashboard
# Navigate to http://localhost:3000

# Check custom metrics
curl http://localhost:8000/performance/stats
```

---

## Getting Help

If you cannot resolve your issue using this guide:

1. **Check Logs:** Always check application logs first
2. **Verify Configuration:** Ensure all environment variables are set correctly
3. **Test Components:** Test each component individually (database, Redis, Qdrant, Ollama)
4. **Check Resources:** Ensure sufficient system resources (CPU, memory, disk)
5. **Review Documentation:** Check relevant documentation in Docs/ directory
6. **Contact Support:** engineering@icap-enterprise.com

## Emergency Procedures

### Database Recovery
```bash
# Restore from backup
python scripts/restore_enterprise.py --backup backups/icap_backup_20260626.sql
```

### Service Restart
```bash
# Graceful restart
docker-compose restart

# Force restart
docker-compose down
docker-compose up -d
```

### Cache Clear
```python
from utils.redis_cache import cache
cache.clear_all()
```

---

*Last Updated: 2026-06-26*
*Version: 8.10.0 Enterprise*
