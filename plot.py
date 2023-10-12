import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
import os
from bot.utils import calc_bollinger_bands, calc_RSI, calc_stochastic
from matplotlib.dates import DateFormatter
from matplotlib.gridspec import GridSpec
from matplotlib import style
from matplotlib.patches import Rectangle


def format_to_dollars(x, pos):
    return f"${x:,.0f}"


def parse_snapshot_to_dataframe(snapshot):
    columns = [
        "Timestamp",
        "Price_open",
        "Price_high",
        "Price_low",
        "Price_close",
        "Volume_sum",
    ]
    df = pd.DataFrame(snapshot, columns=columns)

    df["Timestamp"] = df["Timestamp"].astype(
        "int64"
    )  # Cast to integer before converting to datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")

    df.set_index("Timestamp", inplace=True)

    # Rename columns
    df.rename(
        columns={
            "Price_open": "Open",
            "Price_high": "High",
            "Price_low": "Low",
            "Price_close": "Close",
            "Volume_sum": "Volume",
        },
        inplace=True,
    )

    # Convert to numeric types
    df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
    df["High"] = pd.to_numeric(df["High"], errors="coerce")
    df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

    # Calculate Bollinger Bands, RSI, and Stochastic (assuming you have these utility functions)
    df = calc_bollinger_bands(df)
    df = calc_RSI(df)
    df = calc_stochastic(df)

    return df


def plot_bollinger_bands(ax, df, labels_colors):
    for label, color in labels_colors.items():
        ax.plot(
            df["Date"],
            df[label],
            color=color,
            label=label,
            linewidth=0.3,
        )


def plot_candlestick_with_bollinger(df, save_path=None):
    df = df.copy()
    df["Date"] = df.index
    df.sort_values(by="Date", inplace=True)

    df["Date"] = (
        pd.to_datetime(df["Date"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/Los_Angeles")
    )

    style.use("dark_background")

    # Setup the plot
    fig = plt.figure(figsize=(30, 20))
    gs = GridSpec(3, 1, hspace=0)
    ax = plt.subplot(gs[:2, 0])
    ax_indicator = plt.subplot(gs[2, 0], sharex=ax)

    # Condensed candlestick and indicator configurations
    candle_config = {
        "width": 0.0006,
        "width2": 0.00015,
        "colors": {"up": "green", "down": "red"},
    }

    # Generate candlesticks
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

    # Bollinger Bands
    bollinger_labels_colors = {
        "Bollinger_Upper_2": "red",
        "Bollinger_Lower_2": "red",
        "Bollinger_Upper_3": "yellow",
        "Bollinger_Lower_3": "yellow",
        "Bollinger_Upper_4": "orange",
        "Bollinger_Lower_4": "orange",
    }
    plot_bollinger_bands(ax, df, bollinger_labels_colors)

    # Calculate RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ax_indicator.plot(df["Date"], rsi, label="RSI", color="b")

    # Calculate Stochastic Oscillator and Plot on ax_indicator
    low_min = df["Low"].rolling(window=14).min()
    high_max = df["High"].rolling(window=14).max()
    k = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    ax_indicator.plot(df["Date"], k, label="Stochastic %K", color="g")

    # Common indicators for ax_indicator
    ax_indicator.axhline(80, linestyle="--", linewidth=1, color="grey")
    ax_indicator.axhline(20, linestyle="--", linewidth=1, color="grey")
    ax_indicator.set_title("RSI and Stochastic Indicators")
    ax_indicator.set_ylim([0, 100])
    ax_indicator.legend(loc="upper left")

    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    title_date = df["Date"].iloc[0].strftime("%B %d")
    ax.set_title(f"{title_date} BTCUSDT")

    date_format = DateFormatter("%H:%M", tz=df["Date"].dt.tz)
    ax.xaxis.set_major_formatter(date_format)

    formatter = FuncFormatter(format_to_dollars)
    ax.yaxis.set_major_formatter(formatter)

    plt.tight_layout()

    ax.legend(loc="upper left")
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # Set plot output size
    fig.set_size_inches(30, 20)

    if save_path is None:
        plt.show()
        return None
    else:
        # Save the plot
        if not os.path.exists("plots"):
            os.makedirs("plots")

        print(f"Saving plot: {save_path}")
        plt.savefig(save_path)

        return save_path
