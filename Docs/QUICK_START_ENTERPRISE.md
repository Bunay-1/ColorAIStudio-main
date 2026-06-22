# Quick Start Guide: ICAP Enterprise Features
============================================

## Overview
This guide helps you quickly get started with ICAP v8.9.5 Enterprise features including authentication, multi-tenancy, audit logging, rate limiting, and data encryption.

## Prerequisites
- ICAP v8.9.5 Enterprise installed
- Python 3.10 or 3.11
- Basic knowledge of REST APIs
- Terminal access

## 5-Minute Quick Start

### Step 1: Configure Environment Variables

Create or update `.env` file:

```bash
# Authentication
ICAP_SECRET_KEY=your-very-secure-secret-key-minimum-32-characters-long
ICAP_ACCESS_TOKEN_EXPIRE=480
ICAP_REFRESH_TOKEN_EXPIRE=10080

# Encryption
ICAP_ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Multi-tenancy
DEFAULT_TENANT_ID=default

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Step 2: Start the Application

```bash
# Start ICAP
python irm_api.py
```

The application will be available at `http://localhost:8000`

### Step 3: Create Admin User

```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@company.com",
    "password": "secure_password",
    "role": "ADMIN",
    "tenant_id": "default"
  }'
```

### Step 4: Login and Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'
```

Save the `access_token` from the response.

### Step 5: Use the API

```bash
# Get current user info
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Analyze color with authentication
curl -X POST http://localhost:8000/color/analyze \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{
    "lab_sample": [50.0, 2.0, 5.0],
    "lab_standard": [50.0, 2.0, 5.0],
    "tolerance": 1.0,
    "batch_id": "batch_001",
    "operator_id": "admin",
    "machine_id": "machine_1",
    "client_id": "client_a",
    "method": "CIE2000",
    "illuminant": "D65",
    "batch_size": 1000
  }'
```

## Authentication

### User Roles

ICAP Enterprise includes 6 predefined roles:

- **ADMIN**: Full access to all features
- **SUPERVISOR**: Can view, analyze, configure, generate reports, control IoT
- **OPERATOR**: Can view and analyze
- **QUALITY_CONTROL**: Can view, analyze, generate reports
- **MAINTENANCE**: Can view and control IoT
- **VIEWER**: Read-only access

### Creating Users

```bash
# Create operator user
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator1",
    "email": "operator1@company.com",
    "password": "operator_password",
    "role": "OPERATOR",
    "tenant_id": "default"
  }'
```

### Token Management

```bash
# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'

# Logout (blacklist token)
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Multi-Tenancy

### Create Tenant

```bash
curl -X POST http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_a",
    "name": "Company A",
    "config": {
      "max_users": 50,
      "storage_quota_gb": 100
    }
  }'
```

### Create User in Tenant

```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user_a",
    "email": "user@company_a.com",
    "password": "password",
    "role": "OPERATOR",
    "tenant_id": "company_a"
  }'
```

### Use Tenant Context

```bash
curl -X POST http://localhost:8000/color/analyze \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: company_a" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Audit Logging

### Query Audit Logs

```bash
# Get recent logs
curl -X GET "http://localhost:8000/auth/audit/logs?limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Filter by user
curl -X GET "http://localhost:8000/auth/audit/logs?user_id=admin&limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Filter by action
curl -X GET "http://localhost:8000/auth/audit/logs?action=login&limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get User Activity Summary

```bash
curl -X GET http://localhost:8000/auth/audit/summary/admin \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get Audit Statistics

```bash
curl -X GET http://localhost:8000/auth/audit/stats \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Rate Limiting

### Default Rate Limits

- **Light operations**: 60 requests/minute
- **Heavy operations**: 20 requests/minute
- **Authentication**: 20 requests/minute

### Role-Based Multipliers

- **ADMIN**: 3x multiplier
- **SUPERVISOR**: 2x multiplier
- **OPERATOR**: 1x multiplier
- **VIEWER**: 0.5x multiplier

### Check Rate Limit Status

```bash
curl -X GET http://localhost:8000/auth/rate-limit-status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-User-ID: admin"
```

### Handling Rate Limit Errors

When you receive a 429 status code:

```python
import time
import requests

def make_request_with_retry(url, headers, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 429:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
        else:
            return response
    return response
```

## Data Encryption

### Encrypt Sensitive Data

```python
from utils.encryption import encrypt_value, decrypt_value

# Encrypt
encrypted = encrypt_value("sensitive_data")

# Decrypt
decrypted = decrypt_value(encrypted)
```

### Encrypt Configuration Values

```python
from utils.encryption import encrypt_config_value, decrypt_config_value

# Encrypt config
encrypted_config = encrypt_config_value("database_password")

# Decrypt config
password = decrypt_config_value(encrypted_config)
```

## Python Client Example

```python
import httpx

class ICAPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    async def login(self, username, password):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return data
    
    async def get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def analyze_color(self, lab_sample, lab_standard, tenant_id="default"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/color/analyze",
                headers=await self.get_headers(),
                headers_extra={"X-Tenant-ID": tenant_id},
                json={
                    "lab_sample": lab_sample,
                    "lab_standard": lab_standard,
                    "tolerance": 1.0,
                    "batch_id": "batch_001",
                    "operator_id": "admin",
                    "machine_id": "machine_1",
                    "client_id": "client_a",
                    "method": "CIE2000",
                    "illuminant": "D65",
                    "batch_size": 1000
                }
            )
            return response.json()

# Usage
client = ICAPClient()
await client.login("admin", "secure_password")
result = await client.analyze_color([50.0, 2.0, 5.0], [50.0, 2.0, 5.0])
```

## Common Use Cases

### Use Case 1: Single Organization

For single organization deployments:

1. Use default tenant
2. Create users with appropriate roles
3. Enable audit logging for compliance
4. Configure rate limits based on usage

### Use Case 2: Multi-Tenant SaaS

For multi-tenant SaaS deployments:

1. Create tenant for each customer
2. Assign users to respective tenants
3. Configure tenant-specific quotas
4. Monitor tenant resource usage

### Use Case 3: High-Security Environment

For high-security environments:

1. Enable SSL/TLS
2. Use strong encryption keys
3. Enable comprehensive audit logging
4. Implement strict rate limiting
5. Regular security audits

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Postman Collection

Import the Postman collection for easy API testing:

```bash
# Import postman/ICAP_Enterprise_Collection.json into Postman
# Update environment variables:
# - base_url: http://localhost:8000
# - access_token: (obtained from login)
# - tenant_id: default
```

## Troubleshooting

### Issue: 401 Unauthorized
**Solution**: Check that your access token is valid and not expired. Refresh token if needed.

### Issue: 403 Forbidden
**Solution**: Verify your user role has the required permissions for the endpoint.

### Issue: 429 Too Many Requests
**Solution**: You've hit the rate limit. Wait before retrying or request higher limits.

### Issue: Tenant Not Found
**Solution**: Verify the tenant ID exists and is active. Check tenant_id header value.

### Issue: Encryption Key Error
**Solution**: Ensure ICAP_ENCRYPTION_KEY is set and is exactly 32 bytes long.

## Next Steps

- Read [Enterprise Security Guide](ENTERPRISE_SECURITY.md)
- Read [Multi-Tenancy Setup Guide](MULTI_TENANCY_SETUP.md)
- Read [Performance Tuning Guide](PERFORMANCE_TUNING.md)
- Review [API Examples](API_EXAMPLES.md)
- Set up [Monitoring and Alerting](MONITORING_ALERTING.md)

## Support

- **Documentation**: See Docs/ directory
- **API Examples**: Docs/API_EXAMPLES.md
- **Postman Collection**: postman/ICAP_Enterprise_Collection.json
- **Email**: support@icap-enterprise.com

---

*Last Updated: 2026-06-20*
*Version: 8.9.5 Enterprise*
