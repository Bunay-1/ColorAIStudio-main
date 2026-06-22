"""
Notification Router for ICAP Enterprise
======================================
REST API endpoints for notifications and alerts management.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from utils.notification_service import (
    NotificationService, Notification, Alert, NotificationSeverity,
    NotificationType, NotificationChannel, NotificationPreference
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger("Notification_Router")

notification_service = NotificationService()

@router.post("/send")
async def send_notification(
    notification: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a notification.
    
    - **type**: Notification type (system, user, tenant, security, performance, compliance)
    - **severity**: Severity level (info, warning, error, critical)
    - **title**: Notification title
    - **message**: Notification message
    - **channels**: Delivery channels (websocket, email, slack, webhook)
    - **user_id**: Target user ID (optional)
    - **tenant_id**: Target tenant ID (optional)
    """
    try:
        notification_obj = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType(notification.get("type", "system")),
            severity=NotificationSeverity(notification.get("severity", "info")),
            title=notification["title"],
            message=notification["message"],
            user_id=notification.get("user_id"),
            tenant_id=notification.get("tenant_id"),
            channels=[NotificationChannel(c) for c in notification.get("channels", ["websocket"])],
            metadata=notification.get("metadata", {})
        )
        
        success = await notification_service.send_notification(notification_obj)
        
        if success:
            return {"status": "success", "notification_id": notification_obj.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_notifications(
    user_id: str,
    unread_only: bool = Query(False),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user)
):
    """
    Get notifications for a user.
    
    - **user_id**: User ID
    - **unread_only**: Only return unread notifications
    - **limit**: Maximum number of notifications to return
    """
    try:
        # Check permission - users can only see their own notifications unless admin
        if user_id != current_user["username"] and current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
        
        return {
            "notifications": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "severity": n.severity.value,
                    "title": n.title,
                    "message": n.message,
                    "created_at": n.created_at,
                    "read": n.read,
                    "read_at": n.read_at,
                    "metadata": n.metadata
                }
                for n in notifications
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read."""
    try:
        success = notification_service.mark_notification_read(notification_id, current_user["username"])
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts")
async def create_alert(
    alert: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create an alert.
    
    - **severity**: Severity level (info, warning, error, critical)
    - **title**: Alert title
    - **description**: Alert description
    - **source**: Alert source
    - **condition**: Alert condition
    - **threshold**: Alert threshold value
    - **current_value**: Current metric value
    """
    try:
        alert_obj = Alert(
            id=str(uuid.uuid4()),
            severity=NotificationSeverity(alert.get("severity", "warning")),
            title=alert["title"],
            description=alert["description"],
            source=alert["source"],
            condition=alert["condition"],
            threshold=alert["threshold"],
            current_value=alert["current_value"],
            user_id=alert.get("user_id"),
            tenant_id=alert.get("tenant_id"),
            metadata=alert.get("metadata", {})
        )
        
        success = notification_service.create_alert(alert_obj)
        
        if success:
            return {"status": "success", "alert_id": alert_obj.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to create alert")
            
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    unresolved_only: bool = Query(True),
    current_user: dict = Depends(get_current_user)
):
    """
    Get alerts.
    
    - **user_id**: Filter by user ID
    - **tenant_id**: Filter by tenant ID
    - **unresolved_only**: Only return unresolved alerts
    """
    try:
        # Non-admins can only see their own alerts
        if current_user["role"] != "ADMIN":
            user_id = current_user["username"]
        
        alerts = notification_service.get_active_alerts(
            user_id=user_id,
            tenant_id=tenant_id,
            unresolved_only=unresolved_only
        )
        
        return {
            "alerts": [
                {
                    "id": a.id,
                    "severity": a.severity.value,
                    "title": a.title,
                    "description": a.description,
                    "source": a.source,
                    "condition": a.condition,
                    "threshold": a.threshold,
                    "current_value": a.current_value,
                    "acknowledged": a.acknowledged,
                    "acknowledged_by": a.acknowledged_by,
                    "acknowledged_at": a.acknowledged_at,
                    "resolved": a.resolved,
                    "resolved_at": a.resolved_at,
                    "created_at": a.created_at,
                    "metadata": a.metadata
                }
                for a in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge an alert."""
    try:
        success = notification_service.acknowledge_alert(alert_id, current_user["username"])
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resolve an alert."""
    try:
        success = notification_service.resolve_alert(alert_id)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_id}")
async def get_user_preferences(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user notification preferences."""
    try:
        # Users can only see their own preferences unless admin
        if user_id != current_user["username"] and current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        preferences = notification_service.get_user_preferences(user_id)
        
        if preferences:
            return {
                "user_id": preferences.user_id,
                "enabled": preferences.enabled,
                "channels": preferences.channels,
                "severity_filter": preferences.severity_filter,
                "type_filter": preferences.type_filter,
                "quiet_hours_start": preferences.quiet_hours_start,
                "quiet_hours_end": preferences.quiet_hours_end
            }
        else:
            raise HTTPException(status_code=404, detail="Preferences not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/{user_id}")
async def set_user_preferences(
    user_id: str,
    preferences: dict,
    current_user: dict = Depends(get_current_user)
):
    """Set user notification preferences."""
    try:
        # Users can only set their own preferences unless admin
        if user_id != current_user["username"] and current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        pref_obj = NotificationPreference(
            user_id=user_id,
            enabled=preferences.get("enabled", True),
            channels=preferences.get("channels", {
                "websocket": True,
                "email": False,
                "slack": False,
                "webhook": False
            }),
            severity_filter=preferences.get("severity_filter", ["info", "warning", "error", "critical"]),
            type_filter=preferences.get("type_filter", ["system", "user", "tenant", "security", "performance", "compliance"]),
            quiet_hours_start=preferences.get("quiet_hours_start"),
            quiet_hours_end=preferences.get("quiet_hours_end")
        )
        
        success = notification_service.set_user_preferences(pref_obj)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to set preferences")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time notifications.
    
    Connect to this endpoint to receive real-time notifications for a user.
    """
    await websocket.accept()
    
    # Register WebSocket connection
    notification_service.register_websocket(user_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"status": "connected", "user_id": user_id})
            
    except WebSocketDisconnect:
        # Unregister WebSocket connection
        notification_service.unregister_websocket(user_id)
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        notification_service.unregister_websocket(user_id)

@router.post("/check-alerts")
async def check_alert_conditions(
    metrics: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Check alert conditions against current metrics.
    
    - **metrics**: Dictionary of metric names and values
    """
    try:
        # Only admins can trigger alert checks
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        await notification_service.check_alert_conditions(metrics)
        
        return {"status": "success", "message": "Alert conditions checked"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking alert conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
