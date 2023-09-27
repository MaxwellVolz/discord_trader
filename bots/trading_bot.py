from discord import Intents, File
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import os
import requests
import pandas as pd
import numpy as np
import json
import logging
from plot_candlestick_with_bollinger import plot_and_save_candlestick


logging.basicConfig(
    filename="trade_bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

from util import calculate_bollinger_bands, calculate_RSI, calculate_stochastic

print("hey")


class TradeBot:
    def __init__(self, ctx):
        logging.info("Initializing TradeBot...")
        self.ctx = ctx
        self.trade_initialized = False
        self.entry_price = None
        self.last_timestamp = 0
        self.position_open = False
        self.df = pd.DataFrame(
            columns=[
                "Price",
                "Volume",
                "Timestamp",
                "Buy/Sell",
                "Market/Limit",
                "Misc",
                "TradeID",
            ],
            dtype=object,
        )

        # Explicitly set numeric dtypes for specific columns
        self.df["Price"] = self.df["Price"].astype(float)
        self.df["Volume"] = self.df["Volume"].astype(float)
        self.df["Timestamp"] = self.df["Timestamp"].astype(float)

    def fetch_data(self):
        logging.info("Fetching data...")
        kraken_url = f"https://api.kraken.com/0/public/Trades?pair=btcusd&since={self.last_timestamp}"

        try:
            response = requests.get(kraken_url)
            new_data = response.json()["result"]["XXBTZUSD"]

            # Creating a DataFrame from the new data
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

            # Convert the necessary columns to numeric types
            for col in ["Price", "Volume", "Timestamp"]:
                new_df[col] = pd.to_numeric(new_df[col], errors="coerce")

            # Concatenate the new data to the existing DataFrame
            if not self.df.empty and not new_df.empty:
                self.df = pd.concat([self.df, new_df], sort=False).reset_index(
                    drop=True
                )
            elif not new_df.empty:
                self.df = new_df

            logging.info(f"DataFrame head: {self.df.head()}")
            logging.info(f"DataFrame columns: {self.df.columns}")

            # Convert UNIX 'Timestamp' to datetime
            self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], unit="s")

            # Set 'Timestamp' as the index
            self.df.set_index("Timestamp", inplace=True)

            # Log the first and last timestamps, and duration
            first_ts = self.df.index.min()
            last_ts = self.df.index.max()
            duration = last_ts - first_ts
            logging.info(
                f"First Timestamp: {first_ts}, Last Timestamp: {last_ts}, Duration: {duration}"
            )

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def determine_best_bucket_size(self, df):
        # Calculate standard deviation of price changes
        df["Price_Change"] = df["Price"].diff()
        std_dev_price = np.std(df["Price_Change"].dropna())

        # Calculate average trade volume
        avg_volume = np.mean(df["Volume"])

        # Dynamically set bucket size based on calculated metrics
        if std_dev_price > 20:  # or any other threshold
            bucket_size = "1T"  # 1 minute
        elif std_dev_price > 10:  # or any other threshold
            bucket_size = "5T"  # 5 minutes
        else:
            bucket_size = "15T"  # 15 minutes

        logging.info(f"Standard Deviation of Price: {std_dev_price}")
        logging.info(f"Average Trade Volume: {avg_volume}")
        logging.info(f"Selected Bucket Size: {bucket_size}")

        return bucket_size

    def calculate_indicators(self):
        best_bucket_size = self.determine_best_bucket_size(self.df)

        logging.info("Calculating indicators...")

        # Use the dynamically determined bucket size
        df_resampled = self.df.resample(best_bucket_size).agg(
            {
                "Price": "ohlc",
                "Volume": "sum",
            }
        )

        logging.info(f"DataFrame head: {df_resampled.head()}")
        logging.info(f"DataFrame columns: {df_resampled.columns}")

        df_resampled.columns = [f"{y}_{x}" for x, y in df_resampled.columns]

        df_resampled = calculate_bollinger_bands(df_resampled)
        df_resampled = calculate_RSI(df_resampled)
        df_resampled = calculate_stochastic(df_resampled)

        # Drop NaN values
        df_resampled.dropna(inplace=True)

        self.df = df_resampled

        logging.info(f"DataFrame head: {self.df.head()}")
        logging.info(f"DataFrame columns: {self.df.columns}")

        logging.info(f"DataFrame size after dropping NaNs: {len(self.df)}")

        logging.info("Indicators calculated.")

    def evaluate_entry_conditions(self):
        logging.info("Evaluating entry conditions...")

        if len(self.df) < 2:
            logging.info("Not enough data to evaluate entry conditions.")
            return False, "Not enough data"

        last_row = self.df.iloc[-1]
        reason = "Conditions not met"

        # Log the specific indicators you're evaluating
        logging.info(f"Evaluating for Timestamp: {last_row.name}")
        logging.info(f"BBAND_lower: {last_row['BBAND_lower']}")
        logging.info(f"close_Price: {last_row['close_Price']}")
        logging.info(f"RSI: {last_row['RSI']}")
        logging.info(f"STOCH_fastk: {last_row['STOCH_fastk']}")
        logging.info(f"STOCH_fastd: {last_row['STOCH_fastd']}")

        # Check if the conditions for entry are met
        if (
            last_row["BBAND_lower"] >= last_row["close_Price"]
            and last_row["RSI"] < 20
            and last_row["STOCH_fastk"] < 20
            and last_row["STOCH_fastd"] < 20
        ):
            # Check the next candle
            next_row = self.df.iloc[
                -2
            ]  # Assuming the data is sorted in ascending order by time
            if (
                next_row["close_Price"] > next_row["BBAND_lower"]
                and next_row["RSI"] > 20
                and 20 <= next_row["STOCH_fastk"] <= 40
                and 20 <= next_row["STOCH_fastd"] <= 40
            ):
                logging.info("Entry conditions met.")
                self.entry_price = last_row["close_Price"]
                reason = "Entry conditions met"
                return True, reason

        return False, reason

    def evaluate_exit_conditions(self):
        logging.info("Evaluating exit conditions...")
        last_row = self.df.iloc[-1]
        reason = "Conditions not met"

        if self.entry_price is None:
            reason = "Exit conditions can't be evaluated before an entry."
            return False, reason

        stop_loss = last_row["BBAND_middle"]
        take_profit = self.entry_price * 2 - stop_loss

        if (
            last_row["close_Price"] <= stop_loss
            or last_row["close_Price"] >= take_profit
        ):
            logging.info("Exit conditions met.")
            reason = "Exit conditions met"
            return True, reason
        return False, reason

    def place_order(self, entry_exit, price, profit_or_loss=None):
        logging.info(f"Placing {entry_exit} order at {price}.")
        # Place your order here
        return

    async def save_and_post_plot(self):
        # Generate the plot and save it to a file
        file_path = "path/to/save/plot.png"
        plot_and_save_candlestick(self.df, file_path)

        # Post the plot to Discord
        with open(file_path, "rb") as f:
            picture = File(f)
            await self.ctx.send("Here is the plot:", file=picture)

    async def run(self):
        logging.info("Running TradeBot...")
        if not self.trade_initialized:
            logging.info("Trade not initialized. Exiting run.")
            return

        self.fetch_data()
        self.calculate_indicators()
        await self.save_and_post_plot()  # Add this line to post the plot

        entry_met, entry_reason = self.evaluate_entry_conditions()
        if entry_met:
            logging.info(f"Entry Reason: {entry_reason}")
            self.entry_price = 0.0  # Replace with actual entry price
            await self.place_order("entry", self.entry_price)
            self.position_open = True

        if self.position_open:
            exit_met, exit_reason = self.evaluate_exit_conditions()
            logging.info(f"Exit Reason: {exit_reason}")
            if exit_met:
                await self.place_order("exit", self.entry_price)
                self.position_open = False


intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="The coolest crypto plotting bot around!",
    intents=intents,
)

trading_bot_instance = None


@bot.command(aliases=["trade"])
async def start(ctx):
    global trading_bot_instance

    trading_bot_instance = TradeBot(ctx)
    trading_bot_instance.trade_initialized = True
    await ctx.send("Initialized TradeBot.")


@tasks.loop(seconds=2)
async def trading_loop():
    global trading_bot_instance
    if trading_bot_instance:
        try:
            await trading_bot_instance.run()
        except Exception as e:
            logging.error(f"An error occurred in trading_loop: {e}")


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    trading_loop.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(f"Command not found: {ctx.message.content}")
    else:
        logging.error(f"An error occurred: {str(error)}")


bot.run(os.environ["DISCORD_TOKEN"])
