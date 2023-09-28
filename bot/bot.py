import logging
import pandas as pd
import requests
import time
import asyncio
import os
import discord
from bot.utils import calc_bollinger_bands, calc_RSI, calc_stochastic
from bot.plot import plot_and_save

# from bot.plot import candlestick_plot


class TradeBot:
    def __init__(self, ctx):
        logging.info("Initializing TradeBot...")
        self.ctx = ctx
        self.last_timestamp = int(time.time()) - 30 * 60
        # Initialize DataFrame with specified columns and types
        self.one_min_ohlc = pd.DataFrame(
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
        self.one_min_ohlc = self.one_min_ohlc.astype(
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
        raw_data = self.get_data()
        self.calc_indicators(raw_data)
        logging.info(self.one_min_ohlc)
        # await self.ctx.send(self.one_min_ohlc)
        filename = plot_and_save(self.one_min_ohlc)
        print(f"plotted! {filename}")

        await self.ctx.send(file=discord.File(filename))
        print("posted!")

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

            logging.info(f"Fetched {len(new_df)} new data rows.")
            return new_df
        else:
            logging.error(f"Failed to fetch data. HTTP status: {response.status_code}")
            return None

    def calc_indicators(self, raw_data):
        # Convert the 'Timestamp' column to a DatetimeIndex
        raw_data.index = pd.to_datetime(raw_data["Timestamp"], unit="s")

        raw_data["Timestamp"] = pd.to_datetime(raw_data["Timestamp"], unit="s")
        raw_data.set_index("Timestamp", inplace=True)

        price_ohlc = raw_data["Price"].resample("1T").ohlc()
        price_ohlc.columns = ["Open", "High", "Low", "Close"]
        price_ohlc["Timestamp"] = (
            price_ohlc.index.astype("int64") // 10**9
        )  # Convert to UNIX timestamp
        price_ohlc.reset_index(drop=True, inplace=True)

        price_ohlc = calc_bollinger_bands(price_ohlc)
        print("calc_bollinger_bands complete")
        price_ohlc = calc_RSI(price_ohlc)
        print("calc_RSI complete")
        price_ohlc = calc_stochastic(price_ohlc)
        print("calc_stochastic complete")

        self.one_min_ohlc = pd.concat([self.one_min_ohlc, price_ohlc]).drop_duplicates()

    async def start_polling(self):
        # Placeholder
        pass

    async def start(self):
        # Placeholder
        pass
