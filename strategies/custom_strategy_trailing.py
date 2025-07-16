import pandas as pd
import ta


def apply_custom_strategy(df, trailing_pct=0.015, return_df=False):
    """Custom RSI/price momentum strategy with trailing stop."""
    df = df.copy()
    if 'price' not in df.columns:
        df['price'] = df['close']

    df['rsi'] = ta.momentum.RSIIndicator(close=df['price'], window=14).rsi()
    df['low_20'] = df['price'].rolling(window=20).min()
    df.dropna(inplace=True)

    signals = []
    position = None
    entry_price = 0
    stop_price = 0
    peak_price = 0

    for i in range(2, len(df)):
        timestamp = df.index[i]
        price = df['price'].iloc[i]
        rsi = df['rsi'].iloc[i]
        low_20 = df['low_20'].iloc[i]

        momentum = df['price'].iloc[i] > df['price'].iloc[i-1] > df['price'].iloc[i-2]
        dip_near = (price - low_20) / low_20 < 0.02

        if rsi < 35 and momentum and dip_near and position is None:
            signals.append({'timestamp': timestamp, 'signal': 'BUY', 'price': price, 'value': rsi})
            position = 'LONG'
            entry_price = price
            stop_price = price * (1 - trailing_pct)
            peak_price = price

        elif position == 'LONG':
            if price > peak_price:
                peak_price = price
                stop_price = max(stop_price, peak_price * (1 - trailing_pct))

            if price < stop_price or rsi > 70:
                signals.append({'timestamp': timestamp, 'signal': 'SELL', 'price': price, 'value': rsi})
                position = None

    signals_df = pd.DataFrame(signals)

    latest_signal = None
    if not signals_df.empty and signals_df.iloc[-1]['timestamp'] == df.index[-1]:
        latest_signal = signals_df.iloc[-1]['signal']

    latest_value = df['rsi'].iloc[-1]

    if return_df:
        return latest_signal, latest_value, signals_df

    return latest_signal, latest_value
