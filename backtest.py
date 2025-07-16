from services.backtest_service import run_backtest
from strategies.rsi_strategy_trailing import apply_rsi_strategy
from strategies.macd_strategy_trailing import apply_macd_strategy
from strategies.bollinger_strategy_trailing import apply_bollinger_strategy
from strategies.ma_cross_strategy_trailing import apply_ma_cross_strategy
from strategies.custom_strategy_trailing import apply_custom_strategy


if __name__ == "__main__":
    strategies = {
        "RSI": apply_rsi_strategy,
        "MACD": apply_macd_strategy,
        "BOLLINGER": apply_bollinger_strategy,
        "MA_CROSS": apply_ma_cross_strategy,
        "CUSTOM": apply_custom_strategy,
    }

    metrics = run_backtest(strategies, symbol="BTC/USDT", timeframe="5m", limit=500)
    for name, result in metrics.items():
        total = result["total_return"] * 100
        win_rate = result["win_rate"] * 100
        drawdown = result["drawdown"] * 100
        print(
            f"{name}: Return {total:.2f}% | Win Rate {win_rate:.2f}% | Max Drawdown {drawdown:.2f}%"
        )
