import os
from typing import Callable, Dict
import pandas as pd
from services.data_service import fetch_ohlcv
from services.simulation import Simulation


def compute_metrics(trade_history):
    profit = 0.0
    max_drawdown = 0.0
    win_trades = 0
    total_trades = 0
    cumulative = 0.0

    for trade in trade_history:
        if trade.get("signal") == "SELL":
            diff = trade.get("profit", 0.0)
            profit += diff
            cumulative += diff
            if diff > 0:
                win_trades += 1
            total_trades += 1
            if cumulative < max_drawdown:
                max_drawdown = cumulative
    winrate = (win_trades / total_trades * 100) if total_trades else 0
    return profit, max_drawdown, winrate


class Backtester:
    """Utility for running strategy backtests."""

    def __init__(self, strategies: Dict[str, Callable]):
        self.strategies = strategies

    def run(self, symbol: str, timeframe: str, limit: int = 500):
        df = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        results = {}
        for name, strategy in self.strategies.items():
            sim = Simulation(log_dir=os.path.join("logs", "backtests"),
                             log_file=f"{name.lower()}_backtest.csv")
            signals = strategy(df.copy())
            for _, row in signals.iterrows():
                sim.place_order(row["signal"], row["price"])
            profit, drawdown, winrate = compute_metrics(sim.trade_history)
            results[name] = {
                "profit": round(profit, 2),
                "drawdown": round(drawdown, 2),
                "winrate": round(winrate, 2),
            }
        return results
