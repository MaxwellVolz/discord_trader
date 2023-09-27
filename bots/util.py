def calculate_bollinger_bands(df, column, length, k_values):
    # Calculate Simple Moving Average (SMA)
    sma = df[column].rolling(window=length).mean()
    std = df[column].rolling(window=length).std()

    bollinger_bands = {}

    for k in k_values:
        bollinger_bands[f"Upper_{k}"] = sma + (std * k)
        bollinger_bands[f"Lower_{k}"] = sma - (std * k)

    return bollinger_bands


def calculate_RSI(df, column, length=14):
    delta = df[column].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_stochastic(df, column, length=14):
    low_min = df[column].rolling(window=length).min()
    high_max = df[column].rolling(window=length).max()
    stochastic = (df[column] - low_min) / (high_max - low_min) * 100
    return stochastic
