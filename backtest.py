from services.backtester import Backtester
from strategies.rsi_strategy_trailing import apply_rsi_strategy
from strategies.macd_strategy_trailing import apply_macd_strategy
from strategies.bollinger_strategy_trailing import apply_bollinger_strategy
from strategies.ma_cross_strategy_trailing import apply_ma_cross_strategy
from strategies.custom_strategy_trailing import apply_custom_strategy
from settings import SYMBOL, TIMEFRAME


if __name__ == "__main__":
    strategies = {
        "RSI": apply_rsi_strategy,
        "MACD": apply_macd_strategy,
        "BOLLINGER": apply_bollinger_strategy,
        "MA_CROSS": apply_ma_cross_strategy,
        "CUSTOM": apply_custom_strategy,
    }

    tester = Backtester(strategies)
    results = tester.run(SYMBOL, TIMEFRAME, limit=500)

    for name, stats in results.items():
        print(f"{name}: Profit={stats['profit']} Drawdown={stats['drawdown']} Winrate={stats['winrate']}%")

