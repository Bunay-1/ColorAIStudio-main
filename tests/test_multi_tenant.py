"""
Unit tests for Multi-Tenancy Module
===================================
"""

import pytest
from utils.multi_tenant import (
    create_tenant, get_tenant, get_all_tenants, update_tenant, delete_tenant,
    activate_tenant, deactivate_tenant, TenantContext, get_tenant_isolated_path,
    check_tenant_permission, get_tenant_stats
)

class TestTenantManagement:
    """Test tenant management functions."""
    
    def test_create_tenant(self):
        """Test tenant creation."""
        tenant = create_tenant("test_tenant", "Test Tenant")
        
        assert tenant is not None
        assert tenant["tenant_id"] == "test_tenant"
        assert tenant["name"] == "Test Tenant"
        assert tenant["is_active"] is True
        
    def test_create_duplicate_tenant(self):
        """Test that duplicate tenant creation fails."""
        create_tenant("duplicate_tenant", "Duplicate")
        
        with pytest.raises(Exception):
            create_tenant("duplicate_tenant", "Duplicate")
            
    def test_get_tenant(self):
        """Test getting a tenant by ID."""
        create_tenant("get_test", "Get Test")
        tenant = get_tenant("get_test")
        
        assert tenant is not None
        assert tenant["tenant_id"] == "get_test"
        assert tenant["name"] == "Get Test"
        
    def test_get_nonexistent_tenant(self):
        """Test getting a nonexistent tenant."""
        tenant = get_tenant("nonexistent_tenant")
        assert tenant is None
        
    def test_get_all_tenants(self):
        """Test getting all tenants."""
        create_tenant("tenant1", "Tenant 1")
        create_tenant("tenant2", "Tenant 2")
        
        tenants = get_all_tenants()
        
        assert isinstance(tenants, dict)
        assert "tenant1" in tenants
        assert "tenant2" in tenants
        
    def test_update_tenant(self):
        """Test updating tenant configuration."""
        create_tenant("update_test", "Update Test")
        updated = update_tenant("update_test", {"name": "Updated Name"})
        
        assert updated is not None
        assert updated["name"] == "Updated Name"
        
    def test_update_nonexistent_tenant(self):
        """Test updating nonexistent tenant."""
        updated = update_tenant("nonexistent_tenant", {"name": "New Name"})
        assert updated is None
        
    def test_delete_tenant(self):
        """Test deleting a tenant."""
        create_tenant("delete_test", "Delete Test")
        success = delete_tenant("delete_test")
        
        assert success is True
        assert get_tenant("delete_test") is None
        
    def test_delete_default_tenant(self):
        """Test that default tenant cannot be deleted."""
        with pytest.raises(Exception):
            delete_tenant("default")
            
    def test_activate_tenant(self):
        """Test tenant activation."""
        create_tenant("activate_test", "Activate Test")
        deactivate_tenant("activate_test")
        
        success = activate_tenant("activate_test")
        assert success is True
        
        tenant = get_tenant("activate_test")
        assert tenant["is_active"] is True
        
    def test_deactivate_tenant(self):
        """Test tenant deactivation."""
        create_tenant("deactivate_test", "Deactivate Test")
        
        success = deactivate_tenant("deactivate_test")
        assert success is True
        
        tenant = get_tenant("deactivate_test")
        assert tenant["is_active"] is False
        
    def test_deactivate_default_tenant(self):
        """Test that default tenant cannot be deactivated."""
        with pytest.raises(Exception):
            deactivate_tenant("default")

class TestTenantContext:
    """Test tenant context management."""
    
    def test_get_current_tenant_default(self):
        """Test getting current tenant when none is set."""
        tenant_id = TenantContext.get_current_tenant()
        assert tenant_id == "default"
        
    def test_set_and_get_tenant(self):
        """Test setting and getting tenant context."""
        TenantContext.set_tenant("test_tenant")
        tenant_id = TenantContext.get_current_tenant()
        
        assert tenant_id == "test_tenant"
        
    def test_tenant_scope(self):
        """Test tenant context scope."""
        with TenantContext.tenant_scope("scope_test"):
            tenant_id = TenantContext.get_current_tenant()
            assert tenant_id == "scope_test"
            
        # After scope, should return to default
        tenant_id = TenantContext.get_current_tenant()
        assert tenant_id == "default"

class TestTenantPermissions:
    """Test tenant permission checks."""
    
    def test_check_tenant_permission_admin(self):
        """Test admin can access any tenant."""
        admin_user = {"username": "admin", "role": "ADMIN", "tenant_id": "default"}
        
        assert check_tenant_permission("other_tenant", admin_user) is True
        
    def test_check_tenant_permission_same_tenant(self):
        """Test user can access their own tenant."""
        user = {"username": "user1", "role": "OPERATOR", "tenant_id": "tenant1"}
        
        assert check_tenant_permission("tenant1", user) is True
        
    def test_check_tenant_permission_different_tenant(self):
        """Test user cannot access different tenant."""
        user = {"username": "user1", "role": "OPERATOR", "tenant_id": "tenant1"}
        
        assert check_tenant_permission("tenant2", user) is False

class TestTenantStats:
    """Test tenant statistics."""
    
    def test_get_tenant_stats(self):
        """Test getting tenant statistics."""
        create_tenant("stats_test", "Stats Test")
        stats = get_tenant_stats("stats_test")
        
        assert stats is not None
        assert stats["tenant_id"] == "stats_test"
        assert stats["name"] == "Stats Test"
        assert "is_active" in stats
        assert "max_users" in stats
        
    def test_get_stats_nonexistent_tenant(self):
        """Test getting stats for nonexistent tenant."""
        stats = get_tenant_stats("nonexistent_tenant")
        assert stats is None

class TestTenantPaths:
    """Test tenant-isolated file paths."""
    
    def test_get_tenant_isolated_path(self):
        """Test getting tenant-isolated path."""
        path = get_tenant_isolated_path("/base/path", "test_tenant")
        
        assert "tenants" in path
        assert "test_tenant" in path
        
    def test_get_tenant_isolated_path_default(self):
        """Test getting tenant-isolated path with default tenant."""
        path = get_tenant_isolated_path("/base/path")
        
        assert "tenants" in path
        assert "default" in path

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
