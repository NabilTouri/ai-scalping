import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys - Alpaca (for Claude agent)
    ALPACA_KEY_CLAUDE = os.getenv("ALPACA_API_KEY_CLAUDE")
    ALPACA_SECRET_CLAUDE = os.getenv("ALPACA_SECRET_KEY_CLAUDE")

    # AI Keys - Claude
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Trading Settings
    PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"
    BASE_URL = "https://paper-api.alpaca.markets" if PAPER_TRADING else "https://api.alpaca.markets"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Risk Management Guardrails
    MAX_POSITION_SIZE_PERCENT = 0.20  # Max 20% of equity per trade
    MAX_DAILY_LOSS_PERCENT = 0.05     # Stop trading if equity drops 5% in a day
    HARD_STOP_LOSS_PERCENT = 0.05     # Force close trade if loss > 5%
    MIN_CONFIDENCE = 0.6              # Skip trade if AI confidence below this

    # Strategy Settings
    TIMEFRAME = "15Min"               # Data granularity for AI analysis
    STRATEGY_UPDATE_INTERVAL = 30 * 60 # Seconds (30 minutes)
    
    # Asset Universe (Crypto available on Alpaca)
    TRADING_UNIVERSE = ["BTC/USD", "ETH/USD"]

    # Database - uses data directory for Docker compatibility
    DATABASE_URL = "sqlite:///data/trading_bot.db"

    @classmethod
    def validate(cls):
        """Checks if essential config is present."""
        if not cls.ALPACA_KEY_CLAUDE or not cls.ALPACA_SECRET_CLAUDE:
            raise ValueError("Alpaca API credentials for CLAUDE missing in .env")
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API Key missing in .env")

# Validation check on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
