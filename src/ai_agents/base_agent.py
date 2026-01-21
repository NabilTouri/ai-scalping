from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, symbol: str, market_data_df) -> dict:
        """
        Analyzes the market data and returns a structured signal.
        Args:
            symbol: e.g., 'BTC/USD'
            market_data_df: Pandas DataFrame with OHLCV data.
        Returns:
            dict with keys matching the response format (action, sentiment, etc.)
        """
        pass
