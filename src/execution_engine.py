from datetime import datetime
from sqlalchemy.orm import Session
from .database import Trade, StrategicSignal, Log
from .market_data import MarketDataManager
from .config import Config

class ExecutionEngine:
    def __init__(self, db_session: Session, market_manager: MarketDataManager):
        self.db = db_session
        self.market = market_manager

    def log(self, message, level="INFO"):
        """Central logging to DB."""
        print(f"[{level}] {message}") # Also print to stdout
        log_entry = Log(
            level=level,
            source="EXECUTION_ENGINE",
            message=message
        )
        self.db.add(log_entry)
        self.db.commit()

    def process_signals(self):
        """Checks all active 'StrategicSignals' against current market data."""
        active_signals = self.db.query(StrategicSignal).filter(StrategicSignal.is_active == True).all()
        
        for signal in active_signals:
            try:
                self._evaluate_signal(signal)
            except Exception as e:
                self.log(f"Error evaluating signal {signal.id}: {e}", "ERROR")

    def _evaluate_signal(self, signal: StrategicSignal):
        # 1. Check if we already have an open trade for this signal
        existing_trade = self.db.query(Trade).filter(
            Trade.strategy_signal_id == signal.id,
            Trade.status == "OPEN"
        ).first()

        current_price = self.market.get_current_price(signal.target_symbol)
        
        # LOGIC: ENTRY
        if not existing_trade:
            if signal.action == "BUY":
                # Check entry conditions
                # If entry_price_max is set, price must be below it
                # If entry_price_min is set, price must be above it
                below_max = (current_price <= signal.entry_price_max) if signal.entry_price_max else True
                above_min = (current_price >= signal.entry_price_min) if signal.entry_price_min else True

                if below_max and above_min:
                    self._execute_entry(signal, current_price, "buy")
            
            elif signal.action == "SELL":
                # For short selling (if supported) or just selling existing holdings
                # Simplifying to just BUY logic for now unless user asked for Shorting? 
                # User said "Scalping", usually implies both ways, but Alpaca paper supports shorting.
                # Let's implement SHORT logic too.
                
                # For SHORT entry: Price should be HIGH.
                # If entry_price_min is set (e.g. support level), maybe we wait for break?
                # Using simple logic: 
                # signal.entry_price_min could act as "sell limit" (don't sell below this)
                above_min = (current_price >= signal.entry_price_min) if signal.entry_price_min else True
                
                if above_min:
                    self._execute_entry(signal, current_price, "sell")

        # LOGIC: EXIT (Stop Loss / Take Profit)
        else:
            self._manage_open_trade(existing_trade, current_price, signal)

    def _execute_entry(self, signal, price, side):
        # Risk Management: Calculate Position Size
        # Fixed % of equity for now
        # Risk Management: Calculate Position Size
        # Fixed % of equity for now
        account = self.market.get_account(signal.agent_name)
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        
        # Max Risk per trade
        trade_amount = equity * Config.MAX_POSITION_SIZE_PERCENT
        
        if trade_amount > buying_power:
            trade_amount = buying_power * 0.95 # Safety buffer

        qty = trade_amount / price
        
        # Send Order to Alpaca
        try:
            order = self.market.submit_order(signal.agent_name, signal.target_symbol, qty, side)
            self.log(f"Executed {side.upper()} {signal.target_symbol} at {price} (Qty: {qty:.4f})")
            
            # Record in DB
            new_trade = Trade(
                agent_name=signal.agent_name,
                symbol=signal.target_symbol,
                side=side,
                qty=float(qty),
                entry_price=price,
                status="OPEN",
                strategy_signal_id=signal.id
            )
            self.db.add(new_trade)
            self.db.commit()
            
        except Exception as e:
            self.log(f"Order Failed: {e}", "ERROR")
            # Deactivate signal to prevent infinite retry loop
            signal.is_active = False
            self.db.commit()

    def _manage_open_trade(self, trade, current_price, signal):
        # Check Stop Loss
        if signal.stop_loss:
            if trade.side == "buy" and current_price <= signal.stop_loss:
                self._close_trade(trade, current_price, "Hit Stop Loss")
                return
            if trade.side == "sell" and current_price >= signal.stop_loss:
                self._close_trade(trade, current_price, "Hit Stop Loss")
                return

        # Check Take Profit
        if signal.take_profit:
            if trade.side == "buy" and current_price >= signal.take_profit:
                self._close_trade(trade, current_price, "Hit Take Profit")
                return
            if trade.side == "sell" and current_price <= signal.take_profit:
                self._close_trade(trade, current_price, "Hit Take Profit")
                return

        # Hard Guardrails (Backstop)
        pnl_pct = (current_price - trade.entry_price) / trade.entry_price
        if trade.side == "sell": pnl_pct *= -1
        
        if pnl_pct <= -Config.HARD_STOP_LOSS_PERCENT:
             self._close_trade(trade, current_price, "Hard Stop Loss Triggered")

    def _close_trade(self, trade, price, reason):
        try:
            self.market.close_position(trade.agent_name, trade.symbol) # Close all for symbol for now (simpler)
            
            pnl = (price - trade.entry_price) * trade.qty
            if trade.side == "sell": pnl *= -1
            
            trade.exit_price = price
            trade.exit_time = datetime.utcnow()
            trade.status = "CLOSED"
            trade.pnl = pnl
            
            self.db.commit()
            
            # Deactivate signal so we don't re-enter immediately
            signal = self.db.query(StrategicSignal).get(trade.strategy_signal_id)
            if signal:
                signal.is_active = False
                self.db.commit()

            self.log(f"Closed {trade.symbol} at {price}. PnL: {pnl:.2f}. Reason: {reason}")
            
        except Exception as e:
            self.log(f"Failed to close trade: {e}", "ERROR")
