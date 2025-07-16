import pandas as pd

def apply_custom_strategy(df):
    # Örnek: Momentum ve hacim ilişkisini kullanan özel bir gösterge
    df['returns'] = df['close'].pct_change()
    df['volume_avg'] = df['volume'].rolling(window=10).mean()
    df['custom_metric'] = df['returns'] * (df['volume'] / df['volume_avg'])
    df.dropna(inplace=True)

    latest_value = df.iloc[-1]['custom_metric']
    signal = None

    if latest_value > 0.01:
        signal = "BUY"
    elif latest_value < -0.01:
        signal = "SELL"

    return signal, latest_value