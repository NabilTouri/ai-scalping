
import unittest
from unittest.mock import MagicMock
from src.execution_engine import ExecutionEngine
from src.database import StrategicSignal, Trade
from src.config import Config

class TestExecutionEngine(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_market = MagicMock()
        self.engine = ExecutionEngine(self.mock_db, self.mock_market)
        
        # Setup common mock behaviors
        self.mock_market.get_current_price.return_value = 100.0
        self.mock_market.get_account.return_value.equity = 10000.0
        self.mock_market.get_account.return_value.buying_power = 10000.0

    def test_infinite_loop_sell_no_position(self):
        # Create a signal that causes the issue: SELL action, but no position exists
        signal = StrategicSignal(
            id=1,
            agent_name="CLAUDE",
            target_symbol="ETH/USD",
            action="SELL",
            is_active=True,
            confidence=0.9
        )
        
        # Mock DB query to return this signal
        self.mock_db.query.return_value.filter.return_value.all.return_value = [signal]
        
        # Mock no existing trade in DB
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock no position in Market (Alpaca)
        self.mock_market.has_position.return_value = False
        self.mock_market.get_position_side.return_value = None
        
        # Run process_signals
        print("Running process_signals...")
        self.engine.process_signals()
        
        # VERIFICATION
        # The bug is that signal.is_active remains True.
        # The fix should set signal.is_active = False.
        
        if signal.is_active:
             print("FAIL: Signal is still active! Infinite loop condition persists.")
        else:
             print("PASS: Signal was deactivated.")

if __name__ == '__main__':
    # Run the specific test case
    t = TestExecutionEngine()
    t.setUp()
    t.test_infinite_loop_sell_no_position()
