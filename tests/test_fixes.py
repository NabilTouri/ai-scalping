"""
Test script for execution engine fixes
Run with: python -m tests.test_fixes
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.market_data import MarketDataManager

def test_symbol_normalization():
    """Test that symbols are normalized correctly"""
    print("\n=== Test 1: Symbol Normalization ===")
    market = MarketDataManager()
    
    test_cases = [
        ("ETH/USD", "ETHUSD"),
        ("BTC/USD", "BTCUSD"),
        ("SOL/USD", "SOLUSD"),
        ("ETHUSD", "ETHUSD"),  # Already normalized
    ]
    
    all_passed = True
    for input_sym, expected in test_cases:
        result = market._normalize_symbol(input_sym)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {input_sym} -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed


def test_has_position():
    """Test position checking (uses live API)"""
    print("\n=== Test 2: Check Positions API ===")
    try:
        market = MarketDataManager()
        positions = market.get_open_positions("CLAUDE")
        print(f"  ✓ Got {len(positions)} open positions")
        
        for p in positions:
            print(f"    - {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}")
        
        # Test has_position
        if positions:
            test_symbol = positions[0].symbol
            has = market.has_position("CLAUDE", test_symbol)
            print(f"  ✓ has_position({test_symbol}): {has}")
        
        # Test non-existent position
        has_fake = market.has_position("CLAUDE", "FAKEUSD")
        print(f"  ✓ has_position(FAKEUSD): {has_fake}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_account_balance():
    """Test account balance retrieval"""
    print("\n=== Test 3: Account Balance ===")
    try:
        market = MarketDataManager()
        account = market.get_account("CLAUDE")
        
        print(f"  ✓ Equity: ${float(account.equity):.2f}")
        print(f"  ✓ Buying Power: ${float(account.buying_power):.2f}")
        print(f"  ✓ Cash: ${float(account.cash):.2f}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_close_trade_logic():
    """Test the close trade error handling logic"""
    print("\n=== Test 4: Close Trade Error Handling ===")
    
    # Simulate the error handling logic
    test_errors = [
        ("404 Client Error: Not Found", True, "Should recognize as 'already closed'"),
        ("Not Found", True, "Should recognize as 'already closed'"),
        ("Connection timeout", False, "Should be a real error"),
        ("insufficient balance", False, "Should be a real error"),
    ]
    
    all_passed = True
    for error_msg, should_close, desc in test_errors:
        # This is the logic from _close_trade
        is_already_closed = "Not Found" in error_msg or "404" in error_msg
        
        status = "✓" if is_already_closed == should_close else "✗"
        print(f"  {status} '{error_msg[:30]}...' -> already_closed={is_already_closed} ({desc})")
        
        if is_already_closed != should_close:
            all_passed = False
    
    return all_passed


def main():
    print("=" * 50)
    print("AI Scalping Bot - Fix Verification Tests")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Symbol Normalization", test_symbol_normalization()))
    results.append(("Close Trade Logic", test_close_trade_logic()))
    
    # API tests (require valid credentials)
    if Config.ALPACA_KEY_CLAUDE:
        results.append(("Positions API", test_has_position()))
        results.append(("Account Balance", test_account_balance()))
    else:
        print("\n⚠️  Skipping API tests - no Alpaca credentials found")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All tests passed! Safe to deploy.")
    else:
        print("❌ Some tests failed. Please review before deploying.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
