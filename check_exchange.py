from dotenv import load_dotenv; load_dotenv()
import os, ccxt
ex_id = os.getenv("EXCHANGE", "binance")
ex = getattr(ccxt, ex_id)({"enableRateLimit": True})
print("OK. Markets sample:", list(ex.load_markets().keys())[:5])
