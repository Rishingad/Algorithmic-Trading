# backtesting/metrics.py
import pandas as pd
import numpy as np

class PerformanceMetrics:
    """
    Performance metrics including round-trip matching, heapmaps, and monte carlo.
    """

    def __init__(self, equity_series: pd.Series, trades: pd.DataFrame, init_cash: float):
        self.equity = equity_series
        self.trades = trades
        self.init_cash = init_cash
        
        # Basic Stats
        self.total_return = (self.equity.iloc[-1] / self.init_cash) - 1
        self.annualized_return = self._annualized_return()
        self.max_drawdown = self._max_drawdown()
        self.sharpe = self._sharpe_ratio()
        
        # Advanced Stats
        self.round_trips = self._calculate_round_trips()
        self.win_rate, self.avg_duration = self._calculate_trade_summary()
        self.monthly_heatmap = self._calculate_monthly_heatmap()

    def _annualized_return(self):
        days = (self.equity.index[-1] - self.equity.index[0]).days
        if days == 0:
            return 0.0
        return (1 + self.total_return) ** (365 / days) - 1

    def _max_drawdown(self):
        roll_max = self.equity.cummax()
        drawdown = (self.equity - roll_max) / roll_max
        return drawdown.min()

    def _sharpe_ratio(self, risk_free=0.0):
        daily_ret = self.equity.pct_change().dropna()
        excess_ret = daily_ret - risk_free / 252
        if excess_ret.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_ret.mean() / excess_ret.std()

    def _calculate_round_trips(self):
        """Reconstruct round-trip trades."""
        if self.trades.empty:
            return []

        round_trips = []
        open_trades = [] # list of dicts: {size, price, time}

        for _, t in self.trades.iterrows():
            size = t['size']
            price = t['price']
            time = t['timestamp']
            
            if size == 0: continue

            # If no open positions, this is an entry
            if not open_trades:
                open_trades.append({'size': size, 'price': price, 'time': time})
                continue
            
            remaining_size = size
            
            # Check for closure (opposite signs)
            if (open_trades[0]['size'] > 0 and size < 0) or \
               (open_trades[0]['size'] < 0 and size > 0):
                
                while remaining_size != 0 and open_trades:
                    match = open_trades[0]
                    match_qty = match['size']
                    
                    if abs(remaining_size) >= abs(match_qty):
                        # Full close of open trade
                        qty_closed = match_qty
                        open_trades.pop(0)
                        remaining_size -= (-qty_closed)
                        
                        pnl = (price - match['price']) * qty_closed if qty_closed > 0 else (match['price'] - price) * abs(qty_closed)
                        duration = time - match['time']
                        
                        # Calculate ROI
                        invested = abs(qty_closed * match['price'])
                        roi = (pnl / invested * 100) if invested > 0 else 0
                        
                        round_trips.append({
                            'entry_time': match['time'],
                            'exit_time': time,
                            'entry_price': match['price'],
                            'exit_price': price,
                            'size': qty_closed,
                            'pnl': pnl,
                            'roi': roi,
                            'duration': duration
                        })
                    else:
                        # Partial close
                        qty_closed = -remaining_size
                        match['size'] += remaining_size
                        remaining_size = 0
                        
                        pnl = (price - match['price']) * qty_closed if qty_closed > 0 else (match['price'] - price) * abs(qty_closed)
                        duration = time - match['time']
                        
                        invested = abs(qty_closed * match['price'])
                        roi = (pnl / invested * 100) if invested > 0 else 0
                        
                        round_trips.append({
                            'entry_time': match['time'],
                            'exit_time': time,
                            'entry_price': match['price'],
                            'exit_price': price,
                            'size': qty_closed,
                            'pnl': pnl,
                            'roi': roi,
                            'duration': duration
                        })
                
                if remaining_size != 0:
                    open_trades.append({'size': remaining_size, 'price': price, 'time': time})
            else:
                open_trades.append({'size': size, 'price': price, 'time': time})
                
        return round_trips

    def _calculate_trade_summary(self):
        if not self.round_trips:
            return 0.0, pd.Timedelta(0)
            
        df_rt = pd.DataFrame(self.round_trips)
        win_rate = (len(df_rt[df_rt['pnl'] > 0]) / len(df_rt)) * 100
        avg_duration = df_rt['duration'].mean()
        return win_rate, avg_duration

    def _calculate_monthly_heatmap(self):
        """Returns {Year: {Month: Return%}}"""
        # Resample equity to monthly
        monthly_equity = self.equity.resample('ME').last()
        # Handle case where start of month is missing by prepending init_cash if needed
        # Or simpler: calculate monthly returns from percentage change
        
        monthly_returns = monthly_equity.pct_change().dropna()
        
        # Structure: {2023: {1: 5.2, 2: -1.1, ...}}
        heatmap = {}
        for timestamp, ret in monthly_returns.items():
            year = timestamp.year
            month = timestamp.month
            if year not in heatmap:
                heatmap[year] = {}
            heatmap[year][month] = ret * 100
            
        return heatmap

    def run_monte_carlo(self, n=50):
        """
        Shuffle trade sequence 50 times to generate confidence intervals.
        Returns: { 'scenarios': [[final_equity_1, ...]], 'quantiles': ... }
        """
        if not self.round_trips:
            return {}
            
        pnls = [t['pnl'] for t in self.round_trips]
        
        scenarios = []
        for _ in range(n):
            shuffled_pnls = np.random.permutation(pnls)
            # Reconstruct equity curve from shuffled pnls + init_cash
            # This is an approximation since it ignores compounding logic if strategy used % sizing
            # But acceptable for "what if trade order was different" 
            path = np.cumsum(shuffled_pnls) + self.init_cash
            scenarios.append(path.tolist())
            
        return {
            'scenarios': scenarios, # Be careful sending huge data. 
            # maybe just send final values
            'final_values': [s[-1] for s in scenarios]
        }

    def print_summary(self):
        print("\n=== Back‑test Summary ===")
        print(f"Initial cash          : ${self.init_cash:,.2f}")
        print(f"Final equity          : ${self.equity.iloc[-1]:,.2f}")
        print(f"Total return          : {self.total_return*100:6.2f}%")
        print(f"Annualized return    : {self.annualized_return*100:6.2f}%")
        print(f"Max drawdown          : {self.max_drawdown*100:6.2f}%")
        print(f"Sharpe ratio          : {self.sharpe:6.3f}")
        print(f"Win Rate              : {self.win_rate:6.2f}%")
        print(f"Avg Trade Duration    : {self.avg_duration}")
        print("==========================\n")

    def to_dict(self):
        # Convert round trips to JSON serializable format
        rt_serializable = []
        for t in self.round_trips:
            rt_serializable.append({
                'entry_time': str(t['entry_time']),
                'exit_time': str(t['exit_time']),
                'entry_price': t['entry_price'],
                'exit_price': t['exit_price'],
                'size': t['size'],
                'pnl': t['pnl'],
                'roi': t['roi'],
                'duration': str(t['duration'])
            })
            
        def clean(v):
            if isinstance(v, (float, np.float64, np.float32)):
                if np.isnan(v) or np.isinf(v):
                    return None
            return v
            
        return {
            "initial_cash": self.init_cash,
            "final_equity": clean(self.equity.iloc[-1]),
            "total_return": clean(self.total_return),
            "annualized_return": clean(self.annualized_return),
            "max_drawdown": clean(self.max_drawdown),
            "sharpe_ratio": clean(self.sharpe),
            "num_trades": len(self.round_trips),
            "win_rate": clean(self.win_rate),
            "avg_trade_duration": str(self.avg_duration),
            
            # Advanced Data
            "round_trips": rt_serializable,
            "monthly_heatmap": {y: {m: clean(v) for m, v in months.items()} for y, months in self.monthly_heatmap.items()},
            "monte_carlo": self.run_monte_carlo()
        }
