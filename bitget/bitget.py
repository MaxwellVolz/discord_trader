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
from bitget.utils import (
    calc_bollinger_bands,
    calc_RSI,
    calc_stochastic,
    convert_to_dataframe,
    update_dataframe_with_new_data,
    format_trigger_stats,
    format_entry_stats,
)

# Place configurations and constants here
RATE_LIMIT_CONNECTIONS = 100
RATE_LIMIT_SUBSCRIPTIONS = 240


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
        self.trigger_conditions_met = False

        self.curr_trigger_stats = None
        self.curr_entry_stats = None

    # Remember to call check_rate_limits before making additional
    # subscriptions in other parts of your code to ensure
    # you don't exceed the rate limits.
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

    def generate_signature(self):
        timestamp = str(int(time.time()))
        content = f"{timestamp}GET/user/verify"

        h = hmac.new(
            self.secret_key.encode(), msg=content.encode(), digestmod=hashlib.sha256
        )
        hashed_content = h.digest()

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

                    action_type = parsed_message.get("action", "")

                    if action_type == "snapshot":
                        self.snapshot_received = True
                        self.df = convert_to_dataframe(parsed_message["data"])

                        if self.check_trigger_conditions(self.df):
                            print("Conditions met on snapshot! Incredible!!")

                        # TODO: remove this exit on snapshot
                        async with self.update_received:
                            self.update_received.notify_all()

                    elif action_type == "update":
                        latest_candle = parsed_message["data"][0]
                        # Check if new_candle is different from the last candle in the DataFrame
                        if latest_candle == self.df.iloc[-1].to_dict():
                            self.df = update_dataframe_with_new_data(
                                self.df, latest_candle
                            )

                            if self.trigger_conditions_met:
                                if self.check_entry_conditions(self.df):
                                    # self.place_order()

                                    self.trigger_conditions_met = False

                                    async with self.update_received:
                                        self.update_received.notify_all()

                            elif self.check_trigger_conditions(self.df):
                                print("Trigger conditions met!")
                                self.trigger_conditions_met = True
                            else:
                                self.trigger_conditions_met = False

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

    def check_trigger_conditions(self, df_to_check):
        # Check if the last candle touches or penetrates the lower red Bollinger band
        last_candle = df_to_check.iloc[-1]
        lower_bollinger = last_candle["Bollinger_Lower_2"]

        touch_or_penetrate = any(
            [
                last_candle["Open"] <= lower_bollinger,
                last_candle["Close"] <= lower_bollinger,
                last_candle["Low"] <= lower_bollinger,
                last_candle["High"] <= lower_bollinger,
            ]
        )

        # Check if both RSI and stochastic are below the 20 level for the last candle
        rsi_val = last_candle["RSI"]
        rsi_below_20 = rsi_val < 20

        last_candle_stoch = last_candle["Stochastic"]
        stochastic_below_20 = last_candle_stoch < 20

        # if touch_or_penetrate:
        #     print("Touch or penetrate")
        # if rsi_below_20:
        #     print("RSI below 20")
        # if stochastic_below_20:
        #     print("Stochastic below 20")

        self.curr_trigger_stats = {
            "touch_or_penetrate": touch_or_penetrate,
            "rsi_val": rsi_val,
            "rsi_below_20": rsi_below_20,
            "stoch_val": last_candle_stoch,
            "stochastic_below_20": stochastic_below_20,
        }

        # Both conditions must be met
        if touch_or_penetrate and (rsi_below_20 or stochastic_below_20):
            # Debug / pretty print for understanding

            self.trigger_conditions_met = True
            return True
        return False

    def check_entry_conditions(self, df_to_check):
        last_candle = df_to_check.iloc[-1]
        second_last_candle = df_to_check.iloc[-2]

        # The next candle retraces and closes back through the red Bollinger band.
        retraces_through_band = last_candle["Close"] > last_candle["Bollinger_Lower_2"]

        # RSI goes above 20
        rsi_val = last_candle["RSI"]
        rsi_above_20 = rsi_val > 20

        # Stochastic lines cross between the 20 and 40 levels
        last_candle_stoch = last_candle["Stochastic"]

        stochastic_cross = (second_last_candle["Stochastic"] < 20) and (
            last_candle_stoch > 20
        )
        stochastic_between_20_and_40 = 20 < last_candle["Stochastic"] < 40

        self.curr_entry_stats = {
            "retraces_through_band": retraces_through_band,
            "rsi_above_20": rsi_above_20,
            "rsi_val": rsi_val,
            "stochastic_cross": stochastic_cross,
            "stochastic_between_20_and_40": stochastic_between_20_and_40,
            "last_candle_stoch": last_candle_stoch,
        }

        print(format_trigger_stats(self.curr_trigger_stats))
        print(format_entry_stats(self.curr_entry_stats))

        if (
            retraces_through_band
            and rsi_above_20
            and stochastic_cross
            and stochastic_between_20_and_40
        ):
            return True

        return False

    def get_order(self):
        last_candle = self.df.iloc[-1]
        buy_price = last_candle[
            "Close"
        ]  # Assuming you are buying at the close price of the last candle
        stop_loss_level = last_candle[
            "Bollinger_Lower_3"
        ]  # Yellow Bollinger band, adjust as needed
        risk_amount = buy_price - stop_loss_level  # The risk for this trade

        take_profit_level = buy_price + risk_amount  # One-to-one risk-reward ratio

        # TODO: Place the buy order using your trading API here

        # TODO: Set the stop loss using your trading API here

        # TODO: Set the take profit using your trading API here

        return (
            f"Buy order placed at {buy_price}\n"
            + f"Stop loss set at {stop_loss_level}\n"
            + f"Take profit set at {take_profit_level}"
        )

    def backtest_on_snapshot(self):
        self.df.reset_index(inplace=True)  # Reset the index to integers
        n_rows = len(self.df)
        print(f"Total rows to check: {n_rows}")  # Debug statement

        for i in range(n_rows):
            temp_df = self.df.iloc[
                : i + 1
            ].copy()  # Create a temporary DataFrame using a copy

            if self.check_trigger_conditions(temp_df):
                row = temp_df.iloc[-1]
                timestamp_utc = row["Timestamp"].tz_localize(
                    "UTC"
                )  # Localize the timestamp to UTC
                timestamp_pst = timestamp_utc.tz_convert(
                    "America/Los_Angeles"
                )  # Convert to PST

                print(f"Trigger met at index {i}, {timestamp_pst} PST".center(80, "*"))

                # Check entry conditions on the next row, if it exists
                if i + 1 < n_rows:
                    next_df = self.df.iloc[
                        i : i + 2
                    ].copy()  # Include the current and the next row
                    if self.check_entry_conditions(
                        next_df
                    ):  # Send the DataFrame, not Series
                        next_row = next_df.iloc[-1]
                        next_timestamp_utc = next_row["Timestamp"].tz_localize("UTC")
                        next_timestamp_pst = next_timestamp_utc.tz_convert(
                            "America/Los_Angeles"
                        )

                        print("".center(80, "*"))
                        print(
                            f"Entry conditions met at index {i + 1}, {next_timestamp_pst} PST".center(
                                80, "*"
                            )
                        )
                        print("".center(80, "*"))

                    else:
                        print(f" No entry at index {i + 1} ".center(80, "*"))

        print(f"Total rows checked: {n_rows}")  # Debug statement

    def get_candle_data(self):
        return self.df


# Initialize and connect
# bitget = BitGet()
# asyncio.get_event_loop().run_until_complete(bitget.connect(duration=10))
