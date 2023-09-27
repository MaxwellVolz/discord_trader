# main_trading_bot.py
from discord.ext import commands, tasks
import pandas as pd
import requests
import talib
from util import calculate_bollinger_bands, calculate_RSI, calculate_stochastic
from KrakenDataPlotter import KrakenDataPlotter  # Import your plotting class
import os
import json

# Setup Discord Bot
bot = commands.Bot(command_prefix="!")


class KrakenTradeBot:
    def __init__(self, initial_time_since):
        self.df = None  # Initialize DataFrame to store trade data
        self.time_since = initial_time_since  # Initialize with some start time

    def fetch_and_append_data(self):
        last_timestamp = (
            self.df["Timestamp"].max() if self.df is not None else self.time_since
        )
        kraken_url = (
            f"https://api.kraken.com/0/public/Trades?pair=btcusd&since={last_timestamp}"
        )

        # Fetch new trades
        response = requests.get(kraken_url)
        new_data = response.json()["result"]["XXBTZUSD"]

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

        # Append new data to existing DataFrame
        self.df = (
            pd.concat([self.df, new_df]).reset_index(drop=True)
            if self.df is not None
            else new_df
        )

    def consolidate_data(self):
        # Ensure data and Timestamp exist
        if self.df is None or "Timestamp" not in self.df.columns:
            return

        # Convert the Timestamp to a DateTimeIndex
        self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], unit="s")
        self.df.set_index("Timestamp", inplace=True)

        # Use resample to create OHLC candles
        ohlc_dict = {
            "Price": "ohlc",
            "Volume": "sum",
        }

        self.df_resampled = self.df.resample("1S").apply(ohlc_dict).dropna()

        # Flatten the MultiIndex for ease of use
        self.df_resampled.columns = [
            "_".join(tup).rstrip("_") for tup in self.df_resampled.columns.values
        ]

    def calculate_indicators(self):
        # Logic to calculate Bollinger Bands, RSI, and Stochastic:

        # Bollinger Bands: The upper, middle (SMA), and lower Bollinger
        # Bands are calculated for the 'Close' prices with a 20-period
        # window. We store these in the DataFrame under the respective column
        # names.

        # RSI (Relative Strength Index): The RSI is calculated for the 'Close'
        # prices over a 14-period window
        # and stored in the DataFrame.

        # Stochastic Oscillator: The fast %K and %D lines are calculated using
        # the high, low, and close prices.

        # They are stored in the DataFrame under their respective column names.

        if self.df_resampled is None:
            return

        close = self.df_resampled["Price_close"]

        # Calculate Bollinger Bands
        upper, middle, lower = talib.BBANDS(close, timeperiod=20)
        self.df_resampled["BBAND_upper"] = upper
        self.df_resampled["BBAND_middle"] = middle
        self.df_resampled["BBAND_lower"] = lower

        # Calculate RSI
        rsi = talib.RSI(close, timeperiod=14)
        self.df_resampled["RSI"] = rsi

        # Calculate Stochastic
        high = self.df_resampled["Price_high"]
        low = self.df_resampled["Price_low"]
        fastk, fastd = talib.STOCH(
            high,
            low,
            close,
            fastk_period=5,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0,
        )
        self.df_resampled["STOCH_fastk"] = fastk
        self.df_resampled["STOCH_fastd"] = fastd

    def evaluate_entry_conditions(self):
        # Assuming self.df_resampled contains the indicators and close price
        last_row = self.df_resampled.iloc[-1]
        second_last_row = self.df_resampled.iloc[-2]

        # Initialize entry condition variables
        entry_conditions_met = False
        reason = ""

        # Trigger Conditions for Entry
        if (
            second_last_row["Price_close"] < second_last_row["BBAND_lower"]
            and last_row["Price_close"] > last_row["BBAND_lower"]
            and last_row["RSI"] > 20
            and 20 < last_row["STOCH_fastk"] < 40
            and 20 < last_row["STOCH_fastd"] < 40
        ):
            entry_conditions_met = True
            reason = f"Entry conditions met. RSI: {last_row['RSI']}, Stochastic: {last_row['STOCH_fastk']}, Band crossed: BBAND_lower"

        return entry_conditions_met, reason

    def evaluate_exit_conditions(self, entry_price):
        # Assuming self.df_resampled contains the indicators and close price
        last_row = self.df_resampled.iloc[-1]

        # Initialize exit condition variables
        exit_conditions_met = False
        exit_type = ""
        exit_price = 0.0
        profit_or_loss = ""

        # Calculate the yellow band (as it wasn't in your original requirements, assuming it's a simple average)
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
            msg = await ctx.send(
                f"Looking for trade...\nFound an entry at {price}. Placing a buy order..."
            )
            # Simulate placing a buy order here
            await msg.edit(content=f"Buy order placed at {price}.")

        elif entry_exit == "exit":
            msg = await ctx.send(
                f"Exiting position at {price} for a {profit_or_loss}. Placing a sell order..."
            )
            # Simulate placing a sell order here
            await msg.edit(
                content=f"Exited position at {price} for a {profit_or_loss}."
            )

        else:
            await ctx.send("Invalid order type.")

    async def run(self, ctx):
        self.fetch_and_append_data()
        self.consolidate_data()
        self.calculate_indicators()

        entry_met, entry_reason = self.evaluate_entry_conditions()

        if entry_met:
            entry_price = self.df_resampled.iloc[-1]["Price_close"]
            await self.place_order(ctx, "entry", entry_price)

        exit_met, exit_type, exit_price, profit_or_loss = self.evaluate_exit_conditions(
            entry_price
        )

        if exit_met:
            await self.place_order(ctx, "exit", exit_price, profit_or_loss)


@tasks.loop(seconds=2)
async def trading_bot(ctx):
    # Instantiate the KrakenTradeBot class
    bot = KrakenTradeBot(initial_time_since="some_initial_time")

    # Run the trading bot logic
    await bot.run(ctx)


# Starts the trading_bot loop running in the background
trading_bot.start()
bot.run("your_token_here")
