
import sqlite3
import pandas as pd

DB_PATH = "trading_bot_server.db"

def analyze_db():
    conn = sqlite3.connect(DB_PATH)
    
    print("=== AI TRADING BOT - DEEP ANALYSIS REPORT ===\n")
    
    # --- 1. FINANCIAL ANALYSIS ---
    print("## 1. FINANCIAL PERFORMANCE")
    try:
        trades = pd.read_sql_query("SELECT * FROM trades", conn)
        if not trades.empty:
            closed_trades = trades[trades['status'] == 'CLOSED']
            if not closed_trades.empty:
                total_pnl = closed_trades['pnl'].sum()
                win_count = len(closed_trades[closed_trades['pnl'] > 0])
                loss_count = len(closed_trades[closed_trades['pnl'] <= 0])
                total_count = len(closed_trades)
                win_rate = (win_count / total_count) * 100
                
                avg_win = closed_trades[closed_trades['pnl'] > 0]['pnl'].mean() if win_count > 0 else 0
                avg_loss = closed_trades[closed_trades['pnl'] <= 0]['pnl'].mean() if loss_count > 0 else 0
                profit_factor = abs(closed_trades[closed_trades['pnl'] > 0]['pnl'].sum() / closed_trades[closed_trades['pnl'] <= 0]['pnl'].sum()) if loss_count > 0 else float('inf')

                print(f"- Total PnL: ${total_pnl:.2f}")
                print(f"- Win Rate: {win_rate:.1f}% ({win_count}W / {loss_count}L)")
                print(f"- Profit Factor: {profit_factor:.2f}")
                print(f"- Avg Win: ${avg_win:.2f}")
                print(f"- Avg Loss: ${avg_loss:.2f}")
                print(f"- Total Trades: {total_count}")
                
                # Duration analysis
                closed_trades['entry_time'] = pd.to_datetime(closed_trades['entry_time'])
                closed_trades['exit_time'] = pd.to_datetime(closed_trades['exit_time'])
                closed_trades['duration'] = closed_trades['exit_time'] - closed_trades['entry_time']
                print(f"- Avg Trade Duration: {closed_trades['duration'].mean()}")
            else:
                print("No closed trades to analyze.")
                
            open_trades = trades[trades['status'] == 'OPEN']
            print(f"- Open Positions: {len(open_trades)}")
            if not open_trades.empty:
                print(open_trades[['symbol', 'side', 'entry_price', 'qty']].to_string(index=False))
        else:
            print("No trades found in database.")
    except Exception as e:
        print(f"Error analyzing financials: {e}")

    # --- 2. TECHNICAL ANALYSIS ---
    print("\n## 2. TECHNICAL HEALTH")
    try:
        # Signal Consistency
        signals = pd.read_sql_query("SELECT * FROM strategic_signals", conn)
        signals['timestamp'] = pd.to_datetime(signals['timestamp'])
        
        if not signals.empty:
            sig_count = len(signals)
            last_sig = signals.iloc[0]['timestamp']
            first_sig = signals.iloc[-1]['timestamp']
            # Sort by timestamp ascending for plotting logic if needed, but here just descriptive
            signals_sorted = signals.sort_values('timestamp')
            
            # Check gap between signals
            signals_sorted['delta'] = signals_sorted['timestamp'].diff()
            avg_gap = signals_sorted['delta'].mean()
            max_gap = signals_sorted['delta'].max()
            
            print(f"- Total AI Signals: {sig_count}")
            print(f"- Signal Frequency: Avg every {avg_gap}")
            print(f"- Max Silence: {max_gap}")
            
            # Action distribution
            print("- Action Distribution:")
            print(signals['action'].value_counts().to_string())
        
        # Log Analysis
        logs = pd.read_sql_query("SELECT * FROM logs", conn)
        if not logs.empty:
            error_logs = logs[logs['level'] == 'ERROR']
            warn_logs = logs[logs['level'] == 'WARNING']
            print(f"\n- Total Logs: {len(logs)}")
            print(f"- Error Count: {len(error_logs)}")
            print(f"- Warning Count: {len(warn_logs)}")
            
            if not error_logs.empty:
                print("\nMost Recent Errors:")
                print(error_logs[['timestamp', 'message']].head(5).to_string(index=False))
                
            # Check for specific "No position" spam pattern frequency
            spam_logs = logs[logs['message'].str.contains("No existing position", na=False)]
            if not spam_logs.empty:
                print(f"\n- 'No existing position' Spam Count: {len(spam_logs)}")
                print("  (This indicates the bug presence duration)")
    except Exception as e:
        print(f"Error analyzing technicals: {e}")
        
    conn.close()

if __name__ == "__main__":
    analyze_db()
