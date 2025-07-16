# Crypto Trading Bot

This project provides a collection of simple trading strategies and tools for
paper trading cryptocurrency markets.  Strategies generate BUY/SELL signals using
price data fetched from Binance via `ccxt`.

## Components

- `services/` – Data fetching, logging and simulation utilities.
- `strategies/` – Example trading strategies.
- `monitor.py` – Matplotlib dashboard showing recent signals and paper P/L.
- `backtest.py` – Run strategies on historical data to evaluate performance.

## Backtesting

`backtest.py` will download historical OHLCV data and replay each strategy.
Results show total profit, maximum drawdown and win rate. Logs are written under
`logs/backtests/`.

Run:

```bash
python backtest.py
```

Edit `settings.py` to change symbol or timeframe.
