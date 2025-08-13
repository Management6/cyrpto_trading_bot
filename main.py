import os
import time
from dotenv import load_dotenv

# --- load .env so we can use DRY_RUN and other settings without editing code ---
load_dotenv()
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"

from services.data_service import fetch_ohlcv, get_available_timeframes
from strategies.rsi_strategy_trailing import apply_rsi_strategy
from strategies.macd_strategy_trailing import apply_macd_strategy
from strategies.bollinger_strategy_trailing import apply_bollinger_strategy
from strategies.ma_cross_strategy_trailing import apply_ma_cross_strategy
from strategies.custom_strategy_trailing import apply_custom_strategy
from services.simulation import Simulation
from services.logger import log_trade
from settings import CHECK_INTERVAL_SECONDS, SYMBOL, TIMEFRAME


def select_best_timeframe():
    timeframes = get_available_timeframes()
    # For now we honor TIMEFRAME from settings/.env; plug your logic here if you
    # later want to scan `timeframes` and auto-pick.
    return TIMEFRAME


if __name__ == "__main__":
    current_timeframe = select_best_timeframe()
    print(f"\n[INFO] Using timeframe: {current_timeframe}")
    print(f"[INFO] DRY_RUN={'ON' if DRY_RUN else 'OFF'}\n")

    simulation = Simulation()  # unchanged

    strategies = {
        "RSI": apply_rsi_strategy,
        "MACD": apply_macd_strategy,
        "BOLLINGER": apply_bollinger_strategy,
        "MA_CROSS": apply_ma_cross_strategy,
        "CUSTOM": apply_custom_strategy,
    }

    while True:
        try:
            df = fetch_ohlcv(symbol=SYMBOL, timeframe=current_timeframe)
            price = df.iloc[-1]["close"]
            timestamp = df.iloc[-1]["timestamp"]

            for name, strategy in strategies.items():
                signal, value, *_ = strategy(df.copy())
                print(f"[{name}] Signal: {signal or '-'} | Value: {round(value, 2)} | Price: {price}")

                # keep your existing log line (records signal & context)
                log_trade(timestamp, SYMBOL, current_timeframe, value, price, signal, strategy_name=name)

                if signal:
                    if DRY_RUN:
                        # paper mode: don't place real orders; just make it explicit in the console
                        print(f"[PAPER] Would {signal} {SYMBOL} at {price} (strategy={name})")
                        # optionally, you can also log a synthetic paper fill:
                        # log_trade(timestamp, SYMBOL, current_timeframe, value, price, f'PAPER_{signal}', strategy_name=name)
                    else:
                        # live path (unchanged; uses your Simulation class)
                        simulation.place_order(signal, price)

            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(60)
