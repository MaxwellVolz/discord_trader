import logging
import pandas as pd
import requests
import time
import discord
import asyncio
from datetime import datetime, timedelta
from bot.utils import calc_bollinger_bands, calc_RSI, calc_stochastic
from bot.plot_bot import plot_candlestick_with_bollinger
import os


class DataBot:
    def __init__(self, ctx, initial_time=None):
        logging.info("Initializing DataBot...")
        self.ctx = ctx
        # Set the initial time to 9/27 00:00 of the current year - 7
        self.initial_time = (
            initial_time if initial_time else datetime(2023, 9, 27, 0, 0)
        )

        self.last_timestamp = int(self.initial_time.timestamp())
        # Define end time as 9/27 24:00
        self.end_time = self.initial_time + timedelta(days=1)
        self.end_timestamp = int(self.end_time.timestamp())

        self.ctx = ctx
        # Initialize DataFrame with specified columns and types
        self.ohlc = pd.DataFrame(
            columns=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume_sum",
                "SMA",
                "Rolling_STD",
                "Bollinger_Upper_2",
                "Bollinger_Lower_2",
                "Bollinger_Upper_3",
                "Bollinger_Lower_3",
                "Bollinger_Upper_4",
                "Bollinger_Lower_4",
                "RSI",
                "Stochastic",
            ]
        )
        self.ohlc = self.ohlc.astype(
            {
                "Timestamp": "int64",
                "Open": "float64",
                "High": "float64",
                "Low": "float64",
                "Close": "float64",
                "Volume_sum": "float64",
                "SMA": "float64",
                "Rolling_STD": "float64",
                "Bollinger_Upper_2": "float64",
                "Bollinger_Lower_2": "float64",
                "Bollinger_Upper_3": "float64",
                "Bollinger_Lower_3": "float64",
                "Bollinger_Upper_4": "float64",
                "Bollinger_Lower_4": "float64",
                "RSI": "float64",
                "Stochastic": "float64",
            }
        )

    async def initialize(self):
        adjusted_date = self.initial_time + timedelta(days=1)
        csv_filename = f"output/{adjusted_date.strftime('%Y-%m-%d')}.csv"

        logging.info(f"Checking if we have {csv_filename}...")

        if os.path.exists(f"./{csv_filename}"):
            logging.info(f"Loading data from {csv_filename}")
            await self.ctx.send(
                "<:Pokeball:1157070938920190014> Data already captured, no "
                + f"need to catch 'em all again! Using {csv_filename} 🌟"
            )

            self.ohlc = pd.read_csv(f"./{csv_filename}")
        else:
            start_time = int(time.time())
            last_data_fetch_time = None
            temp_data_list = []

            while self.last_timestamp < self.end_timestamp:
                current_time = int(time.time())
                total_time_elapsed = current_time - start_time

                if last_data_fetch_time:
                    time_since_last_fetch = (
                        current_time - last_data_fetch_time
                    )  # Time since last get_data call
                else:
                    time_since_last_fetch = 0  # No data fetch has happened yet

                # Log the details
                logging.info(
                    "Running data collection cycle... Total time elapsed: "
                    + f"{total_time_elapsed}s, "
                    + f"Time since last fetch: {time_since_last_fetch}s."
                )

                last_data_fetch_time = (
                    current_time  # Update the time of the last data fetch
                )

                # Fetch raw data and append it to temp_data_list
                raw_data = self.get_data()
                if raw_data is not None:
                    temp_data_list.append(raw_data)

                await asyncio.sleep(2)

            # Concatenate all collected data and calculate indicators
            complete_raw_data = pd.concat(temp_data_list, ignore_index=True)
            self.calc_indicators(complete_raw_data)
            self.write_to_csv()

        plot_filename = plot_candlestick_with_bollinger(self.ohlc)
        logging.info(f"Images saved to {plot_filename}")
        await self.ctx.send(file=discord.File(plot_filename))

    def write_to_csv(self):
        adjusted_date = self.initial_time + timedelta(days=1)
        date_str = adjusted_date.strftime("%Y-%m-%d")  # Convert date to string
        output_path = f"./output/{date_str}.csv"
        self.ohlc.to_csv(output_path, index=False)
        logging.info(f"Data saved to {output_path}")

    def get_data(self):
        logging.info(f"Fetching data since {self.last_timestamp}...")
        kraken_url = f"https://api.kraken.com/0/public/Trades?pair=btcusd&since={self.last_timestamp}"
        response = requests.get(kraken_url)

        if response.status_code == 200:
            new_data = response.json()["result"]["XXBTZUSD"]
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

            self.last_timestamp = new_df["Timestamp"].max()

            logging.info(f"Fetched {len(new_df)} new data rows.")
            return new_df
        else:
            logging.error(f"Failed to fetch data. HTTP status: {response.status_code}")
            return None

    def calc_indicators(self, raw_data):
        raw_data.index = pd.to_datetime(raw_data["Timestamp"], unit="s")
        raw_data["Timestamp"] = pd.to_datetime(raw_data["Timestamp"], unit="s")

        price_ohlc = raw_data["Price"].resample("1T").ohlc()
        price_ohlc.columns = ["Open", "High", "Low", "Close"]

        # Calculate the volume sum for each time period.
        volume_sum = raw_data["Volume"].resample("1T").sum()
        price_ohlc["Volume_sum"] = volume_sum.values

        # Forward fill gaps in the data
        price_ohlc.bfill(inplace=True)

        price_ohlc["Timestamp"] = price_ohlc.index.astype("int64") // 10**9
        price_ohlc.reset_index(drop=True, inplace=True)

        price_ohlc = calc_bollinger_bands(price_ohlc)
        price_ohlc = calc_RSI(price_ohlc)
        price_ohlc = calc_stochastic(price_ohlc)

        self.ohlc = pd.concat([self.ohlc, price_ohlc]).drop_duplicates()


if __name__ == "__main__":
    logging.basicConfig(
        filename="data_bot.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    ctx = []

    my_bot = DataBot(26, ctx)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(my_bot.initialize())
