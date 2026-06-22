# ICAP Deployment Guide

## Table of Contents
- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Deployment Options

ICAP supports multiple deployment scenarios:

1. **Docker Compose** - Recommended for small to medium deployments
2. **Kubernetes** - For large-scale, production deployments
3. **Manual Deployment** - For development or custom setups

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB
- GPU: Optional (for Vision AI)

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 200+ GB SSD
- GPU: NVIDIA GPU with CUDA support (for Vision AI)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+ (for manual deployment)
- Kubernetes 1.20+ (for K8s deployment)

## Docker Deployment

### Quick Start

1. **Clone repository**
```bash
git clone <repository-url>
cd ColorAIStudio
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with production values
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Verify deployment**
```bash
curl http://localhost:8000/health
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  icap-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: icap-api-prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ICAP_ENVIRONMENT=production
      - ICAP_DATABASE_URL=postgresql://user:pass@postgres:5432/icap
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./AuditTrail:/app/AuditTrail
      - ./RAG:/app/RAG
    depends_on:
      - postgres
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  postgres:
    image: postgres:15-alpine
    container_name: icap-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=icap
      - POSTGRES_USER=icap_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U icap_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: icap-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    container_name: icap-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  nginx:
    image: nginx:alpine
    container_name: icap-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - icap-api

volumes:
  postgres_data:
  qdrant_data:
  ollama_data:
```

### Deploy with Production Config

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Namespace Setup

```bash
kubectl create namespace icap
```

### ConfigMap

Create `configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: icap-config
  namespace: icap
data:
  ICAP_ENVIRONMENT: "production"
  ICAP_RATE_LIMIT: "100"
  QDRANT_URL: "http://qdrant-service:6333"
  OLLAMA_URL: "http://ollama-service:11434"
```

```bash
kubectl apply -f configmap.yaml
```

### Secret

Create `secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: icap-secret
  namespace: icap
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/icap"
  SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/..."
```

```bash
kubectl apply -f secret.yaml
```

### Deployment

Create `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: icap-api
  namespace: icap
spec:
  replicas: 3
  selector:
    matchLabels:
      app: icap-api
  template:
    metadata:
      labels:
        app: icap-api
    spec:
      containers:
      - name: icap-api
        image: icap-api:8.9.3
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: icap-config
        - secretRef:
            name: icap-secret
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: audit-trail
          mountPath: /app/AuditTrail
        - name: rag-storage
          mountPath: /app/RAG
      volumes:
      - name: audit-trail
        persistentVolumeClaim:
          claimName: audit-trail-pvc
      - name: rag-storage
        persistentVolumeClaim:
          claimName: rag-storage-pvc
```

### Service

Create `service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: icap-api-service
  namespace: icap
spec:
  selector:
    app: icap-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Apply Kubernetes Resources

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Production Configuration

### Environment Variables

Critical production variables:

```bash
# Security
ICAP_ENVIRONMENT=production
ICAP_ALLOWED_ORIGINS=https://your-domain.com

# Database
ICAP_DATABASE_URL=postgresql://user:pass@host:5432/icap

# External Services
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://ollama:11434

# Monitoring
ICAP_ENABLE_TRACING=true
PROMETHEUS_ENABLED=true

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=alerts@your-domain.com
```

### Security Best Practices

1. **Use HTTPS** - Configure SSL/TLS certificates
2. **Secrets Management** - Use Kubernetes Secrets or Vault
3. **Network Policies** - Restrict pod-to-pod communication
4. **RBAC** - Implement role-based access control
5. **Regular Updates** - Keep dependencies updated

### Performance Tuning

**Database:**
- Enable connection pooling
- Configure appropriate cache size
- Regular vacuum and analyze

**Qdrant:**
- Configure HNSW parameters
- Set appropriate collection size limits
- Enable persistence

**Application:**
- Adjust worker count based on CPU cores
- Configure appropriate cache sizes
- Enable compression for large responses

## Monitoring and Logging

### Prometheus Metrics

Metrics available at `/metrics`:

- Request count and latency
- Database query performance
- Cache hit rates
- Business KPIs (scrap rate, OEE, etc.)

### Logging

Structured logs with correlation IDs:

```json
{
  "timestamp": "2026-06-20T10:00:00Z",
  "level": "INFO",
  "correlation_id": "abc-123",
  "message": "Request processed",
  "endpoint": "/color/analyze",
  "duration_ms": 150
}
```

### Distributed Tracing

Enable OpenTelemetry tracing:

```bash
ICAP_ENABLE_TRACING=true
JAEGER_HOST=jaeger
JAEGER_PORT=6831
```

### Health Checks

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-06-20T10:00:00Z",
  "services": {
    "database": "connected",
    "qdrant": "connected",
    "ollama": "connected"
  }
}
```

## Backup and Recovery

### Database Backup

**PostgreSQL:**
```bash
docker exec icap-postgres pg_dump -U icap_user icap > backup.sql
```

**SQLite:**
```bash
cp AuditTrail/icap_enterprise.db backup/icap_$(date +%Y%m%d).db
```

### Qdrant Backup

```bash
docker exec icap-qdrant qdrant snapshot create
```

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
docker exec icap-postgres pg_dump -U icap_user icap > $BACKUP_DIR/database.sql

# Qdrant backup
docker exec icap-qdrant qdrant snapshot create
docker cp icap-qdrant:/qdrant/storage $BACKUP_DIR/qdrant

# RAG documents
cp -r RAG $BACKUP_DIR/

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Keep last 7 days
find /backups -name "*.tar.gz" -mtime +7 -delete
```

### Recovery

**Restore Database:**
```bash
docker exec -i icap-postgres psql -U icap_user icap < backup.sql
```

**Restore Qdrant:**
```bash
docker cp qdrant_backup icap-qdrant:/qdrant/storage
docker restart icap-qdrant
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
docker-compose logs icap-api
```

**Database connection failed:**
```bash
docker-compose exec postgres pg_isready
```

**Qdrant not responding:**
```bash
curl http://localhost:6333/health
```

**High memory usage:**
- Check cache sizes in configuration
- Reduce batch processing size
- Monitor with `docker stats`

### Debug Mode

Enable debug logging:
```bash
ICAP_LOG_LEVEL=DEBUG docker-compose up
```

### Health Check Failures

Check individual services:
```bash
curl http://localhost:8000/health
curl http://localhost:6333/health
curl http://localhost:11434/api/tags
```

### Performance Issues

1. Check metrics: `curl http://localhost:8000/metrics`
2. Review logs: `docker-compose logs -f icap-api`
3. Monitor resources: `docker stats`
4. Check cache hit rates in business metrics

## Scaling

### Horizontal Scaling

Increase replicas in Kubernetes:
```bash
kubectl scale deployment icap-api --replicas=5
```

### Vertical Scaling

Update resource limits in deployment:
```yaml
resources:
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### Load Balancing

Use Kubernetes Service with LoadBalancer type or configure Nginx ingress.

## Maintenance

### Regular Tasks

- Daily: Check health endpoints
- Weekly: Review logs and metrics
- Monthly: Update dependencies
- Quarterly: Security audit

### Updates

1. Backup current deployment
2. Pull new image
3. Update deployment
4. Verify health checks
5. Rollback if needed

### Rollback

```bash
docker-compose down
docker-compose up -d --scale icap-api=1
# Or for Kubernetes
kubectl rollout undo deployment icap-api
```
