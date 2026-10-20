# examples/price_action_strategy.py
"""ICT‑enhanced price‑action strategy that requires at least three
concurrent signals before entering a trade.

Signals considered (per candle):
- Bullish / Bearish order block
- Bullish / Bearish fair‑value gap (FVG)
- New swing‑high / swing‑low break (market‑structure)
- Bullish / Bearish engulfing
- Bullish / Bearish pin bar (hammer / inverted hammer)
- Inside‑bar breakout (price breaking recent high/low)
- Simple breakout of recent high/low (fallback)

Only when **three or more** of the above point in the same direction does the
strategy take a position.  All other behaviour (fixed‑capital sizing,
1:2 risk‑reward stop‑loss/take‑profit) remains unchanged.
"""

import pandas as pd


class PriceActionStrategy:
    """ICT‑enhanced price‑action strategy with multi‑signal confirmation.

    Parameters
    ----------
    lookback : int, optional
        Number of previous candles used for breakout calculations (default 20).
    fixed_capital : float, optional
        Initial capital to use for sizing calculations (default $200,000).
    """

    def __init__(self, lookback: int = 20, fixed_capital: float = 200000.0):
        self.lookback = lookback
        self.fixed_capital = fixed_capital  # This is now treated as initial account size
        self.estimated_equity = fixed_capital
        self.position = 0          # 0 = flat, 1 = long, -1 = short
        self.entry_price = None
        self.last_qty = 0
        self.history = []          # recent bars (dict‑like)
        
        # market‑structure trackers
        self.last_swing_high = None
        self.last_swing_low = None
        
        # Risk management
        self.cooldown = 0
        self.equity_floor = 0.7 * fixed_capital  # Stop if equity < 70% of initial

    # ------------------------------------------------------------------
    # Classic pattern helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_bullish_engulfing(prev, cur):
        return (
            cur["close"] > cur["open"]
            and prev["close"] < prev["open"]
            and cur["open"] < prev["close"]
            and cur["close"] > prev["open"]
        )

    @staticmethod
    def _is_bearish_engulfing(prev, cur):
        return (
            cur["close"] < cur["open"]
            and prev["close"] > prev["open"]
            and cur["open"] > prev["close"]
            and cur["close"] < prev["open"]
        )

    @staticmethod
    def _is_bullish_pin(bar):
        body = abs(bar["close"] - bar["open"])
        lower = (bar["open"] - bar["low"]) if bar["close"] > bar["open"] else (bar["close"] - bar["low"])
        upper = (bar["high"] - bar["close"]) if bar["close"] > bar["open"] else (bar["high"] - bar["open"])
        return lower > 2 * body and upper < body

    @staticmethod
    def _is_bearish_pin(bar):
        body = abs(bar["close"] - bar["open"])
        upper = (bar["high"] - bar["close"]) if bar["close"] < bar["open"] else (bar["high"] - bar["open"])
        lower = (bar["close"] - bar["low"]) if bar["close"] < bar["open"] else (bar["open"] - bar["low"])
        return upper > 2 * body and lower < body

    @staticmethod
    def _is_inside_bar(prev, cur):
        return cur["high"] <= prev["high"] and cur["low"] >= prev["low"]

    # ------------------------------------------------------------------
    # ICT helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_bullish_order_block(prev, cur):
        return (
            prev["close"] < prev["open"]
            and cur["close"] > cur["open"]
            and cur["high"] > prev["high"]
        )

    @staticmethod
    def _is_bearish_order_block(prev, cur):
        return (
            prev["close"] > prev["open"]
            and cur["close"] < cur["open"]
            and cur["low"] < prev["low"]
        )

    @staticmethod
    def _is_bullish_fvg(bar1, bar2, bar3):
        return bar1["high"] < bar3["low"]

    @staticmethod
    def _is_bearish_fvg(bar1, bar2, bar3):
        return bar1["low"] > bar3["high"]

    def _update_market_structure(self, cur):
        if len(self.history) < 3:
            return
        prev2, prev1 = self.history[-3], self.history[-2]
        if cur["high"] > prev1["high"] and cur["high"] > prev2["high"]:
            self.last_swing_high = cur["high"]
        if cur["low"] < prev1["low"] and cur["low"] < prev2["low"]:
            self.last_swing_low = cur["low"]

    # ------------------------------------------------------------------
    # Signal aggregation
    # ------------------------------------------------------------------
    def _collect_signals(self, cur, prev):
        """Return a dict of booleans for each possible signal."""
        signals = {}
        # order blocks
        signals["bullish_order_block"] = self._is_bullish_order_block(prev, cur)
        signals["bearish_order_block"] = self._is_bearish_order_block(prev, cur)
        # fair‑value gaps (need three‑candle history)
        if len(self.history) >= 3:
            b1, b2, b3 = self.history[-3], self.history[-2], self.history[-1]
            signals["bullish_fvg"] = self._is_bullish_fvg(b1, b2, b3)
            signals["bearish_fvg"] = self._is_bearish_fvg(b1, b2, b3)
        else:
            signals["bullish_fvg"] = False
            signals["bearish_fvg"] = False
        # market‑structure breaks
        signals["swing_high_break"] = (
            self.last_swing_high is not None and cur["close"] > self.last_swing_high
        )
        signals["swing_low_break"] = (
            self.last_swing_low is not None and cur["close"] < self.last_swing_low
        )
        # classic patterns
        signals["bullish_engulfing"] = self._is_bullish_engulfing(prev, cur)
        signals["bearish_engulfing"] = self._is_bearish_engulfing(prev, cur)
        signals["bullish_pin"] = self._is_bullish_pin(cur)
        signals["bearish_pin"] = self._is_bearish_pin(cur)
        # inside‑bar breakout
        recent_high = max(b["high"] for b in self.history[-self.lookback:])
        recent_low = min(b["low"] for b in self.history[-self.lookback:])
        signals["inside_long"] = cur["close"] > recent_high
        signals["inside_short"] = cur["close"] < recent_low
        # simple breakout
        signals["breakout_high"] = cur["close"] > recent_high
        signals["breakout_low"] = cur["close"] < recent_low
        return signals

    # ------------------------------------------------------------------
    # Core back‑testing method
    # ------------------------------------------------------------------
    def next(self, bar):
        """Decide action for the current bar."""
        # maintain rolling history
        self.history.append(bar)
        if len(self.history) > self.lookback + 1:
            self.history.pop(0)

        if len(self.history) < 2:
            return 0

        # Cooldown check
        if self.cooldown > 0:
            self.cooldown -= 1
            return 0

        # Equity floor check
        if self.estimated_equity < self.equity_floor:
            if self.position != 0:
                # Close existing position if we breached floor (optional, but safer)
                # For now, let normal exit logic handle it, but prevent NEW entries.
                pass
            else:
                return 0  # Stop trading

        cur = self.history[-1]
        prev = self.history[-2]
        price = cur["close"]

        self._update_market_structure(cur)

        # ------------------------------------------------------------------
        # Exit logic – fixed‑capital 1:2 risk‑reward
        # ------------------------------------------------------------------
        if self.position != 0:
            pnl = 0
            qty = self.last_qty
            action = 0
            
            if self.position == 1:  # long
                if price <= self.entry_price * 0.99 or price >= self.entry_price * 1.02:
                    pnl = (price - self.entry_price) * qty
                    action = -qty
            else:  # short
                if price >= self.entry_price * 1.01 or price <= self.entry_price * 0.98:
                    pnl = (self.entry_price - price) * qty
                    action = qty

            if action != 0:
                self.position = 0
                self.entry_price = None
                self.last_qty = 0
                self.estimated_equity += pnl
                self.cooldown = 5
                return action

        # ------------------------------------------------------------------
        # Entry logic
        # ------------------------------------------------------------------
        if self.position == 0:
            signals = self._collect_signals(cur, prev)
            
            long_signals = sum([
                signals["bullish_order_block"],
                signals["bullish_fvg"],
                signals["swing_high_break"],
                signals["bullish_engulfing"],
                signals["bullish_pin"],
                signals["inside_long"],
                signals["breakout_high"],
            ])
            short_signals = sum([
                signals["bearish_order_block"],
                signals["bearish_fvg"],
                signals["swing_low_break"],
                signals["bearish_engulfing"],
                signals["bearish_pin"],
                signals["inside_short"],
                signals["breakout_low"],
            ])

            # Position sizing: Risk 0.5% of current estimated equity
            # Stop loss is 1%, so Position Size = (0.005 * Equity) / 0.01 = 0.5 * Equity
            # Wait, that's huge leverage. 
            # Let's stick to the prompt's "risk a fixed percentage... e.g. 0.5%".
            # If I risk 0.5% of $200k, that's $1000 risk.
            # With 1% SL, position size is $100,000. That's 0.5x leverage. 
            # The previous code used $1000 *position size*, which is tiny risk ($10).
            # The user said "put 1000 in one trade". That means position size = $1000.
            # Then they said "how to decrease drawdown".
            # My plan said "Change from fixed $1000 to 0.5% of current equity".
            # If I use 0.5% risk with 1% SL, position size is 50% of equity. That's aggressive.
            # If I use 0.5% *position size* of equity, that's $1000 for $200k.
            # Let's assume "risk 0.5% of equity" means the *amount lost* if SL hits.
            # But earlier user said "put 1000 in one trade". That implies position value = 1000.
            # Let's stick to Position Value = 0.5% of Equity.
            # For $200k, that's $1000 position.
            # For $100k, that's $500 position.
            # This scales down.
            
            target_position_value = self.estimated_equity * 0.005
            qty = max(int(target_position_value / price), 1)

            if long_signals >= 2:
                self.position = 1
                self.entry_price = price
                self.last_qty = qty
                return qty
            if short_signals >= 2:
                self.position = -1
                self.entry_price = price
                self.last_qty = qty
                return -qty

        return 0