import pytest
from app.core.ws_manager import ConnectionManager
from fastapi import WebSocket
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_ws_manager_connect_disconnect():
    manager = ConnectionManager()
    websocket = AsyncMock(spec=WebSocket)

    await manager.connect(websocket)
    assert websocket in manager.active_connections

    manager.disconnect(websocket)
    assert websocket not in manager.active_connections

@pytest.mark.asyncio
async def test_ws_manager_broadcast():
    manager = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)

    await manager.connect(ws1)
    await manager.connect(ws2)

    message = {"test": "data"}
    await manager.broadcast(message)

    ws1.send_json.assert_called_with(message)
    ws2.send_json.assert_called_with(message)
