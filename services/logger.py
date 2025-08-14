# services/logger.py
import os, csv, math

def _safe_round(x, ndigits=2):
    """Return rounded float or empty string for None/NaN/non-numeric."""
    try:
        if x is None:
            return ""
        fx = float(x)
        if math.isnan(fx):
            return ""
        return round(fx, ndigits)
    except (ValueError, TypeError):
        return ""

def log_trade(timestamp, symbol, timeframe, indicator_value, price, signal, strategy_name="UNKNOWN"):
    os.makedirs("logs", exist_ok=True)
    path = os.path.join("logs", f"{str(strategy_name).lower()}_log.csv")
    write_header = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["timestamp","symbol","timeframe","value","price","signal","strategy_name"])
        w.writerow([
            timestamp,
            symbol,
            timeframe,
            _safe_round(indicator_value),
            _safe_round(price),
            (signal if signal else "-"),
            strategy_name
        ])
