import os
from dotenv import load_dotenv
from discord import Intents, File
from discord.ext import commands
from plot import plot_candlestick_with_bollinger
import asyncio

from bitget.trader import Trader

from logger_config import main_logger

# Load environment variables from .env file
load_dotenv()

# Access the DISCORD_TOKEN variable
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="The coolest crypto plotting bot around!",
    intents=intents,
)


trader = None  # Initialize trader to None


@bot.command(name="kraken")
async def kraken(ctx):
    global trader
    await ctx.send("🥚 Initializing Kraken bot🥚. Hold please ⏳")

    # Initialize Trader and connect
    trader = Trader()
    asyncio.create_task(trader.connect())

    await ctx.send("🐣 Kraken bot Initialized 🐙")

    # trading_task = asyncio.create_task(trader.connect())
    # Wait for the trading task to complete (if ever)
    # await trading_task


@bot.command(name="plot")
async def plot(ctx, hours: int = 8):
    global trader
    if trader is None:
        await ctx.send("❌ Kraken bot is not initialized. Please run !kraken first.")
        return

    await ctx.send(f"📊 Generating the plot for the last {hours} hours. Hold please ⏳")

    # Fetch and print the trading data
    # data = trader.get_data()

    # Fetch and filter the trading data based on the number of hours
    data = trader.get_data_last_n_hours(hours)

    # Generate the plot and save it as a PNG file
    file_path = "kraken_plot.png"
    plot_candlestick_with_bollinger(data, save_path=file_path)

    # await ctx.send("", file=File(file_path))
    await ctx.send(file=File(file_path))


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        main_logger.info(f"Command not found: {ctx.message.content}")
    else:
        main_logger.error(f"An error occurred: {str(error)}")


bot.run(DISCORD_TOKEN)


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
