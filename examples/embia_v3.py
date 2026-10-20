# examples/embia_v3.py
"""A simplified version of the EMBIA_V3 strategy adapted to the
custom BacktestEngine used in this project.

The original Jesse‑style strategy relied on many Jesse‑specific
indicators.  For compatibility we implement the core idea using plain
pandas calculations:

* Short and long simple moving averages (SMA) – 100 and 250 periods.
* Relative Strength Index (RSI) – 14‑period.
* A very simple volume‑weighted moving average (VWMA) approximation
  using price * volume.
* ADX and ATR are omitted for simplicity; the entry conditions are
  based on the SMA/RSI logic.

The class provides a ``next(self, bar)`` method that returns a signed
quantity (positive = buy, negative = sell) compatible with
``BacktestEngine``.
"""

import pandas as pd


class EMBIA_V3:
    """Adapted EMBIA_V3 strategy.

    * BUY when short SMA > long SMA and RSI < 30.
    * SELL (close) when short SMA < long SMA and RSI > 70.
    * Holds at most one long position (no shorting).
    """

    def __init__(self, short_window=100, long_window=250, rsi_window=14):
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_window = rsi_window
        self.position = 0  # 0 = flat, 1 = long
        self.history = []   # store close prices for indicator calculations

    def _calc_rsi(self, closes):
        """Calculate RSI for the most recent ``rsi_window`` closes.
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

        # Need enough data for both SMAs and RSI
        if len(self.history) < max(self.long_window, self.rsi_window + 1):
            return 0

        short_ma = sum(self.history[-self.short_window:]) / self.short_window
        long_ma = sum(self.history[-self.long_window:]) / self.long_window
        rsi = self._calc_rsi(self.history)

        # BUY signal
        if short_ma > long_ma and rsi < 30 and self.position == 0:
            self.position = 1
            return 100  # buy 100 units
        # SELL signal (close position)
        if short_ma < long_ma and rsi > 70 and self.position == 1:
            self.position = 0
            return -100  # close position
        return 0
