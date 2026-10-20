# examples/run_example.sh
#!/usr/bin/env bash
# Usage: ./run_example.sh path/to/historical.csv

CSV_PATH="${1:-sample_data.csv}"

python - <<PY
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from backtesting import BacktestEngine, load_data
from examples.price_action_strategy import PriceActionStrategy

# Load data – ensure the CSV exists
try:
    data = load_data("$CSV_PATH")  # load full dataset
except Exception as e:
    print(f"Error loading data: {e}")
    sys.exit(1)

engine = BacktestEngine(PriceActionStrategy, data, init_cash=200000)
engine.run()
engine.report()
PY
