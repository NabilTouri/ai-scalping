import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    # Account 1: Gemini Agent
    ALPACA_KEY_GEMINI = os.getenv("ALPACA_API_KEY_GEMINI")
    ALPACA_SECRET_GEMINI = os.getenv("ALPACA_SECRET_KEY_GEMINI")
    
    # Account 2: Claude Agent
    ALPACA_KEY_CLAUDE = os.getenv("ALPACA_API_KEY_CLAUDE")
    ALPACA_SECRET_CLAUDE = os.getenv("ALPACA_SECRET_KEY_CLAUDE")

    # AI Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Trading Settings
    PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"
    BASE_URL = "https://paper-api.alpaca.markets" if PAPER_TRADING else "https://api.alpaca.markets"
    
    # Risk Management Guardrails
    MAX_POSITION_SIZE_PERCENT = 0.20  # Max 20% of equity per trade
    MAX_DAILY_LOSS_PERCENT = 0.05     # Stop trading if equity drops 5% in a day
    HARD_STOP_LOSS_PERCENT = 0.05     # Force close trade if loss > 5%

    # Strategy Settings
    TIMEFRAME = "15Min"               # Data granularity for AI analysis
    STRATEGY_UPDATE_INTERVAL = 30 * 60 # Seconds (30 minutes)
    
    # Asset Universe (Liquid Crypto)
    TRADING_UNIVERSE = ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD"]

    # Database
    DATABASE_URL = "sqlite:///trading_bot.db"

    @classmethod
    def validate(cls):
        """Checks if essential config is present."""
        if not cls.ALPACA_KEY_GEMINI or not cls.ALPACA_SECRET_GEMINI:
            raise ValueError("Alpaca API credentials for GEMINI (Account 1) missing in .env")
        if not cls.ALPACA_KEY_CLAUDE or not cls.ALPACA_SECRET_CLAUDE:
            raise ValueError("Alpaca API credentials for CLAUDE (Account 2) missing in .env")
        if not cls.GEMINI_API_KEY:
            raise ValueError("Gemini API Key missing in .env")
        if not cls.ANTHROPIC_API_KEY:
            print("Warning: Anthropic API Key missing. Claude agent will not work.")

# Validation check on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
