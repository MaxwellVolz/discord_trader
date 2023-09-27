from discord import Intents, File
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import os
import requests
import pandas as pd
import numpy as np
import json

import logging

logging.basicConfig(
    filename="trade_bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

from util import calculate_bollinger_bands, calculate_RSI, calculate_stochastic

# from KrakenDataPlotter import KrakenDataPlotter


class KrakenTradeBot:
    def __init__(self, initial_time_since, ctx):
        self.ctx = ctx
        self.df = None
        self.time_since = initial_time_since
        self.trade_end_time = datetime.now() + timedelta(hours=1)
        self.trade_initialized = False
        self.df_resampled = None

    def fetch_and_append_data(self):
        if self.df is not None and "Timestamp" in self.df.columns:
            last_timestamp = self.df["Timestamp"].max()
        else:
            last_timestamp = (
                self.time_since
            )  # This value will be used if `self.df` is None or if "Timestamp" is not in columns

        kraken_url = (
            f"https://api.kraken.com/0/public/Trades?pair=btcusd&since={last_timestamp}"
        )

        # Fetch new trades

        try:
            response = requests.get(kraken_url)
            new_data = response.json()["result"]["XXBTZUSD"]
            # logging.info(
            #     f"Fetched new data from Kraken: \n{json.dumps(new_data[:5], indent=4)}"
            # )
            logging.info(f"DataFrame before resampling: \n{self.df.head()}")
            logging.info(f"DataFrame dtypes: \n{self.df.dtypes}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

        # Create DataFrame for new trades
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

        # Cast columns to appropriate data types
        numeric_cols = ["Price", "Volume", "Timestamp", "TradeID"]
        new_df[numeric_cols] = new_df[numeric_cols].apply(
            pd.to_numeric, errors="coerce"
        )

        # Append new data to existing DataFrame
        self.df = (
            pd.concat([self.df, new_df]).reset_index(drop=True)
            if self.df is not None
            else new_df
        )

        # Log the DataFrame head to verify
        logging.info(f"Appended DataFrame: \n{self.df.head()}")
        logging.info(f"DataFrame dtypes after casting: \n{self.df.dtypes}")

    def consolidate_data(self):
        # Ensure data and Timestamp exist
        if self.df is None or "Timestamp" not in self.df.columns:
            return

        # Check if DataFrame is empty
        if self.df.empty:
            print("DataFrame is empty. Skipping resampling.")
            return

        # Check if DataFrame has numeric columns
        if not any(self.df.dtypes.apply(np.issubdtype, args=(np.number,))):
            print("No numeric columns to aggregate in DataFrame.")
            return

        # Convert the Timestamp to a DateTimeIndex
        self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], unit="s")
        self.df.set_index("Timestamp", inplace=True)

        # Use resample to create OHLC candles
        ohlc_dict = {
            "Price": "ohlc",
            "Volume": "sum",
        }

        try:
            self.df_resampled = self.df.resample("1S").apply(ohlc_dict).dropna()

            # Flatten the MultiIndex for ease of use
            self.df_resampled.columns = [
                "_".join(tup).rstrip("_") for tup in self.df_resampled.columns.values
            ]
        except Exception as e:
            print(f"An error occurred during resampling: {e}")

    def calculate_indicators(self):
        # Bollinger Bands: The upper, middle (SMA), and lower Bollinger
        # Bands are calculated for the 'Close' prices with a 20-period
        # window. We store these in the DataFrame under the respective column
        # names.
        self.df_resampled = calculate_bollinger_bands(self.df_resampled)

        # RSI (Relative Strength Index): The RSI is calculated for the 'Close'
        # prices over a 14-period window
        # and stored in the DataFrame.
        self.df_resampled = calculate_RSI(self.df_resampled)

        # Stochastic Oscillator: The fast %K and %D lines are calculated using
        # the high, low, and close prices.
        self.df_resampled = calculate_stochastic(self.df_resampled)

    def evaluate_entry_conditions(self):
        last_row = self.df_resampled.iloc[-1]
        second_last_row = self.df_resampled.iloc[-2]
        entry_conditions_met = False
        reason = ""

        if (
            last_row["Price_close"] <= last_row["BBAND_lower"]
            and last_row["RSI"] < 20
            and (last_row["STOCH_fastk"] < 20 and last_row["STOCH_fastd"] < 20)
        ):
            if (
                second_last_row["Price_close"] < second_last_row["BBAND_lower"]
                and last_row["Price_close"] > last_row["BBAND_lower"]
                and last_row["RSI"] > 20
                and (
                    20 < last_row["STOCH_fastk"] < 40
                    and 20 < last_row["STOCH_fastd"] < 40
                )
            ):
                entry_conditions_met = True
                reason = (
                    f"Entry conditions met.\n"
                    f"RSI: {last_row['RSI']}\n"
                    f"Stochastic: {last_row['STOCH_fastk']}\n"
                    f"Band crossed: BBAND_lower"
                )

        return entry_conditions_met, reason

    def evaluate_exit_conditions(self, entry_price):
        if entry_price is None:
            return

        # Assuming self.df_resampled contains the indicators and close price
        last_row = self.df_resampled.iloc[-1]

        # Initialize exit condition variables
        exit_conditions_met = False
        exit_type = ""
        exit_price = 0.0
        profit_or_loss = ""

        # Calculate the yellow band (as it wasn't in your original
        # requirements, assuming it's a simple average)
        bb_yellow = (last_row["BBAND_upper"] + last_row["BBAND_lower"]) / 2

        # Stop Loss at Yellow Band
        if last_row["Price_close"] <= bb_yellow:
            exit_conditions_met = True
            exit_type = "Stop Loss"
            exit_price = bb_yellow
            profit_or_loss = "loss" if exit_price < entry_price else "profit"

        # Take Profit (For a one-to-one risk-reward ratio)
        take_profit = entry_price + (
            entry_price - bb_yellow
        )  # One-to-one risk-reward ratio
        if last_row["Price_close"] >= take_profit:
            exit_conditions_met = True
            exit_type = "Take Profit"
            exit_price = take_profit
            profit_or_loss = "profit"

        return exit_conditions_met, exit_type, exit_price, profit_or_loss

    async def place_order(self, ctx, entry_exit, price, profit_or_loss=None):
        if entry_exit == "entry":
            msg = await self.ctx.send(
                f"Looking for trade...\nFound an entry at {price}."
                "Placing a buy order..."
            )
            # Simulate placing a buy order here
            await msg.edit(content=f"Buy order placed at {price}.")

        elif entry_exit == "exit":
            msg = await self.ctx.send(
                f"Exiting position at {price} for a {profit_or_loss}. "
                "Placing a sell order..."
            )
            # Simulate placing a sell order here
            await msg.edit(
                content=f"Exited position at {price} for a {profit_or_loss}."
            )

        else:
            await self.ctx.send("Invalid order type.")

    async def run(self):
        entry_price = None  # Initialize to None as you've done

        if not self.trade_initialized or datetime.now() >= self.trade_end_time:
            return

        self.fetch_and_append_data()
        self.consolidate_data()

        if self.df_resampled is None:
            return

        self.calculate_indicators()

        entry_met, entry_reason = self.evaluate_entry_conditions()

        if entry_met:
            entry_price = self.df_resampled.iloc[-1]["Price_close"]
            await self.place_order(self.ctx, "entry", entry_price)

        if entry_price is not None:
            (
                exit_met,
                exit_type,
                exit_price,
                profit_or_loss,
            ) = self.evaluate_exit_conditions(entry_price)
            if exit_met:
                await self.place_order(self.ctx, "exit", exit_price, profit_or_loss)
        else:
            # Log or handle the case where entry_price remains None.
            logging.info("entry_price is None.")


intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="The coolest crypto plotting bot around!",
    intents=intents,
)

trading_bot_instance = None


@bot.event
async def on_command_error(ctx, error):
    print(error)


@tasks.loop(seconds=5)
async def trading_bot():
    global trading_bot_instance
    if trading_bot_instance:
        await trading_bot_instance.run()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.command(aliases=["trade"])
async def start(ctx):
    global trading_bot_instance
    trading_bot_instance = KrakenTradeBot("some_initial_time", ctx)
    trading_bot_instance.trade_initialized = True
    trading_bot.start()  # Starts the loop to run every 5 minutes
    await ctx.send("Initialized KrakenTradeBot.")


@bot.command(aliases=["stonks"])
async def plot_kraken_data(ctx):
    msg = await ctx.send("Generating plot...")
    # ... (your plotting code)
    await msg.edit(content="Plotted.")


bot.run(os.environ["DISCORD_TOKEN"])
