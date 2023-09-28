import logging
import os
from discord import Intents
from discord.ext import commands
from bot.bot import TradeBot

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


@bot.command(aliases=["trade"])
async def start(ctx):
    trading_bot_instance = TradeBot(ctx)
    await ctx.send("Initialized TradeBot.")
    await trading_bot_instance.initialize_data()


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
