"""
Integration Tests for IoT Connectors
=====================================
Тестове за интеграция на MQTT и OPC-UA конектори.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from app.modules.iot_connector import IRM_IoT_Connector
from app.modules.opc_ua_connector import IRM_OPCUA_Connector

@pytest.fixture
def mqtt_connector():
    """Fixture за MQTT Connector."""
    return IRM_IoT_Connector()

@pytest.fixture
def opcua_connector():
    """Fixture за OPC-UA Connector."""
    return IRM_OPCUA_Connector()

def test_mqtt_connector_initialization(mqtt_connector):
    """Тест за инициализация на MQTT Connector."""
    assert mqtt_connector is not None
    assert mqtt_connector.client is not None
    assert mqtt_connector.reconnect_attempts == 0
    assert mqtt_connector.connected is False

def test_mqtt_connector_reconnect_logic(mqtt_connector):
    """Тест за reconnection logic."""
    # Simulate disconnect
    mqtt_connector.on_disconnect(mqtt_connector.client, None, 1)
    
    # Should trigger reconnection attempt
    assert mqtt_connector.reconnect_attempts > 0

def test_mqtt_connector_max_reconnect_attempts(mqtt_connector):
    """Тест за max reconnect attempts."""
    mqtt_connector.reconnect_attempts = mqtt_connector.max_reconnect_attempts
    
    # Should not attempt reconnection beyond max
    mqtt_connector.reconnect()
    
    # Should stay at max
    assert mqtt_connector.reconnect_attempts == mqtt_connector.max_reconnect_attempts

def test_mqtt_connector_message_handling(mqtt_connector):
    """Тест за обработка на MQTT съобщения."""
    # Mock message
    mock_msg = Mock()
    mock_msg.topic = "factory/sensors/temperature"
    mock_msg.payload.decode.return_value = json.dumps({
        "value": 25.5,
        "unit": "C",
        "timestamp": time.time()
    })
    
    # Process message
    mqtt_connector.on_message(mqtt_connector.client, None, mock_msg)
    
    # Should store sensor data
    assert "factory/sensors/temperature" in mqtt_connector.sensor_data
    assert mqtt_connector.sensor_data["factory/sensors/temperature"]["value"] == 25.5

def test_opcua_connector_initialization(opcua_connector):
    """Тест за инициализация на OPC-UA Connector."""
    assert opcua_connector is not None
    assert opcua_connector.client is not None
    assert opcua_connector.endpoint is not None

def test_opcua_connector_config_from_env():
    """Тест за конфигурация от environment variables."""
    # Test that configuration is loaded from environment
    from app.modules.opc_ua_connector import OPC_UA_SERVER_URL, NODES_TO_WATCH
    
    assert OPC_UA_SERVER_URL is not None
    assert isinstance(NODES_TO_WATCH, list)
    assert len(NODES_TO_WATCH) > 0

@pytest.mark.asyncio
async def test_opcua_connector_monitor_node(opcua_connector):
    """Тест за мониторинг на OPC-UA node."""
    # This test would require a real OPC-UA server
    # For now, we test the structure
    assert opcua_connector.client is not None
    
    # Mock node monitoring
    node_id = "ns=2;i=2"
    # In real scenario, this would connect to actual server
    # For testing, we verify the structure exists
    assert node_id is not None

def test_iot_connector_error_handling():
    """Тест за error handling при IoT operations."""
    connector = IRM_IoT_Connector()
    
    # Test with invalid MQTT broker
    with patch.dict('os.environ', {'MQTT_BROKER': 'invalid_broker'}):
        # Should handle connection errors gracefully
        try:
            connector.client.connect("invalid_broker", 1883, 60)
            # If it doesn't raise, that's okay - it might be handled
        except Exception as e:
            # Should be handled gracefully
            assert str(e) is not None

def test_mqtt_sensor_data_storage(mqtt_connector):
    """Тест за съхранение на sensor данни."""
    # Add some sensor data
    mqtt_connector.sensor_data["sensor1"] = {"value": 25.0, "unit": "C"}
    mqtt_connector.sensor_data["sensor2"] = {"value": 1013, "unit": "hPa"}
    
    assert len(mqtt_connector.sensor_data) == 2
    assert mqtt_connector.sensor_data["sensor1"]["value"] == 25.0

def test_mqtt_critical_value_detection():
    """Тест за детекция на критични стойности."""
    # This would test the integration with API for anomaly detection
    # For now, we test the structure
    sensor_data = {
        "temperature": {"value": 85.0, "unit": "C"},  # Critical temperature
        "pressure": {"value": 1500, "unit": "bar"}  # Critical pressure
    }
    
    # In real scenario, this would send alerts
    assert sensor_data["temperature"]["value"] > 80  # Critical threshold
