from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd


def calculate_bollinger_bands(df, column, length, k_values):
    sma = df[column].rolling(window=length).mean()
    std = df[column].rolling(window=length).std()
    bollinger_bands = {}
    for k in k_values:
        bollinger_bands[f"Upper_{k}"] = sma + (std * k)
        bollinger_bands[f"Lower_{k}"] = sma - (std * k)
    return bollinger_bands


def plot_and_save(df, filename="plot.png"):
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)

    k_values = [2, 3, 4]
    length = 20
    bands = calculate_bollinger_bands(df, "Close", length, k_values)

    for key, value in bands.items():
        df[key] = value

    df.reset_index(inplace=True)
    df["Timestamp"] = df["Timestamp"].map(mdates.date2num)

    fig, ax = plt.subplots(figsize=(15, 8))

    ax.set_facecolor("#151823")
    fig.patch.set_facecolor("#151823")

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
    plt.xticks(rotation=45)

    candlestick_ohlc(
        ax,
        df[["Timestamp", "Open", "High", "Low", "Close"]].values,
        width=0.01,
        colorup="g",
        colordown="r",
    )

    colors = ["red", "yellow", "orange"]
    for k, color in zip(k_values, colors):
        ax.plot(df["Timestamp"], df[f"Upper_{k}"], color=color, label=f"Upper {k} std")
        ax.plot(df["Timestamp"], df[f"Lower_{k}"], color=color, label=f"Lower {k} std")

    def format_to_dollars(x, pos):
        return f"${x:,.0f}"

    formatter = FuncFormatter(format_to_dollars)
    ax.yaxis.set_major_formatter(formatter)

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")

    ax.legend(loc="upper left")

    # Save first plot
    fig.savefig(f"output/{filename}")

    return f"output/{filename}"
