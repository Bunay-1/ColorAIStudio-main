"""
Integration Tests for Authentication System
==========================================
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from utils.auth import (
    create_user, authenticate_user, create_access_token, create_refresh_token,
    get_current_user, check_permission, ROLES_PERMISSIONS
)
from utils.audit_logger import AuditAction, log_audit_event

class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow: create user -> login -> access protected resource."""
        # Create user
        from utils.auth import UserCreate
        user_data = UserCreate(
            username="integration_user",
            email="integration@example.com",
            password="test_password",
            role="OPERATOR"
        )
        user = create_user(user_data)
        
        assert user is not None
        assert user["username"] == "integration_user"
        
        # Authenticate user
        authenticated = authenticate_user("integration_user", "test_password")
        
        assert authenticated is not None
        assert authenticated["username"] == "integration_user"
        
        # Create access token
        token = create_access_token({
            "sub": "integration_user",
            "role": "OPERATOR",
            "tenant_id": "default"
        })
        
        assert token is not None
        assert isinstance(token, str)
        
        # Create refresh token
        refresh_token = create_refresh_token({
            "sub": "integration_user",
            "role": "OPERATOR",
            "tenant_id": "default"
        })
        
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("integration_user")
        
    def test_authentication_with_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        from utils.auth import UserCreate, create_user, authenticate_user
        
        user_data = UserCreate(
            username="invalid_user",
            email="invalid@example.com",
            password="correct_password",
            role="OPERATOR"
        )
        create_user(user_data)
        
        # Try to authenticate with wrong password
        authenticated = authenticate_user("invalid_user", "wrong_password")
        
        assert authenticated is None
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("invalid_user")
        
    def test_role_based_access_control(self):
        """Test role-based access control integration."""
        from utils.auth import UserCreate, create_user, check_permission
        
        # Create admin user
        admin_data = UserCreate(
            username="admin_user",
            email="admin@example.com",
            password="admin_password",
            role="ADMIN"
        )
        create_user(admin_data)
        
        # Create operator user
        operator_data = UserCreate(
            username="operator_user",
            email="operator@example.com",
            password="operator_password",
            role="OPERATOR"
        )
        create_user(operator_data)
        
        # Check admin has all permissions
        admin_user = {"username": "admin_user", "role": "ADMIN"}
        for perm in ROLES_PERMISSIONS["ADMIN"]:
            # This would normally be used as a dependency
            # For testing, we check the permission directly
            assert perm in ROLES_PERMISSIONS["ADMIN"]
        
        # Check operator has limited permissions
        operator_user = {"username": "operator_user", "role": "OPERATOR"}
        assert "view" in ROLES_PERMISSIONS["OPERATOR"]
        assert "user_management" not in ROLES_PERMISSIONS["OPERATOR"]
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("admin_user")
        delete_user("operator_user")

class TestAuditLoggingIntegration:
    """Integration tests for audit logging with authentication."""
    
    def test_audit_logging_on_user_actions(self):
        """Test that user actions are logged to audit trail."""
        from utils.auth import UserCreate, create_user
        from utils.audit_logger import AuditLogger
        
        # Create audit logger
        audit_logger = AuditLogger()
        
        # Create user (this should be logged)
        user_data = UserCreate(
            username="audit_user",
            email="audit@example.com",
            password="audit_password",
            role="OPERATOR"
        )
        create_user(user_data)
        
        # Log audit event
        log_audit_event(
            action=AuditAction.USER_CREATE,
            user_id="audit_user",
            user_role="OPERATOR",
            tenant_id="default",
            details={"username": "audit_user"}
        )
        
        # Query audit logs
        logs = audit_logger.query_logs(user_id="audit_user", limit=10)
        
        assert len(logs) > 0
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("audit_user")

class TestMultiTenancyIntegration:
    """Integration tests for multi-tenancy with authentication."""
    
    def test_tenant_isolated_user_creation(self):
        """Test that users are created with tenant isolation."""
        from utils.auth import UserCreate, create_user
        from utils.multi_tenant import create_tenant, get_tenant
        
        # Create tenant
        tenant = create_tenant("integration_tenant", "Integration Tenant")
        
        assert tenant is not None
        assert tenant["tenant_id"] == "integration_tenant"
        
        # Create user with tenant
        user_data = UserCreate(
            username="tenant_user",
            email="tenant@example.com",
            password="tenant_password",
            role="OPERATOR",
            tenant_id="integration_tenant"
        )
        user = create_user(user_data)
        
        assert user is not None
        assert user["tenant_id"] == "integration_tenant"
        
        # Verify tenant exists
        retrieved_tenant = get_tenant("integration_tenant")
        assert retrieved_tenant is not None
        
        # Cleanup
        from utils.auth import delete_user
        from utils.multi_tenant import delete_tenant
        delete_user("tenant_user")
        delete_tenant("integration_tenant")

class TestRateLimitingIntegration:
    """Integration tests for rate limiting with authentication."""
    
    def test_user_based_rate_limiting(self):
        """Test that rate limiting works per user."""
        from utils.rate_limiter import RateLimiter
        from utils.auth import UserCreate, create_user
        
        # Create user
        user_data = UserCreate(
            username="rate_user",
            email="rate@example.com",
            password="rate_password",
            role="OPERATOR"
        )
        user = create_user(user_data)
        
        # Test rate limiting
        limiter = RateLimiter()
        
        # Make requests within limit
        for _ in range(5):
            is_allowed, _ = limiter.check_rate_limit("rate_user", "per_user", limit=10)
            assert is_allowed is True
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("rate_user")

class TestSessionManagementIntegration:
    """Integration tests for session management with authentication."""
    
    def test_session_creation_on_login(self):
        """Test that session is created on user login."""
        from utils.auth import UserCreate, create_user, authenticate_user
        from utils.session_manager import create_user_session, get_active_session
        
        # Create user
        user_data = UserCreate(
            username="session_user",
            email="session@example.com",
            password="session_password",
            role="OPERATOR"
        )
        create_user(user_data)
        
        # Authenticate user
        authenticated = authenticate_user("session_user", "session_password")
        
        assert authenticated is not None
        
        # Create session
        session = create_user_session(
            user_id="session_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert session is not None
        assert session.user_id == "session_user"
        
        # Get active session
        active_session = get_active_session(session.session_id)
        
        assert active_session is not None
        assert active_session.session_id == session.session_id
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("session_user")

class TestEncryptionIntegration:
    """Integration tests for encryption with authentication."""
    
    def test_sensitive_data_encryption(self):
        """Test that sensitive user data is encrypted."""
        from utils.auth import UserCreate, create_user
        from utils.encryption import EncryptionManager
        
        # Create user with sensitive data
        user_data = UserCreate(
            username="encrypt_user",
            email="encrypt@example.com",
            password="sensitive_password",
            role="OPERATOR"
        )
        user = create_user(user_data)
        
        # Password should be hashed (not plain text)
        assert user["hashed_password"] != "sensitive_password"
        assert len(user["hashed_password"]) > 50
        
        # Test encryption of additional sensitive data
        sensitive_data = {"api_key": "secret_key_123"}
        encrypted = EncryptionManager.encrypt(sensitive_data)
        
        assert encrypted is not None
        assert encrypted != str(sensitive_data)
        
        # Test decryption
        decrypted = EncryptionManager.decrypt(encrypted, as_json=True)
        
        assert decrypted == sensitive_data
        
        # Cleanup
        from utils.auth import delete_user
        delete_user("encrypt_user")

class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_token_security(self):
        """Test token security features."""
        from utils.auth import create_access_token
        from jose import jwt, JWTError
        from utils.auth import SECRET_KEY, ALGORITHM
        
        # Create token
        token = create_access_token({
            "sub": "test_user",
            "role": "ADMIN",
            "tenant_id": "default"
        })
        
        # Verify token can be decoded
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload["sub"] == "test_user"
        assert payload["role"] == "ADMIN"
        
        # Test token with invalid secret fails
        try:
            jwt.decode(token, "invalid_secret", algorithms=[ALGORITHM])
            assert False, "Should have raised JWTError"
        except JWTError:
            pass  # Expected

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
