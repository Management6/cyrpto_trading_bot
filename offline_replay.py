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

# --- exec logger (paper fills) ---
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
EXEC = LOG_DIR / "exec_log.csv"
if not EXEC.exists():
    with open(EXEC, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp","strategy_name","side","price"])

def log_exec(ts, strat, side, price):
    with open(EXEC, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([ts, strat, side, f"{float(price):.2f}"])

# --- options ---
ENFORCE_TRANSITIONS = True  # BUY only when flat; SELL only when long (set False to log every BUY/SELL)

# --- state ---
pos = {"RSI":0, "MACD":0, "BOLLINGER":0, "MA_CROSS":0, "CUSTOM":0}
exec_rows = 0

# --- data ---
df_all = pd.read_csv("data/BTCUSDT-1m-sample.csv", parse_dates=["timestamp"])

# --- strategies ---
strategies = {
    "RSI": apply_rsi_strategy,
    "MACD": apply_macd_strategy,
    "BOLLINGER": apply_bollinger_strategy,
    "MA_CROSS": apply_ma_cross_strategy,
    "CUSTOM": apply_custom_strategy,
}

sim = Simulation()

def normalize_side(sig) -> str | None:
    """Map many signal variants to 'BUY'/'SELL'; return None for hold/unknown."""
    if sig is None:
        return None
    s = str(sig).strip().upper()
    if s in ("BUY","LONG","OPEN_LONG","GO_LONG","ENTER_LONG"):
        return "BUY"
    if s in ("SELL","SHORT","CLOSE_LONG","EXIT","EXIT_LONG","CLOSE","CLOSE_POSITION"):
        return "SELL"
    if "BUY" in s:
        return "BUY"
    if "SELL" in s:
        return "SELL"
    return None

print(f"\n[OFFLINE] Replaying {len(df_all)} candles for {SYMBOL} @ {TIMEFRAME}\n")

# simple warmup so indicators have history
WARMUP = 120
for i in range(max(WARMUP, len(df_all))):
    if i >= len(df_all):
        break
    df = df_all.iloc[: i + 1].copy()
    price = float(df.iloc[-1]["close"])
    ts = df.iloc[-1]["timestamp"]

    for name, strat in strategies.items():
        try:
            signal, value, *_ = strat(df)
        except Exception as e:
            # indicator not ready yet; skip
            continue

        # keep your existing signal log
        log_trade(ts, SYMBOL, TIMEFRAME, value, price, signal, strategy_name=name)

        # normalize and decide whether to log an execution
        side = normalize_side(signal)
        if not side:
            continue

        # still call your simulator so behavior matches your previous runs
        sim.place_order(side, price)

        if ENFORCE_TRANSITIONS:
            if side == "BUY" and pos[name] == 0:
                log_exec(ts, name, "BUY", price); exec_rows += 1
                pos[name] = 1
            elif side == "SELL" and pos[name] == 1:
                log_exec(ts, name, "SELL", price); exec_rows += 1
                pos[name] = 0
        else:
            # log every normalized BUY/SELL regardless of position
            log_exec(ts, name, side, price); exec_rows += 1

    time.sleep(CHECK_INTERVAL_SECONDS)

print("\n[OFFLINE] Done.")
print(f"Wrote {exec_rows} execution row(s) to {EXEC}")
