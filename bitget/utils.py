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
    print("Converting to dataframe...")
    df = pd.DataFrame(
        candle_data, columns=["UnixTimestamp", "Open", "High", "Low", "Close", "Volume"]
    )

    # Convert to DateTime in PST
    df["Timestamp"] = pd.to_datetime(df["UnixTimestamp"].astype("int64"), unit="ms")
    df["Timestamp"] = (
        df["Timestamp"].dt.tz_localize("UTC").dt.tz_convert("America/Los_Angeles")
    )

    df.set_index(["UnixTimestamp"], inplace=True)

    df[["Open", "High", "Low", "Close", "Volume"]] = df[
        ["Open", "High", "Low", "Close", "Volume"]
    ].apply(pd.to_numeric, errors="coerce")

    # Calculate Bollinger Bands, RSI, and Stochastic
    df = calc_bollinger_bands(df)
    df = calc_RSI(df)
    df = calc_stochastic(df)

    # print(df.describe())
    return df


def get_last_timestamp(df):
    return df.iloc[-1]["Timestamp"]


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
