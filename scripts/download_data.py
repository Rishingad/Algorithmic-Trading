# scripts/download_data.py
import argparse
import sys
import os
import yfinance as yf
import pandas as pd

def download_data(symbol, period="1y", interval="1d", output_path=None):
    """
    Download historical data from Yahoo Finance.
    
    Args:
        symbol (str): Ticker symbol (e.g., 'GC=F' for Gold, 'AAPL' for Apple).
        period (str): Data period to download (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max).
        interval (str): Data interval (e.g., 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo).
        output_path (str): Path to save the CSV file. If None, saves to root as {symbol}_{interval}_{period}.csv.
    """
    print(f"Downloading {symbol} data (Period: {period}, Interval: {interval})...")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"Error: No data found for symbol '{symbol}'. Please check the ticker.")
            sys.exit(1)

        # Yahoo Finance returns index as Datetime (tz-aware).
        # We need to structure it like the project expects: datetime,open,high,low,close,volume
        
        df.reset_index(inplace=True)
        
        # Rename columns to lowercase matches
        # YF columns: Date/Datetime, Open, High, Low, Close, Volume, Dividends, Stock Splits
        df.columns = [c.lower() for c in df.columns]
        
        # Handle 'date' vs 'datetime' column name difference
        if 'date' in df.columns:
            df.rename(columns={'date': 'datetime'}, inplace=True)
            
        # Ensure we have the required columns
        required_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        available_cols = [c for c in required_cols if c in df.columns]
        
        if len(available_cols) < 6:
            print(f"Warning: Some columns missing. Found: {available_cols}")
        
        # Select and reorder
        df = df[available_cols]
        
        # Generate filename if not provided
        if not output_path:
            # Clean symbol for filename (e.g., GC=F -> GC-F)
            safe_symbol = symbol.replace("=", "-").replace("^", "")
            filename = f"{safe_symbol}_{interval}_{period}.csv"
            # Save to project root (parent of 'scripts')
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(root_dir, filename)
            
        df.to_csv(output_path, index=False)
        print(f"Successfully saved {len(df)} rows to {output_path}")
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download financial data from Yahoo Finance.")
    parser.add_argument("--symbol", type=str, required=True, help="Ticker symbol (e.g., GC=F, AAPL)")
    parser.add_argument("--period", type=str, default="1y", help="Period (e.g., 1y, 5y, max)")
    parser.add_argument("--interval", type=str, default="1d", help="Interval (e.g., 1d, 1h, 5m)")
    parser.add_argument("--output", type=str, help="Output CSV path")
    
    args = parser.parse_args()
    
    download_data(args.symbol, args.period, args.interval, args.output)
