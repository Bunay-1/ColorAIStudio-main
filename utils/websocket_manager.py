"""
WebSocket Manager for Real-Time Data Streaming
===============================================
Manages WebSocket connections for real-time data streaming to clients.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from datetime import datetime
from enum import Enum

logger = logging.getLogger("WebSocketManager")

class WebSocketEventType(str, Enum):
    """WebSocket event types."""
    MEASUREMENT = "measurement"
    ALERT = "alert"
    SYSTEM_STATUS = "system_status"
    QUALITY_METRIC = "quality_metric"
    VISION_RESULT = "vision_result"
    RAG_RESULT = "rag_result"
    IOT_DATA = "iot_data"
    NOTIFICATION = "notification"

class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """
    
    def __init__(self):
        # Store active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Store subscriptions by event type
        self.subscriptions: Dict[str, Set[str]] = {
            event_type.value: set() for event_type in WebSocketEventType
        }
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            client_id: Unique client identifier
            metadata: Optional connection metadata (user_id, tenant_id, etc.)
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = metadata or {}
        
        # Subscribe to all events by default
        for event_type in WebSocketEventType:
            self.subscriptions[event_type.value].add(client_id)
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Send welcome message
        await self.send_personal_message(
            client_id,
            {
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket connection established"
            }
        )
    
    def disconnect(self, client_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: Client identifier to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all subscriptions
        for event_type in self.subscriptions:
            self.subscriptions[event_type].discard(client_id)
        
        # Remove metadata
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific client.
        
        Args:
            client_id: Client identifier
            message: Message to send (will be JSON serialized)
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, event_type: WebSocketEventType, data: Dict[str, Any]):
        """
        Broadcast a message to all subscribed clients.
        
        Args:
            event_type: Type of event to broadcast
            data: Data to broadcast
        """
        message = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        subscribers = self.subscriptions.get(event_type.value, set()).copy()
        
        # Send to all subscribers
        for client_id in subscribers:
            await self.send_personal_message(client_id, message)
        
        logger.debug(f"Broadcasted {event_type.value} to {len(subscribers)} clients")
    
    async def broadcast_to_tenant(self, tenant_id: str, event_type: WebSocketEventType, data: Dict[str, Any]):
        """
        Broadcast a message to all clients of a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            event_type: Type of event to broadcast
            data: Data to broadcast
        """
        message = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Find all clients for this tenant
        tenant_clients = [
            client_id for client_id, metadata in self.connection_metadata.items()
            if metadata.get("tenant_id") == tenant_id
        ]
        
        for client_id in tenant_clients:
            await self.send_personal_message(client_id, message)
        
        logger.debug(f"Broadcasted {event_type.value} to {len(tenant_clients)} clients in tenant {tenant_id}")
    
    def subscribe(self, client_id: str, event_type: WebSocketEventType):
        """
        Subscribe a client to a specific event type.
        
        Args:
            client_id: Client identifier
            event_type: Event type to subscribe to
        """
        if event_type.value in self.subscriptions:
            self.subscriptions[event_type.value].add(client_id)
            logger.info(f"Client {client_id} subscribed to {event_type.value}")
    
    def unsubscribe(self, client_id: str, event_type: WebSocketEventType):
        """
        Unsubscribe a client from a specific event type.
        
        Args:
            client_id: Client identifier
            event_type: Event type to unsubscribe from
        """
        if event_type.value in self.subscriptions:
            self.subscriptions[event_type.value].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from {event_type.value}")
    
    def get_active_connections_count(self) -> int:
        """Get the number of active WebSocket connections."""
        return len(self.active_connections)
    
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.
        
        Args:
            client_id: Client identifier
        
        Returns:
            Connection metadata or None if not found
        """
        return self.connection_metadata.get(client_id)
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active connections.
        
        Returns:
            Dictionary of client_id to connection metadata
        """
        return {
            client_id: {
                **metadata,
                "connected": True
            }
            for client_id, metadata in self.connection_metadata.items()
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Helper functions for broadcasting specific events

async def broadcast_measurement(measurement_data: Dict[str, Any]):
    """Broadcast a new measurement event."""
    await websocket_manager.broadcast(
        WebSocketEventType.MEASUREMENT,
        measurement_data
    )

async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast an alert event."""
    await websocket_manager.broadcast(
        WebSocketEventType.ALERT,
        alert_data
    )

async def broadcast_system_status(status_data: Dict[str, Any]):
    """Broadcast system status update."""
    await websocket_manager.broadcast(
        WebSocketEventType.SYSTEM_STATUS,
        status_data
    )

async def broadcast_quality_metric(metric_data: Dict[str, Any]):
    """Broadcast quality metric update."""
    await websocket_manager.broadcast(
        WebSocketEventType.QUALITY_METRIC,
        metric_data
    )

async def broadcast_vision_result(vision_data: Dict[str, Any]):
    """Broadcast vision analysis result."""
    await websocket_manager.broadcast(
        WebSocketEventType.VISION_RESULT,
        vision_data
    )

async def broadcast_rag_result(rag_data: Dict[str, Any]):
    """Broadcast RAG analysis result."""
    await websocket_manager.broadcast(
        WebSocketEventType.RAG_RESULT,
        rag_data
    )

async def broadcast_iot_data(iot_data: Dict[str, Any]):
    """Broadcast IoT sensor data."""
    await websocket_manager.broadcast(
        WebSocketEventType.IOT_DATA,
        iot_data
    )

async def broadcast_notification(notification_data: Dict[str, Any]):
    """Broadcast a notification."""
    await websocket_manager.broadcast(
        WebSocketEventType.NOTIFICATION,
        notification_data
    )
