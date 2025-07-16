import os
import ccxt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

binance = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'
    }
})

def fetch_ohlcv(symbol="BTC/USDT", timeframe="5m", limit=100):
    ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    # many strategy modules expect a ``price`` column which mirrors ``close``.
    # add it here to avoid ``KeyError: 'price'`` during strategy execution.
    df['price'] = df['close']
    return df

def get_available_timeframes():
    return ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]
