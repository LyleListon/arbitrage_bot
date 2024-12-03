import sqlite3
from decimal import Decimal

def init_db() -> None:
    conn = sqlite3.connect('arbitrage_bot.db')
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS trades")
        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                token_pair TEXT NOT NULL,
                exchange_from TEXT NOT NULL,
                exchange_to TEXT NOT NULL,
                amount_in REAL NOT NULL,
                amount_out REAL NOT NULL,
                profit REAL NOT NULL
            )
        """)

        sample_trades = [
            ('USDC/DAI', 'Uniswap', 'Sushiswap', 988.57075, 990.12, 1.55),
            ('DAI/WETH', 'Balancer', 'Curve', 600.63373, 601.23, 0.60),
            ('WETH/ETH', 'Uniswap', '1inch', 0.1, 0.1002, 0.0002),
            ('ETH/USDC', 'Sushiswap', 'Uniswap', 0.0051, 18.25, 0.04)
        ]
        cursor.executemany("INSERT INTO trades (token_pair, exchange_from, exchange_to, amount_in, amount_out, profit) VALUES (?, ?, ?, ?, ?, ?)", sample_trades)

        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
