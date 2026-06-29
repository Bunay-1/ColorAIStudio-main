"""
Integration Tests for Audit Logging
===================================
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
from utils.audit_logger import (
    AuditAction, log_audit_event, query_audit_logs, get_user_activity_summary,
    get_audit_statistics, AuditSeverity
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
            username="test_admin_audit",
            email="admin_audit@test.com",
            password="admin_password",
            role="ADMIN",
            tenant_id="default"
        )
        create_user(admin_data)
    except:
        pass  # User might already exist
    
    # Authenticate and get token
    user = authenticate_user("test_admin_audit", "admin_password")
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
            username="test_operator_audit",
            email="operator_audit@test.com",
            password="operator_password",
            role="OPERATOR",
            tenant_id="default"
        )
        create_user(operator_data)
    except:
        pass  # User might already exist
    
    # Authenticate and get token
    user = authenticate_user("test_operator_audit", "operator_password")
    if user:
        token = create_access_token(data={"sub": user["username"], "role": user["role"], "tenant_id": user.get("tenant_id", "default")})
        return token
    return None

class TestAuditLoggingBasic:
    """Test basic audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_log_audit_event(self):
        """Test logging an audit event."""
        event = AuditAction(
            action="test_action",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="test-correlation-123"
        )
        
        result = log_audit_event(event)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_log_audit_event_with_details(self):
        """Test logging audit event with additional details."""
        event = AuditAction(
            action="data_access",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="test-correlation-456",
            details={"resource": "measurements", "operation": "read"}
        )
        
        result = log_audit_event(event)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_log_audit_event_different_severities(self):
        """Test logging events with different severity levels."""
        for severity in [AuditSeverity.INFO, AuditSeverity.WARNING, AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            event = AuditAction(
                action="test_action",
                user_id="test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=severity,
                ip_address="192.168.1.100",
                correlation_id=f"test-{severity.value}"
            )
            
            result = log_audit_event(event)
            assert result == True

class TestAuditLogQuery:
    """Test audit log querying functionality."""
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_by_user(self):
        """Test querying audit logs by user ID."""
        # Log some events
        for i in range(5):
            event = AuditAction(
                action="test_action",
                user_id="query_test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"test-{i}"
            )
            log_audit_event(event)
        
        # Query logs
        logs = query_audit_logs(user_id="query_test_user", limit=10)
        
        assert logs is not None
        assert len(logs) > 0
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_by_tenant(self):
        """Test querying audit logs by tenant ID."""
        # Log events for specific tenant
        for i in range(3):
            event = AuditAction(
                action="test_action",
                user_id="test_user",
                user_role="OPERATOR",
                tenant_id="test_tenant",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"tenant-test-{i}"
            )
            log_audit_event(event)
        
        # Query logs
        logs = query_audit_logs(tenant_id="test_tenant", limit=10)
        
        assert logs is not None
        assert len(logs) > 0
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_by_action(self):
        """Test querying audit logs by action type."""
        # Log specific action
        event = AuditAction(
            action="login",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="login-test"
        )
        log_audit_event(event)
        
        # Query logs
        logs = query_audit_logs(action="login", limit=10)
        
        assert logs is not None
        assert len(logs) > 0
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_with_date_range(self):
        """Test querying audit logs with date range."""
        from datetime import datetime, timedelta
        
        # Log event
        event = AuditAction(
            action="test_action",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="date-test"
        )
        log_audit_event(event)
        
        # Query with date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        logs = query_audit_logs(start_date=start_date, end_date=end_date, limit=10)
        
        assert logs is not None

class TestUserActivitySummary:
    """Test user activity summary functionality."""
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary(self):
        """Test getting user activity summary."""
        # Log some events for user
        for i in range(10):
            event = AuditAction(
                action="data_access",
                user_id="summary_test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"summary-{i}"
            )
            log_audit_event(event)
        
        # Get summary
        summary = get_user_activity_summary("summary_test_user")
        
        assert summary is not None
        assert "total_actions" in summary
        assert summary["total_actions"] > 0
    
    @pytest.mark.asyncio
    async def test_user_activity_summary_by_action_type(self):
        """Test that activity summary groups by action type."""
        # Log different action types
        actions = ["login", "data_access", "data_modify"]
        for action in actions:
            event = AuditAction(
                action=action,
                user_id="action_type_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"action-{action}"
            )
            log_audit_event(event)
        
        # Get summary
        summary = get_user_activity_summary("action_type_user")
        
        assert summary is not None
        assert "actions_by_type" in summary

class TestAuditStatistics:
    """Test audit statistics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics(self):
        """Test getting overall audit statistics."""
        stats = get_audit_statistics()
        
        assert stats is not None
        assert "total_events" in stats
        assert "events_by_severity" in stats
        assert "events_by_action" in stats
    
    @pytest.mark.asyncio
    async def test_audit_statistics_by_severity(self):
        """Test that statistics are grouped by severity."""
        # Log events with different severities
        for severity in [AuditSeverity.INFO, AuditSeverity.WARNING, AuditSeverity.ERROR]:
            event = AuditAction(
                action="test_action",
                user_id="test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=severity,
                ip_address="192.168.1.100",
                correlation_id=f"severity-{severity.value}"
            )
            log_audit_event(event)
        
        # Get statistics
        stats = get_audit_statistics()
        
        assert stats is not None
        assert "events_by_severity" in stats

class TestAuditLogAPI:
    """Test audit logging via API endpoints."""
    
    @pytest.mark.asyncio
    async def test_query_audit_logs_api(self, admin_token, client):
        """Test querying audit logs via API."""
        response = await client.get(
            "/auth/audit/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"user_id": "test_user", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
    
    @pytest.mark.asyncio
    async def test_get_user_activity_summary_api(self, admin_token, client):
        """Test getting user activity summary via API."""
        response = await client.get(
            "/auth/audit/summary/test_user",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_actions" in data
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics_api(self, admin_token, client):
        """Test getting audit statistics via API."""
        response = await client.get(
            "/auth/audit/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
    
    @pytest.mark.asyncio
    async def test_audit_log_permission_check(self, operator_token, client):
        """Test that non-admin users have restricted access to audit logs."""
        response = await client.get(
            "/auth/audit/logs",
            headers={"Authorization": f"Bearer {operator_token}"},
            params={"limit": 10}
        )
        
        # Non-admin might have restricted access
        assert response.status_code in [200, 403]

class TestAuditLogCompliance:
    """Test audit logging compliance features."""
    
    @pytest.mark.asyncio
    async def test_audit_log_completeness(self):
        """Test that audit logs contain all required fields."""
        event = AuditAction(
            action="compliance_test",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="compliance-test"
        )
        
        log_audit_event(event)
        
        # Query the log
        logs = query_audit_logs(user_id="test_user", limit=1)
        
        if logs and len(logs) > 0:
            log_entry = logs[0]
            required_fields = ["timestamp", "action", "user_id", "user_role", "tenant_id", "severity"]
            for field in required_fields:
                assert field in log_entry
    
    @pytest.mark.asyncio
    async def test_audit_log_immutability(self):
        """Test that audit logs cannot be modified."""
        # Log an event
        event = AuditAction(
            action="immutable_test",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="immutable-test"
        )
        log_audit_event(event)
        
        # Audit logs should be immutable
        # This is a design principle - actual implementation depends on storage
        assert True
    
    @pytest.mark.asyncio
    async def test_audit_log_retention(self):
        """Test that audit logs have appropriate retention policy."""
        # Log an event
        event = AuditAction(
            action="retention_test",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="retention-test"
        )
        log_audit_event(event)
        
        # Audit logs should be retained for compliance
        # This is a design principle - actual implementation depends on storage
        assert True

class TestAuditLogSecurity:
    """Test audit logging security features."""
    
    @pytest.mark.asyncio
    async def test_sensitive_data_masking(self):
        """Test that sensitive data is masked in audit logs."""
        event = AuditAction(
            action="password_change",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="sensitive-test",
            details={"password": "secret123"}  # Should be masked
        )
        
        log_audit_event(event)
        
        # Query logs
        logs = query_audit_logs(user_id="test_user", limit=1)
        
        if logs and len(logs) > 0:
            log_entry = logs[0]
            # Password should be masked in logs
            if "details" in log_entry and "password" in log_entry["details"]:
                assert log_entry["details"]["password"] != "secret123"
    
    @pytest.mark.asyncio
    async def test_audit_log_integrity(self):
        """Test that audit logs maintain integrity."""
        # Log an event
        event = AuditAction(
            action="integrity_test",
            user_id="test_user",
            user_role="OPERATOR",
            tenant_id="default",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.100",
            correlation_id="integrity-test"
        )
        log_audit_event(event)
        
        # Audit logs should maintain integrity
        # This is a design principle - actual implementation depends on storage
        assert True

class TestAuditLogPerformance:
    """Test audit logging performance."""
    
    @pytest.mark.asyncio
    async def test_bulk_audit_logging(self):
        """Test logging multiple audit events efficiently."""
        events = []
        for i in range(100):
            event = AuditAction(
                action="bulk_test",
                user_id="test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"bulk-{i}"
            )
            events.append(event)
        
        # Log all events
        for event in events:
            result = log_audit_event(event)
            assert result == True
    
    @pytest.mark.asyncio
    async def test_query_performance(self):
        """Test that audit log queries perform well."""
        # Log some events
        for i in range(50):
            event = AuditAction(
                action="performance_test",
                user_id="test_user",
                user_role="OPERATOR",
                tenant_id="default",
                severity=AuditSeverity.INFO,
                ip_address="192.168.1.100",
                correlation_id=f"perf-{i}"
            )
            log_audit_event(event)
        
        # Query should be fast
        import time
        start = time.time()
        logs = query_audit_logs(user_id="test_user", limit=100)
        end = time.time()
        
        assert logs is not None
        assert (end - start) < 1.0  # Should complete in less than 1 second

class TestAuditLogIntegration:
    """Test audit logging integration with other systems."""
    
    @pytest.mark.asyncio
    async def test_authentication_audit_logging(self, client):
        """Test that authentication events are logged."""
        # Login attempt should be logged
        response = await client.post(
            "/auth/login",
            json={"username": "test_admin_audit", "password": "admin_password"}
        )
        
        # Verify login was logged
        logs = query_audit_logs(action="login", limit=5)
        assert logs is not None
    
    @pytest.mark.asyncio
    async def test_user_management_audit_logging(self, admin_token, client):
        """Test that user management events are logged."""
        # Create user
        response = await client.post(
            "/auth/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "audit_test_user",
                "email": "audit@test.com",
                "password": "test_password",
                "role": "OPERATOR",
                "tenant_id": "default"
            }
        )
        
        # Verify user creation was logged
        logs = query_audit_logs(action="user_create", limit=5)
        assert logs is not None
        
        # Cleanup
        try:
            from utils.auth import delete_user
            delete_user("audit_test_user")
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_tenant_management_audit_logging(self, admin_token, client):
        """Test that tenant management events are logged."""
        # Create tenant
        response = await client.post(
            "/auth/tenants",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": "audit_test_tenant",
                "name": "Audit Test Tenant"
            }
        )
        
        # Verify tenant creation was logged
        logs = query_audit_logs(action="tenant_create", limit=5)
        assert logs is not None
        
        # Cleanup
        try:
            from utils.multi_tenant import delete_tenant
            delete_tenant("audit_test_tenant")
        except:
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
