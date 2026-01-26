"""
Test script to check all available timeframes on Alpaca Crypto API
"""
from datetime import datetime, timedelta
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# Initialize client (no auth needed for crypto data)
client = CryptoHistoricalDataClient()

# Test symbol
SYMBOL = "BTC/USD"

# All TimeFrame options with CORRECT syntax
timeframes = [
    ("1 Minute", TimeFrame(1, TimeFrameUnit.Minute)),
    ("5 Minutes", TimeFrame(5, TimeFrameUnit.Minute)),
    ("15 Minutes", TimeFrame(15, TimeFrameUnit.Minute)),
    ("30 Minutes", TimeFrame(30, TimeFrameUnit.Minute)),
    ("1 Hour", TimeFrame(1, TimeFrameUnit.Hour)),
    ("4 Hours", TimeFrame(4, TimeFrameUnit.Hour)),
    ("1 Day", TimeFrame(1, TimeFrameUnit.Day)),
    ("1 Week", TimeFrame(1, TimeFrameUnit.Week)),
]

print(f"Testing timeframes for {SYMBOL}...\n")
print("-" * 60)

for name, tf in timeframes:
    try:
        request = CryptoBarsRequest(
            symbol_or_symbols=[SYMBOL],
            timeframe=tf,
            start=datetime.utcnow() - timedelta(days=7),
            limit=50
        )
        bars = client.get_crypto_bars(request)
        
        if not bars.df.empty:
            count = len(bars.df)
            last_time = bars.df.index[-1][1]
            print(f"✅ {name:15} | Bars: {count:3} | Last: {last_time}")
        else:
            print(f"❌ {name:15} | No data returned")
            
    except Exception as e:
        print(f"❌ {name:15} | Error: {str(e)[:50]}")

print("-" * 60)
