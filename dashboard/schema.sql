-- Trade history table
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    token_in TEXT NOT NULL,
    token_out TEXT NOT NULL,
    amount_in DECIMAL(18,8) NOT NULL,
    amount_out DECIMAL(18,8) NOT NULL,
    profit DECIMAL(18,8) NOT NULL,
    gas_used INTEGER NOT NULL,
    tx_hash TEXT NOT NULL UNIQUE
);

-- Bot parameters history
CREATE TABLE IF NOT EXISTS parameter_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,
    old_value TEXT NOT NULL,
    new_value TEXT NOT NULL,
    tx_hash TEXT NOT NULL
);

-- Gas price history
CREATE TABLE IF NOT EXISTS gas_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    gas_price DECIMAL(18,8) NOT NULL
);

-- Token price history
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    token_address TEXT NOT NULL,
    price DECIMAL(18,8) NOT NULL
);

-- Create bot_status table
CREATE TABLE IF NOT EXISTS bot_status (
    id INTEGER PRIMARY KEY,
    is_running BOOLEAN NOT NULL DEFAULT 0,
    last_update INTEGER NOT NULL DEFAULT 0
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_profit ON trades(profit);
CREATE INDEX IF NOT EXISTS idx_parameter_history_timestamp ON parameter_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_gas_history_timestamp ON gas_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_price_history_token ON price_history(token_address);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS hourly_profits AS
SELECT 
    strftime('%Y-%m-%d %H:00:00', datetime(timestamp, 'unixepoch')) as hour,
    SUM(profit) as total_profit,
    COUNT(*) as trade_count,
    AVG(gas_used) as avg_gas_used
FROM trades
GROUP BY hour
ORDER BY hour DESC;

CREATE VIEW IF NOT EXISTS daily_profits AS
SELECT 
    strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as date,
    SUM(profit) as total_profit,
    COUNT(*) as trade_count,
    AVG(gas_used) as avg_gas_used
FROM trades
GROUP BY date
ORDER BY date DESC;
