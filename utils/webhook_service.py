"""
Webhook Service for ICAP Enterprise
===================================
Webhook management and delivery for external integrations.
"""

import asyncio
import httpx
import logging
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import os

logger = logging.getLogger("Webhook_Service")

class WebhookEvent(str, Enum):
    """Webhook event types."""
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    TENANT_CREATED = "tenant.created"
    TENANT_DELETED = "tenant.deleted"
    COLOR_ANALYSIS = "color.analysis"
    VISION_ANALYSIS = "vision.analysis"
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"
    SYSTEM_ERROR = "system.error"

class WebhookStatus(str, Enum):
    """Webhook status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"

@dataclass
class Webhook:
    """Webhook configuration."""
    id: str
    url: str
    events: List[WebhookEvent]
    secret: Optional[str] = None
    headers: Dict[str, str] = None
    status: WebhookStatus = WebhookStatus.ACTIVE
    tenant_id: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    last_triggered: Optional[str] = None
    failure_count: int = 0
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

@dataclass
class WebhookDelivery:
    """Webhook delivery record."""
    id: str
    webhook_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status: str
    status_code: Optional[int] = None
    response: Optional[str] = None
    error: Optional[str] = None
    attempted_at: str = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.attempted_at is None:
            self.attempted_at = datetime.now().isoformat()

class WebhookService:
    """Main webhook service for ICAP Enterprise."""
    
    def __init__(self, db_path: str = None):
        """Initialize webhook service."""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "icap.db")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.event_handlers: Dict[WebhookEvent, List[Callable]] = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize webhook database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Webhooks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhooks (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    events TEXT NOT NULL,
                    secret TEXT,
                    headers TEXT,
                    status TEXT NOT NULL,
                    tenant_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_triggered TEXT,
                    failure_count INTEGER DEFAULT 0
                )
            ''')
            
            # Webhook deliveries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id TEXT PRIMARY KEY,
                    webhook_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    status_code INTEGER,
                    response TEXT,
                    error TEXT,
                    attempted_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Webhook database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize webhook database: {e}")
    
    def create_webhook(
        self,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        tenant_id: Optional[str] = None
    ) -> Webhook:
        """
        Create a new webhook.
        
        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Optional secret for signature verification
            headers: Optional custom headers
            tenant_id: Optional tenant ID
        
        Returns:
            Created webhook
        """
        try:
            webhook = Webhook(
                id=f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                url=url,
                events=events,
                secret=secret,
                headers=headers,
                tenant_id=tenant_id
            )
            
            self._store_webhook(webhook)
            logger.info(f"Webhook created: {webhook.id}")
            return webhook
            
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            raise
    
    def _store_webhook(self, webhook: Webhook):
        """Store webhook in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO webhooks
                (id, url, events, secret, headers, status, tenant_id, created_at, updated_at, last_triggered, failure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                webhook.id,
                webhook.url,
                json.dumps([e.value for e in webhook.events]),
                webhook.secret,
                json.dumps(webhook.headers),
                webhook.status.value,
                webhook.tenant_id,
                webhook.created_at,
                webhook.updated_at,
                webhook.last_triggered,
                webhook.failure_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store webhook: {e}")
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, events, secret, headers, status, tenant_id, created_at, updated_at, last_triggered, failure_count
                FROM webhooks
                WHERE id = ?
            ''', (webhook_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Webhook(
                    id=row[0],
                    url=row[1],
                    events=[WebhookEvent(e) for e in json.loads(row[2])],
                    secret=row[3],
                    headers=json.loads(row[4]),
                    status=WebhookStatus(row[5]),
                    tenant_id=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    last_triggered=row[9],
                    failure_count=row[10]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get webhook: {e}")
            return None
    
    def list_webhooks(
        self,
        event: Optional[WebhookEvent] = None,
        tenant_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None
    ) -> List[Webhook]:
        """
        List webhooks.
        
        Args:
            event: Filter by event
            tenant_id: Filter by tenant ID
            status: Filter by status
        
        Returns:
            List of webhooks
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM webhooks WHERE 1=1'
            params = []
            
            if event:
                query += ' AND events LIKE ?'
                params.append(f'%{event.value}%')
            
            if tenant_id:
                query += ' AND tenant_id = ?'
                params.append(tenant_id)
            
            if status:
                query += ' AND status = ?'
                params.append(status.value)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            webhooks = []
            for row in rows:
                webhooks.append(Webhook(
                    id=row[0],
                    url=row[1],
                    events=[WebhookEvent(e) for e in json.loads(row[2])],
                    secret=row[3],
                    headers=json.loads(row[4]),
                    status=WebhookStatus(row[5]),
                    tenant_id=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    last_triggered=row[9],
                    failure_count=row[10]
                ))
            
            conn.close()
            return webhooks
            
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            return []
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM webhooks WHERE id = ?', (webhook_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def trigger_event(
        self,
        event: WebhookEvent,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> List[WebhookDelivery]:
        """
        Trigger an event to all subscribed webhooks.
        
        Args:
            event: Event type
            payload: Event payload
            tenant_id: Optional tenant ID for filtering
        
        Returns:
            List of delivery records
        """
        try:
            # Get webhooks that subscribe to this event
            webhooks = self.list_webhooks(event=event, tenant_id=tenant_id, status=WebhookStatus.ACTIVE)
            
            deliveries = []
            
            for webhook in webhooks:
                delivery = await self._deliver_webhook(webhook, event, payload)
                deliveries.append(delivery)
            
            logger.info(f"Event {event.value} triggered to {len(webhooks)} webhooks")
            return deliveries
            
        except Exception as e:
            logger.error(f"Failed to trigger event: {e}")
            return []
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event: WebhookEvent,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """
        Deliver webhook to URL.
        
        Args:
            webhook: Webhook configuration
            event: Event type
            payload: Event payload
        
        Returns:
            Delivery record
        """
        delivery_id = f"delivery_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Prepare payload
            webhook_payload = {
                "id": delivery_id,
                "event": event.value,
                "timestamp": datetime.now().isoformat(),
                "data": payload
            }
            
            # Add signature if secret is configured
            headers = webhook.headers.copy()
            if webhook.secret:
                signature = self._generate_signature(webhook_payload, webhook.secret)
                headers["X-Webhook-Signature"] = signature
            
            headers["Content-Type"] = "application/json"
            
            # Send webhook
            response = await self.client.post(
                webhook.url,
                json=webhook_payload,
                headers=headers
            )
            
            # Update webhook
            webhook.last_triggered = datetime.now().isoformat()
            webhook.failure_count = 0
            webhook.updated_at = datetime.now().isoformat()
            self._update_webhook(webhook)
            
            # Create delivery record
            delivery = WebhookDelivery(
                id=delivery_id,
                webhook_id=webhook.id,
                event=event,
                payload=webhook_payload,
                status="success",
                status_code=response.status_code,
                response=response.text[:1000] if response.text else None,
                attempted_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat()
            )
            
            self._store_delivery(delivery)
            logger.info(f"Webhook delivered successfully: {webhook.id}")
            
        except Exception as e:
            # Update webhook failure count
            webhook.failure_count += 1
            webhook.updated_at = datetime.now().isoformat()
            
            # Disable webhook after too many failures
            if webhook.failure_count >= 5:
                webhook.status = WebhookStatus.FAILED
            
            self._update_webhook(webhook)
            
            # Create failed delivery record
            delivery = WebhookDelivery(
                id=delivery_id,
                webhook_id=webhook.id,
                event=event,
                payload=payload,
                status="failed",
                error=str(e),
                attempted_at=datetime.now().isoformat()
            )
            
            self._store_delivery(delivery)
            logger.error(f"Webhook delivery failed: {webhook.id} - {e}")
        
        return delivery
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def _update_webhook(self, webhook: Webhook):
        """Update webhook in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE webhooks
                SET url = ?, events = ?, secret = ?, headers = ?, status = ?, updated_at = ?, last_triggered = ?, failure_count = ?
                WHERE id = ?
            ''', (
                webhook.url,
                json.dumps([e.value for e in webhook.events]),
                webhook.secret,
                json.dumps(webhook.headers),
                webhook.status.value,
                webhook.updated_at,
                webhook.last_triggered,
                webhook.failure_count,
                webhook.id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update webhook: {e}")
    
    def _store_delivery(self, delivery: WebhookDelivery):
        """Store delivery record in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO webhook_deliveries
                (id, webhook_id, event, payload, status, status_code, response, error, attempted_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                delivery.id,
                delivery.webhook_id,
                delivery.event.value,
                json.dumps(delivery.payload),
                delivery.status,
                delivery.status_code,
                delivery.response,
                delivery.error,
                delivery.attempted_at,
                delivery.completed_at
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store delivery: {e}")
    
    def get_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Get delivery records for a webhook."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, webhook_id, event, payload, status, status_code, response, error, attempted_at, completed_at
                FROM webhook_deliveries
                WHERE webhook_id = ?
                ORDER BY attempted_at DESC
                LIMIT ?
            ''', (webhook_id, limit))
            
            rows = cursor.fetchall()
            
            deliveries = []
            for row in rows:
                deliveries.append(WebhookDelivery(
                    id=row[0],
                    webhook_id=row[1],
                    event=WebhookEvent(row[2]),
                    payload=json.loads(row[3]),
                    status=row[4],
                    status_code=row[5],
                    response=row[6],
                    error=row[7],
                    attempted_at=row[8],
                    completed_at=row[9]
                ))
            
            conn.close()
            return deliveries
            
        except Exception as e:
            logger.error(f"Failed to get webhook deliveries: {e}")
            return []
    
    def register_event_handler(self, event: WebhookEvent, handler: Callable):
        """Register a custom event handler."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def process_event(self, event: WebhookEvent, payload: Dict[str, Any]):
        """Process event through registered handlers."""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    await handler(payload)
                except Exception as e:
                    logger.error(f"Event handler error for {event.value}: {e}")

# Global webhook service instance
webhook_service = WebhookService()
