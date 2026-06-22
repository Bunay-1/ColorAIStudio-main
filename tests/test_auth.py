"""
Unit tests for Authentication Module
==================================
"""

import pytest
from datetime import timedelta
from utils.auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    authenticate_user, create_user, get_user, get_all_users, update_user_role, delete_user,
    UserCreate, ROLES_PERMISSIONS
)

class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hash length
        
    def test_password_verification(self):
        """Test that password verification works correctly."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

class TestTokenCreation:
    """Test JWT token creation."""
    
    def test_access_token_creation(self):
        """Test access token creation."""
        data = {"sub": "test_user", "role": "ADMIN"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100
        
    def test_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "test_user", "role": "ADMIN"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))
        
        assert token is not None
        assert isinstance(token, str)
        
    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        data = {"sub": "test_user", "role": "ADMIN"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100

class TestUserManagement:
    """Test user management functions."""
    
    def test_create_user(self):
        """Test user creation."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        user = create_user(user_data)
        
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert user["role"] == "OPERATOR"
        assert user["is_active"] is True
        assert "hashed_password" in user
        
    def test_create_duplicate_user(self):
        """Test that duplicate user creation fails."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        # First creation should succeed
        create_user(user_data)
        
        # Second creation should fail
        with pytest.raises(Exception):
            create_user(user_data)
            
    def test_get_user(self):
        """Test getting a user by username."""
        user_data = UserCreate(
            username="testuser2",
            email="test2@example.com",
            password="test_password",
            role="ADMIN"
        )
        
        create_user(user_data)
        user = get_user("testuser2")
        
        assert user is not None
        assert user["username"] == "testuser2"
        assert user["role"] == "ADMIN"
        
    def test_get_nonexistent_user(self):
        """Test getting a nonexistent user."""
        user = get_user("nonexistent_user")
        assert user is None
        
    def test_get_all_users(self):
        """Test getting all users."""
        users = get_all_users()
        
        assert isinstance(users, list)
        # Check that passwords are not included
        for user in users:
            assert "hashed_password" not in user
            
    def test_update_user_role(self):
        """Test updating user role."""
        user_data = UserCreate(
            username="testuser3",
            email="test3@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        create_user(user_data)
        updated_user = update_user_role("testuser3", "ADMIN")
        
        assert updated_user is not None
        assert updated_user["role"] == "ADMIN"
        
    def test_update_nonexistent_user_role(self):
        """Test updating role for nonexistent user."""
        updated_user = update_user_role("nonexistent_user", "ADMIN")
        assert updated_user is None
        
    def test_delete_user(self):
        """Test deleting a user."""
        user_data = UserCreate(
            username="testuser4",
            email="test4@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        create_user(user_data)
        success = delete_user("testuser4")
        
        assert success is True
        assert get_user("testuser4") is None
        
    def test_delete_admin_user(self):
        """Test that admin user cannot be deleted."""
        with pytest.raises(Exception):
            delete_user("admin")

class TestAuthentication:
    """Test authentication functions."""
    
    def test_authenticate_valid_user(self):
        """Test authenticating with valid credentials."""
        user_data = UserCreate(
            username="testuser5",
            email="test5@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        create_user(user_data)
        user = authenticate_user("testuser5", "test_password")
        
        assert user is not None
        assert user["username"] == "testuser5"
        
    def test_authenticate_invalid_password(self):
        """Test authenticating with invalid password."""
        user_data = UserCreate(
            username="testuser6",
            email="test6@example.com",
            password="test_password",
            role="OPERATOR"
        )
        
        create_user(user_data)
        user = authenticate_user("testuser6", "wrong_password")
        
        assert user is None
        
    def test_authenticate_nonexistent_user(self):
        """Test authenticating nonexistent user."""
        user = authenticate_user("nonexistent_user", "test_password")
        assert user is None

class TestRolePermissions:
    """Test role-based permissions."""
    
    def test_role_permissions_structure(self):
        """Test that role permissions are properly defined."""
        assert "ADMIN" in ROLES_PERMISSIONS
        assert "OPERATOR" in ROLES_PERMISSIONS
        assert "view" in ROLES_PERMISSIONS["ADMIN"]
        assert "user_management" in ROLES_PERMISSIONS["ADMIN"]
        
    def test_admin_has_all_permissions(self):
        """Test that admin has all permissions."""
        admin_perms = ROLES_PERMISSIONS["ADMIN"]
        expected_perms = ["view", "analyze", "configure", "train", "delete", "report", "iot_control", "user_management"]
        
        for perm in expected_perms:
            assert perm in admin_perms
            
    def test_operator_has_limited_permissions(self):
        """Test that operator has limited permissions."""
        operator_perms = ROLES_PERMISSIONS["OPERATOR"]
        
        assert "view" in operator_perms
        assert "analyze" in operator_perms
        assert "user_management" not in operator_perms
        assert "delete" not in operator_perms

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
