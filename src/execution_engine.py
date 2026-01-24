from datetime import datetime
from sqlalchemy.orm import Session
from .database import Trade, StrategicSignal
from .market_data import MarketDataManager
from .config import Config
from .logger import execution_logger as logger


class ExecutionEngine:
    def __init__(self, db_session: Session, market_manager: MarketDataManager):
        self.db = db_session
        self.market = market_manager

    def process_signals(self):
        """Checks all active 'StrategicSignals' against current market data."""
        active_signals = self.db.query(StrategicSignal).filter(StrategicSignal.is_active == True).all()
        
        for signal in active_signals:
            try:
                self._evaluate_signal(signal)
            except Exception as e:
                logger.error(f"Error evaluating signal {signal.id}: {e}")

    def _evaluate_signal(self, signal: StrategicSignal):
        # Skip if confidence is too low
        if signal.confidence is not None and signal.confidence < Config.MIN_CONFIDENCE:
            return
        
        # Check if we already have an open trade for this signal
        existing_trade = self.db.query(Trade).filter(
            Trade.strategy_signal_id == signal.id,
            Trade.status == "OPEN"
        ).first()

        current_price = self.market.get_current_price(signal.target_symbol)
        has_position = self.market.has_position(signal.agent_name, signal.target_symbol)
        
        # LOGIC: ENTRY (no existing trade from this signal)
        if not existing_trade:
            position_side = self.market.get_position_side(signal.agent_name, signal.target_symbol)
            # position_side: "long", "short", or None
            
            if signal.action == "BUY":
                # If we have a short position, close it first
                if position_side == "short":
                    self._close_position_for_symbol(signal, current_price)
                # If no position, open a long
                elif position_side is None:
                    below_max = (current_price <= signal.entry_price_max) if signal.entry_price_max else True
                    above_min = (current_price >= signal.entry_price_min) if signal.entry_price_min else True
                    if below_max and above_min:
                        self._execute_entry(signal, current_price, "buy")
                # If already long, do nothing
            
            elif signal.action == "SELL":
                # If we have a long position, close it first
                if position_side == "long":
                    self._close_position_for_symbol(signal, current_price)
                # If no position, open a short
                elif position_side is None:
                    below_max = (current_price <= signal.entry_price_max) if signal.entry_price_max else True
                    above_min = (current_price >= signal.entry_price_min) if signal.entry_price_min else True
                    if below_max and above_min:
                        self._execute_entry(signal, current_price, "sell")
                # If already short, do nothing

        # LOGIC: EXIT (Stop Loss / Take Profit for existing trade)
        else:
            self._manage_open_trade(existing_trade, current_price, signal)



    def _execute_entry(self, signal, price, side):
        account = self.market.get_account(signal.agent_name)
        equity = float(account.equity)
        buying_power = float(account.buying_power)
        
        MIN_TRADE_PERCENT = 0.05
        min_trade_value = equity * MIN_TRADE_PERCENT
        
        if buying_power < min_trade_value:
            logger.warning(f"Insufficient buying power: ${buying_power:.2f} < {MIN_TRADE_PERCENT*100}% of equity")
            signal.is_active = False
            self.db.commit()
            return
        
        trade_amount = equity * Config.MAX_POSITION_SIZE_PERCENT
        
        if trade_amount > buying_power:
            trade_amount = buying_power * 0.95

        if trade_amount < min_trade_value:
            trade_amount = min_trade_value

        qty = trade_amount / price
        
        # Send Order to Alpaca
        try:
            order = self.market.submit_order(signal.agent_name, signal.target_symbol, qty, side)
            logger.info(f"Executed {side.upper()} {signal.target_symbol} at {price} (Qty: {qty:.4f})")
            
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
            signal.is_active = False
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Order Failed: {e}")
            signal.is_active = False
            self.db.commit()

    def _manage_open_trade(self, trade, current_price, signal):
        if signal.stop_loss:
            if trade.side == "buy" and current_price <= signal.stop_loss:
                self._close_trade(trade, current_price, "Hit Stop Loss")
                return
            if trade.side == "sell" and current_price >= signal.stop_loss:
                self._close_trade(trade, current_price, "Hit Stop Loss")
                return

        if signal.take_profit:
            if trade.side == "buy" and current_price >= signal.take_profit:
                self._close_trade(trade, current_price, "Hit Take Profit")
                return
            if trade.side == "sell" and current_price <= signal.take_profit:
                self._close_trade(trade, current_price, "Hit Take Profit")
                return

        pnl_pct = (current_price - trade.entry_price) / trade.entry_price
        if trade.side == "sell": pnl_pct *= -1
        
        if pnl_pct <= -Config.HARD_STOP_LOSS_PERCENT:
            self._close_trade(trade, current_price, "Hard Stop Loss Triggered")

    def _close_position_for_symbol(self, signal, current_price):
        """Close an existing position when Claude says SELL and we have a long position."""
        # Find the open trade for this symbol
        open_trade = self.db.query(Trade).filter(
            Trade.symbol == signal.target_symbol,
            Trade.status == "OPEN"
        ).first()
        
        if open_trade:
            self._close_trade(open_trade, current_price, "SELL signal from Claude")
            signal.is_active = False
            self.db.commit()
        else:
            # No trade in DB but Alpaca has position - close directly
            try:
                alpaca_symbol = signal.target_symbol.replace("/", "")
                self.market.close_position(signal.agent_name, alpaca_symbol)
                logger.info(f"Closed {signal.target_symbol} at {current_price} (SELL signal)")
                signal.is_active = False
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to close position {signal.target_symbol}: {e}")

    def _close_trade(self, trade, price, reason):

        alpaca_closed = False
        
        try:
            alpaca_symbol = trade.symbol.replace("/", "")
            self.market.close_position(trade.agent_name, alpaca_symbol)
            alpaca_closed = True
        except Exception as e:
            error_msg = str(e)
            if "Not Found" in error_msg or "404" in error_msg:
                logger.info(f"Position {trade.symbol} already closed on Alpaca")
                alpaca_closed = True
            else:
                logger.error(f"Failed to close position on Alpaca: {e}")
        
        try:
            pnl = (price - trade.entry_price) * trade.qty
            if trade.side == "sell": pnl *= -1
            
            trade.exit_price = price
            trade.exit_time = datetime.utcnow()
            trade.status = "CLOSED"
            trade.pnl = pnl
            
            self.db.commit()
            
            signal = self.db.get(StrategicSignal, trade.strategy_signal_id)
            if signal:
                signal.is_active = False
                self.db.commit()

            if alpaca_closed:
                logger.info(f"Closed {trade.symbol} at {price}. PnL: {pnl:.2f}. Reason: {reason}")
        except Exception as e:
            logger.error(f"Failed to update trade in DB: {e}")
