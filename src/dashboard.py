"""
Dashboard Web per AI Trading Bot
FastAPI application per monitorare il bot in tempo reale
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import desc
from datetime import datetime, timedelta
import os

from .config import Config

# Import database from shared module (uses same config)
from .database import SessionLocal, Trade, StrategicSignal, Log, BotStatus, init_db

# Initialize database tables on startup
# init_db()  # Handled by main bot

# Alpaca client for live positions
try:
    from .market_data import MarketDataManager
    market = MarketDataManager()
except Exception as e:
    print(f"Warning: Could not initialize market data: {e}")
    market = None

app = FastAPI(title="AI Trading Dashboard")

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def root():
    """Serve the main dashboard page"""
    return FileResponse(os.path.join(static_path, "index.html"))


@app.get("/api/stats")
async def get_stats():
    """Get aggregate trading statistics"""
    db = SessionLocal()
    try:
        # Total trades
        total_trades = db.query(Trade).count()
        closed_trades = db.query(Trade).filter(Trade.status == "CLOSED").all()
        
        # Calculate PnL
        total_pnl = sum(t.pnl or 0 for t in closed_trades)
        winning_trades = len([t for t in closed_trades if (t.pnl or 0) > 0])
        losing_trades = len([t for t in closed_trades if (t.pnl or 0) < 0])
        
        # Win rate
        win_rate = (winning_trades / len(closed_trades) * 100) if closed_trades else 0
        
        # Active signals
        active_signals = db.query(StrategicSignal).filter(StrategicSignal.is_active == True).count()
        
        # Open positions
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").count()
        
        return {
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "open_positions": open_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 1),
            "active_signals": active_signals
        }
    finally:
        db.close()


@app.get("/api/positions")
async def get_positions():
    """Get current open positions from Alpaca"""
    if not market:
        return {"positions": [], "error": "Market data unavailable"}
    
    try:
        # Get positions using public method
        positions = market.get_open_positions("CLAUDE")
        return {
            "positions": [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "avg_entry": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "unrealized_pnl": float(p.unrealized_pl),
                    "unrealized_pnl_pct": float(p.unrealized_plpc) * 100
                }
                for p in positions
            ]
        }
    except Exception as e:
        return {"positions": [], "error": str(e)}


@app.get("/api/trades")
async def get_trades(limit: int = 20):
    """Get recent trades from database"""
    db = SessionLocal()
    try:
        trades = db.query(Trade).order_by(desc(Trade.entry_time)).limit(limit).all()
        return {
            "trades": [
                {
                    "id": t.id,
                    "agent": t.agent_name,
                    "symbol": t.symbol,
                    "side": t.side,
                    "qty": round(t.qty, 4),
                    "entry_price": round(t.entry_price, 2),
                    "exit_price": round(t.exit_price, 2) if t.exit_price else None,
                    "status": t.status,
                    "pnl": round(t.pnl, 2) if t.pnl else None,
                    "entry_time": t.entry_time.isoformat() if t.entry_time else None,
                    "exit_time": t.exit_time.isoformat() if t.exit_time else None
                }
                for t in trades
            ]
        }
    finally:
        db.close()


@app.get("/api/signals")
async def get_signals(limit: int = 20):
    """Get recent strategic signals"""
    db = SessionLocal()
    try:
        signals = db.query(StrategicSignal).order_by(desc(StrategicSignal.timestamp)).limit(limit).all()
        return {
            "signals": [
                {
                    "id": s.id,
                    "agent": s.agent_name,
                    "symbol": s.target_symbol,
                    "action": s.action,
                    "sentiment": s.sentiment,
                    "confidence": round(s.confidence, 2) if s.confidence else 0,
                    "reasoning": s.reasoning,
                    "is_active": s.is_active,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None
                }
                for s in signals
            ]
        }
    finally:
        db.close()


@app.get("/api/logs")
async def get_logs(
    limit: int = 50,
    source: str = None,  # BOT, EXECUTION, STRATEGY
    symbol: str = None,  # BTC/USD, ETH/USD
    level: str = None,   # INFO, WARNING, ERROR
):
    """Get recent logs with optional filters"""
    db = SessionLocal()
    try:
        query = db.query(Log)
        
        # Apply filters
        if source:
            query = query.filter(Log.source == source)
        if symbol:
            query = query.filter(Log.symbol == symbol)
        if level:
            query = query.filter(Log.level == level)
        
        logs = query.order_by(desc(Log.timestamp)).limit(limit).all()
        return {
            "logs": [
                {
                    "id": l.id,
                    "level": l.level,
                    "source": l.source,
                    "symbol": l.symbol,
                    "message": l.message,
                    "timestamp": l.timestamp.isoformat() if l.timestamp else None
                }
                for l in logs
            ]
        }
    finally:
        db.close()



@app.get("/api/health")
async def health_check():
    """Health check endpoint - verifies bot is running via heartbeat"""
    db = SessionLocal()
    try:
        status = db.query(BotStatus).filter(BotStatus.bot_name == "MAIN").first()
        
        if status and status.last_heartbeat:
            seconds_since_heartbeat = (datetime.utcnow() - status.last_heartbeat).total_seconds()
            bot_active = seconds_since_heartbeat < Config.HEARTBEAT_TIMEOUT
        else:
            bot_active = False
        
        return {
            "status": "ok",
            "bot_active": bot_active,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
