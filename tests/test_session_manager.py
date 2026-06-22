"""
Unit tests for Session Manager Module
=====================================
"""

import pytest
from datetime import datetime, timedelta
from utils.session_manager import (
    Session, SessionManager, create_user_session, get_active_session,
    end_user_session, MAX_CONCURRENT_SESSIONS, MAX_CONCURRENT_OPERATIONS
)

class TestSession:
    """Test session class."""
    
    def test_session_creation(self):
        """Test creating a session."""
        session = Session(
            session_id="test_session",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert session.session_id == "test_session"
        assert session.user_id == "test_user"
        assert session.user_role == "OPERATOR"
        assert session.tenant_id == "default"
        assert session.is_active is True
        
    def test_session_update_activity(self):
        """Test updating session activity."""
        session = Session(
            session_id="test_session",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        original_activity = session.last_activity
        session.update_activity()
        
        assert session.last_activity >= original_activity
        
    def test_session_not_expired(self):
        """Test that session is not expired."""
        session = Session(
            session_id="test_session",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert session.is_expired() is False
        
    def test_session_expired(self):
        """Test that session is expired after timeout."""
        session = Session(
            session_id="test_session",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        # Set last activity to past
        session.last_activity = datetime.utcnow() - timedelta(hours=10)
        
        assert session.is_expired() is True
        
    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        session = Session(
            session_id="test_session",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        session_dict = session.to_dict()
        
        assert isinstance(session_dict, dict)
        assert session_dict["session_id"] == "test_session"
        assert session_dict["user_id"] == "test_user"
        assert "created_at" in session_dict
        assert "last_activity" in session_dict

class TestSessionManager:
    """Test session manager functions."""
    
    def test_session_manager_initialization(self):
        """Test session manager initialization."""
        manager = SessionManager()
        
        assert manager is not None
        assert manager.sessions is not None
        assert manager.user_sessions is not None
        assert manager.tenant_sessions is not None
        
    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert session is not None
        assert session.user_id == "test_user"
        assert session.session_id in manager.sessions
        assert session.session_id in manager.user_sessions["test_user"]
        
    def test_get_session(self):
        """Test getting a session by ID."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        retrieved_session = manager.get_session(session.session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id
        
    def test_get_nonexistent_session(self):
        """Test getting a nonexistent session."""
        manager = SessionManager()
        
        session = manager.get_session("nonexistent_session")
        
        assert session is None
        
    def test_terminate_session(self):
        """Test terminating a session."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        success = manager.terminate_session(session.session_id)
        
        assert success is True
        assert session.session_id not in manager.sessions
        
    def test_terminate_nonexistent_session(self):
        """Test terminating a nonexistent session."""
        manager = SessionManager()
        
        success = manager.terminate_session("nonexistent_session")
        
        assert success is False
        
    def test_terminate_user_sessions(self):
        """Test terminating all sessions for a user."""
        manager = SessionManager()
        
        # Create multiple sessions for the same user
        manager.create_session(user_id="test_user", user_role="OPERATOR", tenant_id="default")
        manager.create_session(user_id="test_user", user_role="OPERATOR", tenant_id="default")
        
        count = manager.terminate_user_sessions("test_user")
        
        assert count == 2
        assert "test_user" not in manager.user_sessions
        
    def test_terminate_tenant_sessions(self):
        """Test terminating all sessions for a tenant."""
        manager = SessionManager()
        
        # Create sessions for the same tenant
        manager.create_session(user_id="user1", user_role="OPERATOR", tenant_id="tenant1")
        manager.create_session(user_id="user2", user_role="OPERATOR", tenant_id="tenant1")
        
        count = manager.terminate_tenant_sessions("tenant1")
        
        assert count == 2
        assert "tenant1" not in manager.tenant_sessions
        
    def test_start_operation(self):
        """Test starting an operation within a session."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        success = manager.start_operation(
            session_id=session.session_id,
            operation_id="op1",
            operation_type="analyze"
        )
        
        assert success is True
        assert "op1" in session.operations
        
    def test_start_operation_limit_reached(self):
        """Test that operation limit is enforced."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        # Start operations up to limit
        for i in range(MAX_CONCURRENT_OPERATIONS):
            manager.start_operation(
                session_id=session.session_id,
                operation_id=f"op{i}",
                operation_type="analyze"
            )
        
        # Next operation should be blocked
        success = manager.start_operation(
            session_id=session.session_id,
            operation_id="op_exceed",
            operation_type="analyze"
        )
        
        assert success is False
        
    def test_end_operation(self):
        """Test ending an operation."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        manager.start_operation(
            session_id=session.session_id,
            operation_id="op1",
            operation_type="analyze"
        )
        
        manager.end_operation(session.session_id, "op1")
        
        assert "op1" not in session.operations
        
    def test_get_user_sessions(self):
        """Test getting all sessions for a user."""
        manager = SessionManager()
        
        manager.create_session(user_id="test_user", user_role="OPERATOR", tenant_id="default")
        manager.create_session(user_id="test_user", user_role="OPERATOR", tenant_id="default")
        
        sessions = manager.get_user_sessions("test_user")
        
        assert len(sessions) == 2
        
    def test_get_tenant_sessions(self):
        """Test getting all sessions for a tenant."""
        manager = SessionManager()
        
        manager.create_session(user_id="user1", user_role="OPERATOR", tenant_id="tenant1")
        manager.create_session(user_id="user2", user_role="OPERATOR", tenant_id="tenant1")
        
        sessions = manager.get_tenant_sessions("tenant1")
        
        assert len(sessions) == 2
        
    def test_get_all_sessions(self):
        """Test getting all active sessions."""
        manager = SessionManager()
        
        manager.create_session(user_id="user1", user_role="OPERATOR", tenant_id="tenant1")
        manager.create_session(user_id="user2", user_role="OPERATOR", tenant_id="tenant2")
        
        sessions = manager.get_all_sessions()
        
        assert len(sessions) >= 2
        
    def test_get_session_stats(self):
        """Test getting session statistics."""
        manager = SessionManager()
        
        manager.create_session(user_id="user1", user_role="OPERATOR", tenant_id="tenant1")
        
        stats = manager.get_session_stats()
        
        assert isinstance(stats, dict)
        assert "active_sessions" in stats
        assert "total_users" in stats
        assert "total_tenants" in stats
        assert "active_operations" in stats

class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_user_session_function(self):
        """Test create_user_session convenience function."""
        session = create_user_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert session is not None
        assert session.user_id == "test_user"
        
    def test_get_active_session_function(self):
        """Test get_active_session convenience function."""
        session = create_user_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        retrieved = get_active_session(session.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        
    def test_end_user_session_function(self):
        """Test end_user_session convenience function."""
        session = create_user_session(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        success = end_user_session(session.session_id)
        
        assert success is True

class TestSessionConstants:
    """Test session configuration constants."""
    
    def test_max_concurrent_sessions(self):
        """Test max concurrent sessions constant."""
        assert isinstance(MAX_CONCURRENT_SESSIONS, int)
        assert MAX_CONCURRENT_SESSIONS > 0
        
    def test_max_concurrent_operations(self):
        """Test max concurrent operations constant."""
        assert isinstance(MAX_CONCURRENT_OPERATIONS, int)
        assert MAX_CONCURRENT_OPERATIONS > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
