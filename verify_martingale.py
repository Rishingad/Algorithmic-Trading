
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath("/Users/rihansh/Desktop/AlgoBacktesting"))

from examples.gambling_strat import PriceActionStrategy

def test_martingale_logic():
    print("Testing Martingale Logic...")
    strat = PriceActionStrategy(fixed_capital=100000.0)
    
    # Initial Check
    base_value = 100000.0 * 0.005 # 500
    assert strat.current_position_value == base_value, f"Expected initial value {base_value}, got {strat.current_position_value}"
    print(f"[PASS] Initial value: {strat.current_position_value}")

    # 1. Simulate Entry
    # We need to bypass _collect_signals logic or force it. 
    # Easier to manually set state since we are testing the sizing logic in 'next'
    
    # Mock some history to avoid index errors
    strat.history = [{"open": 100, "high": 110, "low": 90, "close": 105} for _ in range(50)]
    
    # Manually assume we entered a trade
    strat.position = 1
    strat.entry_price = 100
    strat.last_qty = 5 # 5 * 100 = 500 value
    
    # 2. Simulate LOSS
    # Call next() with a price that triggers stop loss (exit logic)
    # Long @ 100. SL ~99 (0.99). Let's say price hits 98.
    loss_bar = {"open": 98, "high": 98, "low": 98, "close": 98}
    strat.next(loss_bar)
    
    # Now position should be 0, and current_position_value should be DOUBLED
    assert strat.position == 0, "Position should be closed"
    expected_value = base_value * 2
    assert strat.current_position_value == expected_value, f"Expected doubled value {expected_value}, got {strat.current_position_value}"
    print(f"[PASS] Value after LOSS: {strat.current_position_value}")
    
    # 3. Simulate another LOSS
    # Manually reset position to simulate next trade entry (skipping entry logic check for simplicity)
    strat.position = 1
    strat.cooldown = 0
    strat.entry_price = 100
    strat.last_qty = int(expected_value / 100) # 1000 / 100 = 10
    
    strat.next(loss_bar) # Loss again
    
    expected_value_2 = expected_value * 2 # 2000
    assert strat.current_position_value == expected_value_2, f"Expected quadrupled value {expected_value_2}, got {strat.current_position_value}"
    print(f"[PASS] Value after 2nd LOSS: {strat.current_position_value}")

    # 4. Simulate WIN
    strat.position = 1
    strat.cooldown = 0
    strat.entry_price = 100
    strat.last_qty = int(expected_value_2 / 100) # 2000 / 100 = 20
    
    # Win condition: price > 1.02 * entry. say 103.
    win_bar = {"open": 103, "high": 103, "low": 103, "close": 103}
    strat.next(win_bar)
    
    assert strat.current_position_value == base_value, f"Expected reset value {base_value}, got {strat.current_position_value}"
    print(f"[PASS] Value after WIN: {strat.current_position_value} (Reset)")

if __name__ == "__main__":
    try:
        test_martingale_logic()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        exit(1)
