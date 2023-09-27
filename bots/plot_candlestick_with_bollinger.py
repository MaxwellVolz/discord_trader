import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates


def plot_and_save_candlestick(df, file_path):
    # Prepare the DataFrame in the format mplfinance expects
    mpf_df = df[["open_Price", "high_Price", "low_Price", "close_Price"]]
    mpf_df.columns = ["Open", "High", "Low", "Close"]

    # Bollinger Bands as additional plots
    apds = [
        mpf.make_addplot(df["BBAND_upper"], panel=0, color="c"),
        mpf.make_addplot(df["BBAND_lower"], panel=0, color="c"),
    ]

    # Setup and plot
    kwargs = dict(type="candle", addplot=apds)
    mpf.plot(mpf_df, **kwargs, savefig=file_path)

    return file_path
