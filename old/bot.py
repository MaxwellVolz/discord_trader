import logging
import pandas as pd
import requests
import time
import asyncio
import os
from bot.utils import calc_bollinger_bands, calc_RSI, calc_stochastic
from bot.plot import candlestick_plot


class TradeBot:
    def __init__(self, ctx):
        logging.info("Initializing TradeBot...")
        self.ctx = ctx
        self.last_timestamp = (
            int(time.time()) - 30 * 60
        )  # Timestamp from 30 minutes ago
        self.one_min_ohlc = None

    async def initialize_data(self):
        logging.info("Fetching initial data...")
        raw_data = self.fetch_data()
        parsed_data, self.one_min_ohlc, insights = self.initial_summary(raw_data)

        logging.info(f"Initial insights: {insights}")
        await self.ctx.send(f"Here we go! Initial insights:\n{insights}")

        logging.info("Starting to poll for new data...")
        await self.start_polling()

    def initial_summary(self, raw_data):
        summary = raw_data.describe()

        # Time-related calculations with reduced precision
        start_time = (
            pd.to_datetime(raw_data["Timestamp"], unit="s")
            .min()
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        end_time = (
            pd.to_datetime(raw_data["Timestamp"], unit="s")
            .max()
            .strftime("%Y-%m-%d %H:%M:%S")
        )

        time_between = pd.to_datetime(end_time) - pd.to_datetime(start_time)

        samples_per_hour = len(raw_data) * 3600 / time_between.total_seconds()

        # Prepare 1-minute OHLC data
        raw_data["Timestamp_copy"] = raw_data["Timestamp"]
        raw_data.index = pd.to_datetime(raw_data["Timestamp"], unit="s")
        raw_data["Timestamp"] = raw_data["Timestamp_copy"]

        price_ohlc = raw_data["Price"].resample("1T").ohlc()
        # price_ohlc.columns = [
        #     f"Price_{col}" for col in price_ohlc.columns
        # ]  # Flatten the columns

        # print("Existing columns in DataFrame:")
        # print(self.one_min_ohlc.columns.tolist())

        price_ohlc.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
            },
            inplace=True,
        )

        print(price_ohlc)

        volume_sum = raw_data["Volume"].resample("1T").sum()
        volume_sum.name = "Volume_sum"

        # Concatenate these DataFrames along axis=1
        one_min_ohlc = pd.concat([price_ohlc, volume_sum], axis=1)

        # Insights
        insights = (
            f"Data Summary:\n{summary}\n"
            f"Start Time: {start_time}\n"
            f"End Time: {end_time}\n"
            f"Samples per Hour: {samples_per_hour:.2f}\n"
            f"One-Min OHLC:\n{one_min_ohlc.head()}"  # Displaying first few rows
        )

        return (
            raw_data,
            one_min_ohlc,
            insights,
        )  # Added one_min_ohlc in the return statement

    async def start_polling(self):
        logging.info("Polling started.")
        start_time = time.time()

        while True:
            # Fetch and append new data
            new_data = self.fetch_data()
            logging.info(f"New raw data: {new_data.head()}")

            _, new_one_min_ohlc, _ = self.initial_summary(new_data)
            logging.info("Appending new 1-minute OHLC data to existing DataFrame.")

            # Append only new rows to avoid overlaps
            self.one_min_ohlc = pd.concat(
                [self.one_min_ohlc, new_one_min_ohlc]
            ).drop_duplicates()

            # calc the Simple Moving Average (SMA) and Rolling Standard Deviation (Rolling_STD)
            window_size = 20  # You can choose another window size
            self.one_min_ohlc["SMA"] = (
                self.one_min_ohlc["Close"].rolling(window=window_size).mean().ffill()
            )
            self.one_min_ohlc["Rolling_STD"] = (
                self.one_min_ohlc["Close"].rolling(window=window_size).std().ffill()
            )

            try:
                self.one_min_ohlc = calc_bollinger_bands(self.one_min_ohlc)
                self.one_min_ohlc = calc_RSI(self.one_min_ohlc)
                self.one_min_ohlc = calc_stochastic(self.one_min_ohlc)
            except Exception as e:
                logging.error(
                    f"An error occurred in one of the calculation functions: {e}"
                )

            elapsed_time = time.time() - start_time
            if elapsed_time >= 20:
                if not os.path.exists("output"):
                    os.mkdir("output")

                self.one_min_ohlc.to_csv("output/one_min_ohlc.csv")
                logging.info("Saved one_min_ohlc to output/one_min_ohlc.csv.")

                image_path_1, image_path_2 = candlestick_plot(
                    self.one_min_ohlc
                )  # Call your plotting function
                await self.ctx.send(file=image_path_1)
                await self.ctx.send(file=image_path_2)

                start_time = time.time()

            await asyncio.sleep(2)

    def fetch_data(self):
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

            for col in ["Price", "Volume", "Timestamp"]:
                new_df[col] = pd.to_numeric(new_df[col], errors="coerce")

            logging.info(f"Fetched {len(new_df)} new data rows.")
            return new_df
        else:
            logging.error(f"Failed to fetch data. HTTP status: {response.status_code}")
            return None

    async def start(self):
        await self.ctx.send("TradeBot is running.")
