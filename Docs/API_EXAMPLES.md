# API Examples for Enterprise Features
=====================================

## Authentication Examples

### User Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Get Current User
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "username": "john_doe",
  "email": "john@company.com",
  "role": "OPERATOR",
  "tenant_id": "company_a",
  "is_active": true,
  "created_at": "2026-06-20T10:30:00Z"
}
```

### Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## User Management Examples

### Create User
```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "email": "jane@company.com",
    "password": "secure_password",
    "role": "OPERATOR",
    "tenant_id": "company_a"
  }'
```

**Response:**
```json
{
  "username": "jane_smith",
  "email": "jane@company.com",
  "role": "OPERATOR",
  "tenant_id": "company_a",
  "is_active": true,
  "created_at": "2026-06-20T10:35:00Z"
}
```

### List All Users
```bash
curl -X GET http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "john_doe": {
    "username": "john_doe",
    "email": "john@company.com",
    "role": "SUPERVISOR",
    "tenant_id": "company_a",
    "is_active": true
  },
  "jane_smith": {
    "username": "jane_smith",
    "email": "jane@company.com",
    "role": "OPERATOR",
    "tenant_id": "company_a",
    "is_active": true
  }
}
```

### Update User Role
```bash
curl -X PUT http://localhost:8000/auth/users/jane_smith/role \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_role": "SUPERVISOR"
  }'
```

### Delete User
```bash
curl -X DELETE http://localhost:8000/auth/users/jane_smith \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Tenant Management Examples

### Create Tenant
```bash
curl -X POST http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_b",
    "name": "Company B",
    "config": {
      "max_users": 50,
      "storage_quota_gb": 100
    }
  }'
```

**Response:**
```json
{
  "tenant_id": "company_b",
  "name": "Company B",
  "is_active": true,
  "config": {
    "max_users": 50,
    "storage_quota_gb": 100
  },
  "created_at": "2026-06-20T10:40:00Z"
}
```

### List All Tenants
```bash
curl -X GET http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "default": {
    "tenant_id": "default",
    "name": "Default Tenant",
    "is_active": true,
    "config": {}
  },
  "company_a": {
    "tenant_id": "company_a",
    "name": "Company A",
    "is_active": true,
    "config": {
      "max_users": 50,
      "storage_quota_gb": 100
    }
  }
}
```

### Get Tenant Statistics
```bash
curl -X GET http://localhost:8000/auth/tenants/company_a/stats \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "tenant_id": "company_a",
  "name": "Company A",
  "user_count": 25,
  "api_calls": 15000,
  "storage_used_gb": 45.2,
  "is_active": true
}
```

### Activate Tenant
```bash
curl -X POST http://localhost:8000/auth/tenants/company_b/activate \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Deactivate Tenant
```bash
curl -X POST http://localhost:8000/auth/tenants/company_b/deactivate \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Delete Tenant
```bash
curl -X DELETE http://localhost:8000/auth/tenants/company_b \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Color Analysis with Authentication

### Analyze Color with Tenant Context
```bash
curl -X POST http://localhost:8000/color/analyze \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: company_a" \
  -H "Content-Type: application/json" \
  -d '{
    "lab_sample": [50.0, 2.0, 5.0],
    "lab_standard": [50.0, 2.0, 5.0],
    "tolerance": 1.0,
    "batch_id": "batch_123",
    "operator_id": "john_doe",
    "machine_id": "machine_1",
    "client_id": "client_a",
    "method": "CIE2000",
    "illuminant": "D65",
    "batch_size": 1000
  }'
```

**Response:**
```json
{
  "delta_e": 0.5,
  "status": "Pass",
  "method": "CIE2000",
  "illuminant": "D65",
  "timestamp": "2026-06-20T10:45:00Z",
  "batch_id": "batch_123"
}
```

## Vision Analysis with Authentication

### Analyze Vision with Rate Limiting
```bash
curl -X POST http://localhost:8000/vision/analyze \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: company_a" \
  -F "file=@surface_image.jpg" \
  -F "generate_map=true"
```

**Response:**
```json
{
  "defects": [
    {
      "class": "scratch",
      "confidence": 0.92,
      "bbox": [100, 150, 200, 250]
    }
  ],
  "defect_map": "base64_encoded_image_data",
  "timestamp": "2026-06-20T10:50:00Z"
}
```

## RAG Query with Authentication

### Diagnose with RAG
```bash
curl -X POST http://localhost:8000/rag/diagnose \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: company_a" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What causes color variations in batch processing?",
    "use_rag": true,
    "temperature": 0.7
  }'
```

**Response:**
```json
{
  "analysis": "Color variations in batch processing are typically caused by...",
  "sources": [
    {
      "document": "Color_Processing_Guide.pdf",
      "page": 15,
      "relevance": 0.92
    }
  ],
  "timestamp": 1.234,
  "model": "irm-industrial"
}
```

## Rate Limiting Examples

### Check Rate Limit Status
```bash
curl -X GET http://localhost:8000/auth/rate-limit-status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-User-ID: john_doe"
```

**Response:**
```json
{
  "limit": 50,
  "used": 15,
  "remaining": 35,
  "reset": 1624234567
}
```

## Audit Log Examples

### Query Audit Logs
```bash
curl -X GET "http://localhost:8000/auth/audit/logs?user_id=john_doe&limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2026-06-20T10:30:00Z",
      "action": "login",
      "user_id": "john_doe",
      "user_role": "OPERATOR",
      "tenant_id": "company_a",
      "severity": "info",
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 15
}
```

### Get User Activity Summary
```bash
curl -X GET http://localhost:8000/auth/audit/summary/john_doe \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "user_id": "john_doe",
  "total_actions": 150,
  "actions_by_type": {
    "login": 5,
    "data_access": 100,
    "data_modify": 45
  },
  "last_activity": "2026-06-20T10:55:00Z"
}
```

## Error Handling Examples

### Authentication Error
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "invalid_user",
    "password": "wrong_password"
  }'
```

**Response (401):**
```json
{
  "detail": "Incorrect username or password"
}
```

### Permission Error
```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_OPERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "new@company.com",
    "password": "password",
    "role": "OPERATOR"
  }'
```

**Response (403):**
```json
{
  "detail": "Insufficient permissions for user_management"
}
```

### Rate Limit Error
```bash
# Make too many requests
for i in {1..60}; do
  curl -X GET http://localhost:8000/color/analyze \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
done
```

**Response (429):**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## Python Client Examples

### Authentication Client
```python
import httpx

class ICAPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    async def login(self, username: str, password: str):
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
    
    async def analyze_color(self, lab_sample: list, lab_standard: list):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/color/analyze",
                headers=await self.get_headers(),
                json={
                    "lab_sample": lab_sample,
                    "lab_standard": lab_standard,
                    "tolerance": 1.0,
                    "batch_id": "batch_123"
                }
            )
            return response.json()

# Usage
client = ICAPClient()
await client.login("john_doe", "secure_password")
result = await client.analyze_color([50.0, 2.0, 5.0], [50.0, 2.0, 5.0])
```

### Tenant Management Client
```python
class TenantManager:
    def __init__(self, client: ICAPClient):
        self.client = client
    
    async def create_tenant(self, tenant_id: str, name: str, config: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.client.base_url}/auth/tenants",
                headers=await self.client.get_headers(),
                json={
                    "tenant_id": tenant_id,
                    "name": name,
                    "config": config or {}
                }
            )
            return response.json()
    
    async def get_tenant_stats(self, tenant_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.client.base_url}/auth/tenants/{tenant_id}/stats",
                headers=await self.client.get_headers()
            )
            return response.json()

# Usage
client = ICAPClient()
await client.login("admin", "admin_password")
tenant_mgr = TenantManager(client)
await tenant_mgr.create_tenant("company_c", "Company C", {"max_users": 100})
stats = await tenant_mgr.get_tenant_stats("company_c")
```

## JavaScript Client Examples

### Authentication with Fetch
```javascript
class ICAPClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.accessToken = null;
        this.refreshToken = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        this.accessToken = data.access_token;
        this.refreshToken = data.refresh_token;
        return data;
    }

    getHeaders() {
        return {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
        };
    }

    async analyzeColor(labSample, labStandard) {
        const response = await fetch(`${this.baseUrl}/color/analyze`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                lab_sample: labSample,
                lab_standard: labStandard,
                tolerance: 1.0,
                batch_id: 'batch_123'
            })
        });
        return await response.json();
    }
}

// Usage
const client = new ICAPClient();
await client.login('john_doe', 'secure_password');
const result = await client.analyzeColor([50.0, 2.0, 5.0], [50.0, 2.0, 5.0]);
```

## Multi-Tenancy Examples

### Tenant-Specific Request
```bash
curl -X GET http://localhost:8000/measurements \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-ID: company_a"
```

### Cross-Tenant Access (Admin Only)
```bash
# Admin can access any tenant
curl -X GET http://localhost:8000/measurements \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "X-Tenant-ID: company_b"
```

## Testing Examples

### Test Authentication Flow
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin_password"}' \
  | jq -r '.access_token')

# 2. Use token for authenticated request
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### Test Rate Limiting
```bash
# Make requests until rate limit is hit
for i in {1..60}; do
  RESPONSE=$(curl -s -w "\n%{http_code}" -X GET http://localhost:8000/color/analyze \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN")
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  
  if [ "$HTTP_CODE" = "429" ]; then
    echo "Rate limit hit at request $i"
    break
  fi
done
```

## Notifications API Examples

### Create Notification
```bash
curl -X POST http://localhost:8000/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Alert: Color Deviation",
    "message": "Color deviation detected in batch 001",
    "channel": "websocket",
    "priority": "high",
    "metadata": {
      "batch_id": "batch_001",
      "deviation": 2.5
    }
  }'
```

### List Notifications
```bash
curl -X GET "http://localhost:8000/notifications?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Create Alert
```bash
curl -X POST http://localhost:8000/notifications/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Color Deviation Alert",
    "condition": "delta_e > 2.0",
    "action": "send_notification",
    "enabled": true
  }'
```

## Analytics API Examples

### Get Metrics
```bash
curl -X GET "http://localhost:8000/analytics/metrics/color_analysis?period=24h" \
  -H "Authorization: Bearer $TOKEN"
```

### Generate Report
```bash
curl -X POST http://localhost:8000/analytics/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "color_analysis",
    "params": {
      "period": "7d",
      "format": "pdf"
    }
  }'
```

## Webhooks API Examples

### Create Webhook
```bash
curl -X POST http://localhost:8000/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-webhook-url.com/endpoint",
    "events": ["user.created", "alert.triggered"],
    "secret": "your-webhook-secret",
    "enabled": true
  }'
```

### List Webhooks
```bash
curl -X GET http://localhost:8000/webhooks \
  -H "Authorization: Bearer $TOKEN"
```

### Trigger Webhook Event
```bash
curl -X POST http://localhost:8000/webhooks/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "alert.triggered",
    "payload": {
      "alert_id": "alert_001",
      "severity": "high"
    }
  }'
```

## Compliance API Examples

### Generate Compliance Report
```bash
curl -X POST http://localhost:8000/compliance/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "standard": "GDPR",
    "title": "GDPR Compliance Report",
    "description": "Monthly GDPR compliance check",
    "period_start": "2026-06-01T00:00:00Z",
    "period_end": "2026-06-30T23:59:59Z"
  }'
```

### List Compliance Reports
```bash
curl -X GET http://localhost:8000/compliance/reports \
  -H "Authorization: Bearer $TOKEN"
```

## MFA API Examples

### Setup MFA
```bash
curl -X POST http://localhost:8000/mfa/setup \
  -H "Authorization: Bearer $TOKEN"
```

### Enable MFA
```bash
curl -X POST http://localhost:8000/mfa/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "JBSWY3DPEHPK3PXP",
    "verification_code": "123456"
  }'
```

### Verify MFA Code
```bash
curl -X POST http://localhost:8000/mfa/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "123456",
    "method": "totp"
  }'
```

## Cache API Examples

### Get Cache Statistics
```bash
curl -X GET http://localhost:8000/cache/statistics \
  -H "Authorization: Bearer $TOKEN"
```

### Clear Cache
```bash
curl -X POST "http://localhost:8000/cache/clear?level=memory" \
  -H "Authorization: Bearer $TOKEN"
```

### Invalidate Cache Pattern
```bash
curl -X DELETE "http://localhost:8000/cache/invalidate?pattern=user_*" \
  -H "Authorization: Bearer $TOKEN"
```

## Export/Import API Examples

### Export Data
```bash
curl -X POST http://localhost:8000/export-import/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "users",
    "format": "json",
    "filters": {}
  }'
```

### Import Data
```bash
curl -X POST http://localhost:8000/export-import/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "users",
    "format": "json",
    "data": "[{\"username\":\"user1\",\"email\":\"user1@test.com\"}]",
    "overwrite": false
  }'
```

## Best Practices

### 1. Token Management
- Store access tokens securely
- Use refresh tokens to get new access tokens
- Implement token refresh before expiration
- Blacklist tokens on logout

### 2. Error Handling
- Handle 401 errors by refreshing token
- Handle 403 errors by checking permissions
- Handle 429 errors by implementing retry logic
- Log errors for debugging

### 3. Tenant Context
- Always include tenant context in requests
- Validate tenant permissions before access
- Use tenant-specific data isolation
- Monitor tenant resource usage

### 4. Security
- Never log or expose tokens
- Use HTTPS in production
- Implement proper error messages
- Validate all input data

## Support
For API usage issues:
- **Documentation:** See [API Documentation](http://localhost:8000/docs)
- **Examples:** See [API Examples](Docs/API_EXAMPLES.md)
- **Support:** api-support@icap-enterprise.com
