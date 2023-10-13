import logging
import os
from dotenv import load_dotenv
from discord import Intents, File, Embed
from discord.ext import commands
from bot.data_bot import DataBot
from bitget.bitget import BitGet
from plot import plot_candlestick_with_bollinger
import asyncio

from datetime import datetime, timedelta
import re


# Load environment variables from .env file
load_dotenv()

# Access the DISCORD_TOKEN variable
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


logging.basicConfig(
    filename="discord_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Starting the Discord bot...")

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="The coolest crypto plotting bot around!",
    intents=intents,
)


# @bot.command(name="help")
# async def help_command(ctx):
#     help_embed = Embed(
#         title="🤖 Cryptobot Help Center 🤖",
#         description="Welcome to the ultimate crypto plotting bot! Here's how you can use me:",
#         color=0x00FF00,
#     )

#     # help_embed.add_field(
#     #     name="📊 Plotting Historical Data 📈",
#     #     value="Use `!plot MM-DD` to plot historical data for a given date. Example: `!plot 01-01`.",
#     #     inline=False,
#     # )

#     help_embed.add_field(
#         name="🐙 Kraken Feature 🐙",
#         value="Use `!kraken` to plot real-time data from Kraken. Watch out, the Kraken is unleashed!",
#         inline=False,
#     )

#     help_embed.add_field(
#         name="🚀 Upcoming Features 🌠",
#         value="📊 Plotting Historical Data 📈 Setting Trigger::  rtsssss s🚨!",
#         inline=False,
#     )

#     help_embed.set_footer(text="For more details, text me lol.")

#     await ctx.send(embed=help_embed)


@bot.command(name="kraken")
async def kraken(ctx):
    await ctx.send("🔥 Yo whats Krakennnnn🐙 Hold please ⏳")

    # Initialize BitGet and connect
    bitget = BitGet()
    await bitget.connect()  # Add 'await' here

    # Get the snapshot and parse it into a DataFrame
    snapshot = bitget.get_candle_data()

    # Generate the plot and save it as a PNG file
    file_path = "kraken_plot.png"  # You can name this file as you like
    plot_candlestick_with_bollinger(snapshot, save_path=file_path)

    # bitget.backtest_on_snapshot()

    # Send the PNG file in the Discord channel
    await ctx.send("📊:", file=File(file_path))


@bot.command(aliases=["plot"])
async def start(ctx, *, date: str):
    # Validate the date input
    if not re.match(r"\d{2}-\d{2}", date):
        await ctx.send("Invalid date format. Please use MM-DD.")
        return

    month, day = map(int, date.split("-"))

    # Get the current year and validate that the date is in the past
    current_year = datetime.now().year
    try:
        user_date = datetime(current_year, month, day)
    except ValueError:
        await ctx.send("Invalid date. Please enter a valid month and day.")
        return

    if user_date >= datetime.now():
        await ctx.send("Date must be in the past.")
        return

    adjusted_time = user_date - timedelta(hours=7)

    # Initialize and run the DataBot
    trading_bot_instance = DataBot(ctx, initial_time=adjusted_time)
    await ctx.send(
        f"🚀 Rocketing through the blockchain to grab the data for {date}!"
        + "     📊 Hold tight, this is gonna be out of this world! 🌌"
    )

    await trading_bot_instance.initialize()


# @bot.command(aliases=["trade"])
# async def start(ctx):
#     trading_bot_instance = DataBot(ctx)
#     await ctx.send("Initialized DataBot.")
#     await trading_bot_instance.initialize()


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(f"Command not found: {ctx.message.content}")
    else:
        logging.error(f"An error occurred: {str(error)}")


bot.run(DISCORD_TOKEN)
