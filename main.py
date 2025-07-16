import time
from services.data_service import fetch_ohlcv, get_available_timeframes
from strategies.rsi_strategy_trailing import apply_rsi_strategy
from strategies.macd_strategy_trailing import apply_macd_strategy
from strategies.bollinger_strategy_trailing import apply_bollinger_strategy
from strategies.ma_cross_strategy_trailing import apply_ma_cross_strategy
from strategies.custom_strategy_trailing import apply_custom_strategy
from services.simulation import simulate_order
from services.logger import log_trade
from settings import CHECK_INTERVAL_SECONDS, SYMBOL, TIMEFRAME

def select_best_timeframe():
    timeframes = get_available_timeframes()
    return TIMEFRAME

if __name__ == "__main__":
    current_timeframe = select_best_timeframe()
    print(f"\n[INFO] Using timeframe: {current_timeframe}\n")

    strategies = {
        "RSI": apply_rsi_strategy,
        "MACD": apply_macd_strategy,
        "BOLLINGER": apply_bollinger_strategy,
        "MA_CROSS": apply_ma_cross_strategy,
        "CUSTOM": apply_custom_strategy
    }

    while True:
        try:
            df = fetch_ohlcv(symbol=SYMBOL, timeframe=current_timeframe)
            price = df.iloc[-1]['close']
            timestamp = df.iloc[-1]['timestamp']

            for name, strategy in strategies.items():
                signal, value, *_ = strategy(df.copy())
                print(f"[{name}] Signal: {signal or '-'} | Value: {round(value, 2)} | Price: {price}")
                log_trade(timestamp, SYMBOL, current_timeframe, value, price, signal, strategy_name=name)
                if signal:
                    simulate_order(signal, price)

            time.sleep(CHECK_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Error: {str(e)}")
            time.sleep(60)