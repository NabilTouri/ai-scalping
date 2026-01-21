import sys
import os

print("Testing imports...")
try:
    from src.config import Config
    print("Config imported.")
    from src.database import init_db, engine
    print("Database module imported.")
    from src.market_data import MarketDataManager
    print("MarketData module imported.")
    from src.ai_agents.gemini_agent import GeminiAgent
    print("Gemini Agent imported.")
    from src.ai_agents.claude_agent import ClaudeAgent
    print("Claude Agent imported.")
    
    print("\nInitializing Database...")
    init_db()
    print("Database initialized successfully.")
    
    print("\nChecking API Keys present...")
    print(f"Alpaca Key: {'OK' if Config.ALPACA_API_KEY else 'MISSING'}")
    print(f"Gemini Key: {'OK' if Config.GEMINI_API_KEY else 'MISSING'}")
    print(f"Claude Key: {'OK' if Config.ANTHROPIC_API_KEY else 'MISSING'}")

    print("\nTest passed successfully!")

except Exception as e:
    print(f"\nTEST FAILED: {e}")
    import traceback
    traceback.print_exc()
