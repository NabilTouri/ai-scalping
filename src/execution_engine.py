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
        # Skip if confidence is too low (Bug 2 fix)
        if signal.confidence is not None and signal.confidence < 0.6:
            return  # Don't trade with low confidence
        
        # 1. Check if we already have an open trade for this signal
        existing_trade = self.db.query(Trade).filter(
            Trade.strategy_signal_id == signal.id,
            Trade.status == "OPEN"
        ).first()

        current_price = self.market.get_current_price(signal.target_symbol)
        
        # LOGIC: ENTRY
        if not existing_trade:
            # Bug 4 fix: Check if we already have a position for this symbol
            if self.market.has_position(signal.agent_name, signal.target_symbol):
                # Already have position, don't open another
                return
            
            if signal.action == "BUY":
                # Check entry conditions
                below_max = (current_price <= signal.entry_price_max) if signal.entry_price_max else True
                above_min = (current_price >= signal.entry_price_min) if signal.entry_price_min else True

                if below_max and above_min:
                    self._execute_entry(signal, current_price, "buy")
            
            elif signal.action == "SELL":
                # Only sell if we have existing position (no short selling)
                pass  # Disabled short selling per prompt

        # LOGIC: EXIT (Stop Loss / Take Profit)
        else:
            self._manage_open_trade(existing_trade, current_price, signal)

    def _execute_entry(self, signal, price, side):
        # Get account info
        account = self.market.get_account(signal.agent_name)
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        
        # Minimum trade as percentage of equity (5%)
        MIN_TRADE_PERCENT = 0.05
        min_trade_value = equity * MIN_TRADE_PERCENT
        
        # Check minimum buying power
        if buying_power < min_trade_value:
            self.log(f"Insufficient buying power: ${buying_power:.2f} < {MIN_TRADE_PERCENT*100}% of equity", "WARNING")
            signal.is_active = False
            self.db.commit()
            return
        
        # Risk Management: Calculate Position Size
        trade_amount = equity * Config.MAX_POSITION_SIZE_PERCENT
        
        if trade_amount > buying_power:
            trade_amount = buying_power * 0.95  # Safety buffer
        
        # Ensure minimum trade value
        if trade_amount < min_trade_value:
            trade_amount = min_trade_value

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
            
            # Bug 1 fix: Deactivate signal immediately after opening trade
            signal.is_active = False
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
        alpaca_closed = False
        
        try:
            # Convert symbol format: "ETH/USD" -> "ETHUSD" for Alpaca
            alpaca_symbol = trade.symbol.replace("/", "")
            self.market.close_position(trade.agent_name, alpaca_symbol)
            alpaca_closed = True
        except Exception as e:
            error_msg = str(e)
            # If position not found, it's already closed - not an error
            if "Not Found" in error_msg or "404" in error_msg:
                self.log(f"Position {trade.symbol} already closed on Alpaca", "INFO")
                alpaca_closed = True  # Consider it closed
            else:
                self.log(f"Failed to close position on Alpaca: {e}", "ERROR")
        
        # Always update DB to prevent retry loops
        try:
            pnl = (price - trade.entry_price) * trade.qty
            if trade.side == "sell": pnl *= -1
            
            trade.exit_price = price
            trade.exit_time = datetime.utcnow()
            trade.status = "CLOSED"
            trade.pnl = pnl
            
            self.db.commit()
            
            # Deactivate signal so we don't re-enter immediately
            signal = self.db.get(StrategicSignal, trade.strategy_signal_id)
            if signal:
                signal.is_active = False
                self.db.commit()

            if alpaca_closed:
                self.log(f"Closed {trade.symbol} at {price}. PnL: {pnl:.2f}. Reason: {reason}")
        except Exception as e:
            self.log(f"Failed to update trade in DB: {e}", "ERROR")

