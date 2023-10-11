import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from bitget.bitget import BitGet


@pytest.mark.asyncio
async def test_ping_pong():
    # Mock websockets.connect to return an AsyncMock object
    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = ["pong", "pong"]
        mock_connect.return_value.__aenter__.return_value = mock_ws

        # Initialize BitGet
        bitget = BitGet()

        # Run the connection
        listener_task = asyncio.create_task(bitget.listen(mock_ws))
        ping_task = asyncio.create_task(bitget.send_ping(mock_ws))

        # Let it run for 60 seconds with countdown
        for i in range(60, 0, -5):
            print(f"Waiting... {i} seconds remaining.")
            await asyncio.sleep(5)

        # Cancel tasks
        listener_task.cancel()
        ping_task.cancel()

        # Wait for tasks to be cancelled
        await asyncio.gather(listener_task, ping_task, return_exceptions=True)

        # Check if two 'pong' messages were received
        assert 2 <= mock_ws.recv.await_count <= 3
