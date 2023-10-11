import os
import time
import hashlib
import base64
import asyncio
import websockets
from dotenv import load_dotenv


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
        hashed_content = hashlib.hmac.new(
            self.secret_key.encode(), content.encode(), hashlib.sha256
        ).digest()
        signature = base64.b64encode(hashed_content).decode()
        return timestamp, signature

    async def send_ping(self, ws):
        while True:
            await ws.send("ping")
            await asyncio.sleep(30)

    async def listen(self, ws):
        while True:
            message = await asyncio.wait_for(ws.recv(), timeout=30)
            if message == "pong":
                continue
            else:
                print(f"Received: {message}")
                # Your logic here based on received data

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

            listener_task = asyncio.create_task(self.listen(ws))
            ping_task = asyncio.create_task(self.send_ping(ws))

            await listener_task
            await ping_task

    def get_data(self, start_timestamp, end_timestamp):
        pass  # Your implementation here


# Initialize and connect
bitget = BitGet()
asyncio.get_event_loop().run_until_complete(bitget.connect())
