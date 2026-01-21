# AI Scalping Bot (Gemini vs Claude)

This project runs two AI agents (Gemini and Claude) that compete to trade crypto on a paper trading account.

## Prerequisites
- Python 3.10+
- Alpaca Paper Trading Account
- Google Gemini API Key
- Anthropic Claude API Key

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: manual install was done: `pip install alpaca-py google-generativeai anthropic pandas sqlalchemy python-dotenv nest_asyncio`)*

2. **Configuration**:
   Ensure your `.env` file is set up with:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `GEMINI_API_KEY`
   - `ANTHROPIC_API_KEY`

## How to Run
Run the main script to start the bot:

```bash
python -m src.main
```

## How it Works
1. **Strategy Loop (Every 30 mins)**:
   - Fetches historical data for BTC, ETH, SOL, etc.
   - Sends data to Gemini and Claude.
   - Saves their "Signals" to the local SQLite database (`trading_bot.db`).

2. **Execution Loop (Real-time)**:
   - Monitors the market price.
   - If a signal matches entry conditions (e.g. Price < Entry Limit), it executes a trade.
   - Manages Stop Loss and Take Profit automatically.

## Monitoring
- Check the console logs for activity.
- Inspect `trading_bot.db` using a SQLite viewer to see `trades` and `strategic_signals`.
