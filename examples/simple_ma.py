# examples/simple_ma.py
"""Improved strategy for 5‑minute BTC data.

The strategy expects the DataFrame passed to the back‑testing engine to contain the standard OHLCV columns.
It computes a short and a long simple moving average (SMA) and a 14‑period Relative Strength Index (RSI)
on‑the fly for each bar. The logic is:
  * BUY 100 units when short SMA > long SMA and RSI < 30 (oversold).
  * SELL (close) 100 units when short SMA < long SMA and RSI > 70 (overbought).
  * Otherwise HOLD.

This implementation is self‑contained and does not require pre‑computed indicator columns, keeping the workflow simple.
"""

import pandas as pd


class ImprovedStrategy:
    """Strategy that computes SMA and RSI on‑the‑fly.

    Parameters (default values are tuned for 5‑minute data):
        short_window: 100 periods (~8 hours)
        long_window: 250 periods (~21 hours)
        rsi_window: 14 periods
    """

    def __init__(self, short_window=100, long_window=250, rsi_window=14):
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_window = rsi_window
        self.position = 0  # 0 = flat, 1 = long
        self.history = []   # store close prices for indicator calculations

    def _calc_rsi(self, closes):
        """Calculate RSI for the most recent `rsi_window` closes.
        Returns a float between 0 and 100.
        """
        if len(closes) < self.rsi_window + 1:
            return 50  # neutral when not enough data
        series = pd.Series(closes)
        delta = series.diff().dropna()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(alpha=1 / self.rsi_window, adjust=False).mean()
        roll_down = down.ewm(alpha=1 / self.rsi_window, adjust=False).mean()
        rs = roll_up / roll_down
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def next(self, bar):
        close = bar["close"]
        self.history.append(close)

        # Ensure we have enough data for both SMAs and RSI
        if len(self.history) < max(self.long_window, self.rsi_window + 1):
            return 0

        short_ma = sum(self.history[-self.short_window:]) / self.short_window
        long_ma = sum(self.history[-self.long_window:]) / self.long_window
        rsi = self._calc_rsi(self.history)

        # BUY signal
        if short_ma > long_ma and rsi < 30 and self.position == 0:
            self.position = 1
            return 100  # buy 100 units
        # SELL signal
        if short_ma < long_ma and rsi > 70 and self.position == 1:
            self.position = 0
            return -100  # close position
        return 0
