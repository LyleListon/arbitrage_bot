"""
Database module for arbitrage bot
"""
import sqlite3
import os


DB_FILE = 'arbitrage_bot.db'


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with required tables"""
    # Remove old database if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create trades table with all necessary fields
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  network TEXT,
                  timestamp INTEGER,
                  token_in TEXT,
                  token_out TEXT,
                  amount_in INTEGER,
                  amount_out INTEGER,
                  profit INTEGER,
                  gas_used INTEGER,
                  gas_price INTEGER,
                  success BOOLEAN,
                  tx_hash TEXT)''')
    
    # Create token pairs table
    c.execute('''CREATE TABLE IF NOT EXISTS token_pairs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  network TEXT,
                  symbol TEXT,
                  token_a TEXT,
                  token_b TEXT,
                  UNIQUE(network, symbol))''')
    
    # Create risk metrics table
    c.execute('''CREATE TABLE IF NOT EXISTS risk_metrics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp INTEGER,
                  gas_price INTEGER,
                  profit_multiplier REAL,
                  gas_multiplier REAL,
                  daily_volume INTEGER,
                  daily_trades INTEGER,
                  daily_profit INTEGER,
                  daily_losses INTEGER)''')
    
    conn.commit()
    conn.close()


def store_trade(trade_data):
    """Store trade data to database"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""INSERT INTO trades 
                 (network, timestamp, token_in, token_out,
                  amount_in, amount_out, profit,
                  gas_used, gas_price, success, tx_hash) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (trade_data['network'],
               trade_data['timestamp'],
               trade_data['token_in'],
               trade_data['token_out'],
               trade_data['amount_in'],
               trade_data['amount_out'],
               trade_data['profit'],
               trade_data.get('gas_used', 0),
               trade_data.get('gas_price', 0),
               trade_data.get('success', False),
               trade_data.get('tx_hash', '')))
    
    conn.commit()
    conn.close()


def get_token_pairs(network=None):
    """Get token pairs, optionally filtered by network"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if network:
        c.execute("""SELECT network, symbol, token_a, token_b 
                     FROM token_pairs WHERE network = ?""",
                  (network,))
    else:
        c.execute("SELECT network, symbol, token_a, token_b FROM token_pairs")
    
    pairs = [dict(row) for row in c.fetchall()]
    conn.close()
    return pairs


def add_token_pair(network, symbol, token_a, token_b):
    """Add a new token pair"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute("""INSERT INTO token_pairs 
                     (network, symbol, token_a, token_b) 
                     VALUES (?, ?, ?, ?)""",
                  (network, symbol, token_a, token_b))
        conn.commit()
        print(f"Added new token pair: {symbol} on {network}")
    except sqlite3.IntegrityError:
        print(f"Token pair {symbol} already exists on {network}")
    finally:
        conn.close()


def get_trades_in_time_period(network, start_time, end_time):
    """Get trades within specified time period"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT * FROM trades 
                 WHERE network = ? 
                 AND timestamp >= ? 
                 AND timestamp <= ?
                 ORDER BY timestamp DESC""",
              (network, start_time, end_time))
    
    trades = [dict(row) for row in c.fetchall()]
    conn.close()
    return trades


def get_trade_stats(network, start_time, end_time):
    """Get trade statistics for specified period"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT 
                   COUNT(*) as total_trades,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_trades,
                   SUM(profit) as total_profit,
                   SUM(gas_used * gas_price) as total_gas_cost
                 FROM trades 
                 WHERE network = ? 
                 AND timestamp >= ? 
                 AND timestamp <= ?""",
              (network, start_time, end_time))
    
    stats = dict(c.fetchone())
    conn.close()
    return stats


def store_risk_metrics(metrics):
    """Store risk management metrics"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""INSERT INTO risk_metrics 
                 (timestamp, gas_price, profit_multiplier,
                  gas_multiplier, daily_volume, daily_trades,
                  daily_profit, daily_losses)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (metrics['timestamp'],
               metrics['gas_price'],
               metrics['profit_multiplier'],
               metrics['gas_multiplier'],
               metrics['daily_volume'],
               metrics['daily_trades'],
               metrics['daily_profit'],
               metrics['daily_losses']))
    
    conn.commit()
    conn.close()


# Initialize the database
init_db()
