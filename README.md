# 📊 AlgoBacktesting

A full-stack platform for backtesting algorithmic trading strategies. A Python engine
simulates strategies bar by bar on historical OHLCV data, a FastAPI backend serves the
results, and a React dashboard shows performance analytics, interactive charts and
round-trip trade logs. It can also download market data from Binance on demand.

## Features

- **Pluggable strategy engine**: any Python class with a `next(bar)` method can be a
  strategy. The engine handles order execution, cash and position tracking, and
  commission and slippage.
- **Performance analytics**:
  - Total and annualized return, max drawdown, Sharpe ratio
  - Round-trip trade reconstruction (FIFO matching, partial closes, long and short),
    with PnL, ROI and holding time per trade
  - Win rate and average trade duration
  - Monthly returns heatmap
  - Monte Carlo simulation (trade-order shuffling) to show the spread of outcomes
- **Interactive dashboard (React + Vite)**:
  - Equity curve (Chart.js)
  - Candlestick price chart (TradingView `lightweight-charts`)
  - Monthly heatmap, Monte Carlo paths and trade log
  - Light and dark themes
- **Automated data sourcing**:
  - Binance klines downloader (any symbol, 1m–1d intervals) that pages backwards in
    1,000-candle chunks with rate limiting. You can run it from the UI or the API.
  - Yahoo Finance downloader for stocks, futures and commodities (e.g. `AAPL`, `GC=F`)
- **Example strategies**: SMA/RSI crossover, an ICT-style price-action strategy
  (order blocks, fair-value gaps, market structure, engulfing and pin bars, needing
  3+ confirmations, 1:2 risk/reward), EMBIA_V3, and a martingale sizing strategy.

## Tech stack

| Layer    | Tech |
|----------|------|
| Engine   | Python, pandas, NumPy |
| API      | FastAPI, Uvicorn, Pydantic |
| Frontend | React 19, Vite, Chart.js, lightweight-charts, Axios |
| Data     | python-binance, yfinance |

## Project structure

```
backtesting/       Core library
  engine.py        BacktestEngine: event loop, execution, equity curve
  metrics.py       PerformanceMetrics: stats, round trips, heatmap, Monte Carlo
  data.py          CSV loader (adds SMA/RSI columns) + Binance downloader
  utils.py         Default commission & slippage models
api/main.py        FastAPI server
ui/                React dashboard
examples/          Example strategies + CLI runner
scripts/           Standalone data download scripts (Binance, Yahoo Finance)
*.csv              Sample / downloaded market data
```

## Getting started

### 1. Backend

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd ui
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173). The UI calls the API at
`http://localhost:8000`.

### 3. In the dashboard

1. **Data Downloader**: enter a Binance symbol (e.g. `BTCUSDT`), an interval and a start
   date. The CSV is saved to the project root.
2. **Backtest Strategy**: pick a CSV and a strategy, run it, then look through the
   metrics, charts, heatmap, Monte Carlo and trade log.

## API

| Method | Endpoint          | Description |
|--------|-------------------|-------------|
| GET    | `/api/files`      | List CSV data files in the project root |
| GET    | `/api/strategies` | List strategies exposed to the UI |
| POST   | `/api/download`   | `{symbol, interval, start_date}` → download Binance data |
| POST   | `/api/backtest`   | `{strategy_name, data_file}` → equity curve, OHLCV (last 5,000 bars), metrics |

## Command-line usage

Run a backtest without the UI:

```bash
./examples/run_example.sh sample_data.csv
```

Download data with the scripts:

```bash
python scripts/download_data.py        # Yahoo Finance (see --help)
python scripts/download_btc_1min.py    # BTC/USDT 1-minute from Binance
```

CSV format: `datetime, open, high, low, close, volume`.

## Writing your own strategy

```python
class MyStrategy:
    def __init__(self):
        ...  # state

    def next(self, bar):
        # bar: pandas Series with open, high, low, close, volume (+ sma_short, sma_long, rsi)
        # Return >0 to buy that many units, <0 to sell, 0 to do nothing.
        return 0
```

```python
from backtesting import BacktestEngine, load_data

engine = BacktestEngine(MyStrategy, load_data("my_data.csv"), init_cash=100_000)
engine.run()
engine.report()
```

The engine also sets `self.current_timestamp` and `self.current_bar` on the strategy
before each call. To show a strategy in the dashboard, import it in `api/main.py` and
add it to `/api/strategies` and `/api/backtest`.

You can pass your own `commission_func(size, price)` and `slippage_func(size, price)`
to `BacktestEngine` to change the cost model.

## Limitations

- Orders fill at the bar's close. There are no limit or stop orders, and stops inside
  strategies are checked bar by bar.
- Single asset per backtest.
- Sharpe is annualized with √252 no matter the bar interval.
- Monte Carlo shuffles fixed-dollar trade PnLs, so it doesn't model compounding.
