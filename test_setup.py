"""
Quick test to verify the bot setup is correct.
Run: python test_setup.py
"""
import sys

def test_imports():
    print("Testing imports...")
    try:
        from src.config import Config
        print("✓ Config imported")
        
        from src.database import init_db, SessionLocal
        print("✓ Database module imported")
        
        from src.market_data import MarketDataManager
        print("✓ MarketData module imported")
        
        from src.ai_agents.claude_agent import ClaudeAgent
        print("✓ Claude Agent imported")
        
        from src.execution_engine import ExecutionEngine
        print("✓ Execution Engine imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config():
    print("\nChecking API Keys...")
    from src.config import Config
    
    checks = {
        "ALPACA_KEY_CLAUDE": bool(Config.ALPACA_KEY_CLAUDE),
        "ALPACA_SECRET_CLAUDE": bool(Config.ALPACA_SECRET_CLAUDE),
        "ANTHROPIC_API_KEY": bool(Config.ANTHROPIC_API_KEY),
    }
    
    all_ok = True
    for key, present in checks.items():
        status = "✓ OK" if present else "✗ MISSING"
        print(f"  {key}: {status}")
        if not present:
            all_ok = False
    
    return all_ok

def test_database():
    print("\nTesting database...")
    try:
        from src.database import init_db
        init_db()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def main():
    print("=" * 50)
    print("AI Scalping Bot - Setup Test")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("Database", test_database()))
    
    print("\n" + "=" * 50)
    print("Results:")
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("✓ All tests passed! Bot is ready to run.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check your .env file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
