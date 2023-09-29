import pandas as pd
from plot_bot import plot_candlestick_with_bollinger

df = pd.read_csv("output/2023-09-26.csv")

plot_candlestick_with_bollinger(df)
