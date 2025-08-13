from pathlib import Path
import pandas as pd
import math

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

EXCLUDE = {"summary_counts.csv", "summary_pnl.csv", "summary.txt", "trades.csv"}

def pick(cols, *candidates):
    cols = set(cols)
    for opts in candidates:
        for c in opts:
            if c in cols:
                return c
    return None

def to_ts(s):
    # Handle strings and numeric epochs (s/ms/us/ns)
    ts = pd.to_datetime(s, errors="coerce", utc=True)
    if ts.notna().any():
        return ts
    # try numeric epochs
    x = pd.to_numeric(s, errors="coerce")
    scale = None
    if x.notna().any():
        mx = x.max()
        # heuristics
        if mx > 1e18:   scale = 1e9   # ns
        elif mx > 1e15: scale = 1e6   # µs
        elif mx > 1e12: scale = 1e3   # ms
        else:           scale = 1     # s
        ts = pd.to_datetime(x / scale, unit="s", utc=True, errors="coerce")
    return ts

def normalize_signal(s):
    s = s.astype(str).str.upper()
    # map common variants
    s = s.replace({
        "BUY_SIGNAL":"BUY", "OPEN_LONG":"BUY", "ENTER_LONG":"BUY",
        "SELL_SIGNAL":"SELL", "CLOSE_LONG":"SELL", "EXIT_LONG":"SELL",
        "OPEN_SHORT":"SELL", "ENTER_SHORT":"SELL", "CLOSE_SHORT":"BUY"  # adjust if you trade shorts
    })
    return s

files = sorted(
    f for f in LOG_DIR.rglob("*_log.csv")
    if f.is_file() and f.name not in EXCLUDE
)

if not files:
    raise SystemExit(f"No per-strategy logs found under {LOG_DIR.resolve()} (searched recursively). "
                     f"Expected files like rsi_log.csv, macd_log.csv, exec_log.csv.")

rows_kept = 0
dfs = []
for f in files:
    df_raw = pd.read_csv(f)
    df_raw.columns = [c.strip().lower() for c in df_raw.columns]

    ts_col   = pick(df_raw.columns, ("timestamp","time","ts","datetime","date"))
    px_col   = pick(df_raw.columns, ("fill_price","avg_price","price","px","close"))
    sig_col  = pick(df_raw.columns, ("signal","side","action","type","direction","event"))
    sym_col  = pick(df_raw.columns, ("symbol","market","ticker","instrument"))
    tf_col   = pick(df_raw.columns, ("timeframe","tf","interval"))

    if ts_col is None or sig_col is None or px_col is None:
        print(f"[WARN] {f.name}: missing key columns "
              f"(timestamp? signal? price?). Found: {list(df_raw.columns)[:10]}...")
        continue

    df = pd.DataFrame({
        "timestamp": to_ts(df_raw[ts_col]),
        "symbol": df_raw[sym_col] if sym_col else None,
        "timeframe": df_raw[tf_col] if tf_col else None,
        "price": pd.to_numeric(df_raw[px_col], errors="coerce"),
        "signal": normalize_signal(df_raw[sig_col]),
        "strategy_name": None
    })

    # Filter to executed/meaningful rows if logs contain statuses
    if "status" in df_raw.columns:
        df = df[df_raw["status"].astype(str).str.upper().isin({"FILLED", "EXECUTED", "DONE"})]

    # Infer strategy name from file name (e.g., rsi_log.csv -> RSI)
    inferred = f.stem.replace("_log","").upper()
    df["strategy_name"] = inferred

    before = len(df)
    df = df.dropna(subset=["timestamp","price"])
    kept = len(df)
    rows_kept += kept
    print(f"[OK] {f.name}: kept {kept}/{before} rows as trades/signals; "
          f"first={df['timestamp'].min()} last={df['timestamp'].max()} strategy={inferred}")

    if kept:
        dfs.append(df)

if not dfs:
    raise SystemExit("Parsed 0 usable rows. Check that your logs actually include timestamp, signal and price fields.")

all_trades = pd.concat(dfs, ignore_index=True).sort_values("timestamp")
combined_path = LOG_DIR / "trades.csv"
all_trades.to_csv(combined_path, index=False)

# counts per strategy/signal
counts = (
    all_trades.pivot_table(index="strategy_name", columns="signal", aggfunc="size", fill_value=0)
    .sort_index()
)

def naive_pnl(group: pd.DataFrame):
    pos = 0; entry = None; pnl = 0.0; trades = 0
    for _, row in group.iterrows():
        sig, px = row["signal"], row["price"]
        if sig == "BUY" and pos == 0:
            pos, entry = 1, px
        elif sig == "SELL" and pos == 1:
            pnl += (px - entry); trades += 1; pos, entry = 0, None
    return pd.Series({"round_trips": trades, "pnl_points": pnl})

pnl = all_trades.groupby("strategy_name", sort=True).apply(naive_pnl)

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
