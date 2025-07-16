import pandas as pd
from typing import Callable, Dict

from services.data_service import fetch_ohlcv
from services.simulation import BacktestSimulation


def run_backtest(
    strategies: Dict[str, Callable[[pd.DataFrame], pd.DataFrame]],
    symbol: str = "BTC/USDT",
    timeframe: str = "5m",
    limit: int = 500,
    initial_balance: float = 1000.0,
) -> Dict[str, Dict[str, float]]:
    """Run backtest for provided strategies.

    Parameters
    ----------
    strategies: dict
        Mapping of strategy name to strategy function returning a DataFrame of
        signals with columns ["timestamp", "signal", "price", "value"].
    symbol: str
        Market symbol to fetch OHLCV data for.
    timeframe: str
        Timeframe to request from exchange.
    limit: int
        Number of bars to fetch.
    initial_balance: float
        Starting balance for each strategy simulation.

    Returns
    -------
    dict
        Metrics for each strategy containing total_return, win_rate and
        max_drawdown.
    """
    df = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    df = df.rename(columns={"close": "price"}).set_index("timestamp")

    # Pre-compute all strategy signals on the full dataframe
    strategy_signals = {}
    simulations = {}
    for name, strat in strategies.items():
        signals = strat(df.copy())
        if not isinstance(signals, pd.DataFrame) or signals.empty:
            # normal strategies might return tuple (signal, value)
            signals = pd.DataFrame([], columns=["timestamp", "signal", "price", "value"])
        signals = signals.set_index("timestamp") if not signals.empty else signals
        strategy_signals[name] = signals
        simulations[name] = BacktestSimulation(initial_balance=initial_balance)

    # Iterate through each bar and feed signals to simulations
    for ts, row in df.iterrows():
        price = row["price"]
        for name, signals in strategy_signals.items():
            if not signals.empty and ts in signals.index:
                signal = signals.loc[ts]["signal"]
                simulations[name].process_signal(signal, price)

    # Close any open position at final price
    final_price = df.iloc[-1]["price"]
    metrics = {}
    for name, sim in simulations.items():
        sim.close_final(final_price)
        total_ret, win_rate, drawdown = sim.get_metrics()
        metrics[name] = {
            "total_return": total_ret,
            "win_rate": win_rate,
            "drawdown": drawdown,
        }
    return metrics

