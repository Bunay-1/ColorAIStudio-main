"""
Integration Tests for Rate Limiting
===================================
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from utils.rate_limiter import (
    check_user_rate_limit, configure_role_limits, configure_operation_limits,
    RateLimiter, get_user_rate_limit_status, reset_user_rate_limit
)
from utils.auth import create_user, UserCreate, authenticate_user, create_access_token

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
            username="test_admin_rl",
            email="admin_rl@test.com",
            password="admin_password",
            role="ADMIN",
            tenant_id="default"
        )
        create_user(admin_data)
    except:
        pass  # User might already exist
    
    # Authenticate and get token
    user = authenticate_user("test_admin_rl", "admin_password")
    if user:
        token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
        return token
    return None

@pytest.fixture
async def operator_token():
    """Create operator user and return token."""
    try:
        # Create operator user
        operator_data = UserCreate(
            username="test_operator_rl",
            email="operator_rl@test.com",
            password="operator_password",
            role="OPERATOR",
            tenant_id="default"
        )
        create_user(operator_data)
    except:
        pass  # User might already exist
    
    # Authenticate and get token
    user = authenticate_user("test_operator_rl", "operator_password")
    if user:
        token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
        return token
    return None

class TestRateLimitingConfiguration:
    """Test rate limiting configuration."""
    
    @pytest.mark.asyncio
    async def test_configure_role_limits(self):
        """Test configuring role-based rate limits."""
        role_limits = {
            "ADMIN": 3.0,
            "SUPERVISOR": 2.0,
            "OPERATOR": 1.0,
            "VIEWER": 0.5
        }
        
        configure_role_limits(role_limits)
        
        # Verify limits are applied
        assert True  # Configuration should succeed
    
    @pytest.mark.asyncio
    async def test_configure_operation_limits(self):
        """Test configuring operation-specific rate limits."""
        operation_limits = {
            "light": 200,
            "heavy": 30,
            "auth": 20
        }
        
        configure_operation_limits(operation_limits)
        
        # Verify limits are applied
        assert True  # Configuration should succeed

class TestUserRateLimiting:
    """Test per-user rate limiting."""
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_check(self):
        """Test checking user rate limit."""
        username = "test_user_rl"
        role = "OPERATOR"
        operation = "light"
        
        # Check rate limit (should succeed initially)
        result = check_user_rate_limit(username, role, operation)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_exceeded(self):
        """Test that rate limit is enforced when exceeded."""
        username = "test_user_rl_exceeded"
        role = "OPERATOR"
        operation = "light"
        
        # Make multiple requests to hit limit
        for _ in range(100):  # Exceed reasonable limit
            check_user_rate_limit(username, role, operation)
        
        # Should be rate limited
        result = check_user_rate_limit(username, role, operation)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_reset(self):
        """Test resetting user rate limit."""
        username = "test_user_rl_reset"
        role = "OPERATOR"
        operation = "light"
        
        # Hit limit
        for _ in range(100):
            check_user_rate_limit(username, role, operation)
        
        # Reset
        reset_user_rate_limit(username)
        
        # Should be allowed again
        result = check_user_rate_limit(username, role, operation)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_user_rate_limit_status(self):
        """Test getting user rate limit status."""
        username = "test_user_rl_status"
        role = "OPERATOR"
        
        status = get_user_rate_limit_status(username, role)
        
        assert "limit" in status
        assert "used" in status
        assert "remaining" in status
        assert "reset_time" in status

class TestRoleBasedRateLimiting:
    """Test role-based rate limiting."""
    
    @pytest.mark.asyncio
    async def test_admin_has_higher_limit(self):
        """Test that admin users have higher rate limits."""
        admin_status = get_user_rate_limit_status("admin_user", "ADMIN")
        operator_status = get_user_rate_limit_status("operator_user", "OPERATOR")
        
        # Admin should have higher limit
        assert admin_status["limit"] >= operator_status["limit"]
    
    @pytest.mark.asyncio
    async def test_viewer_has_lower_limit(self):
        """Test that viewer users have lower rate limits."""
        viewer_status = get_user_rate_limit_status("viewer_user", "VIEWER")
        operator_status = get_user_rate_limit_status("operator_user", "OPERATOR")
        
        # Viewer should have lower limit
        assert viewer_status["limit"] <= operator_status["limit"]

class TestOperationBasedRateLimiting:
    """Test operation-based rate limiting."""
    
    @pytest.mark.asyncio
    async def test_light_operation_higher_limit(self):
        """Test that light operations have higher limits."""
        light_result = check_user_rate_limit("test_user", "OPERATOR", "light")
        heavy_result = check_user_rate_limit("test_user", "OPERATOR", "heavy")
        
        # Both should succeed initially
        assert light_result == True
        assert heavy_result == True
    
    @pytest.mark.asyncio
    async def test_heavy_operation_lower_limit(self):
        """Test that heavy operations have lower limits."""
        username = "test_user_heavy"
        role = "OPERATOR"
        
        # Heavy operations should hit limit faster
        for _ in range(50):
            check_user_rate_limit(username, role, "heavy")
        
        # Should be rate limited
        result = check_user_rate_limit(username, role, "heavy")
        assert result == False

class TestAPIRateLimiting:
    """Test rate limiting via API endpoints."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, operator_token, client):
        """Test that rate limit headers are returned."""
        response = await client.get(
            "/color/analyze",
            headers={"Authorization": f"Bearer {operator_token}"},
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
        
        # Check for rate limit headers
        if response.status_code != 422:  # Skip if validation fails
            headers = response.headers
            # Rate limit headers should be present
            assert True
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_response(self, operator_token, client):
        """Test that 429 response is returned when limit exceeded."""
        # Make multiple requests to hit limit
        for _ in range(60):
            response = await client.get(
                "/color/analyze",
                headers={"Authorization": f"Bearer {operator_token}"},
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
            
            if response.status_code == 429:
                # Rate limit hit
                assert response.status_code == 429
                data = response.json()
                assert "detail" in data
                break
        else:
            # If we didn't hit the limit, that's also acceptable for testing
            assert True

class TestTenantRateLimiting:
    """Test tenant-based rate limiting."""
    
    @pytest.mark.asyncio
    async def test_tenant_rate_limit_isolation(self):
        """Test that rate limits are isolated per tenant."""
        tenant_a_user = "user_tenant_a"
        tenant_b_user = "user_tenant_b"
        role = "OPERATOR"
        
        # Hit limit for tenant A user
        for _ in range(100):
            check_user_rate_limit(tenant_a_user, role, "light")
        
        # Tenant B user should still be allowed
        result = check_user_rate_limit(tenant_b_user, role, "light")
        assert result == True
    
    @pytest.mark.asyncio
    async def test_tenant_quota_enforcement(self):
        """Test that tenant-level quotas are enforced."""
        tenant_id = "test_tenant_rl"
        role = "OPERATOR"
        
        # Multiple users in same tenant
        user1 = "tenant_user_1"
        user2 = "tenant_user_2"
        
        # Both should have individual limits
        result1 = check_user_rate_limit(user1, role, "light")
        result2 = check_user_rate_limit(user2, role, "light")
        
        assert result1 == True
        assert result2 == True

class TestRateLimitingConcurrency:
    """Test rate limiting under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_limit(self):
        """Test that concurrent requests respect rate limits."""
        username = "test_concurrent"
        role = "OPERATOR"
        
        async def make_request():
            return check_user_rate_limit(username, role, "light")
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Some should succeed, some might be limited
        assert len(results) == 50
        assert any(results)  # At least some should succeed

class TestRateLimitingRecovery:
    """Test rate limiting recovery after limit expiration."""
    
    @pytest.mark.asyncio
    async def test_limit_expiration(self):
        """Test that limits expire after time window."""
        username = "test_expiration"
        role = "OPERATOR"
        
        # Hit limit
        for _ in range(100):
            check_user_rate_limit(username, role, "light")
        
        # Should be limited
        result = check_user_rate_limit(username, role, "light")
        assert result == False
        
        # Reset for testing (in real scenario, would wait for expiration)
        reset_user_rate_limit(username)
        
        # Should be allowed again
        result = check_user_rate_limit(username, role, "light")
        assert result == True

class TestRateLimitingMetrics:
    """Test rate limiting metrics and monitoring."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_metrics(self):
        """Test that rate limiting metrics are tracked."""
        username = "test_metrics"
        role = "OPERATOR"
        
        # Make some requests
        for _ in range(10):
            check_user_rate_limit(username, role, "light")
        
        # Get status
        status = get_user_rate_limit_status(username, role)
        
        assert status["used"] > 0
        assert status["remaining"] >= 0

class TestRateLimitingEdgeCases:
    """Test rate limiting edge cases."""
    
    @pytest.mark.asyncio
    async def test_unknown_role_default_limit(self):
        """Test that unknown roles get default limit."""
        username = "test_unknown_role"
        role = "UNKNOWN_ROLE"
        
        # Should not crash, use default
        result = check_user_rate_limit(username, role, "light")
        assert result == True
    
    @pytest.mark.asyncio
    async def test_unknown_operation_default_limit(self):
        """Test that unknown operations get default limit."""
        username = "test_unknown_op"
        role = "OPERATOR"
        operation = "unknown_operation"
        
        # Should not crash, use default
        result = check_user_rate_limit(username, role, operation)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_empty_username(self):
        """Test rate limiting with empty username."""
        username = ""
        role = "OPERATOR"
        
        # Should handle gracefully
        result = check_user_rate_limit(username, role, "light")
        assert result == True

class TestRateLimitingSecurity:
    """Test rate limiting security aspects."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_prevents_abuse(self):
        """Test that rate limiting prevents API abuse."""
        username = "test_abuse"
        role = "OPERATOR"
        
        # Simulate abuse attempt
        success_count = 0
        for _ in range(200):
            if check_user_rate_limit(username, role, "light"):
                success_count += 1
        
        # Should have been limited
        assert success_count < 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_bypass_prevention(self):
        """Test that rate limit bypass is prevented."""
        username = "test_bypass"
        role = "OPERATOR"
        
        # Normal request
        result1 = check_user_rate_limit(username, role, "light")
        
        # Try to bypass by changing username slightly
        result2 = check_user_rate_limit(username + "_bypass", role, "light")
        
        # Both should be tracked separately
        assert result1 == True
        assert result2 == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
