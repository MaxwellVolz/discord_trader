import logging
import os
from discord import Intents
from discord.ext import commands
from bot.data_bot import DataBot

from datetime import datetime, timedelta
import re

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


bot.run(os.environ["DISCORD_TOKEN"])
