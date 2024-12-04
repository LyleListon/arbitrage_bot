"""Initialize database with required tables"""

import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def init_database(db_path: str = 'arbitrage_bot.db') -> None:
    """Initialize database with required tables"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create dex_prices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dex_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_pair TEXT NOT NULL,
            dex TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create trades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_pair TEXT NOT NULL,
            exchange_from TEXT NOT NULL,
            exchange_to TEXT NOT NULL,
            amount_in REAL NOT NULL,
            amount_out REAL NOT NULL,
            profit REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create opportunity_scores table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunity_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_pair TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create opportunity_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunity_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_pair TEXT NOT NULL,
            spread_percent REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create risk_metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create system_metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_percent REAL NOT NULL,
            memory_percent REAL NOT NULL,
            network_sent REAL NOT NULL,
            network_recv REAL NOT NULL,
            active_connections INTEGER NOT NULL,
            error_rate REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        # Create system_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')

        conn.commit()
        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
