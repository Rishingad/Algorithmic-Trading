# 📊 AlgoBacktesting – Simple Python Back‑testing Framework

## What it is
A tiny, dependency‑light back‑testing engine that lets you plug‑in any
algorithm written as a Python class with a `next(self, bar)` method.

## Quick start
```bash
# 1️⃣ Install deps
pip install -r requirements.txt

# 2️⃣ Prepare historical data (CSV with columns: datetime, open, high, low, close, volume)
#    Example: `sample_data.csv`

# 3️⃣ Run the demo (moving‑average crossover)
./examples/run_example.sh sample_data.csv
```

## Writing your own strategy
Create a class with a `next(self, bar)` method:
```python
class MyStrategy:
    def __init__(self):
        # initialise any state you need
        ...

    def next(self, bar):
        # `bar` is a pandas Series with keys: open, high, low, close, volume
        # Return:
        #   >0  → buy that many units
        #   <0  → sell that many units
        #   0   → do nothing
        ...
```
Then run:
```python
from backtesting import BacktestEngine, load_data
engine = BacktestEngine(MyStrategy, load_data("my_data.csv"))
engine.run()
engine.report()
```

## Extending
- **Custom commission / slippage** – pass your own functions to `BacktestEngine`.
- **Multiple symbols** – feed a multi‑index DataFrame (datetime, symbol) and adapt the strategy.
- **Export results** – `engine.trades` and `engine.equity_curve` are pandas objects you can save to CSV/HTML.

Run Frontend
```bash
# 1️⃣ Install deps
npm install

# 2️⃣ Run dev
npm run dev
```

Run Backend
```bash
# 1️⃣ Install deps
pip install -r requirements.txt

# 2️⃣ Run dev
uvicorn api.main:app --reload --port 8000
```

---
Enjoy back‑testing! 🎉
