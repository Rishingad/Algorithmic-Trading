# backtesting/utils.py

def default_commission(size: int, price: float) -> float:
    """
    Simple flat‑fee commission: $0.01 per share/contract.
    """
    return abs(size) * 0.01


def default_slippage(size: int, price: float) -> float:
    """
    Simple slippage model: 0.01% of price per 1000 units.
    Positive size = buy (price goes up), negative = sell (price goes down).
    """
    slippage_pct = 0.0001 * (abs(size) / 1000)
    return slippage_pct if size > 0 else -slippage_pct
