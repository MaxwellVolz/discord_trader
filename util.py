def calculate_bollinger_bands(df, column, length, k_values):
    # Calculate Simple Moving Average (SMA)
    sma = df[column].rolling(window=length).mean()
    std = df[column].rolling(window=length).std()

    bollinger_bands = {}

    for k in k_values:
        bollinger_bands[f"Upper_{k}"] = sma + (std * k)
        bollinger_bands[f"Lower_{k}"] = sma - (std * k)

    return bollinger_bands
