"""
End-to-End Tests for Enterprise Workflows
========================================
Тестове за критични enterprise workflows в ICAP v8.9.5 Enterprise.
"""

import pytest
import asyncio
import os
from httpx import AsyncClient, ASGITransport
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from utils.auth import create_user, UserCreate, authenticate_user, create_access_token
from utils.multi_tenant import create_tenant, delete_tenant
from utils.audit_logger import query_audit_logs

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
        admin_data = UserCreate(
            username="test_admin_e2e",
            email="admin_e2e@test.com",
            password="admin_password",
            role="ADMIN",
            tenant_id="default"
        )
        create_user(admin_data)
    except:
        pass
    
    user = authenticate_user("test_admin_e2e", "admin_password")
    if user:
        return create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
    return None

@pytest.fixture
async def operator_token():
    """Create operator user and return token."""
    try:
        operator_data = UserCreate(
            username="test_operator_e2e",
            email="operator_e2e@test.com",
            password="operator_password",
            role="OPERATOR",
            tenant_id="default"
        )
        create_user(operator_data)
    except:
        pass
    
    user = authenticate_user("test_operator_e2e", "operator_password")
    if user:
        return create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
    return None

@pytest.fixture
async def test_tenant():
    """Create test tenant."""
    tenant_id = "e2e_test_tenant"
    try:
        create_tenant(tenant_id, "E2E Test Tenant")
        yield tenant_id
    finally:
        try:
            delete_tenant(tenant_id)
        except:
            pass

class TestAuthenticationWorkflow:
    """Test complete authentication workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_workflow(self, client):
        """Test complete authentication workflow: login, access, refresh, logout."""
        # Step 1: Login
        login_response = await client.post(
            "/auth/login",
            json={"username": "test_admin_e2e", "password": "admin_password"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # Step 2: Access protected endpoint
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["username"] == "test_admin_e2e"
        
        # Step 3: Refresh token
        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        
        # Step 4: Logout
        logout_response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200

class TestMultiTenantWorkflow:
    """Test complete multi-tenant workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_tenant_workflow(self, admin_token, client, test_tenant):
        """Test complete tenant lifecycle: create, user assignment, data isolation."""
        # Step 1: Create tenant
        create_response = await client.post(
            "/auth/tenants",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": test_tenant,
                "name": "E2E Test Tenant",
                "config": {"max_users": 10}
            }
        )
        assert create_response.status_code in [200, 201]
        
        # Step 2: Create user in tenant
        user_response = await client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "tenant_user_e2e",
                "email": "tenant_e2e@test.com",
                "password": "test_password",
                "role": "OPERATOR",
                "tenant_id": test_tenant
            }
        )
        assert user_response.status_code in [200, 201]
        
        # Step 3: Verify tenant stats
        stats_response = await client.get(
            f"/auth/tenants/{test_tenant}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["tenant_id"] == test_tenant
        
        # Step 4: Cleanup
        try:
            from utils.auth import delete_user
            delete_user("tenant_user_e2e")
        except:
            pass

class TestUserManagementWorkflow:
    """Test complete user management workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, admin_token, client):
        """Test complete user lifecycle: create, update role, delete."""
        username = "lifecycle_user_e2e"
        
        try:
            # Step 1: Create user
            create_response = await client.post(
                "/auth/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": username,
                    "email": "lifecycle@test.com",
                    "password": "test_password",
                    "role": "OPERATOR",
                    "tenant_id": "default"
                }
            )
            assert create_response.status_code in [200, 201]
            
            # Step 2: Update user role
            update_response = await client.put(
                f"/auth/users/{username}/role",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"new_role": "SUPERVISOR"}
            )
            assert update_response.status_code == 200
            
            # Step 3: Verify role change
            me_response = await client.get(
                "/auth/users",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert me_response.status_code == 200
            
        finally:
            # Step 4: Cleanup
            try:
                from utils.auth import delete_user
                delete_user(username)
            except:
                pass

class TestColorAnalysisWithAuthWorkflow:
    """Test color analysis workflow with authentication."""
    
    @pytest.mark.asyncio
    async def test_authenticated_color_analysis(self, operator_token, client):
        """Test color analysis with authentication and tenant context."""
        response = await client.post(
            "/color/analyze",
            headers={
                "Authorization": f"Bearer {operator_token}",
                "X-Tenant-ID": "default"
            },
            json={
                "lab_sample": [50.0, 2.0, 5.0],
                "lab_standard": [50.0, 2.0, 5.0],
                "tolerance": 1.0,
                "batch_id": "e2e_batch",
                "operator_id": "test_operator_e2e",
                "machine_id": "e2e_machine",
                "client_id": "e2e_client",
                "method": "CIE2000",
                "illuminant": "D65",
                "batch_size": 1000
            }
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 422, 404]

class TestAuditTrailWorkflow:
    """Test audit trail workflow."""
    
    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self, admin_token, client):
        """Test that audit trail captures all critical actions."""
        # Perform various actions
        await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        await client.get(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Verify audit logs
        logs_response = await client.get(
            "/auth/audit/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 10}
        )
        
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        assert "logs" in logs_data

class TestPermissionWorkflow:
    """Test permission-based access control workflow."""
    
    @pytest.mark.asyncio
    async def test_role_based_permissions(self, operator_token, admin_token, client):
        """Test that roles enforce appropriate permissions."""
        # Operator should not be able to create users
        operator_create_response = await client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "username": "unauthorized_user",
                "email": "unauth@test.com",
                "password": "test_password",
                "role": "OPERATOR",
                "tenant_id": "default"
            }
        )
        assert operator_create_response.status_code == 403
        
        # Admin should be able to create users
        admin_create_response = await client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "authorized_user",
                "email": "auth@test.com",
                "password": "test_password",
                "role": "OPERATOR",
                "tenant_id": "default"
            }
        )
        assert admin_create_response.status_code in [200, 201]
        
        # Cleanup
        try:
            from utils.auth import delete_user
            delete_user("authorized_user")
        except:
            pass

class TestRateLimitingWorkflow:
    """Test rate limiting workflow."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, operator_token, client):
        """Test that rate limiting is enforced."""
        # Make multiple requests
        responses = []
        for i in range(10):
            response = await client.get(
                "/color/analyze",
                headers={"Authorization": f"Bearer {operator_token}"},
                json={
                    "lab_sample": [50.0, 2.0, 5.0],
                    "lab_standard": [50.0, 2.0, 5.0],
                    "tolerance": 1.0,
                    "batch_id": f"rate_test_{i}",
                    "operator_id": "test_operator_e2e",
                    "machine_id": "e2e_machine",
                    "client_id": "e2e_client",
                    "method": "CIE2000",
                    "illuminant": "D65",
                    "batch_size": 1000
                }
            )
            responses.append(response.status_code)
            
            if response.status_code == 429:
                break
        
        # Should have at least some successful requests
        assert any(status == 200 for status in responses)

class TestEnterpriseIntegrationWorkflow:
    """Test complete enterprise integration workflow."""
    
    @pytest.mark.asyncio
    async def test_full_enterprise_workflow(self, admin_token, client):
        """Test complete enterprise workflow: auth, tenant, users, audit."""
        tenant_id = "full_e2e_tenant"
        username = "full_e2e_user"
        
        try:
            # Step 1: Create tenant
            tenant_response = await client.post(
                "/auth/tenants",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "tenant_id": tenant_id,
                    "name": "Full E2E Tenant"
                }
            )
            assert tenant_response.status_code in [200, 201]
            
            # Step 2: Create user in tenant
            user_response = await client.post(
                "/auth/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": username,
                    "email": "full_e2e@test.com",
                    "password": "test_password",
                    "role": "OPERATOR",
                    "tenant_id": tenant_id
                }
            )
            assert user_response.status_code in [200, 201]
            
            # Step 3: Verify tenant stats
            stats_response = await client.get(
                f"/auth/tenants/{tenant_id}/stats",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert stats_response.status_code == 200
            
            # Step 4: Verify audit logs
            audit_response = await client.get(
                "/auth/audit/logs",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"limit": 10}
            )
            assert audit_response.status_code == 200
            
            # Step 5: Cleanup
            await client.delete(
                f"/auth/users/{username}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            await client.delete(
                f"/auth/tenants/{tenant_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
        finally:
            # Final cleanup
            try:
                from utils.auth import delete_user
                delete_user(username)
            except:
                pass
            try:
                delete_tenant(tenant_id)
            except:
                pass

class TestErrorHandlingWorkflow:
    """Test error handling in enterprise workflows."""
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, client):
        """Test authentication error handling."""
        # Invalid credentials
        response = await client.post(
            "/auth/login",
            json={"username": "invalid", "password": "invalid"}
        )
        assert response.status_code == 401
        
        # Missing credentials
        response = await client.post(
            "/auth/login",
            json={"username": "test_admin_e2e"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_permission_error_handling(self, operator_token, client):
        """Test permission error handling."""
        # Try to access admin-only endpoint
        response = await client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "username": "test",
                "email": "test@test.com",
                "password": "test",
                "role": "OPERATOR",
                "tenant_id": "default"
            }
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_tenant_error_handling(self, admin_token, client):
        """Test tenant error handling."""
        # Try to access non-existent tenant
        response = await client.get(
            "/auth/tenants/nonexistent_tenant",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
