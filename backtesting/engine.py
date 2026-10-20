# backtesting/engine.py
import pandas as pd
from .metrics import PerformanceMetrics
from .utils import default_commission, default_slippage

class BacktestEngine:

    def __init__(
        self,
        strategy_cls,
        data: pd.DataFrame,
        init_cash: float = 100000,
        commission_func=default_commission,
        slippage_func=default_slippage,
    ):
        self.strategy = strategy_cls()
        self.data = data.sort_index()
        self.cash = init_cash
        self.starting_cash = init_cash  
        self.position = 0          
        self.commission = commission_func
        self.slippage = slippage_func
        self.trades = []          
        self.equity_curve = []   

    def _execute_trade(self, timestamp, price, size):
        """Buy (+size) or sell (-size) at given price."""
        # Apply slippage & commission
        price = price * (1 + self.slippage(size, price))
        commission = self.commission(size, price)

        cost = price * size + commission
        self.cash -= cost
        self.position += size

        self.trades.append(
            {
                "timestamp": timestamp,
                "price": price,
                "size": size,
                "commission": commission,
                "cash_after": self.cash,
                "position_after": self.position,
            }
        )

    def run(self):
        """Iterate over the data and let the strategy act."""
        for ts, row in self.data.iterrows():
            self.strategy.current_timestamp = ts
            self.strategy.current_bar = row

            action = self.strategy.next(row)

            if action:
                self._execute_trade(ts, row["close"], action)

            equity = self.cash + self.position * row["close"]
            self.equity_curve.append((ts, equity))

        self.metrics = PerformanceMetrics(
            equity_series=pd.Series(
                [e for _, e in self.equity_curve],
                index=[t for t, _ in self.equity_curve],
            ),
            trades=pd.DataFrame(self.trades),
            init_cash=self.starting_cash,
        )
        return self.metrics

    def report(self):
        """Print a concise performance summary."""
        if not hasattr(self, "metrics"):
            raise RuntimeError("Run the engine first (engine.run())")
        self.metrics.print_summary()
