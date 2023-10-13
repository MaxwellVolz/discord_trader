import asyncio
import websockets
import json
import time
import hmac
import hashlib
import base64
import pandas as pd
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

from bitget.utils import convert_to_dataframe

from logger_config import trader_logger

# Load environment variables from .env file
load_dotenv()

RATE_LIMIT_CONNECTIONS = 100
RATE_LIMIT_SUBSCRIPTIONS = 240


class Trader:
    def __init__(self):
        # Default Variables
        self.api_key = os.getenv("API_KEY")
        self.secret_key = os.getenv("SECRET_KEY")
        self.passphrase = os.getenv("PASSPHRASE")

        self.connection_count = 0
        self.subscription_count = 0
        self.connection_timestamps = []
        self.subscription_timestamps = []

        self.uri = "wss://ws.bitget.com/mix/v1/stream"
        self.subscribed = False
        self.snapshot_received = False
        self.df = None
        self.ws = None
        self.data = []

    async def connect(self):
        # Add this line to keep track of connections
        self.connection_timestamps.append(time.time())

        self.check_rate_limits()
        timestamp, signature = self.generate_signature()
        headers = {
            "apiKey": self.api_key,
            "passphrase": self.passphrase,
            "timestamp": timestamp,
            "sign": signature,
        }

        self.ws = await websockets.connect(self.uri, extra_headers=headers)

        try:
            await self.subscribe()
            while True:
                msg = await self.ws.recv()
                await self.handle_message(msg)
        except Exception as e:
            trader_logger.error(f"Error occurred: {e}")
        finally:
            await self.ws.close()

    async def subscribe(self):
        subscription_msg = {
            "op": "subscribe",
            "args": [{"instType": "mc", "channel": "candle1m", "instId": "BTCUSDT"}],
        }

        await self.ws.send(json.dumps(subscription_msg))

    async def handle_message(self, msg):
        parsed_msg = json.loads(msg)
        # trader_logger.debug(f"parsed_msg: {parsed_msg}")
        if self.is_subscription_ack(parsed_msg):
            self.subscribed = True
            trader_logger.info("Successfully subscribed.")
            return

        if not self.snapshot_received:
            trader_logger.info("Snapshot not received yet.")
            await self.handle_snapshot(parsed_msg)
        else:
            await self.handle_update(parsed_msg)

    def is_subscription_ack(self, parsed_msg):
        return parsed_msg.get("event") == "subscribed"

    async def handle_snapshot(self, parsed_msg):
        if "data" in parsed_msg:
            self.snapshot_received = True
            trader_logger.debug(f"parsed_msg: {parsed_msg}")

            self.data = parsed_msg["data"]
            self.df = convert_to_dataframe(parsed_msg["data"])
            trader_logger.info(f"Snapshot received.")

    async def handle_update(self, parsed_msg):
        if "data" in parsed_msg:
            new_data = parsed_msg["data"][0]
            new_timestamp = new_data[0]

            existing_timestamps = [row[0] for row in self.data]

            # Debug logging to understand the values
            # trader_logger.debug(f"Existing Timestamps: {existing_timestamps}")

            # Check if a row with the same timestamp exists in self.data
            if new_timestamp not in existing_timestamps:
                self.data.append(new_data)
                self.df = convert_to_dataframe(self.data)
                trader_logger.info(f"New update, df regenerated: {new_timestamp}")

            await self.maintain_data_size()
        else:
            trader_logger.debug("[WARNING WARNING] data: MISSING")

    async def maintain_data_size(self):
        if len(self.df) > 1000:  # Limit data size to 1000 records
            self.df = self.df[-1000:]

    def get_data(self):
        # print(self.df.describe())
        return self.df

    def get_data_last_n_hours(self, hours):
        # Get the latest timestamp in the DataFrame
        latest_timestamp = self.df["Timestamp"].max()

        # Convert the number of hours into a timedelta
        time_delta = timedelta(hours=hours)

        # Calculate the oldest data point that we are interested in based on the latest timestamp
        oldest_time_of_interest = latest_timestamp - time_delta

        # Filter the DataFrame to only include data from the last 'hours' hours
        filtered_df = self.df[self.df["Timestamp"] >= oldest_time_of_interest]

        return filtered_df

    def generate_signature(self):
        timestamp = str(int(time.time()))
        content = f"{timestamp}GET/user/verify"

        h = hmac.new(
            self.secret_key.encode(), msg=content.encode(), digestmod=hashlib.sha256
        )
        hashed_content = h.digest()

        signature = base64.b64encode(hashed_content).decode()
        return timestamp, signature

    def check_rate_limits(self):
        current_time = time.time()

        # Check Connection Limit
        self.connection_timestamps = [
            t for t in self.connection_timestamps if current_time - t <= 3600
        ]
        if len(self.connection_timestamps) >= RATE_LIMIT_CONNECTIONS:
            raise Exception(
                "Connection limit reached: 100 connections per IP per hour."
            )

        # Check Subscription Limit
        self.subscription_timestamps = [
            t for t in self.subscription_timestamps if current_time - t <= 3600
        ]
        if len(self.subscription_timestamps) >= RATE_LIMIT_SUBSCRIPTIONS:
            raise Exception("Subscription limit reached: 240 subscriptions per hour.")
