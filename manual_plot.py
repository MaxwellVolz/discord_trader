import pandas as pd
from plot import plot_candlestick_with_bollinger
from bot.utils import calc_bollinger_bands, calc_RSI, calc_stochastic
from datetime import timedelta


def parse_trades(file_path):
    # Example Data:
    #
    # Price,Volume,Timestamp,Buy/Sell,Market/Limit,Misc,TradeID
    # 28245.7,0.00108234,1682035201,b,m,,58370417
    # 28245.7,0.00177018,1682035203,b,m,,58370418
    # ...

    df = pd.read_csv(file_path)

    # Convert 'Timestamp' to datetime format (assuming it's in seconds)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s")

    # Set 'Timestamp' as index
    df.set_index("Timestamp", inplace=True)

    # Resample into 2-minute intervals
    # You can customize the aggregation functions as needed
    # two_minute_candles = df.resample("2T").agg({"Price": "ohlc", "Volume": "sum"})
    # two_minute_candles = df.resample("5T").agg({"Price": "ohlc", "Volume": "sum"})

    # Resample to 20-minute intervals
    two_minute_candles = df.resample("2T").agg({"Price": "ohlc", "Volume": "sum"})

    # Flatten the multi-level column index
    two_minute_candles.columns = [
        "_".join(col).strip() for col in two_minute_candles.columns.values
    ]

    # Rename the relevant columns to match with the utility functions
    two_minute_candles.rename(
        columns={
            "Price_open": "Open",
            "Price_high": "High",
            "Price_low": "Low",
            "Price_close": "Close",
            "Volume_sum": "Volume",
        },
        inplace=True,
    )

    # Apply utility functions to populate the DataFrame with the calculated fields
    two_minute_candles = calc_bollinger_bands(two_minute_candles)
    two_minute_candles = calc_RSI(two_minute_candles)
    two_minute_candles = calc_stochastic(two_minute_candles)

    return two_minute_candles


if __name__ == "__main__":
    # file_path = "output/1680307200_to_1696791819.csv"
    file_path = "output/1696449600_to_1697055144.csv"

    df = parse_trades(file_path)

    min_date = df.index.min()
    max_date = df.index.max()

    delta = timedelta(days=3)

    current_date = min_date

    while current_date <= max_date:
        next_date = current_date + delta
        subset_df = df[current_date:next_date]
        plot_name = (
            f"{current_date.strftime('%m-%d')}-{next_date.strftime('%m-%d')}.png"
        )

        if not subset_df.empty:
            plot_candlestick_with_bollinger(subset_df, plot_name)

        current_date = next_date

        exit()

    # plot_candlestick_with_bollinger(df)
