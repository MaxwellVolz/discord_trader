import asyncio
from bitget.bitget import BitGet
from plot import plot_candlestick_with_bollinger


async def main():
    # Initialize BitGet and connect
    bitget = BitGet()
    await bitget.connect(5)  # 'await' is valid because we're inside an async function

    # Get the snapshot df
    snapshot = bitget.get_data()

    print("Plotting first candles...")

    # Generate the plot and save it as a PNG file
    plot_candlestick_with_bollinger(snapshot, save_path="kraken_plot.png")

    print("Subscribing to conditions...")

    duration = 60
    # for example, subscribe for 300 seconds with no delay in reporting the
    # conditions; they're reported in real-time!
    await bitget.subscribe_conditions(duration)

    # Get the snapshot df
    snapshot = bitget.get_data()

    # Generate the plot and save it as a PNG file
    plot_candlestick_with_bollinger(snapshot, save_path="kraken_plot_2.png")

    # Backtest the strategy
    # bitget.backtest_on_snapshot()

    # Send the PNG file in the Discord channel
    # (you can add your Discord bot sending logic here)


# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())
