import asyncio
import pytest
import json
from unittest.mock import AsyncMock, patch, call
from bitget.bitget import BitGet


@pytest.mark.asyncio
async def test_ping_pong():
    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = ["pong", "pong"]
        mock_connect.return_value.__aenter__.return_value = mock_ws

        bitget = BitGet()

        listener_task = asyncio.create_task(bitget.listen(mock_ws))
        ping_task = asyncio.create_task(bitget.send_ping(mock_ws))

        await asyncio.sleep(31)

        listener_task.cancel()
        ping_task.cancel()

        await asyncio.gather(listener_task, ping_task, return_exceptions=True)

        # Check if two or three 'pong' messages were received
        assert 1 <= mock_ws.recv.await_count <= 3
