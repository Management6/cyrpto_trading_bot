import pandas as pd

def apply_ma_cross_strategy(df):
    df['ma_fast'] = df['close'].rolling(window=5).mean()
    df['ma_slow'] = df['close'].rolling(window=20).mean()
    df.dropna(inplace=True)

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signal = None
    if prev['ma_fast'] < prev['ma_slow'] and curr['ma_fast'] > curr['ma_slow']:
        signal = "BUY"
    elif prev['ma_fast'] > prev['ma_slow'] and curr['ma_fast'] < curr['ma_slow']:
        signal = "SELL"

    return signal, curr['close']