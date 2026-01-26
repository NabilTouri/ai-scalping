import anthropic
from ..config import Config
from .base_agent import BaseAgent
from .prompts import SYSTEM_PROMPT, parse_ai_response
import pandas as pd

class ClaudeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CLAUDE")
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = Config.CLAUDE_MODEL

    def analyze(self, symbol: str, market_data_df: pd.DataFrame) -> dict:
        recent_data = market_data_df.tail(20).to_string()
        
        user_message = f"""
        Analyze current market data for {symbol}.
        
        Recent OHLCV Data:
        {recent_data}
        
        Provide your trading decision in JSON.
        """
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=Config.CLAUDE_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            response_text = message.content[0].text
            return parse_ai_response(response_text)
        except Exception as e:
            print(f"Claude API Error: {e}")
            return {"action": "HOLD", "reasoning": f"API Error: {e}"}
