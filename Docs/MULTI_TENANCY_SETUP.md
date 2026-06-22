# Multi-Tenancy Setup Guide
==========================

## Overview
ICAP v8.9.5 Enterprise supports multi-tenancy, allowing multiple organizations or departments to use the same ICAP instance while maintaining complete data isolation.

## Architecture

### Tenant Isolation Model
- **Database Isolation:** All data includes tenant_id for filtering
- **Context Management:** Automatic tenant context from request headers
- **Resource Isolation:** Separate resources per tenant (files, cache, etc.)
- **Permission Isolation:** Role-based access control within tenant context

### Tenant Hierarchy
```
ICAP Instance
├── Tenant: default (System Tenant)
├── Tenant: company_a
│   ├── Users: [user1, user2, ...]
│   ├── Data: Isolated measurements, clients, models
│   └── Resources: Dedicated file storage
├── Tenant: company_b
│   ├── Users: [user3, user4, ...]
│   ├── Data: Isolated measurements, clients, models
│   └── Resources: Dedicated file storage
└── ...
```

## Setup Steps

### 1. Environment Configuration
Add multi-tenancy configuration to your `.env` file:
```env
# Multi-Tenancy Configuration
ICAP_MULTI_TENANT_ENABLED=true
ICAP_DEFAULT_TENANT=default
ICAP_TENANT_ISOLATION_LEVEL=strict
```

### 2. Database Schema Update
The database schema automatically includes tenant_id columns:
```sql
-- Measurements table
ALTER TABLE measurements ADD COLUMN tenant_id TEXT DEFAULT 'default';
CREATE INDEX idx_measurements_tenant_id ON measurements(tenant_id);

-- Clients table
ALTER TABLE clients ADD COLUMN tenant_id TEXT DEFAULT 'default';
CREATE INDEX idx_clients_tenant_id ON clients(tenant_id);

-- Models table
ALTER TABLE models ADD COLUMN tenant_id TEXT DEFAULT 'default';
CREATE INDEX idx_models_tenant_id ON models(tenant_id);
```

### 3. Create Tenant
Use the tenant management API to create a new tenant:
```bash
curl -X POST http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "company_a",
    "name": "Company A",
    "description": "Company A Production Line",
    "max_users": 50,
    "storage_quota_gb": 100
  }'
```

### 4. Create Users for Tenant
Create users assigned to the specific tenant:
```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@company_a.com",
    "password": "secure_password",
    "role": "OPERATOR",
    "tenant_id": "company_a"
  }'
```

### 5. Configure Tenant Context
Include tenant information in API requests:
```http
POST /color/analyze
X-Tenant-ID: company_a
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "lab_sample": [50.0, 2.0, 5.0],
  "lab_standard": [50.0, 2.0, 5.0],
  "tolerance": 1.0,
  ...
}
```

## Tenant Management

### Create Tenant
```python
from utils.multi_tenant import create_tenant

tenant = create_tenant(
    tenant_id="company_a",
    name="Company A",
    description="Company A Production Line",
    max_users=50,
    storage_quota_gb=100
)
```

### Update Tenant Configuration
```python
from utils.multi_tenant import update_tenant

updated = update_tenant("company_a", {
    "name": "Company A (Updated)",
    "max_users": 100
})
```

### Activate/Deactivate Tenant
```python
from utils.multi_tenant import activate_tenant, deactivate_tenant

# Activate tenant
activate_tenant("company_a")

# Deactivate tenant
deactivate_tenant("company_a")
```

### Delete Tenant
```python
from utils.multi_tenant import delete_tenant

# Delete tenant (will fail if not empty)
delete_tenant("company_a")
```

## User Management

### Create User with Tenant Assignment
```python
from utils.auth import UserCreate, create_user

user_data = UserCreate(
    username="john_doe",
    email="john@company_a.com",
    password="secure_password",
    role="OPERATOR",
    tenant_id="company_a"
)

user = create_user(user_data)
```

### Get Users by Tenant
```python
from utils.auth import get_all_users

users = get_all_users()
tenant_users = [u for u in users if u.get("tenant_id") == "company_a"]
```

### Update User Role
```python
from utils.auth import update_user_role

updated = update_user_role("john_doe", "SUPERVISOR")
```

## Database Operations

### Tenant-Aware Queries
All database operations automatically include tenant filtering:
```python
from database import get_measurements_by_batch

# Automatically filters by current tenant context
measurements = get_measurements_by_batch("batch_123")
```

### Explicit Tenant Specification
```python
from database import get_measurements_by_batch

# Explicitly specify tenant
measurements = get_measurements_by_batch(
    "batch_123",
    tenant_id="company_a"
)
```

### Insert with Tenant Context
```python
from database import insert_measurement

measurement_data = {
    "timestamp": "2026-06-20 10:30:00",
    "batch_id": "batch_123",
    "operator_id": "john_doe",
    "machine_id": "machine_1",
    "client_id": "client_a",
    "delta_e": 0.5,
    "status": "Pass",
    "method": "CIE2000",
    "illuminant": "D65"
}

# Automatically includes current tenant_id
insert_measurement(measurement_data)
```

## File Storage

### Tenant-Isolated File Paths
```python
from utils.multi_tenant import get_tenant_isolated_path

# Get tenant-specific path
file_path = get_tenant_isolated_path(
    "/base/path",
    tenant_id="company_a"
)
# Returns: /base/path/tenants/company_a/...
```

### Directory Structure
```
RAG/
├── tenants/
│   ├── default/
│   │   └── documents/
│   ├── company_a/
│   │   └── documents/
│   └── company_b/
│       └── documents/
AuditTrail/
├── tenants/
│   ├── default/
│   ├── company_a/
│   └── company_b/
```

## API Integration

### Middleware Integration
The tenant middleware is automatically integrated in `irm_api.py`:
```python
from utils.multi_tenant import TenantMiddleware

app.add_middleware(TenantMiddleware)
```

### Tenant Context in Endpoints
```python
from fastapi import Request, Depends
from utils.multi_tenant import TenantContext

@router.get("/measurements")
async def get_measurements(request: Request):
    # Get current tenant from context
    tenant_id = TenantContext.get_current_tenant()
    
    # Use tenant_id in queries
    measurements = get_measurements_by_tenant(tenant_id)
    return measurements
```

### Tenant-Sensitive Endpoints
```python
from utils.auth import check_permission, get_current_user

@router.post("/analyze")
@Depends(check_permission("analyze"))
async def analyze_color(request: ColorAnalysisRequest, current_user: dict = Depends(get_current_user)):
    # current_user includes tenant_id
    tenant_id = current_user.get("tenant_id", "default")
    
    # Process with tenant context
    result = process_analysis(request, tenant_id)
    return result
```

## Security Considerations

### Tenant Isolation Security
- **Database Queries:** All queries include tenant_id filtering
- **File Access:** File paths are tenant-isolated
- **Cache Keys:** Cache keys include tenant_id
- **API Responses:** Never expose data from other tenants

### Cross-Tenant Access Prevention
```python
from utils.multi_tenant import check_tenant_permission

# Prevent users from accessing other tenants
def check_tenant_access(user: dict, target_tenant_id: str) -> bool:
    return check_tenant_permission(target_tenant_id, user)
```

### Admin Override
Admin users can access all tenants:
```python
if user["role"] == "ADMIN":
    # Admin can access any tenant
    return True
```

## Monitoring

### Tenant Statistics
```python
from utils.multi_tenant import get_tenant_stats

stats = get_tenant_stats("company_a")
print(f"Users: {stats['user_count']}")
print(f"Storage Used: {stats['storage_used_gb']} GB")
print(f"API Calls: {stats['api_calls']}")
```

### Tenant Activity Monitoring
```python
from utils.audit_logger import audit_logger

# Query audit logs for specific tenant
logs = audit_logger.query_logs(tenant_id="company_a", limit=100)
```

### Resource Usage per Tenant
```python
from utils.session_manager import session_manager

# Get sessions for specific tenant
sessions = session_manager.get_tenant_sessions("company_a")
print(f"Active Sessions: {len(sessions)}")
```

## Troubleshooting

### Tenant Not Found
```bash
# Check if tenant exists
curl -X GET http://localhost:8000/auth/tenants/company_a \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create tenant if it doesn't exist
curl -X POST http://localhost:8000/auth/tenants \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "company_a", "name": "Company A"}'
```

### User Cannot Access Tenant Data
```bash
# Check user's tenant assignment
curl -X GET http://localhost:8000/auth/users/USERNAME \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Update user's tenant if needed
curl -X PUT http://localhost:8000/auth/users/USERNAME \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "company_a"}'
```

### Data Not Isolated
```python
# Ensure tenant context is set
from utils.multi_tenant import TenantContext

TenantContext.set_tenant("company_a")

# Verify current tenant
current_tenant = TenantContext.get_current_tenant()
print(f"Current tenant: {current_tenant}")
```

## Best Practices

### 1. Tenant Design
- Use meaningful tenant IDs (e.g., company names, department codes)
- Set appropriate resource quotas per tenant
- Regularly review tenant usage and capacity

### 2. User Management
- Assign users to appropriate tenants
- Use role-based access control within tenants
- Regularly audit user access and permissions

### 3. Data Management
- Ensure all data includes tenant_id
- Use tenant-aware queries consistently
- Implement tenant-specific data retention policies

### 4. Security
- Never expose tenant data to other tenants
- Implement tenant-specific audit logging
- Regularly review tenant access logs

### 5. Performance
- Monitor resource usage per tenant
- Implement tenant-specific caching strategies
- Consider resource quotas for large tenants

## Migration Guide

### Single-Tenant to Multi-Tenant
If migrating from single-tenant to multi-tenant:

1. **Backup existing data**
   ```bash
   cp AuditTrail/icap_enterprise.db AuditTrail/icap_enterprise.db.backup
   ```

2. **Add tenant_id columns**
   ```sql
   ALTER TABLE measurements ADD COLUMN tenant_id TEXT DEFAULT 'default';
   ALTER TABLE clients ADD COLUMN tenant_id TEXT DEFAULT 'default';
   ALTER TABLE models ADD COLUMN tenant_id TEXT DEFAULT 'default';
   ```

3. **Update existing records**
   ```sql
   UPDATE measurements SET tenant_id = 'default';
   UPDATE clients SET tenant_id = 'default';
   UPDATE models SET tenant_id = 'default';
   ```

4. **Create new tenants**
   ```python
   from utils.multi_tenant import create_tenant
   create_tenant("new_tenant", "New Tenant")
   ```

5. **Migrate users to new tenants**
   ```python
   from utils.auth import update_user_role
   update_user_role("username", {"tenant_id": "new_tenant"})
   ```

## Support
For multi-tenancy issues:
- **Documentation:** See [Multi-Tenancy Guide](Docs/MULTI_TENANCY_SETUP.md)
- **API Reference:** See [API Documentation](http://localhost:8000/docs)
- **Support:** support@icap-enterprise.com
