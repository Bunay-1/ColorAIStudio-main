"""
Audit Logging for ICAP
========================
Comprehensive audit logging for compliance and security.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import threading

logger = logging.getLogger("AuditLogger")

class AuditAction(Enum):
    """Audit action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    TENANT_CREATE = "tenant_create"
    TENANT_UPDATE = "tenant_update"
    TENANT_DELETE = "tenant_delete"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"
    SECURITY_EVENT = "security_event"

class AuditSeverity(Enum):
    """Audit severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditLog:
    """Audit log entry."""
    
    def __init__(
        self,
        action: AuditAction,
        user_id: str,
        user_role: str,
        tenant_id: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.timestamp = datetime.utcnow().isoformat()
        self.action = action.value
        self.user_id = user_id
        self.user_role = user_role
        self.tenant_id = tenant_id
        self.severity = severity.value
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.correlation_id = correlation_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "tenant_id": self.tenant_id,
            "severity": self.severity,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "correlation_id": self.correlation_id
        }
    
    def to_json(self) -> str:
        """Convert audit log to JSON string."""
        return json.dumps(self.to_dict())

class AuditLogger:
    """Audit logger for tracking user actions."""
    
    def __init__(self, log_file: str = "AuditTrail/audit.log"):
        self.log_file = log_file
        self._lock = threading.Lock()
        self._ensure_log_directory()
        
        # Configure audit logger
        self.logger = logging.getLogger("AuditTrail")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # JSON formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _ensure_log_directory(self):
        """Ensure log directory exists."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, audit_log: AuditLog):
        """
        Log an audit event.
        
        Args:
            audit_log: AuditLog instance to log
        """
        with self._lock:
            try:
                self.logger.info(audit_log.to_json())
                
                # Also log to application logger for immediate visibility
                log_message = f"[AUDIT] {audit_log.action} by {audit_log.user_id} ({audit_log.user_role}) in tenant {audit_log.tenant_id}"
                if audit_log.severity == AuditSeverity.CRITICAL.value:
                    logger.critical(log_message)
                elif audit_log.severity == AuditSeverity.ERROR.value:
                    logger.error(log_message)
                elif audit_log.severity == AuditSeverity.WARNING.value:
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
                    
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
    
    def log_user_action(
        self,
        action: AuditAction,
        user_id: str,
        user_role: str,
        tenant_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log a user action.
        
        Args:
            action: Type of action
            user_id: User ID
            user_role: User role
            tenant_id: Tenant ID
            details: Additional details
            ip_address: IP address
            correlation_id: Correlation ID for request tracing
        """
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            user_role=user_role,
            tenant_id=tenant_id,
            details=details,
            ip_address=ip_address,
            correlation_id=correlation_id
        )
        self.log(audit_log)
    
    def log_data_access(
        self,
        user_id: str,
        user_role: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str = "read",
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log data access event.
        
        Args:
            user_id: User ID
            user_role: User role
            tenant_id: Tenant ID
            resource_type: Type of resource accessed
            resource_id: Resource ID
            access_type: Type of access (read, write, delete)
            ip_address: IP address
            correlation_id: Correlation ID
        """
        audit_log = AuditLog(
            action=AuditAction.DATA_ACCESS,
            user_id=user_id,
            user_role=user_role,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"access_type": access_type},
            ip_address=ip_address,
            correlation_id=correlation_id
        )
        self.log(audit_log)
    
    def log_security_event(
        self,
        event_type: str,
        user_id: str,
        user_role: str,
        tenant_id: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            user_id: User ID
            user_role: User role
            tenant_id: Tenant ID
            severity: Severity level
            details: Additional details
            ip_address: IP address
            correlation_id: Correlation ID
        """
        audit_log = AuditLog(
            action=AuditAction.SECURITY_EVENT,
            user_id=user_id,
            user_role=user_role,
            tenant_id=tenant_id,
            severity=severity,
            details={"event_type": event_type, **(details or {})},
            ip_address=ip_address,
            correlation_id=correlation_id
        )
        self.log(audit_log)
    
    def log_error(
        self,
        error_message: str,
        user_id: str,
        user_role: str,
        tenant_id: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log an error event.
        
        Args:
            error_message: Error message
            user_id: User ID
            user_role: User role
            tenant_id: Tenant ID
            details: Additional details
            correlation_id: Correlation ID
        """
        audit_log = AuditLog(
            action=AuditAction.ERROR,
            user_id=user_id,
            user_role=user_role,
            tenant_id=tenant_id,
            severity=AuditSeverity.ERROR,
            details={"error_message": error_message, **(details or {})},
            correlation_id=correlation_id
        )
        self.log(audit_log)
    
    def query_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs.
        
        Args:
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            action: Filter by action
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of results
            
        Returns:
            List of matching audit logs
        """
        results = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        if tenant_id and log_entry.get("tenant_id") != tenant_id:
                            continue
                        if action and log_entry.get("action") != action:
                            continue
                        if start_date and log_entry.get("timestamp") < start_date:
                            continue
                        if end_date and log_entry.get("timestamp") > end_date:
                            continue
                        
                        results.append(log_entry)
                        
                        if len(results) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file}")
        except Exception as e:
            logger.error(f"Error querying audit logs: {e}")
        
        return results
    
    def get_user_activity_summary(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get activity summary for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID (optional)
            days: Number of days to look back
            
        Returns:
            Activity summary
        """
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow().isoformat()
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        logs = self.query_logs(
            user_id=user_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        # Calculate summary
        action_counts = {}
        for log in logs:
            action = log.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "period_days": days,
            "total_actions": len(logs),
            "action_breakdown": action_counts,
            "first_action": logs[-1]["timestamp"] if logs else None,
            "last_action": logs[0]["timestamp"] if logs else None
        }

# Global audit logger instance
audit_logger = AuditLogger()

# Convenience functions
def log_audit_event(
    action: AuditAction,
    user_id: str,
    user_role: str,
    tenant_id: str,
    **kwargs
):
    """Convenience function to log an audit event."""
    audit_logger.log_user_action(
        action=action,
        user_id=user_id,
        user_role=user_role,
        tenant_id=tenant_id,
        **kwargs
    )

def log_security_event(
    event_type: str,
    user_id: str,
    user_role: str,
    tenant_id: str,
    **kwargs
):
    """Convenience function to log a security event."""
    audit_logger.log_security_event(
        event_type=event_type,
        user_id=user_id,
        user_role=user_role,
        tenant_id=tenant_id,
        **kwargs
    )
