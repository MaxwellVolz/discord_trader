import logging
import pandas as pd
import time
import asyncio
from datetime import datetime, timedelta
from pytz import timezone
from pathlib import Path

import os
import aiohttp

# Initialize a lock for thread-safe operations
lock = asyncio.Lock()


class DataBot:
    def __init__(self, initial_time=None):
        logging.info("Initializing DataBot...")
        # Define the time zone
        pst = timezone("America/Los_Angeles")

        # Backup of times
        # self.initial_time = datetime(2023, 4, 1, 0, 0) - timedelta(hours=7)
        # self.last_timestamp = int(self.initial_time.timestamp())
        # self.end_time = datetime(2023, 5, 1, 0, 0, 0) - timedelta(hours=7)
        # self.end_timestamp = int(self.end_time.timestamp())

        self.initial_time = pst.localize(datetime(2023, 10, 4, 13, 0))
        self.end_time = pst.localize(datetime(2023, 10, 4, 20, 0))

        print(f"{self.initial_time} to {self.end_time}")
        print(
            f"{int(self.initial_time.timestamp())} to {int(self.end_time.timestamp())}"
        )

        # Convert to UNIX timestamps
        self.last_timestamp = int(self.initial_time.timestamp())
        self.end_timestamp = int(self.end_time.timestamp())

        self.temp_data_list = []

    async def initialize(self):
        # Divide the total time into parts
        amt_of_parts = 6
        time_range = (self.end_timestamp - self.last_timestamp) // amt_of_parts

        coroutines = [
            self.get_data(
                self.last_timestamp + i * time_range,
                self.last_timestamp + (i + 1) * time_range,
            )
            for i in range(amt_of_parts)
        ]
        await asyncio.gather(*coroutines)
        await self.save_to_csv()

    async def get_data(self, start_timestamp, end_timestamp):
        current_timestamp = start_timestamp
        last_pull_time = time.time()  # Initialize to current time

        total_time = end_timestamp - start_timestamp

        while current_timestamp < end_timestamp:
            curr_time = time.time()
            time_since_last_pull = int(curr_time - last_pull_time)

            progress_bar = self.format_progress_bar(
                current_timestamp - start_timestamp, total_time, time_since_last_pull
            )
            logging.info(progress_bar)

            raw_data, new_timestamp = await self.fetch_data(
                current_timestamp
            )  # Note the 'await' here

            async with lock:  # Lock only for this specific operation
                if raw_data is not None:
                    self.temp_data_list.append(raw_data)
                    current_timestamp = new_timestamp

            last_pull_time = curr_time
            await asyncio.sleep(2)

    async def fetch_data(self, current_timestamp):  # Made this coroutine
        await asyncio.sleep(1)
        kraken_url = f"https://api.kraken.com/0/public/Trades?pair=btcusd&since={current_timestamp}"
        async with aiohttp.ClientSession() as session:
            async with session.get(kraken_url) as response:
                data = await response.json()

                if "result" in data:
                    new_data = data["result"]["XXBTZUSD"]
                    new_df = pd.DataFrame(
                        new_data,
                        columns=[
                            "Price",
                            "Volume",
                            "Timestamp",
                            "Buy/Sell",
                            "Market/Limit",
                            "Misc",
                            "TradeID",
                        ],
                    )
                    new_df = new_df.astype(
                        {"Price": "float64", "Volume": "float64", "Timestamp": "int64"}
                    )
                    return new_df, new_df["Timestamp"].max()
                else:
                    logging.error(f"Failed to fetch data. Response: {data}")
                    await asyncio.sleep(5)  # Wait for 5 seconds on bad response
                    return None, current_timestamp

    def format_progress_bar(self, current, total, last_pull, bar_length=30):
        progress = current / total
        arrow = "=" * int(round(progress * bar_length) - 1)
        spaces = "-" * (bar_length - len(arrow))

        if len(arrow) > 0:
            arrow = arrow[:-1] + "o"

        return f"[{arrow}{spaces}] {current}/{total} - last pull {last_pull}s"

    async def save_to_csv(self):
        async with lock:
            if not self.temp_data_list:
                logging.info("No data to save.")
                return

            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            df = pd.concat(self.temp_data_list, ignore_index=True)
            # Sort the data by Timestamp
            df = df.sort_values(by="Timestamp")

            csv_filename = (
                output_dir / f"{self.last_timestamp}_to_{int(time.time())}.csv"
            )

            try:
                df.to_csv(csv_filename, index=False)
                self.temp_data_list.clear()
                print(f"Data successfully written to {csv_filename}")
                logging.info(f"Data successfully written to {csv_filename}")
            except Exception as e:
                logging.error(f"Failed to save CSV. Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        filename="super_data_bot.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    data_bot = DataBot()
    asyncio.run(data_bot.initialize())
