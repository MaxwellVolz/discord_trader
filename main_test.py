import asyncio

from bitget.trader import Trader
from plot import plot_candlestick_with_bollinger


async def main():
    trader = Trader()

    # Start the trading connection as a background task
    trading_task = asyncio.create_task(trader.connect())

    # Wait for a few seconds for the trading data to populate
    await asyncio.sleep(5)  # adjust the time as needed

    # Fetch and print the trading data
    data = trader.get_data()
    print("Current Data:", data)

    plot_candlestick_with_bollinger(data, save_path="kraken_plot.png", save_csv=True)

    await asyncio.sleep(60)  # adjust the time as needed

    # Fetch and print the trading data
    data = trader.get_data()
    print("Current Data:", data)

    # Generate the plot and save it as a PNG file
    plot_candlestick_with_bollinger(data, save_path="kraken_plot2.png")

    # Wait for the trading task to complete (if ever)
    await trading_task

    # Backtest the strategy
    # bitget.backtest_on_snapshot()


if __name__ == "__main__":
    asyncio.run(main())
