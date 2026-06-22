"""
Real-time Notifications and Alerts Service for ICAP Enterprise
==============================================================
Comprehensive notification system with real-time delivery, alert management, and user preferences.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import sqlite3
import websockets
from fastapi import WebSocket
import os

logger = logging.getLogger("Notification_Service")

class NotificationSeverity(str, Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationType(str, Enum):
    """Notification types."""
    SYSTEM = "system"
    USER = "user"
    TENANT = "tenant"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"

class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"

@dataclass
class Notification:
    """Notification data structure."""
    id: str
    type: NotificationType
    severity: NotificationSeverity
    title: str
    message: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    channels: List[NotificationChannel] = None
    metadata: Dict[str, Any] = None
    created_at: str = None
    expires_at: Optional[str] = None
    read: bool = False
    read_at: Optional[str] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [NotificationChannel.WEBSOCKET]
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    severity: NotificationSeverity
    title: str
    description: str
    source: str
    condition: str
    threshold: float
    current_value: float
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None
    created_at: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NotificationPreference:
    """User notification preferences."""
    user_id: str
    enabled: bool = True
    channels: Dict[str, bool] = None
    severity_filter: List[str] = None
    type_filter: List[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = {
                "websocket": True,
                "email": False,
                "slack": False,
                "webhook": False
            }
        if self.severity_filter is None:
            self.severity_filter = ["info", "warning", "error", "critical"]
        if self.type_filter is None:
            self.type_filter = ["system", "user", "tenant", "security", "performance", "compliance"]

class NotificationService:
    """Main notification service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize notification service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self.active_connections: Dict[str, WebSocket] = {}
        self.alert_rules: List[Dict] = []
        self._init_database()
        self._load_alert_rules()
    
    def _init_database(self):
        """Initialize notification database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    user_id TEXT,
                    tenant_id TEXT,
                    channels TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    read BOOLEAN DEFAULT FALSE,
                    read_at TEXT
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold REAL,
                    current_value REAL,
                    user_id TEXT,
                    tenant_id TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Notification preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    user_id TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    channels TEXT,
                    severity_filter TEXT,
                    type_filter TEXT,
                    quiet_hours_start TEXT,
                    quiet_hours_end TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Notification database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize notification database: {e}")
    
    def _load_alert_rules(self):
        """Load alert rules from configuration."""
        # Default alert rules
        self.alert_rules = [
            {
                "id": "high_cpu_usage",
                "name": "High CPU Usage",
                "condition": "cpu_usage > 80",
                "severity": "warning",
                "threshold": 80.0,
                "enabled": True
            },
            {
                "id": "high_memory_usage",
                "name": "High Memory Usage",
                "condition": "memory_usage > 85",
                "severity": "warning",
                "threshold": 85.0,
                "enabled": True
            },
            {
                "id": "high_error_rate",
                "name": "High Error Rate",
                "condition": "error_rate > 5",
                "severity": "error",
                "threshold": 5.0,
                "enabled": True
            },
            {
                "id": "disk_space_low",
                "name": "Disk Space Low",
                "condition": "disk_usage > 90",
                "severity": "critical",
                "threshold": 90.0,
                "enabled": True
            }
        ]
    
    async def send_notification(
        self,
        notification: Notification
    ) -> bool:
        """
        Send notification to user(s).
        
        Args:
            notification: Notification object
        
        Returns:
            True if sent successfully
        """
        try:
            # Store notification in database
            self._store_notification(notification)
            
            # Send via enabled channels
            for channel in notification.channels:
                if channel == NotificationChannel.WEBSOCKET:
                    await self._send_via_websocket(notification)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_via_email(notification)
                elif channel == NotificationChannel.SLACK:
                    await self._send_via_slack(notification)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_via_webhook(notification)
            
            logger.info(f"Notification sent: {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _store_notification(self, notification: Notification):
        """Store notification in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications 
                (id, type, severity, title, message, user_id, tenant_id, channels, metadata, created_at, expires_at, read, read_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                notification.id,
                notification.type.value,
                notification.severity.value,
                notification.title,
                notification.message,
                notification.user_id,
                notification.tenant_id,
                json.dumps([c.value for c in notification.channels]),
                json.dumps(notification.metadata),
                notification.created_at,
                notification.expires_at,
                notification.read,
                notification.read_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
    
    async def _send_via_websocket(self, notification: Notification):
        """Send notification via WebSocket."""
        if notification.user_id and notification.user_id in self.active_connections:
            try:
                ws = self.active_connections[notification.user_id]
                await ws.send_json(asdict(notification))
                logger.info(f"WebSocket notification sent to {notification.user_id}")
            except Exception as e:
                logger.error(f"Failed to send WebSocket notification: {e}")
    
    async def _send_via_email(self, notification: Notification):
        """Send notification via email."""
        # Implementation would use SMTP or email service
        logger.info(f"Email notification: {notification.title}")
    
    async def _send_via_slack(self, notification: Notification):
        """Send notification via Slack webhook."""
        # Implementation would use Slack webhook
        logger.info(f"Slack notification: {notification.title}")
    
    async def _send_via_webhook(self, notification: Notification):
        """Send notification via custom webhook."""
        # Implementation would send to configured webhook URL
        logger.info(f"Webhook notification: {notification.title}")
    
    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
        
        Returns:
            List of notifications
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, type, severity, title, message, user_id, tenant_id, 
                       channels, metadata, created_at, expires_at, read, read_at
                FROM notifications
                WHERE user_id = ?
            '''
            
            if unread_only:
                query += ' AND read = FALSE'
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            cursor.execute(query, (user_id, limit))
            rows = cursor.fetchall()
            
            notifications = []
            for row in rows:
                notification = Notification(
                    id=row[0],
                    type=NotificationType(row[1]),
                    severity=NotificationSeverity(row[2]),
                    title=row[3],
                    message=row[4],
                    user_id=row[5],
                    tenant_id=row[6],
                    channels=[NotificationChannel(c) for c in json.loads(row[7])],
                    metadata=json.loads(row[8]),
                    created_at=row[9],
                    expires_at=row[10],
                    read=row[11],
                    read_at=row[12]
                )
                notifications.append(notification)
            
            conn.close()
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE notifications
                SET read = TRUE, read_at = ?
                WHERE id = ? AND user_id = ?
            ''', (datetime.now().isoformat(), notification_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def create_alert(
        self,
        alert: Alert
    ) -> bool:
        """
        Create and store an alert.
        
        Args:
            alert: Alert object
        
        Returns:
            True if created successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts
                (id, severity, title, description, source, condition, threshold, current_value,
                 user_id, tenant_id, acknowledged, acknowledged_by, acknowledged_at,
                 resolved, resolved_at, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.severity.value,
                alert.title,
                alert.description,
                alert.source,
                alert.condition,
                alert.threshold,
                alert.current_value,
                alert.user_id,
                alert.tenant_id,
                alert.acknowledged,
                alert.acknowledged_by,
                alert.acknowledged_at,
                alert.resolved,
                alert.resolved_at,
                alert.created_at,
                json.dumps(alert.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            # Send notification for alert
            notification = Notification(
                id=f"notif_{alert.id}",
                type=NotificationType.SYSTEM,
                severity=alert.severity,
                title=alert.title,
                description=alert.description,
                user_id=alert.user_id,
                tenant_id=alert.tenant_id,
                metadata={"alert_id": alert.id}
            )
            asyncio.create_task(self.send_notification(notification))
            
            logger.info(f"Alert created: {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return False
    
    def get_active_alerts(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        unresolved_only: bool = True
    ) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            unresolved_only: Only return unresolved alerts
        
        Returns:
            List of alerts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM alerts WHERE 1=1'
            params = []
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if tenant_id:
                query += ' AND tenant_id = ?'
                params.append(tenant_id)
            
            if unresolved_only:
                query += ' AND resolved = FALSE'
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alert = Alert(
                    id=row[0],
                    severity=NotificationSeverity(row[1]),
                    title=row[2],
                    description=row[3],
                    source=row[4],
                    condition=row[5],
                    threshold=row[6],
                    current_value=row[7],
                    user_id=row[8],
                    tenant_id=row[9],
                    acknowledged=row[10],
                    acknowledged_by=row[11],
                    acknowledged_at=row[12],
                    resolved=row[13],
                    resolved_at=row[14],
                    created_at=row[15],
                    metadata=json.loads(row[16])
                )
                alerts.append(alert)
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str
    ) -> bool:
        """Acknowledge an alert."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts
                SET acknowledged = TRUE, acknowledged_by = ?, acknowledged_at = ?
                WHERE id = ?
            ''', (user_id, datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def resolve_alert(
        self,
        alert_id: str
    ) -> bool:
        """Resolve an alert."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts
                SET resolved = TRUE, resolved_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def set_user_preferences(
        self,
        preferences: NotificationPreference
    ) -> bool:
        """Set user notification preferences."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO notification_preferences
                (user_id, enabled, channels, severity_filter, type_filter, quiet_hours_start, quiet_hours_end)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                preferences.user_id,
                preferences.enabled,
                json.dumps(preferences.channels),
                json.dumps(preferences.severity_filter),
                json.dumps(preferences.type_filter),
                preferences.quiet_hours_start,
                preferences.quiet_hours_end
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user preferences: {e}")
            return False
    
    def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, enabled, channels, severity_filter, type_filter, quiet_hours_start, quiet_hours_end
                FROM notification_preferences
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return NotificationPreference(
                    user_id=row[0],
                    enabled=row[1],
                    channels=json.loads(row[2]),
                    severity_filter=json.loads(row[3]),
                    type_filter=json.loads(row[4]),
                    quiet_hours_start=row[5],
                    quiet_hours_end=row[6]
                )
            
            # Return default preferences
            return NotificationPreference(user_id=user_id)
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    def register_websocket(self, user_id: str, websocket: WebSocket):
        """Register WebSocket connection for user."""
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket registered for user: {user_id}")
    
    def unregister_websocket(self, user_id: str):
        """Unregister WebSocket connection for user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket unregistered for user: {user_id}")
    
    async def check_alert_conditions(self, metrics: Dict[str, float]):
        """
        Check alert conditions against current metrics.
        
        Args:
            metrics: Dictionary of metric names and values
        """
        for rule in self.alert_rules:
            if not rule["enabled"]:
                continue
            
            # Evaluate condition
            try:
                # Simple condition evaluation
                if rule["condition"] in metrics:
                    current_value = metrics[rule["condition"]]
                    if current_value > rule["threshold"]:
                        # Create alert
                        alert = Alert(
                            id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rule['id']}",
                            severity=NotificationSeverity(rule["severity"]),
                            title=rule["name"],
                            description=f"{rule['name']}: {rule['condition']} is {current_value} (threshold: {rule['threshold']})",
                            source="system",
                            condition=rule["condition"],
                            threshold=rule["threshold"],
                            current_value=current_value
                        )
                        self.create_alert(alert)
            except Exception as e:
                logger.error(f"Failed to evaluate alert rule {rule['id']}: {e}")

# Global notification service instance
notification_service = NotificationService()
