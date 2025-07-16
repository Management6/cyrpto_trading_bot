# crypto_trading_bot/strategies/rsi_strategy.py
import pandas as pd
import ta
from datetime import datetime

def apply_rsi_strategy(df, rsi_period=14, buy_threshold=30, sell_threshold=70):
    df = df.copy()
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=rsi_period).rsi()

    df['signal'] = None
    position = None

    for i in range(1, len(df)):
        current_rsi = df['rsi'].iloc[i]
        prev_rsi = df['rsi'].iloc[i - 1]
        price = df['close'].iloc[i]
        timestamp = df['timestamp'].iloc[i]

        if position is None and current_rsi < buy_threshold and prev_rsi >= buy_threshold:
            df.at[df.index[i], 'signal'] = 'BUY'
            position = 'LONG'
        elif position == 'LONG' and current_rsi > sell_threshold and prev_rsi <= sell_threshold:
            df.at[df.index[i], 'signal'] = 'SELL'
            position = None

    df['value'] = df['rsi']
    df['price'] = df['close']
    df[['timestamp', 'value', 'signal', 'price']].to_csv('logs/rsi_log.csv', index=False)
    return df