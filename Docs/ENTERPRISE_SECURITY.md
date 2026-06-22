# Enterprise Security Documentation
===================================

## Overview
ICAP v8.9.5 Enterprise includes comprehensive security features designed for production deployments in regulated industrial environments.

## Authentication & Authorization

### JWT Authentication
- **Access Tokens:** Short-lived tokens (default 8 hours) for API access
- **Refresh Tokens:** Long-lived tokens (default 7 days) for session renewal
- **Token Blacklist:** Secure logout mechanism with token revocation
- **Configuration:**
  ```env
  ICAP_SECRET_KEY=your-secret-key-here
  ICAP_ACCESS_TOKEN_EXPIRE=480
  ICAP_REFRESH_TOKEN_EXPIRE=7
  ```

### Role-Based Access Control (RBAC)
ICAP provides 6 predefined roles with specific permissions:

| Role | Permissions |
|------|-------------|
| **ADMIN** | view, analyze, configure, train, delete, report, iot_control, user_management |
| **SUPERVISOR** | view, analyze, configure, report, iot_control |
| **OPERATOR** | view, analyze |
| **QUALITY_CONTROL** | view, analyze, report |
| **MAINTENANCE** | view, iot_control |
| **VIEWER** | view |

### Authentication Endpoints
- `POST /auth/login` - User authentication
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Secure logout with token blacklisting
- `GET /auth/users` - List all users (ADMIN only)
- `POST /auth/users` - Create new user (ADMIN only)
- `PUT /auth/users/{username}` - Update user (ADMIN only)
- `DELETE /auth/users/{username}` - Delete user (ADMIN only)
- `GET /auth/roles` - List available roles

## Multi-Tenancy

### Tenant Isolation
- **Database Isolation:** All data queries include tenant_id filtering
- **Context Management:** Automatic tenant context extraction from headers
- **Tenant Management:** CRUD operations for tenant configuration

### Tenant Endpoints
- `GET /auth/tenants` - List all tenants (ADMIN only)
- `POST /auth/tenants` - Create new tenant (ADMIN only)
- `PUT /auth/tenants/{tenant_id}` - Update tenant (ADMIN only)
- `DELETE /auth/tenants/{tenant_id}` - Delete tenant (ADMIN only)
- `GET /auth/tenants/{tenant_id}/stats` - Tenant statistics

### Tenant Headers
Include tenant information in API requests:
```http
X-Tenant-ID: your-tenant-id
```

## Data Encryption

### Encryption at Rest
- **Algorithm:** AES-256 (CBC mode)
- **Key Management:** Environment variable based
- **Configuration:**
  ```env
  ICAP_ENCRYPTION_KEY=your-32-byte-encryption-key
  ```

### Encryption Utilities
- **Database Values:** Encrypt sensitive fields before storage
- **Configuration Files:** Encrypt sensitive configuration values
- **File Encryption:** Encrypt uploaded files containing sensitive data
- **Environment Variables:** Encrypt secrets in environment files

### Usage Example
```python
from utils.encryption import EncryptionManager

# Encrypt sensitive data
encrypted = EncryptionManager.encrypt("sensitive_password")

# Decrypt data
decrypted = EncryptionManager.decrypt(encrypted)
```

## Secure Communication

### SSL/TLS Configuration
- **Protocol:** TLS 1.2/1.3
- **HTTP Version:** HTTP/2
- **Security Headers:** HSTS, X-Frame-Options, X-Content-Type-Options

### Nginx Configuration
The nginx configuration includes:
- SSL certificate management
- HTTP to HTTPS redirect
- Security headers
- Rate limiting
- Proxy settings for API endpoints

### Certificate Generation
Use the provided script for development/testing:
```bash
./scripts/generate_ssl_certs.sh
```

## Audit Logging

### Audit Trail
ICAP maintains comprehensive audit logs for:
- User authentication events (login, logout, failed attempts)
- User management operations (create, update, delete)
- Tenant management operations
- Data access and modification
- Security events
- System events

### Audit Endpoints
- `GET /auth/audit/logs` - Query audit logs
- `GET /auth/audit/summary/{user_id}` - User activity summary
- `GET /auth/audit/stats` - Audit statistics

### Audit Log Format
```json
{
  "timestamp": "2026-06-20T10:30:00Z",
  "action": "login",
  "user_id": "john.doe",
  "user_role": "OPERATOR",
  "tenant_id": "default",
  "severity": "info",
  "ip_address": "192.168.1.100",
  "correlation_id": "abc-123-def"
}
```

## Rate Limiting

### Rate Limiting Strategy
- **Global Limit:** 100 requests/minute
- **Per-User Limit:** 50 requests/minute (role-based multipliers)
- **Per-Tenant Limit:** 200 requests/minute
- **Auth Endpoints:** 10 requests/minute
- **Heavy Operations:** 20 requests/minute
- **Light Operations:** 100 requests/minute

### Role-Based Multipliers
- **ADMIN:** 2.0x limit
- **SUPERVISOR:** 1.5x limit
- **OPERATOR:** 1.0x limit
- **VIEWER:** 0.5x limit

### Rate Limit Headers
API responses include rate limit information:
```http
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1624234567
```

## Session Management

### Session Configuration
- **Session Timeout:** 8 hours (configurable)
- **Max Concurrent Sessions:** 10 per user
- **Max Concurrent Operations:** 5 per user

### Session Endpoints
- `GET /auth/sessions` - List active sessions
- `DELETE /auth/sessions/{session_id}` - Terminate session
- `DELETE /auth/sessions/user/{user_id}` - Terminate all user sessions
- `GET /auth/sessions/stats` - Session statistics

## Horizontal Scaling

### Kubernetes Deployment
ICAP supports horizontal scaling with:
- **Replicas:** 3 initial replicas
- **HPA:** Horizontal Pod Autoscaler (3-10 replicas)
- **Scaling Metrics:** CPU (70%), Memory (80%)
- **Pod Anti-Affinity:** Distribute across nodes
- **Session Affinity:** Client IP based

### Deployment Configuration
```yaml
# k8s/icap-deployment.yaml
replicas: 3
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
```

## Performance Monitoring

### System Health Monitoring
- **CPU Usage:** Real-time monitoring
- **Memory Usage:** Memory utilization tracking
- **Disk Usage:** Storage capacity monitoring
- **Network:** Network I/O statistics

### Performance Optimization
- **Caching:** In-memory cache with TTL support
- **Query Optimization:** Database query analysis
- **Connection Pooling:** Database connection management
- **Async Operations:** Async/await for I/O operations

### Performance Endpoints
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics
- `GET /performance/stats` - Performance statistics

## Security Best Practices

### Production Deployment
1. **Environment Variables:** Never commit secrets to version control
2. **SSL/TLS:** Always use HTTPS in production
3. **Firewall:** Restrict access to necessary ports only
4. **Updates:** Regular security updates and patches
5. **Backups:** Regular encrypted backups
6. **Monitoring:** Continuous security monitoring
7. **Audit Logs:** Regular review of audit logs
8. **Access Control:** Principle of least privilege

### Key Rotation
- **Secret Keys:** Rotate every 90 days
- **Encryption Keys:** Rotate annually
- **Certificates:** Rotate before expiration
- **API Keys:** Rotate compromised keys immediately

### Incident Response
1. **Detection:** Monitor security alerts
2. **Containment:** Isolate affected systems
3. **Investigation:** Analyze audit logs
4. **Remediation:** Apply security patches
5. **Recovery:** Restore from backups if needed
6. **Post-Mortem:** Document and learn from incidents

## Compliance

### ISO 9001 Support
- **Audit Trail:** Complete traceability of all operations
- **Document Control:** Version-controlled documentation
- **Process Monitoring:** Real-time process tracking
- **Quality Records:** Comprehensive quality data storage

### GDPR Considerations
- **Data Minimization:** Collect only necessary data
- **Data Encryption:** Encrypt sensitive personal data
- **Access Control:** Role-based access to personal data
- **Audit Logging:** Track access to personal data
- **Data Retention:** Implement data retention policies

## Troubleshooting

### Authentication Issues
```bash
# Check token validity
curl -X GET http://localhost:8000/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check user permissions
curl -X GET http://localhost:8000/auth/users/USERNAME \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Rate Limiting Issues
```bash
# Check rate limit status
curl -X GET http://localhost:8000/auth/rate-limit-status \
  -H "X-User-ID: USERNAME"
```

### Tenant Issues
```bash
# Check tenant status
curl -X GET http://localhost:8000/auth/tenants/TENANT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Support
For security-related issues, contact:
- **Security Team:** security@icap-enterprise.com
- **Emergency:** +1-555-SECURITY
- **Documentation:** See [Security Documentation](Docs/ENTERPRISE_SECURITY.md)
