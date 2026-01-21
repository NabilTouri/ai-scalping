import google.generativeai as genai
from ..config import Config
from .base_agent import BaseAgent
from .prompts import SYSTEM_PROMPT, parse_ai_response
import pandas as pd

class GeminiAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GEMINI")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # Using Gemini 2.0 Flash for speed/cost or Pro for reasoning
        # "gemini-2.0-flash-exp" is great, fallback to "gemini-1.5-pro" if needed
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=SYSTEM_PROMPT)

    def analyze(self, symbol: str, market_data_df: pd.DataFrame) -> dict:
        # Format data for the prompt
        # We take the last 20 candles to keep prompt small but context rich
        recent_data = market_data_df.tail(20).to_string()
        
        user_prompt = f"""
        Analyze current market data for {symbol}.
        
        Recent OHLCV Data:
        {recent_data}
        
        Provide your trading decision in JSON.
        """
        
        try:
            response = self.model.generate_content(user_prompt)
            return parse_ai_response(response.text)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return {"action": "HOLD", "reasoning": f"API Error: {e}"}
