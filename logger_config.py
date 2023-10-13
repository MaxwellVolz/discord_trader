import logging

# Setup for main.py logger
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)
main_file_handler = logging.FileHandler("main.log")
main_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
main_logger.addHandler(main_file_handler)

# Setup for trader.py logger
trader_logger = logging.getLogger("trader")
trader_logger.setLevel(logging.INFO)
trader_file_handler = logging.FileHandler("trader.log")
trader_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
trader_logger.addHandler(trader_file_handler)

# Setup for plot.py logger
plot_logger = logging.getLogger("plot")
plot_logger.setLevel(logging.INFO)
plot_file_handler = logging.FileHandler("plot.log")
plot_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
plot_logger.addHandler(plot_file_handler)
