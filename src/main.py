import time
import threading
from datetime import datetime
from src.config import Config
from src.database import SessionLocal, init_db, StrategicSignal
from src.market_data import MarketDataManager
from src.execution_engine import ExecutionEngine
from src.ai_agents.claude_agent import ClaudeAgent
from src.logger import bot_logger as logger, strategy_logger


def strategy_loop(market, SessionFactory):
    """
    Runs every X minutes.
    1. Fetches historical data.
    2. Asks Claude for analysis.
    3. Updates 'StrategicSignal' table.
    """
    claude = None
    if Config.ANTHROPIC_API_KEY:
        claude = ClaudeAgent()
    else:
        logger.error("No Claude API key found!")
        return
    
    strategy_logger.info("Strategy Loop Started")

    while True:
        try:
            db_session = SessionFactory()
            
            for symbol in Config.TRADING_UNIVERSE:
                strategy_logger.info(f"Analyzing {symbol}")
                
                df = market.get_historical_data(symbol, timeframe_str=Config.TIMEFRAME)
                current_price = market.get_current_price(symbol)
                
                strategy_logger.debug(f"Querying Claude for {symbol}")
                c_decision = claude.analyze(symbol, df)
                save_signal(db_session, "CLAUDE", symbol, c_decision, current_price)
                
                time.sleep(5)
            
            db_session.close()
                
            strategy_logger.info(f"Strategy Update Complete. Sleeping for {Config.STRATEGY_UPDATE_INTERVAL}s")
        except Exception as e:
            strategy_logger.error(f"Strategy Loop Error: {e}")
        
        time.sleep(Config.STRATEGY_UPDATE_INTERVAL)


def save_signal(session, agent_name, symbol, decision, current_price=None):
    """Parses decision dict and saves to DB."""
    try:
        session.query(StrategicSignal).filter(
            StrategicSignal.agent_name == agent_name,
            StrategicSignal.target_symbol == symbol,
            StrategicSignal.is_active == True
        ).update({"is_active": False})
        
        new_signal = StrategicSignal(
            agent_name=agent_name,
            target_symbol=symbol,
            action=decision.get("action", "HOLD"),
            sentiment=decision.get("sentiment", "NEUTRAL"),
            confidence=float(decision.get("confidence", 0.0)),
            entry_price_min=decision.get("entry_price_min"),
            entry_price_max=decision.get("entry_price_max"),
            stop_loss=decision.get("stop_loss"),
            take_profit=decision.get("take_profit"),
            price_at_signal=current_price,  # For accuracy analysis
            reasoning=decision.get("reasoning", ""),
            is_active=True
        )
        
        session.add(new_signal)
        session.commit()
        strategy_logger.info(f"[{agent_name}] New Signal: {decision.get('action')} {symbol}")
        
    except Exception as e:
        strategy_logger.error(f"Failed to save signal: {e}")


def execution_loop(execution_engine):
    """
    Runs frequently (e.g. every 10s).
    Checks market price vs active signals and executes.
    """
    logger.info("Execution Loop Started")
    while True:
        execution_engine.process_signals()
        time.sleep(10)


def invalidate_stale_signals():
    """Deactivate all active signals from previous bot sessions."""
    db = SessionLocal()
    try:
        stale_count = db.query(StrategicSignal).filter(StrategicSignal.is_active == True).update({"is_active": False})
        db.commit()
        if stale_count > 0:
            logger.info(f"Invalidated {stale_count} stale signal(s) from previous session")
    except Exception as e:
        logger.error(f"Error invalidating stale signals: {e}")
    finally:
        db.close()


def sync_positions_with_alpaca(market):
    """
    Sync database with real Alpaca positions.
    Alpaca is the source of truth - DB is just for logging.
    """
    from src.database import Trade
    db = SessionLocal()
    
    try:
        real_positions = {}
        try:
            positions = market.get_open_positions("CLAUDE")
            for p in positions:
                raw_symbol = p.symbol
                if raw_symbol.endswith("USD"):
                    symbol = raw_symbol[:-3] + "/USD"
                else:
                    symbol = raw_symbol
                real_positions[symbol] = {
                    "qty": float(p.qty),
                    "entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price)
                }
            logger.info(f"Found {len(real_positions)} real position(s) on Alpaca")
        except Exception as e:
            logger.warning(f"Could not fetch Alpaca positions: {e}")
            return
        
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        closed_count = 0
        for trade in open_trades:
            if trade.symbol not in real_positions:
                trade.status = "CLOSED"
                trade.pnl = 0.0
                closed_count += 1
        
        if closed_count > 0:
            db.commit()
            logger.info(f"Closed {closed_count} stale trade(s) not found on Alpaca")
        
        for symbol, pos_data in real_positions.items():
            existing = db.query(Trade).filter(
                Trade.symbol == symbol,
                Trade.status == "OPEN"
            ).first()
            
            if existing:
                existing.qty = pos_data["qty"]
                existing.entry_price = pos_data["entry_price"]
                logger.info(f"Updated position: {symbol} (qty={pos_data['qty']:.4f}, entry=${pos_data['entry_price']:.2f})")
            else:
                new_trade = Trade(
                    agent_name="CLAUDE",
                    symbol=symbol,
                    side="buy",
                    qty=pos_data["qty"],
                    entry_price=pos_data["entry_price"],
                    status="OPEN",
                    strategy_signal_id=None
                )
                db.add(new_trade)
                logger.info(f"Created position: {symbol} (qty={pos_data['qty']:.4f}, entry=${pos_data['entry_price']:.2f})")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error syncing positions: {e}")
    finally:
        db.close()


def main():
    logger.info("Starting AI Scalping Bot...")
    
    init_db()
    
    market = MarketDataManager()
    
    invalidate_stale_signals()
    sync_positions_with_alpaca(market)
    
    db_session_execution = SessionLocal() 
    execution = ExecutionEngine(db_session_execution, market)
    
    strategy_thread = threading.Thread(target=strategy_loop, args=(market, SessionLocal), daemon=True)
    strategy_thread.start()
    
    execution_loop(execution)


if __name__ == "__main__":
    main()
