# AI Scalping Bot (Claude)

An AI-powered crypto scalping bot that uses Claude to analyze market data and execute paper trades on Alpaca.

## Prerequisites
- Python 3.10+
- Alpaca Paper Trading Account
- Anthropic Claude API Key

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your API keys:
```env
# Alpaca Paper Trading (for Claude agent)
ALPACA_API_KEY_CLAUDE=your_alpaca_key
ALPACA_SECRET_KEY_CLAUDE=your_alpaca_secret

# Claude AI
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: Paper trading mode (default: True)
PAPER_TRADING=True
```

> **Note**: The bot uses separate Alpaca accounts per agent. For Claude-only mode, you need `ALPACA_API_KEY_CLAUDE` and `ALPACA_SECRET_KEY_CLAUDE`.

## How to Run
```bash
python -m src.main
```

## How it Works

### Strategy Loop (Every 30 mins)
1. Fetches historical OHLCV data for crypto assets (BTC, ETH, SOL, AVAX, LINK)
2. Sends data to Claude for analysis
3. Claude returns trading signals with entry/exit prices
4. Signals are saved to SQLite database (`trading_bot.db`)

### Execution Loop (Every 10 seconds)
1. Monitors current market prices
2. If price matches entry conditions → executes trade
3. Manages Stop Loss and Take Profit automatically
4. Applies risk management guardrails (max 20% per trade, 5% hard stop loss)

## Trading Universe
- BTC/USD
- ETH/USD  
- SOL/USD
- AVAX/USD
- LINK/USD

## Risk Management
| Parameter | Value |
|-----------|-------|
| Max Position Size | 20% of equity |
| Hard Stop Loss | 5% per trade |
| Max Daily Loss | 5% of equity |

## Monitoring
- **Console logs**: Real-time activity
- **SQLite Database**: Inspect `trading_bot.db` with any SQLite viewer
  - `trades` table: All executed trades with PnL
  - `strategic_signals` table: AI-generated signals
  - `logs` table: System logs

## Project Structure
```
src/
├── main.py              # Entry point, runs strategy + execution loops
├── config.py            # Configuration and environment variables
├── database.py          # SQLAlchemy models and DB init
├── market_data.py       # Alpaca API wrapper for data + orders
├── execution_engine.py  # Trade execution and risk management
└── ai_agents/
    ├── base_agent.py    # Abstract base class
    ├── claude_agent.py  # Claude implementation
    └── prompts.py       # System prompts and response parsing
```

## Deployment
For hosting options:
- **VPS** (DigitalOcean/Vultr): ~$6/month
- **AWS EC2 Free Tier**: Free for 12 months
- **Railway.app**: $5/month with easy GitHub deploy
