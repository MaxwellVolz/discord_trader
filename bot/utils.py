import pandas as pd


def calc_bollinger_bands(df, window_size=20):
    df["SMA"] = df["Close"].rolling(window=window_size).mean().ffill()
    df["Rolling_STD"] = df["Close"].rolling(window=window_size).std().ffill()

    for std_dev in [2, 3, 4]:
        upper_col = f"Bollinger_Upper_{std_dev}"
        lower_col = f"Bollinger_Lower_{std_dev}"
        df[upper_col] = df["SMA"] + (df["Rolling_STD"] * std_dev)
        df[lower_col] = df["SMA"] - (df["Rolling_STD"] * std_dev)

    return df


def calc_RSI(df, window=14):
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean().ffill()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean().ffill()
    df["RSI"] = 100 - (100 / (1 + (gain / loss)))
    return df


def calc_stochastic(df, window=14):
    low_min = df["Low"].rolling(window=window).min().ffill()
    high_max = df["High"].rolling(window=window).max().ffill()
    df["Stochastic"] = ((df["Close"] - low_min) / (high_max - low_min)) * 100
    return df
