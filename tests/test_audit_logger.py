"""
Unit tests for Audit Logger Module
==================================
"""

import pytest
from utils.audit_logger import (
    AuditLog, AuditAction, AuditSeverity, AuditLogger,
    log_audit_event, log_security_event
)

class TestAuditLog:
    """Test audit log entry creation."""
    
    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        log = AuditLog(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        assert log.action == "login"
        assert log.user_id == "test_user"
        assert log.user_role == "OPERATOR"
        assert log.tenant_id == "default"
        assert log.severity == "info"
        assert log.is_active is True
        
    def test_audit_log_with_details(self):
        """Test creating an audit log with details."""
        log = AuditLog(
            action=AuditAction.DATA_MODIFY,
            user_id="test_user",
            user_role="ADMIN",
            tenant_id="tenant1",
            severity=AuditSeverity.WARNING,
            resource_type="measurement",
            resource_id="12345",
            details={"batch_id": "batch123"}
        )
        
        assert log.action == "data_modify"
        assert log.resource_type == "measurement"
        assert log.resource_id == "12345"
        assert log.details == {"batch_id": "batch123"}
        assert log.severity == "warning"
        
    def test_audit_log_to_dict(self):
        """Test converting audit log to dictionary."""
        log = AuditLog(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        log_dict = log.to_dict()
        
        assert isinstance(log_dict, dict)
        assert log_dict["action"] == "login"
        assert log_dict["user_id"] == "test_user"
        assert "timestamp" in log_dict
        
    def test_audit_log_to_json(self):
        """Test converting audit log to JSON."""
        log = AuditLog(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        json_str = log.to_json()
        
        assert isinstance(json_str, str)
        assert "login" in json_str
        assert "test_user" in json_str

class TestAuditLogger:
    """Test audit logger functions."""
    
    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger()
        
        assert logger is not None
        assert logger.log_file is not None
        
    def test_log_audit_event(self):
        """Test logging an audit event."""
        logger = AuditLogger()
        
        log = AuditLog(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        # Should not raise an exception
        logger.log(log)
        
    def test_log_user_action(self):
        """Test logging a user action."""
        logger = AuditLogger()
        
        # Should not raise an exception
        logger.log_user_action(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
    def test_log_data_access(self):
        """Test logging data access."""
        logger = AuditLogger()
        
        # Should not raise an exception
        logger.log_data_access(
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            resource_type="measurement",
            resource_id="12345",
            access_type="read"
        )
        
    def test_log_security_event(self):
        """Test logging a security event."""
        logger = AuditLogger()
        
        # Should not raise an exception
        logger.log_security_event(
            event_type="failed_login",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.WARNING
        )
        
    def test_log_error(self):
        """Test logging an error event."""
        logger = AuditLogger()
        
        # Should not raise an exception
        logger.log_error(
            error_message="Test error",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
    def test_query_logs(self):
        """Test querying audit logs."""
        logger = AuditLogger()
        
        # Log some events first
        logger.log_user_action(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        logs = logger.query_logs(user_id="test_user", limit=10)
        
        assert isinstance(logs, list)
        
    def test_get_user_activity_summary(self):
        """Test getting user activity summary."""
        logger = AuditLogger()
        
        # Log some events first
        logger.log_user_action(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
        summary = logger.get_user_activity_summary("test_user", days=7)
        
        assert isinstance(summary, dict)
        assert "user_id" in summary
        assert "total_actions" in summary

class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_log_audit_event_function(self):
        """Test log_audit_event convenience function."""
        # Should not raise an exception
        log_audit_event(
            action=AuditAction.LOGIN,
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )
        
    def test_log_security_event_function(self):
        """Test log_security_event convenience function."""
        # Should not raise an exception
        log_security_event(
            event_type="failed_login",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default"
        )

class TestAuditAction:
    """Test audit action enum."""
    
    def test_audit_action_values(self):
        """Test audit action enum values."""
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.USER_CREATE.value == "user_create"
        assert AuditAction.DATA_ACCESS.value == "data_access"
        assert AuditAction.SECURITY_EVENT.value == "security_event"

class TestAuditSeverity:
    """Test audit severity enum."""
    
    def test_audit_severity_values(self):
        """Test audit severity enum values."""
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
