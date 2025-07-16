import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
from datetime import datetime

STRATEGIES = ["rsi", "macd", "bollinger", "ma_cross", "custom"]
LOG_DIR = "logs"

fig, axes = plt.subplots(len(STRATEGIES), 1, figsize=(14, 10), sharex=True)
fig.suptitle("Live Strategy Monitor with Profit Estimation", fontsize=18, color='navy')

lines = []
buy_markers = []
sell_markers = []
profit_texts = []
positional_bars = []
floating_texts = []
annotations = [[] for _ in STRATEGIES]

for ax, strategy in zip(axes, STRATEGIES):
    ax.set_ylabel(strategy.upper(), fontsize=10)
    line, = ax.plot([], [], label=strategy.upper(), linewidth=2, zorder=2)
    buy_marker = ax.plot([], [], 'go', zorder=3)[0]
    sell_marker = ax.plot([], [], 'ro', zorder=3)[0]
    profit_text = ax.text(0.98, 0.95, '', transform=ax.transAxes, fontsize=10,
                          verticalalignment='top', horizontalalignment='right',
                          color='green', fontweight='bold', zorder=4)
    bar = ax.axhline(y=0, color='green', linewidth=4, alpha=0.3, visible=False, zorder=1)
    float_text = ax.text(0.02, 0.05, '', transform=ax.transAxes, fontsize=8, color='gray', zorder=4)

    lines.append(line)
    buy_markers.append(buy_marker)
    sell_markers.append(sell_marker)
    profit_texts.append(profit_text)
    positional_bars.append(bar)
    floating_texts.append(float_text)

    ax.legend(loc="upper left")
    ax.grid(True, linestyle='--', alpha=0.5, zorder=1)

axes[-1].set_xlabel("Timestamp", fontsize=10)

def calculate_profit(df):
    position = None
    entry_price = 0
    profit = 0
    win_count = 0
    trade_count = 0
    max_drawdown = 0
    current_profit = 0

    for _, row in df.iterrows():
        signal = row['signal']
        price = row['price']

        if signal == "BUY" and position is None:
            position = 'LONG'
            entry_price = price

        elif signal == "SELL" and position == 'LONG':
            diff = price - entry_price
            current_profit += diff
            if diff > 0:
                win_count += 1
            trade_count += 1
            if current_profit < max_drawdown:
                max_drawdown = current_profit
            position = None

    winrate = (win_count / trade_count) * 100 if trade_count > 0 else 0
    return current_profit, max_drawdown, winrate

def update(frame):
    for i, strategy in enumerate(STRATEGIES):
        file_path = os.path.join(LOG_DIR, f"{strategy}_log.csv")
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                if df.empty or 'value' not in df.columns or df['value'].dropna().empty:
                    lines[i].set_data([], [])
                    buy_markers[i].set_data([], [])
                    sell_markers[i].set_data([], [])
                    profit_texts[i].set_text("No data")
                    floating_texts[i].set_text("")
                    positional_bars[i].set_visible(False)
                    continue

                df = df.tail(50)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                x = df['timestamp']
                y = df['value'].values

                lines[i].set_data(x, y)

                y_margin = (y.max() - y.min()) * 0.1 if y.max() != y.min() else 1
                axes[i].set_ylim(y.min() - y_margin, y.max() + y_margin)

                axes[i].relim()
                axes[i].autoscale_view()

                buy_df = df[df['signal'] == "BUY"]
                sell_df = df[df['signal'] == "SELL"]

                buy_markers[i].set_data(buy_df['timestamp'], buy_df['value'])
                sell_markers[i].set_data(sell_df['timestamp'], sell_df['value'])

                for ann in annotations[i]:
                    ann.remove()
                annotations[i].clear()

                for _, row in pd.concat([buy_df, sell_df]).iterrows():
                    ann = axes[i].annotate(f"{row['price']:.2f}",
                                           xy=(row['timestamp'], row['value']),
                                           xytext=(5, 5), textcoords='offset points',
                                           fontsize=7, color='black', zorder=4)
                    annotations[i].append(ann)

                profit, drawdown, winrate = calculate_profit(df)
                profit_texts[i].set_text(f"Net P/L: {profit:.2f}")
                floating_texts[i].set_text(f"Drawdown: {drawdown:.2f} | Winrate: {winrate:.1f}%")

                if not df.empty and df.iloc[-1]['signal'] == 'BUY':
                    positional_bars[i].set_ydata(df.iloc[-1]['value'])
                    positional_bars[i].set_visible(True)
                else:
                    positional_bars[i].set_visible(False)

                axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

            except Exception as e:
                print(f"Error reading {strategy} log: {e}")

    for i, strategy in enumerate(STRATEGIES):
        file_path = os.path.join(LOG_DIR, f"{strategy}_log.csv")
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df = df.tail(50)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                if 'value' in df.columns and not df['value'].dropna().empty:
                    x = df['timestamp']
                    y = df['value'].values
                    lines[i].set_data(x, y)

                    # Dinamik Y ekseni aralığı
                    y_margin = (y.max() - y.min()) * 0.1 if y.max() != y.min() else 1
                    axes[i].set_ylim(y.min() - y_margin, y.max() + y_margin)
                else:
                    lines[i].set_data([], [])
                    buy_markers[i].set_data([], [])
                    sell_markers[i].set_data([], [])
                    profit_texts[i].set_text("No data")
                    floating_texts[i].set_text("")
                    positional_bars[i].set_visible(False)
                    continue  # diğer stratejiye geç

                # Dinamik Y ekseni aralığı
                if not y.empty:
                    y_margin = (y.max() - y.min()) * 0.1 if y.max() != y.min() else 1
                    axes[i].set_ylim(y.min() - y_margin, y.max() + y_margin)

                axes[i].relim()
                axes[i].autoscale_view()

                buy_df = df[df['signal'] == "BUY"]
                sell_df = df[df['signal'] == "SELL"]

                buy_markers[i].set_data(buy_df['timestamp'], buy_df['value'])
                sell_markers[i].set_data(sell_df['timestamp'], sell_df['value'])

                # Temizle önceki annotate'ler
                for ann in annotations[i]:
                    ann.remove()
                annotations[i].clear()

                for _, row in pd.concat([buy_df, sell_df]).iterrows():
                    ann = axes[i].annotate(f"{row['price']:.2f}",
                                           xy=(row['timestamp'], row['value']),
                                           xytext=(5, 5), textcoords='offset points',
                                           fontsize=7, color='black', zorder=4)
                    annotations[i].append(ann)

                profit, drawdown, winrate = calculate_profit(df)
                profit_texts[i].set_text(f"Net P/L: {profit:.2f}")
                floating_texts[i].set_text(f"Drawdown: {drawdown:.2f} | Winrate: {winrate:.1f}%")

                if not df.empty and df.iloc[-1]['signal'] == 'BUY':
                    positional_bars[i].set_ydata(df.iloc[-1]['value'])
                    positional_bars[i].set_visible(True)
                else:
                    positional_bars[i].set_visible(False)

                axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

            except Exception as e:
                print(f"Error reading {strategy} log: {e}")

ani = FuncAnimation(fig, update, interval=5000)
plt.tight_layout()
plt.show()