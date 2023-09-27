import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from util import calculate_bollinger_bands


class KrakenDataPlotter:
    def __init__(
        self,
        use_mock_data=True,
        mock_data_file="mock_data/kraken_trades_btc.json",
    ):
        self.use_mock_data = use_mock_data
        self.mock_data_file = mock_data_file
        self.df = None
        self.k_values = [(2, "red"), (3, "yellow"), (4, "orange")]  # Define k_values

    def fetch_data(self):
        kraken_url = f"https://api.kraken.com/0/public/Trades?pair=btcusd"
        if self.use_mock_data:
            with open(self.mock_data_file, "r") as f:
                response = json.load(f)
            data = response["result"]["XXBTZUSD"]
        else:
            response = requests.get(kraken_url)
            data = response.json()["result"]["XXBTZUSD"]
        self.df = pd.DataFrame(
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

    def preprocess_data(self):
        self.df["Price"] = self.df["Price"].astype(float)
        self.df["Volume"] = self.df["Volume"].astype(float)
        self.df["Timestamp"] = pd.to_datetime(self.df["Timestamp"], unit="s")

    def calculate_and_plot(self):
        bands = calculate_bollinger_bands(
            self.df, "Price", length=20, k_values=[k for k, _ in self.k_values]
        )
        for key, value in bands.items():
            self.df[key] = value

        # Rest of your plotting code

        # Plotting
        fig, ax = plt.subplots(figsize=(15, 8))  # Increase the plot size

        # Make background black
        ax.set_facecolor("#151823")
        fig.patch.set_facecolor("#151823")

        # Plot the price
        ax.plot(self.df["Timestamp"], self.df["Price"], label="Price", color="blue")

        # Plot Bollinger Bands
        for k, color in self.k_values:
            # ax.fill_between(self.df['Timestamp'], self.df[f'Lower_{k}'], self.df[f'Upper_{k}'], alpha=0.3, label=f'Bollinger Bands (k={k})')
            ax.plot(
                self.df["Timestamp"],
                self.df[f"Upper_{k}"],
                color=color,
                label=f"Upper Band (k={k})",
            )
            ax.plot(
                self.df["Timestamp"],
                self.df[f"Lower_{k}"],
                color=color,
                label=f"Lower Band (k={k})",
            )

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
        # plt.show()

    def save_plot_to_file(self, file_path):
        plt.savefig(file_path)

    def run(self):
        self.fetch_data()
        self.preprocess_data()
        self.calculate_and_plot()
