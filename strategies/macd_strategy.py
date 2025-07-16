import ta

def apply_macd_strategy(df):
    macd = ta.trend.MACD(close=df['close'])
    df['macd_diff'] = macd.macd_diff()
    df.dropna(inplace=True)

    latest_diff = df.iloc[-1]['macd_diff']
    signal = None

    if latest_diff > 0:
        signal = "BUY"
    elif latest_diff < 0:
        signal = "SELL"

    return signal, latest_diff
