"""
Centralized logging utility for AI Scalping Bot
"""
import logging
import sys
from src.config import Config

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set level from config
        level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Format: [LEVEL] [SOURCE] message
        formatter = logging.Formatter(
            '[%(levelname)s] [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Pre-configured loggers for main components
bot_logger = get_logger("BOT")
execution_logger = get_logger("EXECUTION")
strategy_logger = get_logger("STRATEGY")
