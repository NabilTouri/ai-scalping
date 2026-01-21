import time
import threading
from datetime import datetime
from src.config import Config
from src.database import SessionLocal, init_db, StrategicSignal
from src.market_data import MarketDataManager
from src.execution_engine import ExecutionEngine
from src.ai_agents.gemini_agent import GeminiAgent
from src.ai_agents.claude_agent import ClaudeAgent

def strategy_loop(market, SessionFactory):
    """
    Runs every X minutes.
    1. Fetches historical data.
    2. Asks Claude for analysis.
    3. Updates 'StrategicSignal' table.
    """
    # DISABLED: Gemini due to Free Tier rate limits
    # gemini = GeminiAgent()
    
    claude = None
    if Config.ANTHROPIC_API_KEY:
        claude = ClaudeAgent()
    else:
        print("ERROR: No Claude API key found!")
        return
    
    print(">>> Strategy Loop Started (Claude Only Mode)")

    while True:
        try:
            # Create a fresh session for this cycle
            db_session = SessionFactory()
            
            for symbol in Config.TRADING_UNIVERSE:
                print(f"--- Analyzing {symbol} ---")
                
                # Fetch Data
                df = market.get_historical_data(symbol, timeframe_str=Config.TIMEFRAME)
                
                # DISABLED: Gemini
                # print(f"Querying Gemini for {symbol}...")
                # g_decision = gemini.analyze(symbol, df)
                # save_signal(db_session, "GEMINI", symbol, g_decision)
                
                # Ask Claude
                print(f"Querying Claude for {symbol}...")
                c_decision = claude.analyze(symbol, df)
                save_signal(db_session, "CLAUDE", symbol, c_decision)
                
                # Respect Rate Limits (Free Tier Gemini allows ~15 req/min, but safe to slow down)
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

def main():
    print("Starting AI Scalping Bot...")
    
    # Init DB
    init_db()
    
    # Init Components
    # Main thread uses its own session (via ExecutionEngine)
    db_session_execution = SessionLocal() 
    market = MarketDataManager()
    execution = ExecutionEngine(db_session_execution, market)
    
    # Start Strategy Thread (Daemon) - Pass SessionFactory
    strategy_thread = threading.Thread(target=strategy_loop, args=(market, SessionLocal), daemon=True)
    strategy_thread.start()
    
    # Run Execution Loop in Main Thread
    execution_loop(execution)

if __name__ == "__main__":
    main()
