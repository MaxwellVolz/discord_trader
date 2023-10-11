import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import date2num, DateFormatter
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
import os


def format_to_dollars(x, pos):
    return f"${x:,.0f}"


def plot_candlestick_with_bollinger(df, plot_name=None):
    # Explicit copy of the DataFrame slice
    df = df.copy()
    df["Date"] = df.index
    df.sort_values(by="Date", inplace=True)

    # Convert Unix timestamp to datetime and assign to a new column
    # df["Date"] = df["Date"].dt.tz_localize("UTC").dt.tz_convert("America/Los_Angeles")

    df["Date"] = (
        pd.to_datetime(df["Date"], unit="s")
        .dt.tz_localize("UTC")
        .dt.tz_convert("America/Los_Angeles")
    )
    print("First timestamp:", df["Date"].iloc[0])
    print("Last timestamp:", df["Date"].iloc[-1])

    # Sort DataFrame by datetime

    # Setup the plot
    fig, ax = plt.subplots()

    # Candles

    # Setting width of candlestick elements
    width = 0.0015
    width2 = 0.0003
    # Identify 'up' and 'down' movements in price
    up = df[df["Close"] >= df["Open"]]
    down = df[df["Close"] < df["Open"]]

    # Colors for 'up' and 'down' bars
    col1 = "green"
    col2 = "red"

    # Plotting 'up' prices of the stock
    ax.bar(up.index, up["Close"] - up["Open"], width, bottom=up["Open"], color=col1)
    ax.bar(up.index, up["High"] - up["Close"], width2, bottom=up["Close"], color=col1)
    ax.bar(up.index, up["Low"] - up["Open"], width2, bottom=up["Open"], color=col1)

    # Plotting 'down' prices of the stock
    ax.bar(
        down.index, down["Close"] - down["Open"], width, bottom=down["Open"], color=col2
    )
    ax.bar(
        down.index, down["High"] - down["Open"], width2, bottom=down["Open"], color=col2
    )
    ax.bar(
        down.index,
        down["Low"] - down["Close"],
        width2,
        bottom=down["Close"],
        color=col2,
    )

    # ax.plot(df["Date"], df["Close"], color="k", label="Close Price")

    # Bollinger Bands
    ax.plot(
        df["Date"],
        df["Bollinger_Upper_2"],
        color="red",
        label="Bollinger Upper (2)",
        linewidth=0.3,
    )

    ax.plot(
        df["Date"],
        df["Bollinger_Lower_2"],
        color="red",
        # linestyle="--",
        label="Bollinger Lower (2)",
        linewidth=0.3,
    )

    ax.plot(
        df["Date"],
        df["Bollinger_Upper_3"],
        color="yellow",
        label="Bollinger Upper (3)",
        linewidth=0.3,
    )
    ax.plot(
        df["Date"],
        df["Bollinger_Lower_3"],
        color="yellow",
        label="Bollinger Lower (3)",
        linewidth=0.3,
    )

    ax.plot(
        df["Date"],
        df["Bollinger_Upper_4"],
        color="orange",
        label="Bollinger Upper (4)",
        linewidth=0.3,
    )

    ax.plot(
        df["Date"],
        df["Bollinger_Lower_4"],
        color="orange",
        label="Bollinger Lower (4)",
        linewidth=0.3,
    )

    # Add labels and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.set_title("Line Chart with Bollinger Bands")

    # Add your color and background changes here
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.xaxis.label.set_color("white")
    ax.xaxis_date("America/Los_Angeles")

    ax.yaxis.label.set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.title.set_color("white")
    ax.set_facecolor("#151823")
    fig.patch.set_facecolor("#151823")

    date_format = DateFormatter("%H:%M", tz=df["Date"].dt.tz)
    ax.xaxis.set_major_formatter(date_format)

    # Formatting and legend
    # date_format = DateFormatter("%d-%b")
    # date_format = DateFormatter("%H:%M")
    # ax.xaxis.set_major_formatter(date_format)

    formatter = FuncFormatter(format_to_dollars)
    ax.yaxis.set_major_formatter(formatter)
    ax.legend(loc="upper left")
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # Set plot output size
    fig.set_size_inches(30, 20)

    if plot_name is None:
        plt.show()
        return None
    else:
        # Save the plot
        if not os.path.exists("plots"):
            os.makedirs("plots")
        file_name = (
            f"plots/Bollinger_Plot_{df['Date'].iloc[-1].strftime('%Y%m%d_%H%M%S')}.png"
        )
        print(f"Saving plot: {file_name}")
        plt.savefig(file_name)

        return file_name
