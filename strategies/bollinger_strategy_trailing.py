import pandas as pd
import ta


def apply_bollinger_strategy(df, trailing_pct=0.015, return_df=False):
    """Apply Bollinger Bands strategy with trailing stop."""
    bb = ta.volatility.BollingerBands(close=df['price'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_middle'] = bb.bollinger_mavg()
    df.dropna(inplace=True)

    signals = []
    position = None
    entry_price = 0
    stop_price = 0
    peak_price = 0

    for i in range(1, len(df)):
        timestamp = df.index[i]
        price = df['price'].iloc[i]
        lower = df['bb_lower'].iloc[i]
        upper = df['bb_upper'].iloc[i]

        if price < lower and position is None:
            signals.append({'timestamp': timestamp, 'signal': 'BUY', 'price': price, 'value': lower})
            position = 'LONG'
            entry_price = price
            stop_price = price * (1 - trailing_pct)
            peak_price = price

        elif position == 'LONG':
            if price > peak_price:
                peak_price = price
                stop_price = max(stop_price, peak_price * (1 - trailing_pct))

            if price < stop_price:
                signals.append({'timestamp': timestamp, 'signal': 'SELL', 'price': price, 'value': upper})
                position = None

    signals_df = pd.DataFrame(signals)

    latest_signal = None
    if not signals_df.empty and signals_df.iloc[-1]['timestamp'] == df.index[-1]:
        latest_signal = signals_df.iloc[-1]['signal']

    latest_value = df['price'].iloc[-1]

    if return_df:
        return latest_signal, latest_value, signals_df

    return latest_signal, latest_value
