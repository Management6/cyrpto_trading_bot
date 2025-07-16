import pandas as pd
import ta


def apply_rsi_strategy(df, trailing_pct=0.015, return_df=False):
    """Apply RSI strategy with trailing stop.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing at least a ``price`` column.
    trailing_pct : float, optional
        Trailing stop percentage.
    return_df : bool, optional
        When ``True`` also return the dataframe of generated signals.

    Returns
    -------
    tuple
        ``(signal, value)`` or ``(signal, value, signals_df)`` when
        ``return_df`` is ``True``.
    """

    df['rsi'] = ta.momentum.RSIIndicator(close=df['price'], window=14).rsi()
    df.dropna(inplace=True)

    signals = []
    position = None
    entry_price = 0
    stop_price = 0
    peak_price = 0

    for i in range(1, len(df)):
        timestamp = df.index[i]
        price = df['price'].iloc[i]
        rsi = df['rsi'].iloc[i]

        if rsi < 30 and position is None:
            signals.append({'timestamp': timestamp, 'signal': 'BUY', 'price': price, 'value': rsi})
            position = 'LONG'
            entry_price = price
            stop_price = price * (1 - trailing_pct)
            peak_price = price

        elif position == 'LONG':
            if price > peak_price:
                peak_price = price
                stop_price = max(stop_price, peak_price * (1 - trailing_pct))

            if price < stop_price:
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
