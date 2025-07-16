import pandas as pd

def apply_ma_cross_strategy(df, trailing_pct=0.015):
    df['ma_short'] = df['price'].rolling(window=5).mean()
    df['ma_long'] = df['price'].rolling(window=20).mean()
    df.dropna(inplace=True)

    signals = []
    position = None
    entry_price = 0
    stop_price = 0
    peak_price = 0

    for i in range(1, len(df)):
        timestamp = df.index[i]
        price = df['price'].iloc[i]
        short = df['ma_short'].iloc[i]
        long = df['ma_long'].iloc[i]

        if short > long and df['ma_short'].iloc[i-1] <= df['ma_long'].iloc[i-1]:
            # Golden Cross - BUY sinyali
            signals.append({'timestamp': timestamp, 'signal': 'BUY', 'price': price, 'value': short})
            position = 'LONG'
            entry_price = price
            stop_price = price * (1 - trailing_pct)
            peak_price = price

        elif position == 'LONG':
            if price > peak_price:
                peak_price = price
                stop_price = max(stop_price, peak_price * (1 - trailing_pct))

            if price < stop_price:
                signals.append({'timestamp': timestamp, 'signal': 'SELL', 'price': price, 'value': short})
                position = None

    return pd.DataFrame(signals)
