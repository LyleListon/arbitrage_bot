-- Network threshold settings table
CREATE TABLE IF NOT EXISTS network_thresholds (
    id INTEGER PRIMARY KEY,
    gas_price_threshold INTEGER NOT NULL DEFAULT 100000000000,  -- 100 gwei
    block_time_threshold INTEGER NOT NULL DEFAULT 15,           -- 15 seconds
    transaction_count_threshold INTEGER NOT NULL DEFAULT 1000,  -- 1000 tx per block
    connection_threshold INTEGER NOT NULL DEFAULT 5,            -- 5 seconds
    price_deviation_threshold REAL NOT NULL DEFAULT 0.03,       -- 3%
    error_rate_threshold REAL NOT NULL DEFAULT 0.10,           -- 10%
    last_updated INTEGER NOT NULL
);

-- Insert default values if not exists
INSERT OR IGNORE INTO network_thresholds (
    id,
    gas_price_threshold,
    block_time_threshold,
    transaction_count_threshold,
    connection_threshold,
    price_deviation_threshold,
    error_rate_threshold,
    last_updated
) VALUES (
    1,
    100000000000,
    15,
    1000,
    5,
    0.03,
    0.10,
    strftime('%s', 'now')
);
