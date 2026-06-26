"""
WebSocket Router for Real-Time Data Streaming
===========================================
WebSocket endpoints for real-time data streaming to clients.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging
from utils.websocket_manager import (
    websocket_manager,
    WebSocketEventType
)
from utils.auth import get_current_user_from_token

logger = logging.getLogger("WebSocketRouter")

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time data streaming.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        token: Optional JWT token for authentication
        tenant_id: Optional tenant identifier for multi-tenant filtering
    """
    # Validate token if provided
    user = None
    if token:
        try:
            user = get_current_user_from_token(token)
        except Exception as e:
            logger.warning(f"Invalid token for WebSocket connection: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
    
    # Connection metadata
    metadata = {
        "user_id": user.username if user else None,
        "tenant_id": tenant_id,
        "authenticated": user is not None
    }
    
    # Accept connection
    await websocket_manager.connect(websocket, client_id, metadata)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle client messages (subscriptions, etc.)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific event types
                event_types = data.get("event_types", [])
                for event_type in event_types:
                    try:
                        ws_event_type = WebSocketEventType(event_type)
                        websocket_manager.subscribe(client_id, ws_event_type)
                    except ValueError:
                        logger.warning(f"Invalid event type: {event_type}")
            
            elif message_type == "unsubscribe":
                # Unsubscribe from specific event types
                event_types = data.get("event_types", [])
                for event_type in event_types:
                    try:
                        ws_event_type = WebSocketEventType(event_type)
                        websocket_manager.unsubscribe(client_id, ws_event_type)
                    except ValueError:
                        logger.warning(f"Invalid event type: {event_type}")
            
            elif message_type == "ping":
                # Respond to ping with pong
                await websocket_manager.send_personal_message(
                    client_id,
                    {"type": "pong", "timestamp": data.get("timestamp")}
                )
            
            elif message_type == "get_status":
                # Send connection status
                await websocket_manager.send_personal_message(
                    client_id,
                    {
                        "type": "status",
                        "connected": True,
                        "subscriptions": [
                            event_type for event_type, subscribers in websocket_manager.subscriptions.items()
                            if client_id in subscribers
                        ],
                        "active_connections": websocket_manager.get_active_connections_count()
                    }
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        websocket_manager.disconnect(client_id)


@router.get("/ws/connections")
async def get_websocket_connections():
    """
    Get information about all active WebSocket connections.
    
    Requires ADMIN role.
    """
    return {
        "active_connections": websocket_manager.get_active_connections_count(),
        "connections": websocket_manager.get_all_connections()
    }


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket statistics.
    """
    subscriptions = {}
    for event_type, subscribers in websocket_manager.subscriptions.items():
        subscriptions[event_type] = len(subscribers)
    
    return {
        "active_connections": websocket_manager.get_active_connections_count(),
        "subscriptions": subscriptions
    }
