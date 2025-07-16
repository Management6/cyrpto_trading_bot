import csv
import os

def log_trade(timestamp, symbol, timeframe, indicator_value, price, signal, strategy_name="RSI"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{strategy_name.lower()}_log.csv")

    write_header = not os.path.exists(log_file)

    with open(log_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["timestamp", "symbol", "timeframe", "value", "price", "signal"])
        writer.writerow([timestamp, symbol, timeframe, round(indicator_value, 2), round(price, 2), signal or "-"])
