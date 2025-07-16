import csv
import os
from datetime import datetime


class Simulation:
    """Simple trading account simulation."""

    def __init__(self, initial_balance: float = 0.0, log_dir: str = "logs",
                 log_file: str = "simulation_log.csv") -> None:
        self.balance = initial_balance
        self.position = None  # holds entry price when in position
        self.trade_history = []
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        os.makedirs(self.log_dir, exist_ok=True)
        self._init_log_file()

    def _init_log_file(self) -> None:
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "signal", "price", "balance", "profit"])

    def place_order(self, signal: str, price: float) -> None:
        """Execute an order and update account state."""
        if signal not in {"BUY", "SELL"}:
            return

        timestamp = datetime.utcnow().isoformat()
        profit = 0.0

        if signal == "BUY" and self.position is None:
            self.position = price
            self.trade_history.append({"timestamp": timestamp, "signal": "BUY", "price": price})
        elif signal == "SELL" and self.position is not None:
            profit = price - self.position
            self.balance += profit
            self.trade_history.append({
                "timestamp": timestamp,
                "signal": "SELL",
                "price": price,
                "profit": profit,
            })
            self.position = None
        else:
            return

        with open(self.log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, signal, round(price, 2), round(self.balance, 2), round(profit, 2)])

        print(f"[SIMULATION] {signal} at {price} | Balance: {self.balance:.2f}")

    def get_summary(self) -> dict:
        """Return a summary of the account state."""
        open_pos = {"entry_price": self.position} if self.position is not None else None
        return {
            "balance": self.balance,
            "open_position": open_pos,
            "trade_count": len(self.trade_history),
        }
