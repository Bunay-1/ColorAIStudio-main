# Migration Guide: v8.9.1 to v8.9.5 Enterprise
============================================

## Overview
This guide provides step-by-step instructions for migrating from ICAP v8.9.1 to ICAP v8.9.5 Enterprise. The Enterprise version introduces significant new features including multi-tenancy, enhanced authentication, audit logging, advanced rate limiting, data encryption, and horizontal scaling capabilities.

## Migration Timeline
- **Estimated Time:** 2-4 hours for small deployments, 1-2 days for enterprise deployments
- **Downtime Required:** Yes (database migration and configuration changes)
- **Rollback Possible:** Yes (with database backup)

## Prerequisites

### System Requirements
- Python 3.10 or 3.11
- PostgreSQL 12+ (recommended) or SQLite 3.35+
- 4GB RAM minimum (8GB recommended for Enterprise)
- 20GB disk space minimum
- Kubernetes cluster (for horizontal scaling)
- SSL/TLS certificates

### Backup Requirements
- Full database backup
- Configuration file backup
- RAG index backup (if using RAG)
- Custom scripts and modifications backup

## Pre-Migration Checklist

- [ ] Review new features and breaking changes
- [ ] Create full system backup
- [ ] Document current configuration
- [ ] Review security requirements
- [ ] Plan tenant structure (if using multi-tenancy)
- [ ] Review user roles and permissions
- [ ] Test migration in staging environment
- [ ] Schedule maintenance window
- [ ] Notify users of planned downtime

## Breaking Changes

### 1. Authentication System
**Change:** JWT-based authentication is now required for all API endpoints.

**Impact:** All API calls must include valid JWT tokens.

**Migration Steps:**
```bash
# 1. Set environment variables
export ICAP_SECRET_KEY="your-secret-key-min-32-chars"
export ICAP_ACCESS_TOKEN_EXPIRE="480"
export ICAP_REFRESH_TOKEN_EXPIRE="10080"

# 2. Create initial admin user
# Use the /auth/users endpoint or direct database insertion
```

### 2. Database Schema
**Change:** New columns added to support multi-tenancy and audit logging.

**Impact:** Database migration required.

**Migration Steps:**
```sql
-- Add tenant_id columns
ALTER TABLE measurements ADD COLUMN tenant_id VARCHAR(100) DEFAULT 'default';
ALTER TABLE clients ADD COLUMN tenant_id VARCHAR(100) DEFAULT 'default';

-- Add audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100),
    user_id VARCHAR(100),
    user_role VARCHAR(50),
    tenant_id VARCHAR(100),
    severity VARCHAR(20),
    ip_address VARCHAR(50),
    correlation_id VARCHAR(100),
    details TEXT
);

-- Add tenant management table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    config TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Configuration Changes
**Change:** New environment variables required.

**Impact:** Update .env file or environment configuration.

**New Required Variables:**
```bash
# Authentication
ICAP_SECRET_KEY=your-secret-key-minimum-32-characters
ICAP_ACCESS_TOKEN_EXPIRE=480
ICAP_REFRESH_TOKEN_EXPIRE=10080

# Encryption
ICAP_ENCRYPTION_KEY=your-32-byte-encryption-key

# Multi-tenancy
DEFAULT_TENANT_ID=default

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

## Migration Steps

### Step 1: Backup Current System

```bash
# Backup database
cp icap.db icap.db.backup

# Backup configuration
cp .env .env.backup

# Backup RAG index (if applicable)
cp -r RAG/ RAG.backup/

# Backup custom scripts
cp -r scripts/ scripts.backup/
```

### Step 2: Update Dependencies

```bash
# Install new dependencies
pip install slowapi
pip install email-validator
pip install cryptography
pip install pydantic[email]

# Update existing packages
pip install --upgrade fastapi uvicorn httpx
pip install --upgrade numpy colour
```

### Step 3: Update Configuration

Update your `.env` file with new variables:

```bash
# Existing variables (keep as is)
DATABASE_URL=sqlite:///icap.db
OLLAMA_SERVER_URL=http://localhost:11434
MODEL_NAME=irm-industrial
TIMEOUT=60

# New authentication variables
ICAP_SECRET_KEY=your-very-secure-secret-key-minimum-32-characters-long
ICAP_ACCESS_TOKEN_EXPIRE=480
ICAP_REFRESH_TOKEN_EXPIRE=10080

# New encryption variable
ICAP_ENCRYPTION_KEY=your-32-byte-encryption-key-here

# New multi-tenancy variables
DEFAULT_TENANT_ID=default

# New rate limiting variables
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_HEAVY_OPS_PER_MINUTE=20
```

### Step 4: Database Migration

Run the database migration script:

```bash
# Using Python migration script
python scripts/migrate_database.py
```

Or manually execute SQL statements (see Breaking Changes section).

### Step 5: Initialize Enterprise Features

```python
# Run initialization script
python scripts/initialize_enterprise.py
```

This will:
- Create default tenant
- Create admin user
- Initialize audit logging
- Configure rate limiting
- Set up encryption keys

### Step 6: Update Application Code

If you have custom code that calls ICAP APIs, update to include authentication:

```python
# Old way (no authentication)
response = requests.post("http://localhost:8000/color/analyze", json=data)

# New way (with authentication)
# First, get token
auth_response = requests.post("http://localhost:8000/auth/login", 
                             json={"username": "admin", "password": "password"})
token = auth_response.json()["access_token"]

# Then use token in requests
response = requests.post("http://localhost:8000/color/analyze",
                        json=data,
                        headers={"Authorization": f"Bearer {token}"})
```

### Step 7: Update Client Applications

Update any client applications to:
1. Implement JWT token handling
2. Add token refresh logic
3. Include tenant context headers
4. Handle 401/403 errors appropriately

### Step 8: Test Migration

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests
pytest tests/test_integration_*.py -v

# Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Test API with authentication
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  | jq -r '.access_token')

curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Step 9: Deploy to Production

```bash
# Stop current service
systemctl stop icap

# Deploy new version
git pull origin main
pip install -r requirements.txt

# Start service
systemctl start icap

# Verify
curl http://localhost:8000/health
```

## Post-Migration Tasks

### 1. Configure Multi-Tenancy (if applicable)

```bash
# Create additional tenants
curl -X POST http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_a",
    "name": "Company A",
    "config": {"max_users": 50}
  }'

# Assign users to tenants
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user_a",
    "email": "user@company.com",
    "password": "password",
    "role": "OPERATOR",
    "tenant_id": "company_a"
  }'
```

### 2. Configure Rate Limiting

Review and adjust rate limits based on your usage patterns:

```python
# In utils/rate_limiter.py, customize limits
ROLE_LIMITS = {
    "ADMIN": 3.0,      # 3x multiplier
    "SUPERVISOR": 2.0, # 2x multiplier
    "OPERATOR": 1.0,   # 1x multiplier
    "VIEWER": 0.5      # 0.5x multiplier
}

OPERATION_LIMITS = {
    "light": 200,      # requests per minute
    "heavy": 30,       # requests per minute
    "auth": 20         # requests per minute
}
```

### 3. Set Up Audit Logging

Configure audit log retention and monitoring:

```bash
# Review audit logs
curl -X GET "http://localhost:8000/auth/audit/logs?limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Set up log aggregation (see MONITORING_ALERTING.md)
```

### 4. Configure SSL/TLS

Generate and configure SSL certificates:

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt for production
certbot certonly --standalone -d your-domain.com

# Update nginx configuration
cp nginx/nginx.conf /etc/nginx/sites-available/icap
systemctl reload nginx
```

### 5. Set Up Monitoring

Configure Prometheus and Grafana (see MONITORING_ALERTING.md):

```bash
# Deploy Prometheus
kubectl apply -f k8s/prometheus-config.yaml

# Deploy Grafana
kubectl apply -f k8s/grafana-config.yaml
```

## Rollback Procedure

If migration fails, follow these steps to rollback:

```bash
# Stop service
systemctl stop icap

# Restore database
cp icap.db.backup icap.db

# Restore configuration
cp .env.backup .env

# Restore code
git checkout v8.9.1

# Restart service
systemctl start icap
```

## Troubleshooting

### Issue: Authentication Fails
**Solution:** Verify ICAP_SECRET_KEY is set and at least 32 characters long.

### Issue: Database Migration Fails
**Solution:** Check database permissions and ensure no active connections during migration.

### Issue: Rate Limiting Too Aggressive
**Solution:** Adjust RATE_LIMIT_PER_MINUTE in configuration or customize role multipliers.

### Issue: Multi-Tenancy Not Working
**Solution:** Verify DEFAULT_TENANT_ID is set and tenant middleware is properly configured.

### Issue: SSL/TLS Errors
**Solution:** Verify certificate paths in nginx configuration and certificate validity.

## Support Resources

- **Documentation:** See Docs/ directory for detailed guides
- **API Documentation:** http://your-server:8000/docs
- **Examples:** See Docs/API_EXAMPLES.md
- **Postman Collection:** See postman/ICAP_Enterprise_Collection.json

## Migration Checklist

- [ ] Backup completed
- [ ] Dependencies installed
- [ ] Configuration updated
- [ ] Database migrated
- [ ] Enterprise features initialized
- [ ] Application code updated
- [ ] Client applications updated
- [ ] Testing completed
- [ ] Production deployment completed
- [ ] Multi-tenancy configured (if applicable)
- [ ] Rate limiting configured
- [ ] Audit logging verified
- [ ] SSL/TLS configured
- [ ] Monitoring set up
- [ ] Users notified
- [ ] Documentation updated

## Additional Resources

- [Enterprise Security Guide](ENTERPRISE_SECURITY.md)
- [Multi-Tenancy Setup Guide](MULTI_TENANCY_SETUP.md)
- [Performance Tuning Guide](PERFORMANCE_TUNING.md)
- [Monitoring and Alerting](MONITORING_ALERTING.md)
- [Disaster Recovery](DISASTER_RECOVERY.md)

## Contact Support

For migration assistance:
- **Email:** support@icap-enterprise.com
- **Documentation:** https://docs.icap-enterprise.com
- **Community:** https://community.icap-enterprise.com

---

*Last Updated: 2026-06-20*
*Version: 8.9.5 Enterprise*
