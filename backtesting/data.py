# backtesting/data.py
import pandas as pd
import time
from datetime import datetime
from binance.client import Client

def load_data(csv_path: str, datetime_col: str = "datetime", tz: str = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=[datetime_col])
    df.set_index(datetime_col, inplace=True)

    
    df['sma_short'] = df['close'].rolling(window=100, min_periods=1).mean()
    df['sma_long'] = df['close'].rolling(window=250, min_periods=1).mean()

    
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.ewm(alpha=1/14, adjust=False).mean()
    rs = roll_up / roll_down
    df['rsi'] = 100 - (100 / (1 + rs))

    if tz:
        df.index = df.index.tz_localize(tz)

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df

def download_binance_data(symbol: str, interval: str, start_date_str: str, output_path: str):
   
    client = Client()
    
    # Parse start date
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    start_ts = int(start_dt.timestamp() * 1000)
    
    now = int(time.time() * 1000)
    
    CHUNK_SIZE = 1000
    all_rows = []
    end_time = now
    
    # Loop backwards from now until start_ts
    while end_time > start_ts:
        klines = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=CHUNK_SIZE,
            endTime=end_time,
        )
        if not klines:
            break
            
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
        
        # Keep minimal columns
        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        
        all_rows.insert(0, df)
        
        earliest = df["open_time"].iloc[0]
        end_time = int(earliest.timestamp() * 1000) - 1
        
        # Rate limit
        time.sleep(0.2)
        
        # Safety break
        if len(df) == 0:
            break

    if all_rows:
        full_df = pd.concat(all_rows, ignore_index=True)
        # Filter strictly >= start_date
        full_df = full_df[full_df["open_time"] >= start_dt]
        
        # Save
        full_df.to_csv(output_path, index=False, header=["datetime","open","high","low","close","volume"])
        return len(full_df)
    else:
        return 0
