"""
Webhook Router for ICAP Enterprise
================================
REST API endpoints for webhook management and integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from utils.webhook_service import (
    WebhookService, Webhook, WebhookEvent, WebhookStatus, WebhookDelivery
)
from utils.auth import get_current_user, check_permission

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger("Webhook_Router")

webhook_service = WebhookService()

@router.post("/")
async def create_webhook(
    webhook: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new webhook.
    
    - **url**: Webhook URL
    - **events**: List of events to subscribe to
    - **secret**: Optional secret for signature verification
    - **headers**: Optional custom headers
    - **tenant_id**: Optional tenant ID
    """
    try:
        webhook_obj = webhook_service.create_webhook(
            url=webhook["url"],
            events=[WebhookEvent(e) for e in webhook["events"]],
            secret=webhook.get("secret"),
            headers=webhook.get("headers"),
            tenant_id=webhook.get("tenant_id") if current_user["role"] == "ADMIN" else current_user.get("tenant_id")
        )
        
        return {
            "id": webhook_obj.id,
            "url": webhook_obj.url,
            "events": [e.value for e in webhook_obj.events],
            "status": webhook_obj.status.value,
            "tenant_id": webhook_obj.tenant_id,
            "created_at": webhook_obj.created_at
        }
        
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_webhooks(
    event: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    List webhooks.
    
    - **event**: Filter by event
    - **tenant_id**: Filter by tenant ID
    - **status**: Filter by status
    """
    try:
        # Non-admins can only see their tenant's webhooks
        if current_user["role"] != "ADMIN":
            tenant_id = current_user.get("tenant_id", "default")
        
        event_enum = WebhookEvent(event) if event else None
        status_enum = WebhookStatus(status) if status else None
        
        webhooks = webhook_service.list_webhooks(
            event=event_enum,
            tenant_id=tenant_id,
            status=status_enum
        )
        
        return {
            "webhooks": [
                {
                    "id": w.id,
                    "url": w.url,
                    "events": [e.value for e in w.events],
                    "status": w.status.value,
                    "tenant_id": w.tenant_id,
                    "created_at": w.created_at,
                    "last_triggered": w.last_triggered,
                    "failure_count": w.failure_count
                }
                for w in webhooks
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a webhook by ID."""
    try:
        webhook = webhook_service.get_webhook(webhook_id)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Check permission
        if current_user["role"] != "ADMIN" and webhook.tenant_id != current_user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return {
            "id": webhook.id,
            "url": webhook.url,
            "events": [e.value for e in webhook.events],
            "headers": webhook.headers,
            "status": webhook.status.value,
            "tenant_id": webhook.tenant_id,
            "created_at": webhook.created_at,
            "updated_at": webhook.updated_at,
            "last_triggered": webhook.last_triggered,
            "failure_count": webhook.failure_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a webhook."""
    try:
        # Check permission
        webhook = webhook_service.get_webhook(webhook_id)
        if webhook and current_user["role"] != "ADMIN" and webhook.tenant_id != current_user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        success = webhook_service.delete_webhook(webhook_id)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Webhook not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger")
async def trigger_webhook_event(
    event_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger a webhook event manually.
    
    - **event**: Event type
    - **payload**: Event payload
    - **tenant_id**: Optional tenant ID
    """
    try:
        # Only admins can trigger events manually
        if current_user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        event = WebhookEvent(event_data["event"])
        payload = event_data["payload"]
        tenant_id = event_data.get("tenant_id")
        
        deliveries = await webhook_service.trigger_event(event, payload, tenant_id)
        
        return {
            "event": event.value,
            "deliveries": [
                {
                    "id": d.id,
                    "webhook_id": d.webhook_id,
                    "status": d.status,
                    "status_code": d.status_code,
                    "attempted_at": d.attempted_at
                }
                for d in deliveries
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering webhook event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user)
):
    """
    Get delivery records for a webhook.
    
    - **webhook_id**: Webhook ID
    - **limit**: Maximum number of deliveries to return
    """
    try:
        # Check permission
        webhook = webhook_service.get_webhook(webhook_id)
        if webhook and current_user["role"] != "ADMIN" and webhook.tenant_id != current_user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        deliveries = webhook_service.get_webhook_deliveries(webhook_id, limit)
        
        return {
            "deliveries": [
                {
                    "id": d.id,
                    "webhook_id": d.webhook_id,
                    "event": d.event.value,
                    "status": d.status,
                    "status_code": d.status_code,
                    "error": d.error,
                    "attempted_at": d.attempted_at,
                    "completed_at": d.completed_at
                }
                for d in deliveries
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook deliveries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def list_available_events(current_user: dict = Depends(get_current_user)):
    """List available webhook events."""
    try:
        events = [
            {"value": e.value, "description": e.value.replace("_", " ").title()}
            for e in WebhookEvent
        ]
        
        return {"events": events}
        
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
