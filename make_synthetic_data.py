# Generates data/BTCUSDT-1m-sample.csv for offline tests
import os, math, random, csv, datetime as dt
os.makedirs("data", exist_ok=True)
path = "data/BTCUSDT-1m-sample.csv"

start = dt.datetime(2024, 6, 1, 0, 0)
price = 30000.0
with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestamp","open","high","low","close","volume"])
    for i in range(1500):  # ~25 hours of 1m candles
        t = start + dt.timedelta(minutes=i)
        # synthetic move: slow trend + noise
        drift = 0.00002 * i
        shock = random.gauss(0, 0.0008)
        ret = drift + 0.003 * math.sin(i/120) + shock
        o = price
        c = max(100.0, o * (1 + ret))
        h = max(o, c) * (1 + random.uniform(0, 0.0008))
        l = min(o, c) * (1 - random.uniform(0, 0.0008))
        v = random.uniform(5, 50)
        w.writerow([t.isoformat(), f"{o:.2f}", f"{h:.2f}", f"{l:.2f}", f"{c:.2f}", f"{v:.4f}"])
        price = c

print("Wrote", path)
