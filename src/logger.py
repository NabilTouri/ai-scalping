"""
Centralized logging utility for AI Scalping Bot
Logs to both console and database for dashboard visibility
"""
import logging
import sys
import re
from datetime import datetime
from src.config import Config


class DatabaseHandler(logging.Handler):
    """Custom handler that writes logs to the database."""
    
    def __init__(self):
        super().__init__()
        self._session = None
    
    def _get_session(self):
        """Lazy load session to avoid circular imports."""
        if self._session is None:
            from src.database import SessionLocal
            self._session = SessionLocal()
        return self._session
    
    def _extract_symbol(self, message):
        """Extract symbol from log message if present."""
        # Match any pattern like XXX/USD (3-5 uppercase letters followed by /USD)
        match = re.search(r'[A-Z]{2,5}/USD', message)
        return match.group(0) if match else None
    
    def emit(self, record):
        try:
            from src.database import Log
            session = self._get_session()
            
            log_entry = Log(
                timestamp=datetime.utcnow(),
                level=record.levelname,
                source=record.name,
                symbol=self._extract_symbol(record.getMessage()),
                message=record.getMessage()
            )
            session.add(log_entry)
            session.commit()
        except Exception:
            # Don't let logging errors crash the bot
            pass


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set level from config
        level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Format with timestamp: [TIMESTAMP] [LEVEL] [SOURCE] message
        formatter = logging.Formatter(
            '[%(levelname)s] [%(name)s] %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Database handler
        db_handler = DatabaseHandler()
        db_handler.setLevel(level)
        logger.addHandler(db_handler)
    
    return logger


# Pre-configured loggers for main components
bot_logger = get_logger("BOT")
execution_logger = get_logger("EXECUTION")
strategy_logger = get_logger("STRATEGY")
