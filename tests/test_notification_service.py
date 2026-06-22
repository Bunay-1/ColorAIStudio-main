"""
Unit tests for Notification Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from utils.notification_service import NotificationService, NotificationChannel, NotificationPriority


@pytest.fixture
def notification_service():
    """Fixture for NotificationService instance"""
    return NotificationService()


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    with patch('utils.notification_service.WebSocketManager') as mock:
        yield mock.return_value


@pytest.fixture
def mock_email_client():
    """Mock email client"""
    with patch('utils.notification_service.EmailClient') as mock:
        yield mock.return_value


@pytest.fixture
def mock_slack_client():
    """Mock Slack client"""
    with patch('utils.notification_service.SlackClient') as mock:
        yield mock.return_value


class TestNotificationService:
    """Test cases for NotificationService"""

    def test_create_notification(self, notification_service):
        """Test creating a notification"""
        notification = notification_service.create_notification(
            title="Test Notification",
            message="This is a test notification",
            channel=NotificationChannel.WEBSOCKET,
            priority=NotificationPriority.HIGH,
            metadata={"key": "value"}
        )
        
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.channel == NotificationChannel.WEBSOCKET
        assert notification.priority == NotificationPriority.HIGH
        assert notification.metadata == {"key": "value"}
        assert notification.id is not None
        assert notification.created_at is not None

    def test_send_websocket_notification(self, notification_service, mock_websocket_manager):
        """Test sending WebSocket notification"""
        notification = notification_service.create_notification(
            title="Test",
            message="Test message",
            channel=NotificationChannel.WEBSOCKET
        )
        
        mock_websocket_manager.broadcast.return_value = True
        
        result = notification_service.send_notification(notification)
        
        assert result is True
        mock_websocket_manager.broadcast.assert_called_once()

    def test_send_email_notification(self, notification_service, mock_email_client):
        """Test sending email notification"""
        notification = notification_service.create_notification(
            title="Test",
            message="Test message",
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com"
        )
        
        mock_email_client.send.return_value = True
        
        result = notification_service.send_notification(notification)
        
        assert result is True
        mock_email_client.send.assert_called_once()

    def test_send_slack_notification(self, notification_service, mock_slack_client):
        """Test sending Slack notification"""
        notification = notification_service.create_notification(
            title="Test",
            message="Test message",
            channel=NotificationChannel.SLACK
        )
        
        mock_slack_client.send.return_value = True
        
        result = notification_service.send_notification(notification)
        
        assert result is True
        mock_slack_client.send.assert_called_once()

    def test_send_webhook_notification(self, notification_service):
        """Test sending webhook notification"""
        notification = notification_service.create_notification(
            title="Test",
            message="Test message",
            channel=NotificationChannel.WEBHOOK,
            webhook_url="https://example.com/webhook"
        )
        
        with patch('utils.notification_service.httpx.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            result = notification_service.send_notification(notification)
            
            assert result is True
            mock_post.assert_called_once()

    def test_list_notifications(self, notification_service):
        """Test listing notifications"""
        notification_service.create_notification(
            title="Test 1",
            message="Message 1",
            channel=NotificationChannel.WEBSOCKET
        )
        notification_service.create_notification(
            title="Test 2",
            message="Message 2",
            channel=NotificationChannel.EMAIL
        )
        
        notifications = notification_service.list_notifications(limit=10)
        
        assert len(notifications) == 2
        assert notifications[0].title == "Test 1"
        assert notifications[1].title == "Test 2"

    def test_filter_notifications_by_priority(self, notification_service):
        """Test filtering notifications by priority"""
        notification_service.create_notification(
            title="High Priority",
            message="High",
            channel=NotificationChannel.WEBSOCKET,
            priority=NotificationPriority.HIGH
        )
        notification_service.create_notification(
            title="Low Priority",
            message="Low",
            channel=NotificationChannel.WEBSOCKET,
            priority=NotificationPriority.LOW
        )
        
        notifications = notification_service.list_notifications(
            priority=NotificationPriority.HIGH
        )
        
        assert len(notifications) == 1
        assert notifications[0].title == "High Priority"

    def test_create_alert(self, notification_service):
        """Test creating an alert"""
        alert = notification_service.create_alert(
            name="Color Deviation Alert",
            condition="delta_e > 2.0",
            action="send_notification",
            enabled=True
        )
        
        assert alert.name == "Color Deviation Alert"
        assert alert.condition == "delta_e > 2.0"
        assert alert.action == "send_notification"
        assert alert.enabled is True
        assert alert.id is not None

    def test_evaluate_alert_condition(self, notification_service):
        """Test evaluating alert condition"""
        alert = notification_service.create_alert(
            name="Test Alert",
            condition="delta_e > 2.0",
            action="send_notification"
        )
        
        # Test condition evaluation
        context = {"delta_e": 2.5}
        result = notification_service.evaluate_alert(alert, context)
        
        assert result is True

    def test_trigger_alert(self, notification_service, mock_websocket_manager):
        """Test triggering an alert"""
        alert = notification_service.create_alert(
            name="Test Alert",
            condition="delta_e > 2.0",
            action="send_notification"
        )
        
        mock_websocket_manager.broadcast.return_value = True
        
        context = {"delta_e": 2.5}
        notification_service.trigger_alert(alert, context)
        
        mock_websocket_manager.broadcast.assert_called_once()

    def test_delete_notification(self, notification_service):
        """Test deleting a notification"""
        notification = notification_service.create_notification(
            title="Test",
            message="Test message",
            channel=NotificationChannel.WEBSOCKET
        )
        
        notification_id = notification.id
        result = notification_service.delete_notification(notification_id)
        
        assert result is True
        notifications = notification_service.list_notifications()
        assert len(notifications) == 0

    def test_notification_statistics(self, notification_service):
        """Test getting notification statistics"""
        notification_service.create_notification(
            title="Test 1",
            message="Message 1",
            channel=NotificationChannel.WEBSOCKET,
            priority=NotificationPriority.HIGH
        )
        notification_service.create_notification(
            title="Test 2",
            message="Message 2",
            channel=NotificationChannel.EMAIL,
            priority=NotificationPriority.LOW
        )
        
        stats = notification_service.get_statistics()
        
        assert stats["total"] == 2
        assert stats["by_channel"][NotificationChannel.WEBSOCKET] == 1
        assert stats["by_channel"][NotificationChannel.EMAIL] == 1
        assert stats["by_priority"][NotificationPriority.HIGH] == 1
        assert stats["by_priority"][NotificationPriority.LOW] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
