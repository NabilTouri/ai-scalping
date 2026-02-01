# AI Trading Bot

Claude-powered crypto scalping bot for Alpaca **paper trading**. Generates trading signals with Claude AI, executes through Alpaca, and provides a real-time web dashboard.

## Features

### Trading Engine
- **AI Agent**: Claude 3 Haiku generates structured JSON signals (BUY/SELL/HOLD)
- **Strategy Loop**: Every 30 minutes, fetches Alpaca crypto bars and stores signals
- **Execution Loop**: Every 10 seconds, checks signals vs live prices and executes market orders
- **Symmetric Logic**: SELL closes long positions, BUY closes short positions
- **Assets**: BTC/USD, ETH/USD

### Risk Management
- Max 20% equity per trade
- 5% hard stop loss
- Minimum 60% AI confidence threshold
- Optional stop-loss / take-profit from AI signals

### Dashboard
- Real-time web UI at `http://localhost:8080`
- Live/Offline bot status via heartbeat system
- Total PnL, win rate, open positions
- Recent signals with AI reasoning
- Trade history with entry/exit prices
- Filterable logs (by source, symbol, level)

### Database
SQLite with tables:
- `trades` - All executed trades
- `strategic_signals` - AI-generated signals with `price_at_signal` for accuracy analysis
- `logs` - System logs with timestamp, source, symbol
- `bot_status` - Heartbeat for real-time status

## Prerequisites
- Python 3.10+
- Alpaca account with paper trading enabled (crypto access)
- Anthropic API key

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
Create `.env` in repo root:
```env
ALPACA_API_KEY_CLAUDE=pk_xxx
ALPACA_SECRET_KEY_CLAUDE=sk_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
PAPER_TRADING=True
```

### 3. Run locally
```bash
# Terminal 1 - Bot
python -m src.main

# Terminal 2 - Dashboard
uvicorn src.dashboard:app --reload --port 8080
```

Open http://localhost:8080 to view the dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         MAIN.PY                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐          ┌──────────────────┐              │
│  │ Strategy    │  30 min  │ Claude Agent     │              │
│  │ Loop        │ ───────▶ │ (claude_agent.py)│              │
│  └─────────────┘          └──────────────────┘              │
│         │                          │                         │
│         ▼                          ▼                         │
│  ┌─────────────┐          ┌──────────────────┐              │
│  │ Execution   │  10 sec  │ Market Data      │              │
│  │ Loop        │ ◀──────▶ │ (market_data.py) │              │
│  └─────────────┘          └──────────────────┘              │
│         │                          │                         │
│         ▼                          ▼                         │
│  ┌─────────────────────────────────────────────┐            │
│  │              SQLite Database                 │            │
│  │  trades | strategic_signals | logs | status  │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DASHBOARD.PY                            │
│  FastAPI + Static HTML/CSS/JS                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ /api/stats | /api/positions | /api/signals             │ │
│  │ /api/trades | /api/logs | /api/health                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Configuration (src/config.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `TRADING_UNIVERSE` | BTC/USD, ETH/USD | Assets to trade |
| `STRATEGY_UPDATE_INTERVAL` | 30 min | AI analysis frequency |
| `MAX_POSITION_SIZE_PERCENT` | 20% | Max equity per trade |
| `HARD_STOP_LOSS_PERCENT` | 5% | Force close threshold |
| `MIN_CONFIDENCE` | 60% | Skip low confidence signals |
| `DATABASE_URL` | sqlite:///data/trading_bot.db | Database location |

## Deployment

### Local Development
```bash
python -m src.main
uvicorn src.dashboard:app --reload --port 8080
```

### Docker (Production)
See `docs/DEPLOYMENT.md` for DigitalOcean droplet setup.

```bash
docker compose up -d
docker compose logs -f trading-bot
```

## Project Structure
```
ai-scalping/
├── src/
│   ├── main.py              # Entry point, loops
│   ├── config.py            # Configuration
│   ├── database.py          # SQLAlchemy models
│   ├── execution_engine.py  # Trade execution logic
│   ├── market_data.py       # Alpaca data fetching
│   ├── logger.py            # DB + console logging
│   ├── dashboard.py         # FastAPI web server
│   ├── ai_agents/
│   │   ├── claude_agent.py  # Claude AI integration
│   │   └── prompts.py       # AI system prompts
│   └── static/
│       ├── index.html       # Dashboard frontend
│       └── styles.css       # Dashboard styling
├── data/                    # SQLite database
├── docs/                    # Documentation
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # Bot container
└── Dockerfile.dashboard     # Dashboard container
```

## Important Notes

⚠️ **Paper Trading Only**: Keep `PAPER_TRADING=True` unless you understand the risks.

⚠️ **Market Orders**: The bot submits market orders to Alpaca.

⚠️ **No Guarantees**: This is research/experimentation software. No profit guarantees.

## License

MIT - For educational purposes only.
