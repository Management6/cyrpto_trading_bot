import os
import pandas as pd
from ta.volatility import BollingerBands

BB_LEN = int(os.getenv("BB_LEN", "20"))
BB_STD = float(os.getenv("BB_STD", "2"))
BB_BW_MIN = float(os.getenv("BB_BW_MIN", "0.01"))  # min band width (1%) to avoid chop

def apply_bollinger_strategy(df: pd.DataFrame):
    # Guard: need enough rows and a close column
    if df is None or "close" not in df.columns or len(df) < BB_LEN + 2:
        return None, None

    close = df["close"].astype(float)

    bb = BollingerBands(close=close, window=BB_LEN, window_dev=BB_STD, fillna=False)
    mid = bb.bollinger_mavg()
    low = bb.bollinger_lband()
    high = bb.bollinger_hband()

    # Band width (% of mid) – we’ll skip signals when volatility is tiny
    bw = (high - low) / mid.replace(0, pd.NA)
    enough_vol = bw > BB_BW_MIN

    # Mean-reversion style:
    # BUY when price crosses back up through the lower band (after being below),
    # SELL when price crosses down through the mid band (take profit/exit)
    cross_up_low   = (close.shift(1) < low.shift(1)) & (close >= low) & enough_vol
    cross_down_mid = (close.shift(1) >= mid.shift(1)) & (close <  mid)

    signal = None
    if bool(cross_up_low.iloc[-1]):
        signal = "BUY"
    elif bool(cross_down_mid.iloc[-1]):
        signal = "SELL"

    # Return a useful value to print; band width is a nice diagnostic
    return signal, float(bw.iloc[-1])
