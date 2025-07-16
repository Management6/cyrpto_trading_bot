import pandas as pd
import ta


def apply_macd_strategy(df, trailing_pct=0.015, return_df=False):
    """Apply MACD strategy with trailing stop."""
    macd = ta.trend.MACD(close=df['price'])
    df['macd'] = macd.macd()
    df['signal_line'] = macd.macd_signal()
    df.dropna(inplace=True)

    signals = []
    position = None
    entry_price = 0
    stop_price = 0
    peak_price = 0

    for i in range(1, len(df)):
        timestamp = df.index[i]
        price = df['price'].iloc[i]
        macd_val = df['macd'].iloc[i]
        signal_val = df['signal_line'].iloc[i]

        if macd_val > signal_val and df['macd'].iloc[i-1] <= df['signal_line'].iloc[i-1] and position is None:
            signals.append({'timestamp': timestamp, 'signal': 'BUY', 'price': price, 'value': macd_val})
            position = 'LONG'
            entry_price = price
            stop_price = price * (1 - trailing_pct)
            peak_price = price

        elif position == 'LONG':
            if price > peak_price:
                peak_price = price
                stop_price = max(stop_price, peak_price * (1 - trailing_pct))

            if price < stop_price:
                signals.append({'timestamp': timestamp, 'signal': 'SELL', 'price': price, 'value': macd_val})
                position = None

    signals_df = pd.DataFrame(signals)

    latest_signal = None
    if not signals_df.empty and signals_df.iloc[-1]['timestamp'] == df.index[-1]:
        latest_signal = signals_df.iloc[-1]['signal']

    latest_value = df['macd'].iloc[-1]

    if return_df:
        return latest_signal, latest_value, signals_df

    return latest_signal, latest_value
