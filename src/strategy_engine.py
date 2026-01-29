import time
from src.config import Config
from src.database import StrategicSignal, SessionLocal
from src.ai_agents.claude_agent import ClaudeAgent
from src.logger import strategy_logger as logger

class StrategyEngine:
    def __init__(self, market_manager):
        self.market = market_manager
        self.claude = None
        if Config.ANTHROPIC_API_KEY:
            self.claude = ClaudeAgent()
        else:
            logger.error("No Claude API key found!")

    def run(self):
        """
        Runs the strategy loop.
        1. Fetches historical data.
        2. Asks Claude for analysis.
        3. Updates 'StrategicSignal' table.
        """
        if not self.claude:
            logger.error("Cannot start Strategy Loop: Claude not initialized")
            return

        logger.info("Strategy Loop Started")

        while True:
            try:
                db_session = SessionLocal()
                
                for symbol in Config.TRADING_UNIVERSE:
                    logger.info(f"Analyzing {symbol}")
                    
                    df = self.market.get_historical_data(symbol, timeframe_str=Config.TIMEFRAME)
                    current_price = self.market.get_current_price(symbol)
                    
                    logger.debug(f"Querying Claude for {symbol}")
                    c_decision = self.claude.analyze(symbol, df)
                    self._save_signal(db_session, "CLAUDE", symbol, c_decision, current_price)
                    
                    time.sleep(Config.STRATEGY_SYMBOL_DELAY)
                
                db_session.close()
                    
                logger.info(f"Strategy Update Complete. Sleeping for {Config.STRATEGY_UPDATE_INTERVAL}s")
            except Exception as e:
                logger.error(f"Strategy Loop Error: {e}")
            
            time.sleep(Config.STRATEGY_UPDATE_INTERVAL)

    def _save_signal(self, session, agent_name, symbol, decision, current_price=None):
        """Parses decision dict and saves to DB."""
        try:
            # Inactivate previous active signals for this agent/symbol
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
            logger.info(f"[{agent_name}] New Signal: {decision.get('action')} {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
