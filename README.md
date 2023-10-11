# discord_trader
discord bot for crypto trading and data analysis


## Directory and Roles

- api_utils.py: This will contain utility functions for interacting with the API. For example, getting trading data, sending trades, etc.

- bot.py: This will contain the Discord bot logic, handling commands, and interaction with Discord users.

- utils.py: This could be a general-purpose utility file where you place various helper functions that are used throughout the project but don't necessarily belong in api_utils.py or bot.py.

- __init__.py: This empty file makes the directory a Python package, which means you can run the files as modules. This could be useful for testing and better structure.

## Upon bot deployment

1. run strategy on last 6 hours