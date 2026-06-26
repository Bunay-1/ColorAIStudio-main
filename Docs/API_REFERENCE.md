# ICAP Platform API Reference v8.10.0 Enterprise
=================================================

Complete API documentation for Industrial Color AI Platform

## Base URL
```
Production: https://api.icap-enterprise.com
Development: http://localhost:8000
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Response Format
All responses follow this structure:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "timestamp": "2026-06-26T10:30:00Z"
}
```

---

## Color Analysis Endpoints

### POST /color/analyze
Analyze color difference (Delta E) between sample and standard.

**Authentication:** Required (permission: `analyze`)

**Rate Limit:** 100 requests/minute per IP

**Request Body:**
```json
{
  "lab_sample": [50.0, 2.0, -5.0],
  "lab_standard": [50.5, 2.5, -4.5],
  "method": "CIEDE2000",
  "tolerance": 2.0,
  "batch_id": "BATCH-001",
  "operator_id": "OP-001",
  "machine_id": "M-001",
  "client_id": "CLIENT-001",
  "batch_size": 1000,
  "illuminant": "D65"
}
```

**Response:**
```json
{
  "delta_e": 1.2345,
  "status": "Pass",
  "method": "CIEDE2000",
  "spc_data": {
    "mean": 0.56,
    "std": 0.12,
    "cpk": 1.5
  },
  "mi_data": {
    "metamerism_index": 0.85
  },
  "recommendations": [],
  "closest_ral": "RAL 3000",
  "spectral_data": [0.1, 0.2, 0.3, ...],
  "iot_energy": 150.5,
  "timestamp": 0.123
}
```

**Error Codes:**
- `400`: Invalid Lab coordinates or tolerance
- `401`: Authentication required
- `403`: Insufficient permissions
- `429`: Rate limit exceeded

---

### GET /color/trends
Get color trend predictions for production batches.

**Authentication:** Required (permission: `analyze`)

**Query Parameters:**
- `batch_id` (string): Batch identifier
- `days` (integer): Number of days for trend analysis (default: 30)

**Response:**
```json
{
  "batch_id": "BATCH-001",
  "trend": "increasing",
  "prediction": {
    "next_delta_e": 1.8,
    "confidence": 0.85
  },
  "historical_data": [
    {"date": "2026-06-01", "delta_e": 1.2},
    {"date": "2026-06-02", "delta_e": 1.3}
  ]
}
```

---

## Vision AI Endpoints

### POST /vision/analyze
Analyze image for defects and surface quality.

**Authentication:** Required (permission: `analyze`)

**Request:** multipart/form-data with image file

**Response:**
```json
{
  "defects": [
    {
      "type": "scratch",
      "confidence": 0.95,
      "bbox": [10, 20, 100, 150],
      "severity": "high"
    }
  ],
  "micro_defects": {
    "texture_analysis": 0.85,
    "surface_quality": "good"
  },
  "grad_cam": "base64_encoded_heatmap",
  "processing_time": 0.015
}
```

---

## RAG & Knowledge Endpoints

### POST /rag/diagnose
AI-assisted diagnostic analysis using RAG and knowledge graph.

**Authentication:** Required (permission: `analyze`)

**Rate Limit:** 20 requests/minute per IP (LLM calls are expensive)

**Request Body:**
```json
{
  "query": "Why is the Delta E increasing for batch BATCH-001?",
  "use_rag": true,
  "use_vision": false,
  "image_data": null
}
```

**Response:**
```json
{
  "analysis": "Based on historical data and knowledge graph...",
  "sources": [
    {
      "document": "Quality_Manual.pdf",
      "page": 15,
      "relevance": 0.92
    }
  ],
  "timestamp": 0.456,
  "model": "irm-industrial"
}
```

---

### POST /rag/index_document
Index a document for semantic search.

**Authentication:** Required (permission: `configure`)

**Rate Limit:** 10 requests/minute per IP (indexing is resource-intensive)

**Request Body:**
```json
{
  "file_path": "/path/to/document.pdf",
  "recursive": false
}
```

**Response:**
```json
{
  "status": "indexing",
  "document_count": 1,
  "estimated_time": 120
}
```

---

## Authentication Endpoints

### POST /auth/login
Authenticate user and receive JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "operator1",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "username": "operator1",
    "role": "OPERATOR",
    "tenant_id": "default"
  }
}
```

---

### POST /auth/refresh
Refresh access token using refresh token.

**Authentication:** Not required (but requires valid refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

---

### POST /auth/logout
Logout and invalidate tokens.

**Authentication:** Required

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

---

## User Management Endpoints

### GET /auth/users
List all users (ADMIN only).

**Authentication:** Required (permission: `user_management`)

**Response:**
```json
{
  "users": [
    {
      "username": "operator1",
      "role": "OPERATOR",
      "email": "operator1@company.com",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST /auth/users
Create new user (ADMIN only).

**Authentication:** Required (permission: `user_management`)

**Request Body:**
```json
{
  "username": "new_user",
  "password": "secure_password",
  "role": "OPERATOR",
  "email": "new_user@company.com",
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User created successfully",
  "user": {
    "username": "new_user",
    "role": "OPERATOR"
  }
}
```

---

## Tenant Management Endpoints

### GET /auth/tenants
List all tenants (ADMIN only).

**Authentication:** Required (permission: `user_management`)

**Response:**
```json
{
  "tenants": [
    {
      "tenant_id": "default",
      "tenant_name": "Default Organization",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST /auth/tenants
Create new tenant (ADMIN only).

**Authentication:** Required (permission: `user_management`)

**Request Body:**
```json
{
  "tenant_id": "company_a",
  "tenant_name": "Company A"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tenant created successfully",
  "tenant": {
    "tenant_id": "company_a",
    "tenant_name": "Company A"
  }
}
```

---

## Analytics Endpoints

### GET /analytics/metrics
Get comprehensive analytics metrics.

**Authentication:** Required (permission: `view`)

**Query Parameters:**
- `start_date` (string): Start date (ISO 8601)
- `end_date` (string): End date (ISO 8601)
- `tenant_id` (string): Tenant identifier (optional)

**Response:**
```json
{
  "quality_metrics": {
    "total_measurements": 1000,
    "pass_rate": 0.95,
    "average_delta_e": 1.2,
    "trend": "stable"
  },
  "performance_metrics": {
    "api_response_time": 0.05,
    "cache_hit_rate": 0.85,
    "error_rate": 0.01
  },
  "business_metrics": {
    "oee": 0.92,
    "scrap_rate": 0.05,
    "co2_emissions": 150.5
  }
}
```

---

## Notifications Endpoints

### POST /notifications/send
Send notification via configured channels.

**Authentication:** Required (permission: `configure`)

**Request Body:**
```json
{
  "channel": "slack",
  "message": "Critical quality alert",
  "level": "CRITICAL",
  "recipients": ["#quality-team"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Notification sent successfully",
  "notification_id": "notif-123"
}
```

---

## Webhook Endpoints

### POST /webhooks/subscribe
Subscribe to webhook events.

**Authentication:** Required (permission: `configure`)

**Request Body:**
```json
{
  "url": "https://your-webhook-endpoint.com",
  "events": ["measurement.created", "quality.alert"],
  "secret": "webhook_secret"
}
```

**Response:**
```json
{
  "status": "success",
  "webhook_id": "webhook-123",
  "secret": "webhook_secret"
}
```

---

## Compliance Endpoints

### GET /compliance/report/generate
Generate compliance report.

**Authentication:** Required (permission: `report`)

**Query Parameters:**
- `standard` (string): Standard (GDPR, SOC2, HIPAA, ISO27001, PCI_DSS)
- `start_date` (string): Start date (ISO 8601)
- `end_date` (string): End date (ISO 8601)

**Response:**
```json
{
  "report_id": "report-123",
  "standard": "ISO27001",
  "status": "generated",
  "download_url": "https://api.icap-enterprise.com/reports/report-123.pdf"
}
```

---

## MFA Endpoints

### POST /mfa/setup
Setup Multi-Factor Authentication for user.

**Authentication:** Required

**Response:**
```json
{
  "qr_code": "data:image/png;base64,...",
  "secret": "JBSWY3DPEHPK3PXP",
  "backup_codes": ["123456", "789012", ...]
}
```

---

### POST /mfa/verify
Verify MFA code during login.

**Authentication:** Not required (part of login flow)

**Request Body:**
```json
{
  "username": "operator1",
  "code": "123456"
}
```

**Response:**
```json
{
  "status": "success",
  "verified": true
}
```

---

## Cache Endpoints

### GET /cache/stats
Get cache statistics.

**Authentication:** Required (permission: `view`)

**Response:**
```json
{
  "available": true,
  "connected_clients": 5,
  "used_memory_human": "256M",
  "total_keys": 1000,
  "hits": 8500,
  "misses": 1500,
  "hit_rate": 0.85
}
```

---

### DELETE /cache/clear
Clear all cache (ADMIN only).

**Authentication:** Required (permission: `configure`)

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

---

## Export/Import Endpoints

### POST /export/import/export
Export data in JSON or CSV format.

**Authentication:** Required (permission: `report`)

**Request Body:**
```json
{
  "data_type": "measurements",
  "format": "json",
  "start_date": "2026-01-01",
  "end_date": "2026-06-26",
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "status": "success",
  "download_url": "https://api.icap-enterprise.com/exports/export-123.json",
  "record_count": 1000
}
```

---

### POST /export/import/import
Import data from JSON or CSV file.

**Authentication:** Required (permission: `configure`)

**Request:** multipart/form-data with file

**Response:**
```json
{
  "status": "success",
  "imported_count": 1000,
  "skipped_count": 5,
  "errors": []
}
```

---

## Health & Monitoring Endpoints

### GET /health
Health check endpoint.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "version": "8.10.0",
  "timestamp": "2026-06-26T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy",
    "ollama": "healthy"
  }
}
```

---

### GET /livez
Liveness probe for Kubernetes.

**Authentication:** Not required

**Response:**
```json
{
  "status": "alive"
}
```

---

### GET /readyz
Readiness probe for Kubernetes.

**Authentication:** Not required

**Response:**
```json
{
  "status": "ready"
}
```

---

### GET /metrics
Prometheus metrics endpoint.

**Authentication:** Not required (but recommended to restrict in production)

**Response:** Prometheus metrics format (text/plain)

---

## Error Handling

All errors follow this structure:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "timestamp": "2026-06-26T10:30:00Z"
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: JWT token missing or invalid
- `INSUFFICIENT_PERMISSIONS`: User lacks required permission
- `RATE_LIMIT_EXCEEDED`: Request rate limit exceeded
- `INVALID_REQUEST`: Request validation failed
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `INTERNAL_ERROR`: Internal server error
- `SERVICE_UNAVAILABLE`: External service unavailable

---

## Rate Limiting

Rate limits are applied per endpoint and user role:

| Endpoint | Base Limit | ADMIN | SUPERVISOR | OPERATOR | VIEWER |
|----------|------------|-------|------------|----------|--------|
| /color/analyze | 100/min | 200/min | 150/min | 100/min | 50/min |
| /rag/diagnose | 20/min | 40/min | 30/min | 20/min | 10/min |
| /vision/analyze | 50/min | 100/min | 75/min | 50/min | 25/min |
| /auth/login | 10/min | 20/min | 15/min | 10/min | 5/min |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1624234567
```

---

## Pagination

List endpoints support pagination:

Query Parameters:
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 50, max: 100)

Response:
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1000,
    "pages": 20
  }
}
```

---

## Versioning

API versioning is supported via the `Accept` header:
```
Accept: application/vnd.icap.v1+json
```

Current version: v1
Next version: v2 (in development)

---

## SDKs

Official SDKs are available:
- Python: `sdk/python/icap_client.py`
- JavaScript: `sdk/javascript/icap-client.js`

For more information, see the SDK documentation.

---

*Last Updated: 2026-06-26*
*Version: 8.10.0 Enterprise*
