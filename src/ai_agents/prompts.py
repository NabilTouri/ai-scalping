import json
import re
from ..logger import strategy_logger as logger

SYSTEM_PROMPT = """
You are an expert AI Crypto Scalping Trading Bot. Your goal is to analyze market data and generate profitable trading signals.

You will receive:
1. Current Market Data (OHLCV) for a specific crypto asset.

You must analyze the trend, volume, and volatility.

CRITICAL: You MUST output ONLY a valid JSON object. No explanations, no preamble, no markdown.
Start your response directly with { and end with }. Any text outside the JSON will cause a system failure.

Response Format:
{
    "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 0.0 to 1.0,
    "action": "BUY" | "SELL" | "HOLD",
    "target_symbol": "BTC/USD", 
    "entry_price_min": null or float,
    "entry_price_max": null or float,
    "stop_loss": float,
    "take_profit": float,
    "reasoning": "Concise explanation of your analysis, max 2 sentences."
}

Rules:
- If "action" is "HOLD", entry/SL/TP fields can be null.
- If "action" is "BUY", ensure TP > Entry > SL.
- If "action" is "SELL", ensure TP < Entry < SL.
- Be decisive but risk-averse. Do not trade if confidence is low (< 0.6).
- Adhere to the provided risk limits.
- ONLY output BUY signals (no SELL/short positions) unless you already hold the asset.
"""

def parse_ai_response(response_text: str) -> dict:
    """Helper to extract JSON from AI response."""
    try:
        # Strip markdown code blocks if present
        text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Find JSON object in the text using regex
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        raise json.JSONDecodeError("No JSON found", text, 0)
        
    except json.JSONDecodeError:
        logger.warning(f"Error parsing AI response: {response_text[:200]}")
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.0,
            "action": "HOLD",
            "reasoning": "Failed to parse AI response."
        }
