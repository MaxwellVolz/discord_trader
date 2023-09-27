from discord import Intents, File
from discord.ext import commands
from dotenv import load_dotenv
from KrakenDataPlotter import KrakenDataPlotter
import os

load_dotenv()

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="The coolest crypto plotting bot around!",
    intents=intents,
)


@bot.command(aliases=["stonks"])
async def plot_kraken_data(ctx):
    """Generate an image of Kraken trading data"""
    msg = await ctx.send("Generating plot...")

    # Instantiate the KrakenDataPlotter class and generate the plot
    plotter = KrakenDataPlotter(use_mock_data=False)
    plotter.run()
    plot_file_path = "temp_plot.png"  # Temporary file to hold the plot
    plotter.save_plot_to_file(
        plot_file_path
    )  # Assume this method saves the plot to a file

    # Send the image through Discord
    with open(plot_file_path, "rb") as fp:
        await ctx.send(file=File(fp, "kraken_plot.png"))

    # Remove the temporary file
    os.remove(plot_file_path)

    await msg.edit(content="Plotted.")


bot.run(os.environ["DISCORD_TOKEN"])
