import json
from datetime import datetime

import requests
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import matplotlib.dates as mdates
import pandas as pd

from util import calculate_bollinger_bands

# Flag to determine whether to use mock data
USE_MOCK_DATA = True
kraken_url = "https://api.kraken.com/0/public/Trades?pair=btcusd&since=1688888888"

# Fetch data from the API endpoint
if USE_MOCK_DATA:
    # Read from local mock_data folder
    with open("mock_data/kraken_trades_btc.json", "r") as f:
        response = json.load(f)
    # Assume mock_response is structured like the real API response
    data = response["result"]["XXBTZUSD"]
else:
    # Fetch data from the Kraken API endpoint
    response = requests.get(kraken_url)
    data = response.json()["result"]["XXBTZUSD"]


# Create a Pandas DataFrame
df = pd.DataFrame(
    data,
    columns=[
        "Price",
        "Volume",
        "Timestamp",
        "Buy/Sell",
        "Market/Limit",
        "Misc",
        "TradeID",
    ],
)

df["Price"] = df["Price"].astype(float)
df["Volume"] = df["Volume"].astype(float)
df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s")

df["Buy/Sell"] = df["Buy/Sell"].astype(str)
df["Misc"] = df["Misc"].astype(str)
df["TradeID"] = df["TradeID"].astype(str)

print(df.describe())
# Calculate Bollinger Bands for multiple k values
k_values = [
    (2, "red"),
    (3, "yellow"),
    (4, "orange"),
]  # Replace with your desired k values
length = 20  # Rolling window length

# bands = calculate_bollinger_bands(df, 'Price', length, k_values)
bands = calculate_bollinger_bands(df, "Price", length, [k for k, _ in k_values])

# Add calculated bands to DataFrame
for key, value in bands.items():
    df[key] = value

# Plotting
fig, ax = plt.subplots(figsize=(15, 8))  # Increase the plot size

# Make background black
ax.set_facecolor("#151823")
fig.patch.set_facecolor("#151823")

# Plot the price
ax.plot(df["Timestamp"], df["Price"], label="Price", color="blue")

# Plot Bollinger Bands
for k, color in k_values:
    # ax.fill_between(df['Timestamp'], df[f'Lower_{k}'], df[f'Upper_{k}'], alpha=0.3, label=f'Bollinger Bands (k={k})')
    ax.plot(df["Timestamp"], df[f"Upper_{k}"], color=color, label=f"Upper Band (k={k})")
    ax.plot(df["Timestamp"], df[f"Lower_{k}"], color=color, label=f"Lower Band (k={k})")


# Labels, title, etc.
ax.set_xlabel("Time")
ax.set_ylabel("Price")

# Make text and labels white
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))


def format_to_dollars(x, pos):
    return f"${x:,.0f}"


formatter = FuncFormatter(format_to_dollars)
ax.yaxis.set_major_formatter(formatter)

ax.tick_params(axis="x", colors="white")
ax.tick_params(axis="y", colors="white")
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")

ax.tick_params(axis="y", colors="white")
ax.yaxis.label.set_color("white")

ax.legend()

plt.show()
