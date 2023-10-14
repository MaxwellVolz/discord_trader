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


def check_trigger_conditions(df_to_check):
    """
    Check if trigger conditions are met for trading.
    :param df_to_check: DataFrame containing market data.
    :return: Tuple containing a boolean and a dictionary.
             The boolean indicates if the trigger conditions are met.
             The dictionary contains details about the trigger conditions.
    """

    # Get the last row (last candle) from the DataFrame
    last_candle = df_to_check.iloc[-1]

    # Check if the last candle touches or penetrates the lower red Bollinger band
    lower_bollinger = last_candle["Bollinger_Lower_2"]

    touch_or_penetrate = any(
        [
            last_candle["Open"] <= lower_bollinger,
            last_candle["Close"] <= lower_bollinger,
            last_candle["Low"] <= lower_bollinger,
            last_candle["High"] <= lower_bollinger,
        ]
    )

    # Check if both RSI and stochastic are below the 20 level for the last candle
    rsi_val = last_candle["RSI"]
    rsi_below_20 = rsi_val < 20

    last_candle_stoch = last_candle["Stochastic"]
    stochastic_below_20 = last_candle_stoch < 20

    # Create a dictionary to store the current trigger stats
    curr_trigger_stats = {
        "touch_or_penetrate": touch_or_penetrate,
        "rsi_val": rsi_val,
        "rsi_below_20": rsi_below_20,
        "stoch_val": last_candle_stoch,
        "stochastic_below_20": stochastic_below_20,
    }

    trigger_conditions_met = touch_or_penetrate and (
        rsi_below_20 or stochastic_below_20
    )

    return trigger_conditions_met, curr_trigger_stats


def check_entry_conditions(df_to_check):
    """
    Check if entry conditions are met for trading.
    :param df_to_check: DataFrame containing market data.
    :return: Tuple containing a boolean and a dictionary.
             The boolean indicates if the entry conditions are met.
             The dictionary contains details about the entry conditions.
    """

    last_candle = df_to_check.iloc[-1]
    second_last_candle = df_to_check.iloc[-2]

    # The next candle retraces and closes back through the red Bollinger band.
    retraces_through_band = last_candle["Close"] > last_candle["Bollinger_Lower_2"]

    # RSI goes above 20
    rsi_val = last_candle["RSI"]
    rsi_above_20 = rsi_val > 20

    # Stochastic lines cross between the 20 and 40 levels
    last_candle_stoch = last_candle["Stochastic"]
    second_last_candle_stoch = second_last_candle["Stochastic"]

    stochastic_cross = (second_last_candle_stoch < 20) and (last_candle_stoch > 20)
    stochastic_between_20_and_40 = 20 < last_candle_stoch < 40

    curr_entry_stats = {
        "retraces_through_band": retraces_through_band,
        "rsi_above_20": rsi_above_20,
        "rsi_val": rsi_val,
        "stochastic_cross": stochastic_cross,
        "stochastic_between_20_and_40": stochastic_between_20_and_40,
        "last_candle_stoch": last_candle_stoch,
    }

    entry_conditions_met = (
        retraces_through_band
        and rsi_above_20
        and stochastic_cross
        and stochastic_between_20_and_40
    )

    return entry_conditions_met, curr_entry_stats


def format_backtest_results(results):
    formatted_results = "📊 **Backtest Results:** 📊\n\n"
    trigger_event = None

    for event in results:
        if event["event"] == "trigger":
            trigger_event = event
        elif event["event"] == "entry":
            formatted_results += f"🔻 **Trigger Event** 🔻\n"
            formatted_results += f"- Timestamp: `{trigger_event['timestamp']}`\n"
            for key, value in trigger_event["conditions"].items():
                formatted_results += f"  - {key}: `{value}`\n"

            formatted_results += f"🔺 **Entry Event** 🔺\n"
            formatted_results += f"- Timestamp: `{event['timestamp']}`\n"
            for key, value in event["conditions"].items():
                formatted_results += f"  - {key}: `{value}`\n"

            formatted_results += f"➡️➡️➡️➡️➡️➡️➡️\n\n"

    return formatted_results[
        :4000
    ]  # Limiting characters to 4000 to avoid Discord's message length limit
