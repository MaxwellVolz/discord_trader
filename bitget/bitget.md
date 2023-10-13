
the goal is:

1. add establish websocket def
    1. subscribe to data
    2. get snapshot data
    3. get update data
        1. append when new data 

3. get data(duration = seconds)
    2. trim data to selection
    return df

the current script is:

class BitGet:
    def __init__
    def establish_websocket
        <!-- nothing here... -->
    def check_rate_limits
    def generate_signature
    async def send_ping(self, ws):
        while not self.is_subscribed:  # Only send pings if not subscribed
            await ws.send("ping")
            await asyncio.sleep(30)

    def unsubscribe
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
    def check_trigger_conditions
    def check_entry_conditions
    def get_order
    def backtest_on_snapshot
    def get_candle_data



in our utils thats imported we have 

def trim_data_to_duration(df, duration_in_seconds):
    # we want the data from now until the duration in seconds ago'
    now = pd.Timestamp.now()
    duration = pd.Timedelta(seconds=duration_in_seconds)
    start = now - duration
    df = df.loc[start:]

    return df

let me know if you need more information