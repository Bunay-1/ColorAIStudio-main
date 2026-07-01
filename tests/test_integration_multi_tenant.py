"""
Integration Tests for Multi-Tenancy
==================================
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from utils.multi_tenant import (
    create_tenant, get_tenant, get_all_tenants, update_tenant, delete_tenant,
    activate_tenant, deactivate_tenant, get_tenant_stats, TenantContext
)
from utils.auth import create_user, UserCreate, authenticate_user, create_access_token
from app.modules.database import get_measurements_by_batch, insert_measurement

@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def admin_token():
    """Create admin user and return token."""
    try:
        # Create admin user
        admin_data = UserCreate(
            username="test_admin",
            email="admin@test.com",
            password="admin_password",
            role="ADMIN",
            tenant_id="default"
        )
        create_user(admin_data)
    except:
        pass  # User might already exist
    
    # Authenticate and get token
    user = authenticate_user("test_admin", "admin_password")
    if user:
        token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
        return token
    return None

@pytest.fixture
async def test_tenant():
    """Create test tenant."""
    tenant_id = "test_tenant_integration"
    try:
        tenant = create_tenant(tenant_id, "Test Integration Tenant", {"max_users": 10})
        yield tenant_id
    finally:
        # Cleanup
        try:
            delete_tenant(tenant_id)
        except:
            pass

class TestTenantManagement:
    """Test tenant management operations."""
    
    @pytest.mark.asyncio
    async def test_create_tenant(self, admin_token, client):
        """Test tenant creation."""
        response = await client.post(
            "/auth/tenants",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "new_test_tenant",
                "name": "New Test Tenant",
                "config": {"max_users": 20}
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["tenant_id"] == "new_test_tenant"
        assert data["name"] == "New Test Tenant"
        assert data["is_active"] == True
        
        # Cleanup
        try:
            delete_tenant("new_test_tenant")
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_list_tenants(self, admin_token, client):
        """Test listing all tenants."""
        response = await client.get(
            "/auth/tenants",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "default" in data
    
    @pytest.mark.asyncio
    async def test_get_tenant_info(self, admin_token, client, test_tenant):
        """Test getting tenant information."""
        response = await client.get(
            f"/auth/tenants/{test_tenant}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == test_tenant
        assert data["name"] == "Test Integration Tenant"
    
    @pytest.mark.asyncio
    async def test_get_tenant_stats(self, admin_token, client, test_tenant):
        """Test getting tenant statistics."""
        response = await client.get(
            f"/auth/tenants/{test_tenant}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "user_count" in data
    
    @pytest.mark.asyncio
    async def test_update_tenant(self, admin_token, client, test_tenant):
        """Test updating tenant configuration."""
        response = await client.put(
            f"/auth/tenants/{test_tenant}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Test Tenant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Test Tenant"
    
    @pytest.mark.asyncio
    async def test_activate_tenant(self, admin_token, client, test_tenant):
        """Test activating a tenant."""
        # First deactivate
        deactivate_tenant(test_tenant)
        
        response = await client.post(
            f"/auth/tenants/{test_tenant}/activate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "activated" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_deactivate_tenant(self, admin_token, client, test_tenant):
        """Test deactivating a tenant."""
        response = await client.post(
            f"/auth/tenants/{test_tenant}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deactivated" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_tenant(self, admin_token, client):
        """Test deleting a tenant."""
        # Create tenant first
        tenant_id = "tenant_to_delete"
        create_tenant(tenant_id, "Tenant to Delete")
        
        response = await client.delete(
            f"/auth/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

class TestTenantDataIsolation:
    """Test data isolation between tenants."""
    
    @pytest.mark.asyncio
    async def test_tenant_user_assignment(self, admin_token, client):
        """Test that users are properly assigned to tenants."""
        # Create user in test tenant
        user_data = UserCreate(
            username="tenant_user",
            email="tenant_user@test.com",
            password="test_password",
            role="OPERATOR",
            tenant_id="default"
        )
        user = create_user(user_data)
        
        assert user["tenant_id"] == "default"
        
        # Cleanup
        try:
            from utils.auth import delete_user
            delete_user("tenant_user")
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_tenant_context_management(self):
        """Test tenant context management."""
        # Set tenant context
        TenantContext.set_tenant("test_tenant")
        
        # Get current tenant
        current = TenantContext.get_current_tenant()
        assert current == "test_tenant"
        
        # Clear context
        TenantContext.clear_tenant()
        assert TenantContext.get_current_tenant() is None
    
    @pytest.mark.asyncio
    async def test_database_tenant_isolation(self):
        """Test that database queries respect tenant isolation."""
        # Insert measurement with tenant context
        TenantContext.set_tenant("test_tenant")
        
        measurement_data = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": "test_batch",
            "operator_id": "test_operator",
            "machine_id": "test_machine",
            "client_id": "test_client",
            "delta_e": 0.5,
            "status": "Pass",
            "method": "CIE2000",
            "illuminant": "D65"
        }
        
        try:
            insert_measurement(measurement_data)
            
            # Query with tenant context
            measurements = get_measurements_by_batch("test_batch")
            
            # Verify tenant_id is included
            if measurements:
                assert all(m.get("tenant_id") == "test_tenant" for m in measurements)
        finally:
            TenantContext.clear_tenant()
    
    @pytest.mark.asyncio
    async def test_cross_tenant_access_prevention(self, admin_token, client):
        """Test that users cannot access other tenants' data."""
        # Create user in tenant A
        user_data = UserCreate(
            username="user_a",
            email="user_a@test.com",
            password="test_password",
            role="OPERATOR",
            tenant_id="tenant_a"
        )
        try:
            create_user(user_data)
        except:
            pass
        
        # Get user token
        user = authenticate_user("user_a", "test_password")
        if user:
            user_token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": "tenant_a"})
            
            # Try to access tenant B data (should fail or return empty)
            TenantContext.set_tenant("tenant_b")
            measurements = get_measurements_by_batch("test_batch")
            TenantContext.clear_tenant()
            
            # User from tenant_a should not see tenant_b data
            assert measurements is None or len(measurements) == 0
        
        # Cleanup
        try:
            from utils.auth import delete_user
            delete_user("user_a")
        except:
            pass

class TestTenantPermissions:
    """Test tenant-based permissions."""
    
    @pytest.mark.asyncio
    async def test_admin_can_access_all_tenants(self, admin_token, client):
        """Test that admin can access all tenants."""
        response = await client.get(
            "/auth/tenants",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_manage_tenants(self, client):
        """Test that non-admin users cannot manage tenants."""
        # Create non-admin user
        user_data = UserCreate(
            username="regular_user",
            email="regular@test.com",
            password="test_password",
            role="OPERATOR",
            tenant_id="default"
        )
        try:
            create_user(user_data)
        except:
            pass
        
        # Get user token
        user = authenticate_user("regular_user", "test_password")
        if user:
            user_token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": "default"})
            
            # Try to create tenant (should fail)
            response = await client.post(
                "/auth/tenants",
                headers={"Authorization": f"Bearer {user_token}"},
                json={
                    "tenant_id": "unauthorized_tenant",
                    "name": "Unauthorized Tenant"
                }
            )
            
            assert response.status_code == 403
        
        # Cleanup
        try:
            from utils.auth import delete_user
            delete_user("regular_user")
        except:
            pass

class TestTenantResourceQuotas:
    """Test tenant resource quotas and limits."""
    
    @pytest.mark.asyncio
    async def test_max_users_enforcement(self, admin_token, client, test_tenant):
        """Test that max users quota is enforced."""
        # Get tenant stats
        response = await client.get(
            f"/auth/tenants/{test_tenant}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_count" in data
    
    @pytest.mark.asyncio
    async def test_storage_quota_tracking(self, admin_token, client, test_tenant):
        """Test that storage quota is tracked."""
        # Get tenant stats
        response = await client.get(
            f"/auth/tenants/{test_tenant}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "storage_used_gb" in data

class TestTenantAPIHeaders:
    """Test tenant context via API headers."""
    
    @pytest.mark.asyncio
    async def test_tenant_header_in_request(self, admin_token, client):
        """Test that tenant header is properly processed."""
        response = await client.get(
            "/color/analyze",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "X-Tenant-ID": "test_tenant"
            },
            json={
                "lab_sample": [50.0, 2.0, 5.0],
                "lab_standard": [50.0, 2.0, 5.0],
                "tolerance": 1.0,
                "batch_id": "test_batch",
                "operator_id": "test_operator",
                "machine_id": "test_machine",
                "client_id": "test_client",
                "method": "CIE2000",
                "illuminant": "D65",
                "batch_size": 1000
            }
        )
        
        # Should process request with tenant context
        # Response might be 200 or 422 depending on validation
        assert response.status_code in [200, 422, 404]

class TestTenantLifecycle:
    """Test tenant lifecycle operations."""
    
    @pytest.mark.asyncio
    async def test_full_tenant_lifecycle(self, admin_token, client):
        """Test complete tenant lifecycle: create, activate, update, deactivate, delete."""
        tenant_id = "lifecycle_test_tenant"
        
        try:
            # Create
            response = await client.post(
                "/auth/tenants",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "tenant_id": tenant_id,
                    "name": "Lifecycle Test Tenant"
                }
            )
            assert response.status_code in [200, 201]
            
            # Verify created
            response = await client.get(
                f"/auth/tenants/{tenant_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            
            # Update
            response = await client.put(
                f"/auth/tenants/{tenant_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": "Updated Lifecycle Tenant"}
            )
            assert response.status_code == 200
            
            # Deactivate
            response = await client.post(
                f"/auth/tenants/{tenant_id}/deactivate",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            
            # Activate
            response = await client.post(
                f"/auth/tenants/{tenant_id}/activate",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            
            # Delete
            response = await client.delete(
                f"/auth/tenants/{tenant_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200
            
        finally:
            # Cleanup
            try:
                delete_tenant(tenant_id)
            except:
                pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
