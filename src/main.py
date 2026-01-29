import time
import threading
from datetime import datetime
from src.config import Config
from src.database import SessionLocal, init_db, BotStatus
from src.market_data import MarketDataManager
from src.execution_engine import ExecutionEngine
from src.strategy_engine import StrategyEngine
from src.logger import bot_logger as logger

def update_heartbeat():
    """Update heartbeat timestamp to indicate bot is alive."""
    db = SessionLocal()
    try:
        status = db.query(BotStatus).filter(BotStatus.bot_name == "MAIN").first()
        if status:
            status.last_heartbeat = datetime.utcnow()
        else:
            status = BotStatus(bot_name="MAIN", last_heartbeat=datetime.utcnow())
            db.add(status)
        db.commit()
    except Exception:
        pass  # Never crash for heartbeat
    finally:
        db.close()


def execution_loop(execution_engine, market):
    """
    Runs frequently (e.g. every 10s).
    Checks market price vs active signals and executes.
    Also monitors daily loss and halts trading if exceeded.
    """
    logger.info("Execution Loop Started")
    starting_equity = None
    trading_halted = False
    
    while True:
        # Check daily loss limit
        try:
            account = market.get_account("CLAUDE")
            current_equity = float(account.equity)
            
            # Set starting equity on first run or at midnight reset
            if starting_equity is None:
                starting_equity = current_equity
                logger.info(f"Starting equity: ${starting_equity:.2f}")
            
            # Calculate daily loss
            daily_pnl_pct = (current_equity - starting_equity) / starting_equity
            
            if daily_pnl_pct <= -Config.MAX_DAILY_LOSS_PERCENT:
                if not trading_halted:
                    logger.warning(f"TRADING HALTED - Daily loss {daily_pnl_pct:.2%} exceeds limit {-Config.MAX_DAILY_LOSS_PERCENT:.2%}")
                    trading_halted = True
            else:
                if trading_halted:
                    logger.info("Trading resumed - loss within acceptable range")
                trading_halted = False
                
        except Exception as e:
            logger.error(f"Error checking daily loss: {e}")
        
        # Only process signals if trading is allowed
        if not trading_halted:
            execution_engine.process_signals()
        
        update_heartbeat()
        time.sleep(Config.EXECUTION_LOOP_INTERVAL)


def main():
    logger.info("Starting AI Scalping Bot...")
    
    # 1. Validate Config
    try:
        Config.validate()
    except ValueError as e:
        logger.critical(f"Configuration Error: {e}")
        return

    # 2. Init DB
    init_db()
    
    # 3. Init Market Data
    market = MarketDataManager()
    
    # 4. Init Execution Engine
    db_session_execution = SessionLocal() 
    execution = ExecutionEngine(db_session_execution, market)
    
    # 5. Startup Sync
    logger.info("Running startup sync...")
    execution.invalidate_stale_signals()
    execution.sync_existing_positions()
    
    # 6. Init and Start Strategy Engine
    strategy_engine = StrategyEngine(market)
    strategy_thread = threading.Thread(target=strategy_engine.run, daemon=True)
    strategy_thread.start()
    
    # 7. Run Execution Loop (Main Thread)
    execution_loop(execution, market)


if __name__ == "__main__":
    main()
