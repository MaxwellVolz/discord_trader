import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import date2num, DateFormatter
from matplotlib.ticker import FuncFormatter
import os


def format_to_dollars(x, pos):
    return f"${x:,.0f}"


def plot_candlestick_with_bollinger(df):
    # Convert Unix timestamp to datetime and assign to a new column
    df["Date"] = pd.to_datetime(df["Timestamp"], unit="s")
    df["Date"] = df["Date"].dt.tz_localize("UTC").dt.tz_convert("America/Los_Angeles")

    # Sort DataFrame by datetime
    df.sort_values(by="Date", inplace=True)

    # Setup the plot
    fig, ax = plt.subplots()

    # Create line plots
    ax.plot(df["Date"], df["Close"], color="k", label="Close Price")

    ax.plot(
        df["Date"], df["Bollinger_Upper_2"], color="red", label="Bollinger Upper (2)"
    )
    ax.plot(
        df["Date"],
        df["Bollinger_Lower_2"],
        color="red",
        # linestyle="--",
        label="Bollinger Lower (2)",
    )

    ax.plot(
        df["Date"], df["Bollinger_Upper_3"], color="yellow", label="Bollinger Upper (3)"
    )
    ax.plot(
        df["Date"],
        df["Bollinger_Lower_3"],
        color="yellow",
        label="Bollinger Lower (3)",
    )

    ax.plot(
        df["Date"], df["Bollinger_Upper_4"], color="orange", label="Bollinger Upper (4)"
    )
    ax.plot(
        df["Date"],
        df["Bollinger_Lower_4"],
        color="orange",
        label="Bollinger Lower (4)",
    )

    # Add labels and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.set_title("Line Chart with Bollinger Bands")

    # Add your color and background changes here
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_color("white")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("white")
    ax.title.set_color("white")
    ax.set_facecolor("#151823")
    fig.patch.set_facecolor("#151823")

    # Formatting and legend
    date_format = DateFormatter("%d %H:%M")
    ax.xaxis.set_major_formatter(date_format)
    formatter = FuncFormatter(format_to_dollars)
    ax.yaxis.set_major_formatter(formatter)
    ax.legend(loc="upper left")
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

    # Set plot output size
    fig.set_size_inches(10, 6)

    # Save the plot
    if not os.path.exists("plots"):
        os.makedirs("plots")
    file_name = (
        f"plots/Bollinger_Plot_{df['Date'].iloc[-1].strftime('%Y%m%d_%H%M%S')}.png"
    )
    plt.savefig(file_name)

    return file_name

    # Show plot
    # plt.show()
