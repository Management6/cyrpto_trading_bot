# offline_replay.py
from dotenv import load_dotenv; load_dotenv()
import os, time, csv
from pathlib import Path
import pandas as pd

from strategies.rsi_strategy_trailing import apply_rsi_strategy
from strategies.macd_strategy_trailing import apply_macd_strategy
from strategies.bollinger_strategy_trailing import apply_bollinger_strategy
from strategies.ma_cross_strategy_trailing import apply_ma_cross_strategy
from strategies.custom_strategy_trailing import apply_custom_strategy
from services.simulation import Simulation
from services.logger import log_trade

SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
CHECK_INTERVAL_SECONDS = 0.01   # fast-forward (10 ms per "bar")

# ---- NEW: simple execution logger for paper fills ----
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
EXEC = LOG_DIR / "exec_log.csv"
if not EXEC.exists():
    with open(EXEC, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp","strategy_name","side","price"])

def log_exec(ts, strat, side, price):
    with open(EXEC, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([ts, strat, side, f"{float(price):.2f}"])

# Optional: turn on strict gating later (BUY only when flat, SELL only when long)
ENFORCE_TRANSITIONS = False
pos = {"RSI":0, "MACD":0, "BOLLINGER":0, "MA_CROSS":0, "CUSTOM":0}

# Load local candles
df_all = pd.read_csv("data/BTCUSDT-1m-sample.csv", parse_dates=["timestamp"])

strategies = {
    "RSI": apply_rsi_strategy,
    "MACD": apply_macd_strategy,
    "BOLLINGER": apply_bollinger_strategy,
    "MA_CROSS": apply_ma_cross_strategy,
    "CUSTOM": apply_custom_strategy,
}

sim = Simulation()

print(f"\n[OFFLINE] Replaying {len(df_all)} candles for {SYMBOL} @ {TIMEFRAME}\n")

# keep your original warmup pattern
for i in range(max(60, len(df_all))):
    if i >= len(df_all): break
    df = df_all.iloc[: i + 1].copy()
    price = float(df.iloc[-1]["close"])
    ts = df.iloc[-1]["timestamp"]

    for name, strat in strategies.items():
        try:
            signal, value, *_ = strat(df)
        except Exception as e:
            print(f"[{name}] error: {e}")
            continue

        val_str = f"{value:.2f}" if value is not None else "-"
        print(f"[{name}] Signal: {signal or '-'} | Value: {val_str} | Price: {price}")
        log_trade(ts, SYMBOL, TIMEFRAME, value, price, signal, strategy_name=name)

        if signal:
            sig = str(signal).strip().upper()  # normalize
            if ENFORCE_TRANSITIONS:
                if sig == "BUY" and pos[name] == 0:
                    sim.place_order("BUY", price)
                    log_exec(ts, name, "BUY", price)
                    pos[name] = 1
                elif sig == "SELL" and pos[name] == 1:
                    sim.place_order("SELL", price)
                    log_exec(ts, name, "SELL", price)
                    pos[name] = 0
            else:
                # behave like your working version (execute on any truthy signal)
                sim.place_order(sig, price)
                if sig in ("BUY","SELL"):
                    log_exec(ts, name, sig, price)

    time.sleep(CHECK_INTERVAL_SECONDS)

print("\n[OFFLINE] Done.")
