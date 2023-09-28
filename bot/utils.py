# import pandas as pd
import logging


def calculate_bollinger_bands(df_resampled):
    close = df_resampled["Price_close"]
    # sma = close.rolling(window=20).mean()
    sma = close.rolling(window=20).mean().ffill()

    rolling_std = close.rolling(window=20).std()

    if rolling_std.isna().any() or (rolling_std == 0).any():
        logging.error(
            "Potential division by zero in calculate_bollinger_bands: rolling_std contains NaN or zero"
        )
        return df_resampled

    df_resampled["BBAND_middle"] = sma
    df_resampled["BBAND_upper"] = sma + (rolling_std * 2)
    df_resampled["BBAND_lower"] = sma - (rolling_std * 2)
    return df_resampled


def calculate_RSI(df_resampled):
    close = df_resampled["Price_close"]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().ffill()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().ffill()

    # gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    # loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    if gain.isna().any() or loss.isna().any() or (loss == 0).any():
        logging.error(
            "Potential division by zero in calculate_RSI: gain or loss contains NaN or zero"
        )
        return df_resampled

    rs = gain / loss
    df_resampled["RSI"] = 100 - (100 / (1 + rs))
    return df_resampled


def calculate_stochastic(df_resampled):
    close = df_resampled["Price_close"]
    low_min = df_resampled["Price_low"].rolling(window=14).min().ffill()
    high_max = df_resampled["Price_high"].rolling(window=14).max().ffill()

    if (high_max - low_min).isna().any() or ((high_max - low_min) == 0).any():
        logging.error(
            "Potential division by zero in calculate_stochastic: high_max - low_min is NaN or zero"
        )
        return df_resampled

    fast_k = 100 * ((close - low_min) / (high_max - low_min))
    fast_d = fast_k.rolling(window=3).mean()

    df_resampled["STOCH_fastk"] = fast_k
    df_resampled["STOCH_fastd"] = fast_d
    return df_resampled
