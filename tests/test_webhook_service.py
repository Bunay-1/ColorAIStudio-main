"""
Unit tests for Webhook Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from utils.webhook_service import WebhookService, WebhookEvent, WebhookStatus


@pytest.fixture
def webhook_service():
    """Fixture for WebhookService instance"""
    return WebhookService()


@pytest.fixture
def mock_http_client():
    """Mock HTTP client"""
    with patch('utils.webhook_service.httpx') as mock:
        yield mock


class TestWebhookService:
    """Test cases for WebhookService"""

    def test_create_webhook(self, webhook_service):
        """Test creating a webhook"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED, WebhookEvent.ALERT_TRIGGERED],
            secret="webhook-secret",
            enabled=True
        )
        
        assert webhook.url == "https://example.com/webhook"
        assert WebhookEvent.USER_CREATED in webhook.events
        assert WebhookEvent.ALERT_TRIGGERED in webhook.events
        assert webhook.secret == "webhook-secret"
        assert webhook.enabled is True
        assert webhook.id is not None
        assert webhook.created_at is not None

    def test_list_webhooks(self, webhook_service):
        """Test listing webhooks"""
        webhook_service.create_webhook(
            url="https://example.com/webhook1",
            events=[WebhookEvent.USER_CREATED],
            secret="secret1"
        )
        webhook_service.create_webhook(
            url="https://example.com/webhook2",
            events=[WebhookEvent.ALERT_TRIGGERED],
            secret="secret2"
        )
        
        webhooks = webhook_service.list_webhooks()
        
        assert len(webhooks) == 2
        assert webhooks[0].url == "https://example.com/webhook1"
        assert webhooks[1].url == "https://example.com/webhook2"

    def test_get_webhook_by_id(self, webhook_service):
        """Test getting webhook by ID"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        retrieved_webhook = webhook_service.get_webhook(webhook.id)
        
        assert retrieved_webhook.id == webhook.id
        assert retrieved_webhook.url == webhook.url

    def test_update_webhook(self, webhook_service):
        """Test updating a webhook"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret",
            enabled=True
        )
        
        updated_webhook = webhook_service.update_webhook(
            webhook.id,
            url="https://example.com/new-webhook",
            enabled=False
        )
        
        assert updated_webhook.url == "https://example.com/new-webhook"
        assert updated_webhook.enabled is False

    def test_delete_webhook(self, webhook_service):
        """Test deleting a webhook"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        webhook_id = webhook.id
        result = webhook_service.delete_webhook(webhook_id)
        
        assert result is True
        webhooks = webhook_service.list_webhooks()
        assert len(webhooks) == 0

    def test_trigger_webhook_success(self, webhook_service, mock_http_client):
        """Test triggering webhook successfully"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.post.return_value = mock_response
        
        result = webhook_service.trigger_webhook(
            webhook,
            event=WebhookEvent.USER_CREATED,
            payload={"user_id": "user_123"}
        )
        
        assert result["success"] is True
        assert result["status_code"] == 200
        mock_http_client.post.assert_called_once()

    def test_trigger_webhook_failure(self, webhook_service, mock_http_client):
        """Test triggering webhook with failure"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_http_client.post.return_value = mock_response
        
        result = webhook_service.trigger_webhook(
            webhook,
            event=WebhookEvent.USER_CREATED,
            payload={"user_id": "user_123"}
        )
        
        assert result["success"] is False
        assert result["status_code"] == 500

    def test_trigger_webhook_with_retry(self, webhook_service, mock_http_client):
        """Test triggering webhook with retry logic"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret",
            max_retries=3
        )
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_http_client.post.return_value = mock_response
        
        result = webhook_service.trigger_webhook(
            webhook,
            event=WebhookEvent.USER_CREATED,
            payload={"user_id": "user_123"}
        )
        
        assert result["success"] is False
        assert result["retry_count"] == 3
        assert mock_http_client.post.call_count == 3

    def test_verify_webhook_signature(self, webhook_service):
        """Test webhook signature verification"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="webhook-secret"
        )
        
        payload = {"user_id": "user_123"}
        signature = webhook_service.generate_signature(webhook.secret, payload)
        
        is_valid = webhook_service.verify_signature(webhook.secret, payload, signature)
        
        assert is_valid is True

    def test_verify_webhook_signature_invalid(self, webhook_service):
        """Test webhook signature verification with invalid signature"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="webhook-secret"
        )
        
        payload = {"user_id": "user_123"}
        invalid_signature = "invalid-signature"
        
        is_valid = webhook_service.verify_signature(webhook.secret, payload, invalid_signature)
        
        assert is_valid is False

    def test_get_webhook_delivery_logs(self, webhook_service):
        """Test getting webhook delivery logs"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        # Simulate webhook delivery
        webhook_service.record_delivery(
            webhook.id,
            event=WebhookEvent.USER_CREATED,
            status=WebhookStatus.SUCCESS,
            response_code=200
        )
        
        logs = webhook_service.get_delivery_logs(webhook.id)
        
        assert len(logs) == 1
        assert logs[0]["status"] == WebhookStatus.SUCCESS
        assert logs[0]["response_code"] == 200

    def test_get_webhook_statistics(self, webhook_service):
        """Test getting webhook statistics"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret"
        )
        
        # Record some deliveries
        webhook_service.record_delivery(webhook.id, WebhookEvent.USER_CREATED, WebhookStatus.SUCCESS, 200)
        webhook_service.record_delivery(webhook.id, WebhookEvent.USER_CREATED, WebhookStatus.FAILED, 500)
        
        stats = webhook_service.get_statistics(webhook.id)
        
        assert stats["total_deliveries"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate"] == 50.0

    def test_disable_webhook(self, webhook_service):
        """Test disabling a webhook"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret",
            enabled=True
        )
        
        disabled_webhook = webhook_service.disable_webhook(webhook.id)
        
        assert disabled_webhook.enabled is False

    def test_enable_webhook(self, webhook_service):
        """Test enabling a webhook"""
        webhook = webhook_service.create_webhook(
            url="https://example.com/webhook",
            events=[WebhookEvent.USER_CREATED],
            secret="secret",
            enabled=False
        )
        
        enabled_webhook = webhook_service.enable_webhook(webhook.id)
        
        assert enabled_webhook.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
