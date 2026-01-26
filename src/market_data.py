from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from .config import Config
from datetime import datetime, timedelta

class MarketDataManager:
    def __init__(self):
        # Data client for market data
        self.data_client = CryptoHistoricalDataClient(Config.ALPACA_KEY_CLAUDE, Config.ALPACA_SECRET_CLAUDE)
        
        # Trading client for Claude agent
        self.client_claude = TradingClient(Config.ALPACA_KEY_CLAUDE, Config.ALPACA_SECRET_CLAUDE, paper=Config.PAPER_TRADING)

        self.clients = {
            "CLAUDE": self.client_claude
        }

    def get_account(self, agent_name):
        """Returns the Alpaca account object for the specific agent."""
        return self.clients[agent_name].get_account()

    def get_current_price(self, symbol):
        """Fetches the latest trade price for a symbol."""
        request_params = CryptoBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Minute,
            start=datetime.utcnow() - timedelta(minutes=15)
        )
        bars = self.data_client.get_crypto_bars(request_params)
        if not bars.df.empty:
            return bars.df.iloc[-1]['close']
        raise Exception(f"No price data found for {symbol}")


    def get_historical_data(self, symbol, timeframe_str="15Min", limit=100):
        """Fetches historical OHLCV data for AI analysis.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            timeframe_str: Timeframe string from config (e.g., "15Min", "1Hour")
            limit: Number of bars to fetch (100 at 15min = 25 hours of data)
        """
        # Parse timeframe string to TimeFrame object
        tf = self._parse_timeframe(timeframe_str)
        
        # Calculate start time based on timeframe and limit
        minutes_per_bar = self._get_minutes_per_bar(timeframe_str)
        start_time = datetime.utcnow() - timedelta(minutes=(limit + 10) * minutes_per_bar)

        request_params = CryptoBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=tf,
            start=start_time,
            limit=limit
        )
        bars = self.data_client.get_crypto_bars(request_params)
        return bars.df
    
    def _parse_timeframe(self, timeframe_str):
        """Convert config timeframe string to Alpaca TimeFrame object."""
        tf_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "30Min": TimeFrame(30, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "4Hour": TimeFrame(4, TimeFrameUnit.Hour),
            "1Day": TimeFrame(1, TimeFrameUnit.Day),
        }
        return tf_map.get(timeframe_str, TimeFrame(15, TimeFrameUnit.Minute))
    
    def _get_minutes_per_bar(self, timeframe_str):
        """Get minutes per bar for start time calculation."""
        minutes_map = {
            "1Min": 1,
            "5Min": 5,
            "15Min": 15,
            "30Min": 30,
            "1Hour": 60,
            "4Hour": 240,
            "1Day": 1440,
        }
        return minutes_map.get(timeframe_str, 15)


    def get_open_positions(self, agent_name):
        """Returns a list of open positions for the specific agent."""
        return self.clients[agent_name].get_all_positions()

    def _normalize_symbol(self, symbol):
        """Convert symbol format: 'ETH/USD' -> 'ETHUSD' for Alpaca API."""
        return symbol.replace("/", "")

    def has_position(self, agent_name, symbol):
        """Check if we have an open position for a symbol."""
        try:
            normalized = self._normalize_symbol(symbol)
            positions = self.get_open_positions(agent_name)
            for p in positions:
                if p.symbol == normalized:
                    return True
            return False
        except Exception:
            return False

    def get_position_side(self, agent_name, symbol):
        """Returns 'long', 'short', or None based on the current position."""
        try:
            normalized = self._normalize_symbol(symbol)
            positions = self.get_open_positions(agent_name)
            for p in positions:
                if p.symbol == normalized:
                    qty = float(p.qty)
                    if qty > 0:
                        return "long"
                    elif qty < 0:
                        return "short"
            return None
        except Exception:
            return None

    def submit_order(self, agent_name, symbol, qty, side):
        """Submits a market order for a specific agent."""
        # Normalize symbol for Alpaca
        normalized_symbol = self._normalize_symbol(symbol)
        
        market_order_data = MarketOrderRequest(
            symbol=normalized_symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        return self.clients[agent_name].submit_order(order_data=market_order_data)

    def close_position(self, agent_name, symbol):
        """Closes all positions for a symbol for a specific agent."""
        # Symbol should already be normalized when passed in
        normalized = self._normalize_symbol(symbol)
        return self.clients[agent_name].close_position(normalized)

