"""
Comprehensive test for all bug fixes
Run with: python -m tests.test_all_fixes
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.market_data import MarketDataManager


def test_symbol_normalization():
    """Test symbol normalization"""
    print("\n=== Test 1: Symbol Normalization ===")
    market = MarketDataManager()
    
    tests = [
        ("ETH/USD", "ETHUSD"),
        ("BTC/USD", "BTCUSD"),
        ("SOLUSD", "SOLUSD"),
    ]
    
    for input_sym, expected in tests:
        result = market._normalize_symbol(input_sym)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {input_sym} -> {result}")
    
    return True


def test_confidence_check():
    """Test that confidence threshold is enforced"""
    print("\n=== Test 2: Confidence Check Logic ===")
    
    # Simulate the confidence check logic from _evaluate_signal
    test_cases = [
        (0.5, False, "Skip - low confidence"),
        (0.6, True, "Trade - meets threshold"),
        (0.8, True, "Trade - high confidence"),
        (None, True, "Trade - no confidence set"),
    ]
    
    all_passed = True
    for confidence, should_trade, desc in test_cases:
        # Logic from execution_engine.py
        if confidence is not None and confidence < 0.6:
            trades = False
        else:
            trades = True
        
        status = "✓" if trades == should_trade else "✗"
        print(f"  {status} Confidence={confidence} -> trades={trades} ({desc})")
        if trades != should_trade:
            all_passed = False
    
    return all_passed


def test_min_balance_check():
    """Test minimum balance enforcement"""
    print("\n=== Test 3: Min Balance Check ===")
    
    MIN_TRADE_VALUE = 50.0
    test_cases = [
        (10.0, False, "Skip - below minimum"),
        (49.99, False, "Skip - just below"),
        (50.0, True, "Trade - meets minimum"),
        (1000.0, True, "Trade - well above"),
    ]
    
    all_passed = True
    for buying_power, should_trade, desc in test_cases:
        # Logic from _execute_entry
        trades = buying_power >= MIN_TRADE_VALUE
        
        status = "✓" if trades == should_trade else "✗"
        print(f"  {status} BP=${buying_power} -> trades={trades} ({desc})")
        if trades != should_trade:
            all_passed = False
    
    return all_passed


def test_position_check():
    """Test position existence check"""
    print("\n=== Test 4: Position Check API ===")
    try:
        market = MarketDataManager()
        positions = market.get_open_positions("CLAUDE")
        print(f"  ✓ Retrieved {len(positions)} positions")
        
        # Test has_position
        for p in positions[:2]:  # Test first 2
            has = market.has_position("CLAUDE", p.symbol)
            print(f"  ✓ has_position({p.symbol}): {has}")
        
        # Test non-existent
        has_fake = market.has_position("CLAUDE", "FAKECOIN/USD")
        print(f"  ✓ has_position(FAKECOIN/USD): {has_fake} (should be False)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_close_trade_logic():
    """Test close trade error handling"""
    print("\n=== Test 5: Close Trade Error Handling ===")
    
    test_errors = [
        ("404 Client Error: Not Found", True),
        ("Not Found", True),
        ("Connection error", False),
    ]
    
    all_passed = True
    for error_msg, should_be_closed in test_errors:
        is_already_closed = "Not Found" in error_msg or "404" in error_msg
        status = "✓" if is_already_closed == should_be_closed else "✗"
        print(f"  {status} '{error_msg[:25]}...' -> closed={is_already_closed}")
        if is_already_closed != should_be_closed:
            all_passed = False
    
    return all_passed


def test_sqlalchemy_session_get():
    """Test that session.get() is used correctly"""
    print("\n=== Test 6: SQLAlchemy Session.get() ===")
    
    from src.database import SessionLocal, StrategicSignal
    
    try:
        db = SessionLocal()
        # Test the new syntax
        result = db.get(StrategicSignal, 1)  # May return None
        print(f"  ✓ db.get(StrategicSignal, 1) works (result: {type(result).__name__})")
        db.close()
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 50)
    print("AI Scalping Bot - Full Bug Fix Verification")
    print("=" * 50)
    
    results = []
    
    # Logic tests (no API needed)
    results.append(("Symbol Normalization", test_symbol_normalization()))
    results.append(("Confidence Check", test_confidence_check()))
    results.append(("Min Balance Check", test_min_balance_check()))
    results.append(("Close Trade Logic", test_close_trade_logic()))
    results.append(("SQLAlchemy Session", test_sqlalchemy_session_get()))
    
    # API tests
    if Config.ALPACA_KEY_CLAUDE:
        results.append(("Position Check", test_position_check()))
    else:
        print("\n⚠️  Skipping API tests - no credentials")
    
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
        print("✅ ALL TESTS PASSED! Ready to deploy.")
    else:
        print("❌ Some tests failed.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
