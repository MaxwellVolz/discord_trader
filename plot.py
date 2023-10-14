import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
import os
from matplotlib.dates import DateFormatter
from matplotlib.gridspec import GridSpec
from matplotlib import style

from logger_config import plot_logger


def format_to_dollars(x, pos):
    return f"${x:,.0f}"


def setup_plot(df):
    style.use("dark_background")
    fig = plt.figure(figsize=(30, 20))
    gs = GridSpec(3, 1, hspace=0)
    ax = plt.subplot(gs[:2, 0])
    ax_indicator = plt.subplot(gs[2, 0], sharex=ax)
    return fig, ax, ax_indicator


def plot_candlestick(ax, df):
    candle_config = {
        "width": 0.0006,
        "width2": 0.00015,
        "colors": {"up": "green", "down": "red"},
    }

    up = df[df["Close"] >= df["Open"]]
    down = df[df["Close"] < df["Open"]]

    for direction, color in candle_config["colors"].items():
        segment = up if direction == "up" else down
        ax.bar(
            segment.index,
            segment["Close"] - segment["Open"],
            candle_config["width"],
            bottom=segment["Open"],
            color=color,
            alpha=0.6,
        )
        ax.bar(
            segment.index,
            segment["High"] - segment["Close"],
            candle_config["width2"],
            bottom=segment["Close"],
            color=color,
        )


def plot_indicators(ax_indicator, df):
    ax_indicator.plot(df["Date"], df["RSI"], label="RSI", color="b")
    ax_indicator.plot(df["Date"], df["Stochastic"], label="Stochastic %K", color="g")

    ax_indicator.axhline(80, linestyle="--", linewidth=1, color="grey")
    ax_indicator.axhline(20, linestyle="--", linewidth=1, color="grey")
    ax_indicator.set_title("RSI and Stochastic Indicators")
    ax_indicator.set_ylim([0, 100])
    ax_indicator.legend(loc="upper left")


def plot_common_elements(ax, ax_indicator, df):
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    title_date = df["Date"].iloc[0].strftime("%B %d")
    ax.set_title(f"{title_date} BTCUSDT")

    date_format = DateFormatter("%H:%M", tz=df["Date"].dt.tz)
    ax.xaxis.set_major_formatter(date_format)

    formatter = FuncFormatter(format_to_dollars)
    ax.yaxis.set_major_formatter(formatter)

    ax.legend(loc="upper left")


def plot_bollinger_bands(ax, df, labels_colors):
    for label, color in labels_colors.items():
        ax.plot(
            df["Date"],
            df[label],
            color=color,
            label=label,
            linewidth=0.3,
        )


def plot_candlestick_with_bollinger(df, save_path=None, save_csv=False):
    df = df.copy()

    if save_csv:
        csv_name = f"output/{df['Date'].iloc[0].timestamp()}_{df['Date'].iloc[-1].timestamp()}.csv"
        df.to_csv(csv_name)

    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index.astype("int64"), unit="ms")
        except OverflowError:
            df.index = pd.to_datetime(df.index)

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert("America/Los_Angeles")

    df["Date"] = df.index
    df.sort_values(by="Date", inplace=True)

    style.use("dark_background")

    fig, ax, ax_indicator = setup_plot(df)

    plot_candlestick(ax, df)

    bollinger_labels_colors = {
        "Bollinger_Upper_2": "red",
        "Bollinger_Lower_2": "red",
        "Bollinger_Upper_3": "yellow",
        "Bollinger_Lower_3": "yellow",
        "Bollinger_Upper_4": "orange",
        "Bollinger_Lower_4": "orange",
    }
    plot_bollinger_bands(ax, df, bollinger_labels_colors)

    plot_indicators(ax_indicator, df)
    plot_common_elements(ax, ax_indicator, df)

    plt.tight_layout()

    if save_path is None:
        plt.show()
        return None
    else:
        if not os.path.exists("plots"):
            os.makedirs("plots")

        plot_logger.info(f"Saving plot: {save_path}")
        plt.savefig(save_path)

        return save_path


# Example usage:
# plot_candlestick_with_bollinger(df, save_path="plot.png", save_csv=True)
