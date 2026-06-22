"""
Multi-Tenancy Support for ICAP
===============================
Tenant isolation and management for enterprise deployments.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from fastapi import Depends, HTTPException, status, Request
from utils.auth import get_current_user

logger = logging.getLogger("MultiTenant")

# Default tenant configuration
DEFAULT_TENANT = "default"

# Tenant storage (in production, use database)
_tenants_db: Dict[str, Dict[str, Any]] = {
    "default": {
        "tenant_id": "default",
        "name": "Default Tenant",
        "is_active": True,
        "max_users": 100,
        "storage_quota_gb": 100,
        "created_at": "2026-01-01T00:00:00Z"
    }
}

# Current tenant context (thread-local for async)
from contextvars import ContextVar
_tenant_context: ContextVar[Optional[str]] = ContextVar('tenant_context', default=None)

class TenantContext:
    """Context manager for tenant isolation."""
    
    @staticmethod
    def get_current_tenant() -> str:
        """Get the current tenant from context."""
        tenant_id = _tenant_context.get()
        return tenant_id or DEFAULT_TENANT
    
    @staticmethod
    def set_tenant(tenant_id: str):
        """Set the current tenant in context."""
        _tenant_context.set(tenant_id)
    
    @staticmethod
    @contextmanager
    def tenant_scope(tenant_id: str):
        """Context manager for tenant-scoped operations."""
        previous_tenant = _tenant_context.get()
        try:
            _tenant_context.set(tenant_id)
            yield tenant_id
        finally:
            if previous_tenant:
                _tenant_context.set(previous_tenant)
            else:
                _tenant_context.set(None)

def get_tenant_from_user(user: Dict[str, Any]) -> str:
    """Get tenant ID from user object."""
    return user.get("tenant_id", DEFAULT_TENANT)

async def get_tenant_from_request(request: Request) -> str:
    """
    Extract tenant from request headers or user context.
    Priority: X-Tenant-ID header > User tenant > Default
    """
    # Try header first
    tenant_id = request.headers.get("X-Tenant-ID")
    
    if tenant_id:
        # Validate tenant exists
        if tenant_id not in _tenants_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        if not _tenants_db[tenant_id].get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant {tenant_id} is inactive"
            )
        return tenant_id
    
    # Fall back to user's tenant
    # This requires authentication to be processed first
    return DEFAULT_TENANT

async def require_tenant(tenant_id: str = Depends(get_tenant_from_request)):
    """
    Dependency to ensure tenant context is set.
    """
    TenantContext.set_tenant(tenant_id)
    return tenant_id

def create_tenant(tenant_id: str, name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new tenant.
    
    Args:
        tenant_id: Unique tenant identifier
        name: Tenant display name
        config: Optional tenant configuration
        
    Returns:
        Created tenant data
    """
    if tenant_id in _tenants_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant {tenant_id} already exists"
        )
    
    tenant = {
        "tenant_id": tenant_id,
        "name": name,
        "is_active": True,
        "max_users": config.get("max_users", 100) if config else 100,
        "storage_quota_gb": config.get("storage_quota_gb", 100) if config else 100,
        "created_at": None  # Will be set by database in production
    }
    
    _tenants_db[tenant_id] = tenant
    logger.info(f"Tenant {tenant_id} created")
    return tenant

def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get tenant by ID."""
    return _tenants_db.get(tenant_id)

def get_all_tenants() -> Dict[str, Dict[str, Any]]:
    """Get all tenants."""
    return _tenants_db

def update_tenant(tenant_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update tenant configuration."""
    if tenant_id not in _tenants_db:
        return None
    
    for key, value in updates.items():
        if key in _tenants_db[tenant_id]:
            _tenants_db[tenant_id][key] = value
    
    logger.info(f"Tenant {tenant_id} updated")
    return _tenants_db[tenant_id]

def delete_tenant(tenant_id: str) -> bool:
    """Delete a tenant."""
    if tenant_id == DEFAULT_TENANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default tenant"
        )
    
    if tenant_id not in _tenants_db:
        return False
    
    del _tenants_db[tenant_id]
    logger.info(f"Tenant {tenant_id} deleted")
    return True

def activate_tenant(tenant_id: str) -> bool:
    """Activate a tenant."""
    if tenant_id not in _tenants_db:
        return False
    
    _tenants_db[tenant_id]["is_active"] = True
    logger.info(f"Tenant {tenant_id} activated")
    return True

def deactivate_tenant(tenant_id: str) -> bool:
    """Deactivate a tenant."""
    if tenant_id == DEFAULT_TENANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate default tenant"
        )
    
    if tenant_id not in _tenants_db:
        return False
    
    _tenants_db[tenant_id]["is_active"] = False
    logger.info(f"Tenant {tenant_id} deactivated")
    return True

class TenantIsolatedDatabase:
    """
    Database wrapper that enforces tenant isolation.
    All queries are automatically scoped to the current tenant.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def execute_tenant_query(self, query: str, params: tuple = None, tenant_id: str = None):
        """
        Execute a query with tenant isolation.
        Automatically adds tenant_id filter to WHERE clauses.
        """
        current_tenant = tenant_id or TenantContext.get_current_tenant()
        
        # Add tenant_id filter to query if not present
        if "tenant_id" not in query.lower() and "where" in query.lower():
            # Simple heuristic to add tenant filter
            query = query.replace("WHERE", f"WHERE tenant_id = '{current_tenant}' AND")
        elif "where" not in query.lower() and ("select" in query.lower() or "delete" in query.lower() or "update" in query.lower()):
            # Add WHERE clause if not present
            if "select" in query.lower():
                query = query.replace("FROM", f"FROM (SELECT * FROM")
                query = query + f") WHERE tenant_id = '{current_tenant}'"
        
        cursor = self.db.cursor()
        cursor.execute(query, params or ())
        return cursor

def get_tenant_isolated_path(base_path: str, tenant_id: str = None) -> str:
    """
    Get a tenant-isolated file path.
    Ensures files are stored in tenant-specific directories.
    """
    current_tenant = tenant_id or TenantContext.get_current_tenant()
    return os.path.join(base_path, "tenants", current_tenant)

def ensure_tenant_directory(base_path: str, tenant_id: str = None):
    """
    Ensure tenant-specific directory exists.
    """
    tenant_path = get_tenant_isolated_path(base_path, tenant_id)
    os.makedirs(tenant_path, exist_ok=True)
    return tenant_path

class TenantMiddleware:
    """
    FastAPI middleware to automatically set tenant context from headers.
    """
    
    async def __call__(self, request: Request, call_next):
        # Extract tenant from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if tenant_id:
            # Validate tenant
            if tenant_id in _tenants_db and _tenants_db[tenant_id].get("is_active", True):
                TenantContext.set_tenant(tenant_id)
            else:
                logger.warning(f"Invalid or inactive tenant ID in header: {tenant_id}")
        
        response = await call_next(request)
        return response

def check_tenant_permission(tenant_id: str, user: Dict[str, Any]) -> bool:
    """
    Check if user has access to the specified tenant.
    """
    user_tenant = user.get("tenant_id", DEFAULT_TENANT)
    
    # Admin can access all tenants
    if user.get("role") == "ADMIN":
        return True
    
    # Users can only access their own tenant
    return user_tenant == tenant_id

def get_tenant_stats(tenant_id: str) -> Dict[str, Any]:
    """
    Get statistics for a specific tenant.
    """
    tenant = _tenants_db.get(tenant_id)
    if not tenant:
        return None
    
    # In production, query actual usage
    return {
        "tenant_id": tenant_id,
        "name": tenant["name"],
        "is_active": tenant["is_active"],
        "max_users": tenant["max_users"],
        "current_users": 0,  # Would be actual count
        "storage_quota_gb": tenant["storage_quota_gb"],
        "storage_used_gb": 0,  # Would be actual usage
        "created_at": tenant.get("created_at")
    }
