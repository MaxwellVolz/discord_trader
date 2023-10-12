import os
import time
import hmac
import hashlib
import base64
import asyncio
import websockets
import json
from dotenv import load_dotenv
from asyncio import Condition


class BitGet:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("API_KEY")
        self.secret_key = os.getenv("SECRET_KEY")
        self.passphrase = os.getenv("PASSPHRASE")

        # Rate Limiting Variables
        self.connection_count = 0
        self.subscription_count = 0
        self.connection_timestamps = []
        self.subscription_timestamps = []

        self.snapshot_received = False
        self.is_subscribed = False

        self.candle_data = []
        self.update_received = Condition()

    # Remember to call check_rate_limits before making additional
    # subscriptions in other parts of your code to ensure
    # you don't exceed the rate limits.
    def check_rate_limits(self):
        current_time = time.time()

        # Check Connection Limit
        self.connection_timestamps = [
            t for t in self.connection_timestamps if current_time - t <= 3600
        ]
        if len(self.connection_timestamps) >= 100:
            raise Exception(
                "Connection limit reached: 100 connections per IP per hour."
            )

        # Check Subscription Limit
        self.subscription_timestamps = [
            t for t in self.subscription_timestamps if current_time - t <= 3600
        ]
        if len(self.subscription_timestamps) >= 240:
            raise Exception("Subscription limit reached: 240 subscriptions per hour.")

    def generate_signature(self):
        timestamp = str(int(time.time()))
        content = f"{timestamp}GET/user/verify"

        h = hmac.new(
            self.secret_key.encode(), msg=content.encode(), digestmod=hashlib.sha256
        )
        hashed_content = h.digest()

        # hashed_content = hashlib.hmac.new(
        #     self.secret_key.encode(), content.encode(), hashlib.sha256
        # ).digest()
        signature = base64.b64encode(hashed_content).decode()
        return timestamp, signature

    async def send_ping(self, ws):
        while not self.is_subscribed:  # Only send pings if not subscribed
            await ws.send("ping")
            await asyncio.sleep(30)

    async def unsubscribe(self, ws):
        unsubscribe_msg = {
            "op": "unsubscribe",
            "args": [{"instType": "mc", "channel": "candle1m", "instId": "BTCUSDT"}],
        }
        await ws.send(json.dumps(unsubscribe_msg))
        print("Unsubscribed successfully.")

    async def listen(self, ws):
        while True:
            message = await asyncio.wait_for(ws.recv(), timeout=30)
            if message == "pong":
                continue
            else:
                try:
                    parsed_message = json.loads(message)
                    event_type = parsed_message.get("event", "")
                    if event_type == "subscribe":
                        self.is_subscribed = True
                        print(
                            f"Successfully subscribed to {parsed_message['arg']['channel']} for {parsed_message['arg']['instId']}"
                        )

                    elif event_type == "error":
                        print(
                            f"Error: {parsed_message['msg']} (Code: {parsed_message['code']})"
                        )

                    # Handle action-based messages
                    action_type = parsed_message.get("action", "")

                    if action_type == "snapshot":
                        self.snapshot_received = True
                        self.candle_data = parsed_message["data"]
                        print("Received snapshot:")
                        for candle in parsed_message["data"]:
                            print(
                                f"Timestamp: {candle[0]}, Open: {candle[1]}, High: {candle[2]}, Low: {candle[3]}, Close: {candle[4]}, Volume: {candle[5]}"
                            )

                    elif action_type == "update":
                        for candle in parsed_message["data"]:
                            print(f"Timestamp: {candle[0]}, Open: {candle[1]}, ...")

                        # Check if the new timestamp matches the last in self.candle_data
                        if self.candle_data and self.candle_data[-1][0] == candle[0]:
                            self.candle_data[-1] = candle
                        else:
                            self.candle_data.append(candle)
                            # Notify that an update has been received
                            async with self.update_received:
                                self.update_received.notify_all()

                    else:
                        print(f"Received: {parsed_message}")

                except json.JSONDecodeError:
                    print(f"Could not parse message: {message}")

    async def connect(self):
        self.check_rate_limits()

        timestamp, signature = self.generate_signature()
        uri = "wss://ws.bitget.com/mix/v1/stream"

        # Update rate-limiting variables
        self.connection_timestamps.append(time.time())
        self.connection_count += 1

        headers = {
            "apiKey": self.api_key,
            "passphrase": self.passphrase,
            "timestamp": timestamp,
            "sign": signature,
        }

        async with websockets.connect(uri, extra_headers=headers) as ws:
            print(f"Connected to {uri}")

            # For Subscription Limit
            self.subscription_timestamps.append(time.time())
            self.subscription_count += 1

            # Subscribe to candlestick data for BTCUSDT with 1m interval
            subscription_msg = {
                "op": "subscribe",
                "args": [
                    {"instType": "mc", "channel": "candle1m", "instId": "BTCUSDT"}
                ],
            }

            await ws.send(json.dumps(subscription_msg))

            listener_task = asyncio.create_task(self.listen(ws))
            ping_task = asyncio.create_task(self.send_ping(ws))

            async with self.update_received:
                await self.update_received.wait()

            listener_task.cancel()
            ping_task.cancel()
            await self.unsubscribe(ws)  # Unsubscribe before exiting

            await asyncio.gather(listener_task, ping_task, return_exceptions=True)

    def get_candle_data(self):
        return self.candle_data


# Initialize and connect
# bitget = BitGet()
# asyncio.get_event_loop().run_until_complete(bitget.connect(duration=10))
