# scripts/download_btc_1min.py
"""Download 1‑minute BTC/USDT OHLCV data for the last 5 years from Binance.

The Binance REST API returns at most 1000 klines per request, so we fetch
chunks backwards from the current timestamp until we have ~5 years of data.
The script writes a CSV file ``btc_1min_last5y.csv`` in the project root.

Requirements:
    pip install python-binance pandas
"""
import os
import time
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client

# ---------------------------------------------------------------------------
# Configuration – adjust if you want a different symbol or output path
# ---------------------------------------------------------------------------
SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "btc_5min_last1y.csv")

# Binance public API – no API key needed for public data
client = Client()

# Compute the timestamp for "now" and the timestamp 5 years ago
now = int(time.time() * 1000)  # milliseconds
one_year_ago = int((datetime.utcnow() - timedelta(days=365)).timestamp() * 1000)  # timestamp 1 year ago in ms

# Binance returns data in ascending order; we will request chunks moving
# backwards (endTime parameter) and then prepend them.

CHUNK_SIZE = 1000  # max per request
all_rows = []
end_time = now
while end_time > one_year_ago:
    # Binance will return up to CHUNK_SIZE rows ending *before* end_time
    klines = client.get_klines(
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=CHUNK_SIZE,
        endTime=end_time,
    )
    if not klines:
        break
    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=[
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ])
    # Keep only needed columns and convert timestamps
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    # Prepend to the list (since we are moving backwards)
    all_rows.insert(0, df)
    # Update end_time to the earliest open_time we just fetched minus 1 ms
    earliest = df["open_time"].iloc[0]
    end_time = int(earliest.timestamp() * 1000) - 1
    # Small sleep to respect Binance rate limits (1200 weight per minute)
    time.sleep(0.2)

# Concatenate all chunks
full_df = pd.concat(all_rows, ignore_index=True)
# Trim any rows older than five years (just in case)
cutoff = datetime.utcnow() - timedelta(days=365)
full_df = full_df[full_df["open_time"] >= cutoff]

# Write CSV – columns match the format expected by ``load_data``
full_df.to_csv(OUTPUT_CSV, index=False, header=["datetime","open","high","low","close","volume"])
print(f"Saved {len(full_df)} rows to {OUTPUT_CSV}")
