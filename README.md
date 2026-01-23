# AI Scalping Bot (Claude)

Anthropic Claude-driven crypto scalping bot for Alpaca **paper trading**. The bot generates signals with Claude and executes them through Alpaca, persisting everything to a local SQLite database. Designed for experimentation and monitoring; not financial advice.

## Features
- Single Claude agent (`claude-3-haiku-20240307`) generates structured JSON signals.
- Strategy loop (every 30 minutes) fetches Alpaca crypto bars and stores signals in `strategic_signals`.
- Execution loop (every 10 seconds) checks active signals vs live prices and sends market orders.
- Risk rails: max 20% equity per trade, 5% hard stop loss, optional stop-loss / take-profit from the signal.
- Assets: BTC/USD, ETH/USD, SOL/USD, AVAX/USD (Alpaca crypto symbols).
- Persistence: SQLite `trading_bot.db` with `trades`, `strategic_signals`, and `logs` tables.

## Prerequisites
- Python 3.10+
- Alpaca account with paper trading enabled (crypto access)
- Anthropic API key

## Quickstart
1) Install deps
```bash
pip install -r requirements.txt
```

2) Configure environment (`.env` in repo root)
```env
ALPACA_API_KEY_CLAUDE=pk_xxx
ALPACA_SECRET_KEY_CLAUDE=sk_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
PAPER_TRADING=True  # default True; set False to hit live Alpaca (at your own risk)
```
`Config.validate()` runs on import and will print a configuration error if any key is missing. Execution will still start, but Alpaca/Anthropic calls will fail, so keep the file complete.

3) Run locally (paper mode)
```bash
python -m src.main
```

## How It Works
- **Strategy thread**: Every `STRATEGY_UPDATE_INTERVAL` (30m), pulls recent 1m bars from Alpaca for each symbol, sends the last 20 rows to Claude with the system prompt in src/ai_agents/prompts.py, and stores a single active signal per agent/symbol.
- **Execution loop**: Every 10s, reads active signals, fetches current price, checks entry bounds, sizes position by `MAX_POSITION_SIZE_PERCENT` (20% of equity, capped by buying power), and submits a market order via Alpaca. Open trades are monitored for SL/TP and the hard 5% backstop.
- **Database**: SQLite at `trading_bot.db` (see src/database.py) holds signals, trades, and logs. Signals are deactivated when replaced or when their linked trade is closed.

## Configuration Reference (src/config.py)
- `ALPACA_API_KEY_CLAUDE`, `ALPACA_SECRET_KEY_CLAUDE`: Alpaca keys used for both data and trading.
- `ANTHROPIC_API_KEY`: Claude API key.
- `PAPER_TRADING`: bool, defaults to `True`; controls Alpaca base URL.
- `TRADING_UNIVERSE`: ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD"].
- `TIMEFRAME`: string used in logging (data fetch uses 1m bars for compatibility).
- Risk params: `MAX_POSITION_SIZE_PERCENT=0.20`, `MAX_DAILY_LOSS_PERCENT=0.05`, `HARD_STOP_LOSS_PERCENT=0.05`.
- `DATABASE_URL`: `sqlite:///trading_bot.db`.

## Monitoring & Data
- Stdout logs from strategy/execution loops.
- Inspect SQLite directly:
```bash
sqlite3 trading_bot.db
.tables
SELECT * FROM strategic_signals LIMIT 5;
```

## Deployment
- Local: run `python -m src.main` after creating `.env`.
- VPS/Docker: see docs/DEPLOYMENT.md for the automated Docker-based flow.

## Important Notes
- The code submits **market orders** to Alpaca. Keep `PAPER_TRADING=True` unless you fully understand the risk.
- Claude output is parsed as JSON; malformed responses fall back to a HOLD signal.
- This project is for research/experimentation only and provides no guarantees of profit or safety.
