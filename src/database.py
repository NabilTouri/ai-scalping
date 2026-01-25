from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from .config import Config

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)  # Agent identifier (e.g., 'CLAUDE')
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    qty = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    status = Column(String, default="OPEN")  # OPEN, CLOSED, CANCELED
    pnl = Column(Float, default=0.0)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    strategy_signal_id = Column(Integer, ForeignKey('strategic_signals.id'), nullable=True)

class StrategicSignal(Base):
    """Stores the high-level directives from the AI."""
    __tablename__ = 'strategic_signals'

    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # AI Analysis
    raw_response = Column(Text)  # Full JSON response from AI
    
    # Structured Directives
    sentiment = Column(String)   # BULLISH, BEARISH, NEUTRAL
    target_symbol = Column(String)
    action = Column(String)      # BUY, SELL, HOLD
    confidence = Column(Float)   # 0.0 to 1.0
    
    # Execution Parameters
    entry_price_min = Column(Float, nullable=True)
    entry_price_max = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # For accuracy analysis
    price_at_signal = Column(Float, nullable=True)  # Market price when signal was generated
    
    reasoning = Column(Text)
    
    is_active = Column(Boolean, default=True)

class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String, default="INFO")
    source = Column(String)  # BOT, EXECUTION, STRATEGY
    symbol = Column(String, nullable=True)  # BTC/USD, ETH/USD, etc.
    message = Column(Text)

class BotStatus(Base):
    """Heartbeat table - bot updates this every 10 seconds."""
    __tablename__ = 'bot_status'
    
    id = Column(Integer, primary_key=True)
    bot_name = Column(String, default="MAIN")
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="RUNNING")  # RUNNING, STOPPED

# Database Initialization
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print(f"Database initialized at {Config.DATABASE_URL}")

if __name__ == "__main__":
    init_db()
