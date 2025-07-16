import ta

def apply_bollinger_strategy(df):
    indicator = ta.volatility.BollingerBands(close=df['close'])
    df['bb_upper'] = indicator.bollinger_hband()
    df['bb_lower'] = indicator.bollinger_lband()
    df.dropna(inplace=True)

    price = df.iloc[-1]['close']
    upper = df.iloc[-1]['bb_upper']
    lower = df.iloc[-1]['bb_lower']

    signal = None
    if price < lower:
        signal = "BUY"
    elif price > upper:
        signal = "SELL"

    return signal, price