# import pandas as pd


def calculate_bollinger_bands(df_resampled):
    close = df_resampled["close_Price"]
    sma = close.rolling(window=20).mean()
    rolling_std = close.rolling(window=20).std()
    df_resampled["BBAND_middle"] = sma
    df_resampled["BBAND_upper"] = sma + (rolling_std * 2)
    df_resampled["BBAND_lower"] = sma - (rolling_std * 2)
    return df_resampled


def calculate_RSI(df_resampled):
    close = df_resampled["close_Price"]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_resampled["RSI"] = 100 - (100 / (1 + rs))
    return df_resampled


def calculate_stochastic(df_resampled):
    close = df_resampled["close_Price"]
    low_min = df_resampled["low_Price"].rolling(window=14).min()
    high_max = df_resampled["high_Price"].rolling(window=14).max()

    fast_k = 100 * ((close - low_min) / (high_max - low_min))
    fast_d = fast_k.rolling(window=3).mean()

    df_resampled["STOCH_fastk"] = fast_k
    df_resampled["STOCH_fastd"] = fast_d
    return df_resampled
