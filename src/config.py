import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # ===================
    # API KEYS
    # ===================
    ALPACA_KEY_CLAUDE = os.getenv("ALPACA_API_KEY_CLAUDE")
    ALPACA_SECRET_CLAUDE = os.getenv("ALPACA_SECRET_KEY_CLAUDE")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # ===================
    # TRADING SETTINGS
    # ===================
    PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"
    BASE_URL = "https://paper-api.alpaca.markets" if PAPER_TRADING else "https://api.alpaca.markets"
    
    # Asset Universe (Crypto available on Alpaca)
    TRADING_UNIVERSE = ["BTC/USD", "ETH/USD"]

    # ===================
    # AI MODEL SETTINGS
    # ===================
    CLAUDE_MODEL = "claude-3-haiku-20240307"  # Options: claude-3-haiku, claude-3-sonnet, claude-3-opus
    CLAUDE_MAX_TOKENS = 1000

    # ===================
    # STRATEGY SETTINGS
    # ===================
    TIMEFRAME = "15Min"                        # Data granularity: 1Min, 5Min, 15Min, 30Min, 1Hour
    HISTORICAL_BARS_LIMIT = 100                # Number of bars to fetch for AI analysis
    STRATEGY_UPDATE_INTERVAL = 15 * 60         # Seconds between AI analysis (Should match TIMEFRAME)
    STRATEGY_SYMBOL_DELAY = 5                  # Seconds delay between analyzing each symbol

    # ===================
    # EXECUTION SETTINGS
    # ===================
    EXECUTION_LOOP_INTERVAL = 10               # Seconds between signal checks
    HEARTBEAT_TIMEOUT = 30                     # Seconds - dashboard shows offline if no heartbeat

    # ===================
    # RISK MANAGEMENT
    # ===================
    MAX_POSITION_SIZE_PERCENT = 0.20           # Max 20% of equity per trade
    MIN_TRADE_PERCENT = 0.05                   # Minimum 5% of equity per trade
    MAX_DAILY_LOSS_PERCENT = 0.05              # Stop trading if equity drops 5% in a day
    HARD_STOP_LOSS_PERCENT = 0.05              # Force close trade if loss > 5%
    MIN_CONFIDENCE = 0.6                       # Skip trade if AI confidence below 60%

    # ===================
    # LOGGING
    # ===================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # ===================
    # DATABASE
    # ===================
    DATABASE_URL = "sqlite:///data/trading_bot.db"

    @classmethod
    def validate(cls):
        """Checks if essential config is present."""
        if not cls.ALPACA_KEY_CLAUDE or not cls.ALPACA_SECRET_CLAUDE:
            raise ValueError("Alpaca API credentials for CLAUDE missing in .env")
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API Key missing in .env")

# Validation check on import

