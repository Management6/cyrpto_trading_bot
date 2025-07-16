import csv
import os
from datetime import datetime
from typing import List


class Simulation:
    """Simple trading account simulation."""

    def __init__(self, initial_balance: float = 0.0, log_dir: str = "logs", log_file: str = "simulation_log.csv") -> None:
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


class BacktestSimulation:
    """Simulation engine used for strategy backtesting."""

    def __init__(self, initial_balance: float = 1000.0) -> None:
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_price = None
        self.trades: List[float] = []
        self.equity_curve: List[float] = [initial_balance]

    def process_signal(self, signal: str, price: float) -> None:
        """Process BUY/SELL signal at given price."""
        if signal == "BUY" and self.position_price is None:
            self.position_price = price
        elif signal == "SELL" and self.position_price is not None:
            ret = price / self.position_price - 1
            self.balance *= 1 + ret
            self.trades.append(ret)
            self.equity_curve.append(self.balance)
            self.position_price = None

    def close_final(self, price: float) -> None:
        if self.position_price is not None:
            self.process_signal("SELL", price)

    def get_metrics(self) -> tuple[float, float, float]:
        total_return = self.balance / self.initial_balance - 1
        win_trades = [t for t in self.trades if t > 0]
        win_rate = len(win_trades) / len(self.trades) if self.trades else 0.0
        peak = self.equity_curve[0]
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            drawdown = (peak - val) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        return total_return, win_rate, max_dd


def simulate_order(signal: str, price: float) -> None:
    """Backward compatibility helper."""
    print(f"[SIMULATION] {signal} at price: {price}")
