import asyncio
from bitget.bitget import BitGet
from plot import plot_candlestick_with_bollinger


async def main():
    # Initialize BitGet and connect
    bitget = BitGet()
    await bitget.connect()  # 'await' is valid because we're inside an async function

    # Get the snapshot and parse it into a DataFrame
    snapshot = bitget.get_candle_data()

    # Generate the plot and save it as a PNG file
    plot_candlestick_with_bollinger(snapshot, save_path="kraken_plot.png")

    bitget.backtest_on_snapshot()

    # Send the PNG file in the Discord channel
    # (you can add your Discord bot sending logic here)


# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())
