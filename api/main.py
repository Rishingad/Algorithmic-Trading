
# api/main.py
import glob
import os
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backtesting.engine import BacktestEngine
from backtesting.data import load_data, download_binance_data

# Import strategies
from examples.simple_ma import ImprovedStrategy
try:
    from examples.price_action_strategy import PriceActionStrategy
except ImportError:
    PriceActionStrategy = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

class DownloadRequest(BaseModel):
    symbol: str
    interval: str
    start_date: str

class BacktestRequest(BaseModel):
    strategy_name: str
    data_file: str

# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/api/files")
def list_files():
    """List all CSV files in the project root."""
    files = glob.glob("*.csv")
    return {"files": files}

@app.get("/api/strategies")
def list_strategies():
    """List available strategies."""
    strategies = ["ImprovedStrategy"]
    if PriceActionStrategy:
        strategies.append("PriceActionStrategy")
    return {"strategies": strategies}

@app.post("/api/download")
def download_data(req: DownloadRequest):
    """Download data from Binance."""
    output_filename = f"{req.symbol}_{req.interval}_{req.start_date}.csv"
    output_filename = output_filename.replace(" ", "_").replace(":", "-")
    
    try:
        count = download_binance_data(
            req.symbol, 
            req.interval, 
            req.start_date, 
            output_filename
        )
        if count == 0:
            return {"message": "No data found or downloaded.", "filename": None}
        return {"message": f"Downloaded {count} rows.", "filename": output_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    """Run a backtest."""
    if not os.path.exists(req.data_file):
        raise HTTPException(status_code=404, detail="Data file not found")
        
    try:
        df = load_data(req.data_file)
        
        if req.strategy_name == "ImprovedStrategy":
            strategy_cls = ImprovedStrategy
        elif req.strategy_name == "PriceActionStrategy" and PriceActionStrategy:
            strategy_cls = PriceActionStrategy
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
            
        engine = BacktestEngine(strategy_cls, df)
        stats = engine.run()
        
        # Prepare Result
        equity_data = [
            {"time": str(t), "value": v} 
            for t, v in engine.equity_curve
        ]
        
        # Optimize OHLCV Data for chart
        # Limit to last 5000 candles to prevent frontend crash
        MAX_CANDLES = 5000
        chart_df = df.iloc[-MAX_CANDLES:].copy() if len(df) > MAX_CANDLES else df.copy()
        
        # Convert to list of dicts directly
        chart_df['time'] = chart_df.index.astype(int) // 10**9 # Convert ns to seconds
        # Renaming columns to match lightweight-charts expected format if needed
        # But we are constructing dicts manually.
        
        # Fast conversion
        ohlcv = chart_df[['time', 'open', 'high', 'low', 'close']].to_dict(orient='records')

        metrics_dict = {}
        if hasattr(stats, "to_dict"):
            metrics_dict = stats.to_dict()
        else:
             metrics_dict = {"error": "Metrics serialization failed"}

        return {
            "equity_curve": equity_data,
            "ohlcv": ohlcv,
            "metrics": metrics_dict
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
