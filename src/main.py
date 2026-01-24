import time
import threading
from datetime import datetime
from src.config import Config
from src.database import SessionLocal, init_db, StrategicSignal
from src.market_data import MarketDataManager
from src.execution_engine import ExecutionEngine
from src.ai_agents.claude_agent import ClaudeAgent

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
        print("ERROR: No Claude API key found!")
        return
    
    print(">>> Strategy Loop Started")

    while True:
        try:
            # Create a fresh session for this cycle
            db_session = SessionFactory()
            
            for symbol in Config.TRADING_UNIVERSE:
                print(f"--- Analyzing {symbol} ---")
                
                # Fetch Data
                df = market.get_historical_data(symbol, timeframe_str=Config.TIMEFRAME)
                
                # Ask Claude for analysis
                print(f"Querying Claude for {symbol}...")
                c_decision = claude.analyze(symbol, df)
                save_signal(db_session, "CLAUDE", symbol, c_decision)
                
                # Respect API rate limits
                time.sleep(5)
            
            db_session.close() # Close session after cycle
                
            print(f">>> Strategy Update Complete. Sleeping for {Config.STRATEGY_UPDATE_INTERVAL}s")
        except Exception as e:
            print(f"Strategy Loop Error: {e}")
        
        time.sleep(Config.STRATEGY_UPDATE_INTERVAL)

def save_signal(session, agent_name, symbol, decision):
    """Parses decision dict and saves to DB."""
    try:
        # Deactivate old signals for this agent/symbol
        session.query(StrategicSignal).filter(
            StrategicSignal.agent_name == agent_name,
            StrategicSignal.target_symbol == symbol,
            StrategicSignal.is_active == True
        ).update({"is_active": False})
        
        # Create new signal
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
            reasoning=decision.get("reasoning", ""),
            is_active=True
        )
        
        session.add(new_signal)
        session.commit()
        print(f"[{agent_name}] New Signal Saved: {decision.get('action')} {symbol}")
        
    except Exception as e:
        print(f"Failed to save signal: {e}")

def execution_loop(execution_engine):
    """
    Runs frequently (e.g. every 10s).
    Checks market price vs active signals and executes.
    """
    print(">>> Execution Loop Started")
    while True:
        execution_engine.process_signals()
        time.sleep(10) # 10 seconds check interval

def invalidate_stale_signals():
    """
    Deactivate all active signals from previous bot sessions.
    This prevents executing stale signals that no longer reflect current market conditions.
    """
    db = SessionLocal()
    try:
        stale_count = db.query(StrategicSignal).filter(StrategicSignal.is_active == True).update({"is_active": False})
        db.commit()
        if stale_count > 0:
            print(f">>> Invalidated {stale_count} stale signal(s) from previous session")
    except Exception as e:
        print(f"Error invalidating stale signals: {e}")
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
        # 1. Get real positions from Alpaca
        real_positions = {}
        try:
            positions = market.get_open_positions("CLAUDE")
            for p in positions:
                # Convert ETHUSD/BTCUSD/AVAXUSD back to ETH/USD format for DB consistency
                raw_symbol = p.symbol
                if raw_symbol.endswith("USD"):
                    symbol = raw_symbol[:-3] + "/USD"  # ETHUSD -> ETH/USD, AVAXUSD -> AVAX/USD
                else:
                    symbol = raw_symbol
                real_positions[symbol] = {
                    "qty": float(p.qty),
                    "entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price)
                }
            print(f">>> Found {len(real_positions)} real position(s) on Alpaca")
        except Exception as e:
            print(f"Warning: Could not fetch Alpaca positions: {e}")
            return
        
        # 2. Close DB trades that don't exist on Alpaca anymore
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        closed_count = 0
        for trade in open_trades:
            if trade.symbol not in real_positions:
                # Position no longer exists on Alpaca
                trade.status = "CLOSED"
                trade.pnl = 0.0  # Unknown - was closed externally
                closed_count += 1
        
        if closed_count > 0:
            db.commit()
            print(f">>> Closed {closed_count} stale trade(s) not found on Alpaca")
        
        # 3. Sync DB with Alpaca positions (create or update)
        for symbol, pos_data in real_positions.items():
            existing = db.query(Trade).filter(
                Trade.symbol == symbol,
                Trade.status == "OPEN"
            ).first()
            
            if existing:
                # Update existing trade with current Alpaca values
                existing.qty = pos_data["qty"]
                existing.entry_price = pos_data["entry_price"]
                print(f">>> Updated position: {symbol} (qty={pos_data['qty']:.4f}, entry=${pos_data['entry_price']:.2f})")
            else:
                # Position exists on Alpaca but not tracked in DB - create new
                new_trade = Trade(
                    agent_name="CLAUDE",
                    symbol=symbol,
                    side="buy",  # Assume buy since we don't short
                    qty=pos_data["qty"],
                    entry_price=pos_data["entry_price"],
                    status="OPEN",
                    strategy_signal_id=None  # No signal - pre-existing position
                )
                db.add(new_trade)
                print(f">>> Created position: {symbol} (qty={pos_data['qty']:.4f}, entry=${pos_data['entry_price']:.2f})")
        
        db.commit()
        
    except Exception as e:
        print(f"Error syncing positions: {e}")
    finally:
        db.close()

def main():
    print("Starting AI Scalping Bot...")
    
    # Init DB
    init_db()
    
    # Init market manager first (needed for sync)
    market = MarketDataManager()
    
    # Sync with Alpaca - the source of truth
    invalidate_stale_signals()
    sync_positions_with_alpaca(market)
    
    # Init Components
    # Main thread uses its own session (via ExecutionEngine)
    db_session_execution = SessionLocal() 
    execution = ExecutionEngine(db_session_execution, market)
    
    # Start Strategy Thread (Daemon) - Pass SessionFactory
    strategy_thread = threading.Thread(target=strategy_loop, args=(market, SessionLocal), daemon=True)
    strategy_thread.start()
    
    # Run Execution Loop in Main Thread
    execution_loop(execution)

if __name__ == "__main__":
    main()
