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


def convert_to_dataframe(candle_data):
    columns = [
        "Timestamp",
        "Price_open",
        "Price_high",
        "Price_low",
        "Price_close",
        "Volume_sum",
    ]
    df = pd.DataFrame(candle_data, columns=columns)

    df["Timestamp"] = df["Timestamp"].astype("int64")
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

    # Convert to numeric
    df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
    df["High"] = pd.to_numeric(df["High"], errors="coerce")
    df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

    # Calculate Bollinger Bands, RSI, and Stochastic
    df = calc_bollinger_bands(df)
    df = calc_RSI(df)
    df = calc_stochastic(df)

    return df


def update_dataframe_with_new_data(df, new_candle_data):
    new_df = pd.DataFrame([new_candle_data], columns=df.columns)
    df = pd.concat([df, new_df]).reset_index(drop=True)

    # Recalculate indicators
    df = calc_bollinger_bands(df)
    df = calc_RSI(df)
    df = calc_stochastic(df)

    return df


def format_trigger_stats(trigger_stats: dict):
    width = 80

    lines = []
    lines.append("".center(width, "="))
    lines.append("Evaluating Trigger Conditions".center(width))
    lines.append("".center(width, "="))
    lines.append(
        f"Touch or Penetrate: {trigger_stats['touch_or_penetrate']}".rjust(width)
    )
    lines.append(
        f"RSI Below 20: {trigger_stats['rsi_below_20']}({trigger_stats['rsi_val']})".rjust(
            width
        )
    )
    lines.append(
        f"Stochastic Below 20: {trigger_stats['stochastic_below_20']}({trigger_stats['stoch_val']})".rjust(
            width
        )
    )
    lines.append("".center(width, "="))

    return "\n".join(lines)


def format_entry_stats(entry_stats: dict):
    width = 80

    lines = []
    lines.append("".center(width, "="))
    lines.append("Evaluating Entry Conditions".center(width))
    lines.append("".center(width, "="))
    lines.append(
        f"Retrace Through Band: {entry_stats['retraces_through_band']}".rjust(width)
    )
    lines.append(
        f"RSI Above 20: {entry_stats['rsi_above_20']}({entry_stats['rsi_val']})".rjust(
            width
        )
    )
    lines.append(f"Stochastic Cross: {entry_stats['stochastic_cross']}".rjust(width))
    lines.append(
        f"Stochastic Between 20 and 40: {entry_stats['stochastic_between_20_and_40']}({entry_stats['last_candle_stoch']})".rjust(
            width
        )
    )
    lines.append("".center(width, "="))

    return "\n".join(lines)
