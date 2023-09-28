import matplotlib.pyplot as plt
import pandas as pd


def candlestick_plot(df):
    # Convert the 'Timestamp' column to datetime format and set it as index
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)

    # First Subplot (OHLC)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_title("OHLC and Volume")
    ax1.set_xlabel("Timestamp")
    ax1.set_ylabel("OHLC")
    ax1.plot(df.index, df["Open"], label="Open", color="blue")
    ax1.plot(df.index, df["High"], label="High", color="green")
    ax1.plot(df.index, df["Low"], label="Low", color="red")
    ax1.plot(df.index, df["Close"], label="Close", color="black")

    # Twin axis for Volume
    ax2 = ax1.twinx()
    ax2.set_ylabel("Volume")
    ax2.bar(df.index, df["Volume_sum"], alpha=0.3, color="purple", label="Volume")

    # Save first plot
    fig.savefig("output/OHLC_and_Volume.png")

    # Second Subplot (Indicators)
    fig, ax3 = plt.subplots(figsize=(12, 6))
    ax3.set_title("Indicators")
    ax3.set_xlabel("Timestamp")
    ax3.set_ylabel("SMA, Bollinger Bands")
    ax3.plot(df.index, df["SMA"], label="SMA", color="blue")
    ax3.plot(
        df.index, df["Bollinger_Upper_2"], label="Upper Bollinger x2", color="green"
    )
    ax3.plot(df.index, df["Bollinger_Lower_2"], label="Lower Bollinger x2", color="red")

    # Twin axis for RSI and Stochastic
    ax4 = ax3.twinx()
    ax4.set_ylabel("RSI, Stochastic")
    ax4.plot(df.index, df["RSI"], label="RSI", linestyle="dashed", color="orange")
    ax4.plot(
        df.index,
        df["Stochastic"],
        label="Stochastic",
        linestyle="dashed",
        color="purple",
    )

    # Legends
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    ax3.legend(loc="upper left")
    ax4.legend(loc="upper right")

    plt.tight_layout()

    # Save second plot
    fig.savefig("output/Indicators.png")

    return "output/OHLC_and_Volume.png", "output/Indicators.png"
