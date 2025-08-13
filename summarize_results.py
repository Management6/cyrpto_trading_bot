from pathlib import Path
import pandas as pd

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# collect per-strategy logs (e.g., rsi_log.csv, macd_log.csv, ...)
files = sorted(
    f for f in LOG_DIR.glob("*_log.csv")
    if f.name not in {"summary_counts.csv", "summary_pnl.csv", "summary.txt", "trades.csv"}
)

if not files:
    raise SystemExit(f"No per-strategy logs found in {LOG_DIR.resolve()}")

dfs = []
for f in files:
    # infer strategy name from file name: rsi_log.csv -> RSI
    inferred = f.stem.replace("_log", "").upper()

    df = pd.read_csv(f)
    # normalize column names to lower
    df.columns = [c.strip().lower() for c in df.columns]

    # expected cols (fill if missing)
    needed = ["timestamp", "symbol", "timeframe", "value", "price", "signal", "strategy_name"]
    for col in needed:
        if col not in df.columns:
            df[col] = None

    # if strategy_name missing/empty, use the inferred one
    if df["strategy_name"].isna().all() or (df["strategy_name"] == "").all():
        df["strategy_name"] = inferred

    # coerce types
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["signal"] = df["signal"].astype(str).str.upper()
    df["strategy_name"] = df["strategy_name"].astype(str)

    dfs.append(df[needed])

# merge logs and sort by time
all_trades = pd.concat(dfs, ignore_index=True).dropna(subset=["timestamp"]).sort_values("timestamp")
combined_path = LOG_DIR / "trades.csv"
all_trades.to_csv(combined_path, index=False)

# counts per strategy/signal
counts = (
    all_trades.pivot_table(index="strategy_name", columns="signal", aggfunc="size", fill_value=0)
    .sort_index()
)

# naive long-only PnL per strategy (BUY->SELL sequences inside each strategy)
def naive_pnl(group: pd.DataFrame):
    pos = 0
    entry = None
    pnl = 0.0
    trades = 0
    for _, row in group.iterrows():
        sig, px = row["signal"], row["price"]
        if sig == "BUY" and pos == 0:
            pos, entry = 1, px
        elif sig == "SELL" and pos == 1:
            pnl += (px - entry)
            trades += 1
            pos, entry = 0, None
    return pd.Series({"round_trips": trades, "pnl_points": pnl})

pnl = all_trades.groupby("strategy_name", sort=True).apply(naive_pnl)

# build summary text
summary_txt = []
summary_txt.append(f"Rows: {len(all_trades)}")
summary_txt.append(f"Range: {all_trades['timestamp'].min()} → {all_trades['timestamp'].max()}")
summary_txt.append("\nCounts per strategy/signal:\n")
summary_txt.append(counts.to_string())
summary_txt.append("\nNaive long-only PnL (BUY->SELL pairs; ignores fees/size):\n")
summary_txt.append(pnl.to_string())

(LOG_DIR / "summary.txt").write_text("\n".join(summary_txt), encoding="utf-8")
counts.to_csv(LOG_DIR / "summary_counts.csv")
pnl.to_csv(LOG_DIR / "summary_pnl.csv")

print("\n".join(summary_txt))
print(f"\nWrote: {combined_path}, logs/summary.txt, logs/summary_counts.csv, logs/summary_pnl.csv")
