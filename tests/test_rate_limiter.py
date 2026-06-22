"""
Unit tests for Rate Limiter Module
================================
"""

import pytest
import time
from utils.rate_limiter import (
    RateLimiter, check_rate_limit_dependency,
    check_user_rate_limit, check_tenant_rate_limit,
    get_rate_limit_status, configure_role_limits,
    configure_operation_limits, DEFAULT_LIMITS, ROLE_MULTIPLIERS
)

class TestRateLimiter:
    """Test rate limiter functions."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        
        assert limiter is not None
        assert limiter.request_history is not None
        
    def test_check_rate_limit_allowed(self):
        """Test that rate limit check allows requests within limit."""
        limiter = RateLimiter()
        
        is_allowed, info = limiter.check_rate_limit("test_user", "per_user", limit=5)
        
        assert is_allowed is True
        assert info["limit"] == 5
        assert info["remaining"] >= 0
        
    def test_check_rate_limit_exceeded(self):
        """Test that rate limit check blocks requests over limit."""
        limiter = RateLimiter()
        
        # Make 5 requests (limit is 5)
        for _ in range(5):
            limiter.check_rate_limit("test_user_exceed", "per_user", limit=5)
        
        # 6th request should be blocked
        is_allowed, info = limiter.check_rate_limit("test_user_exceed", "per_user", limit=5)
        
        assert is_allowed is False
        assert info["remaining"] == 0
        
    def test_get_user_limit(self):
        """Test getting user limit based on role."""
        limiter = RateLimiter()
        
        admin_limit = limiter.get_user_limit("ADMIN", "light")
        operator_limit = limiter.get_user_limit("OPERATOR", "light")
        
        assert admin_limit > operator_limit  # Admins get 2x limit
        
    def test_reset_user_limits(self):
        """Test resetting user rate limits."""
        limiter = RateLimiter()
        
        # Add some requests
        limiter.check_rate_limit("reset_user", "per_user", limit=5)
        
        # Reset limits
        limiter.reset_user_limits("reset_user")
        
        # Should be able to make requests again
        is_allowed, _ = limiter.check_rate_limit("reset_user", "per_user", limit=5)
        assert is_allowed is True
        
    def test_reset_tenant_limits(self):
        """Test resetting tenant rate limits."""
        limiter = RateLimiter()
        
        # Add some requests
        limiter.check_rate_limit("tenant1", "per_tenant", limit=10)
        
        # Reset limits
        limiter.reset_tenant_limits("tenant1")
        
        # Should be able to make requests again
        is_allowed, _ = limiter.check_rate_limit("tenant1", "per_tenant", limit=10)
        assert is_allowed is True

class TestRateLimitChecks:
    """Test rate limit check functions."""
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        status = get_rate_limit_status("test_user", "per_user")
        
        assert isinstance(status, dict)
        assert "limit" in status
        assert "used" in status
        assert "remaining" in status
        
    def test_configure_role_limits(self):
        """Test configuring custom role limits."""
        original_multiplier = ROLE_MULTIPLIERS.get("VIEWER", 0.5)
        
        configure_role_limits({"VIEWER": 1.0})
        
        assert ROLE_MULTIPLIERS["VIEWER"] == 1.0
        
        # Restore original
        ROLE_MULTIPLIERS["VIEWER"] = original_multiplier
        
    def test_configure_operation_limits(self):
        """Test configuring custom operation limits."""
        original_limit = DEFAULT_LIMITS.get("light", 100)
        
        configure_operation_limits({"light": 200})
        
        assert DEFAULT_LIMITS["light"] == 200
        
        # Restore original
        DEFAULT_LIMITS["light"] = original_limit

class TestDefaultLimits:
    """Test default rate limits."""
    
    def test_default_limits_structure(self):
        """Test that default limits are properly defined."""
        assert "global" in DEFAULT_LIMITS
        assert "per_user" in DEFAULT_LIMITS
        assert "per_tenant" in DEFAULT_LIMITS
        assert "auth" in DEFAULT_LIMITS
        assert "heavy" in DEFAULT_LIMITS
        assert "light" in DEFAULT_LIMITS
        
    def test_default_limits_values(self):
        """Test default limit values."""
        assert DEFAULT_LIMITS["global"] == 100
        assert DEFAULT_LIMITS["per_user"] == 50
        assert DEFAULT_LIMITS["per_tenant"] == 200
        assert DEFAULT_LIMITS["auth"] == 10
        assert DEFAULT_LIMITS["heavy"] == 20
        assert DEFAULT_LIMITS["light"] == 100

class TestRoleMultipliers:
    """Test role multipliers."""
    
    def test_role_multipliers_structure(self):
        """Test that role multipliers are properly defined."""
        assert "ADMIN" in ROLE_MULTIPLIERS
        assert "SUPERVISOR" in ROLE_MULTIPLIERS
        assert "OPERATOR" in ROLE_MULTIPLIERS
        assert "VIEWER" in ROLE_MULTIPLIERS
        
    def test_role_multipliers_values(self):
        """Test role multiplier values."""
        assert ROLE_MULTIPLIERS["ADMIN"] == 2.0
        assert ROLE_MULTIPLIERS["SUPERVISOR"] == 1.5
        assert ROLE_MULTIPLIERS["OPERATOR"] == 1.0
        assert ROLE_MULTIPLIERS["VIEWER"] == 0.5

class TestRateLimitDependency:
    """Test rate limit dependency function."""
    
    def test_check_rate_limit_dependency(self):
        """Test rate limit dependency function."""
        # This is a dependency function that would be used in FastAPI
        # We can test that it returns a callable
        dependency = check_rate_limit_dependency("light", limit=50)
        
        assert dependency is not None
        assert callable(dependency)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
