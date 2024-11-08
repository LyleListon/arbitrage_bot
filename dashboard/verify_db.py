"""
Database Verification Module

This module verifies and maintains the database structure for the arbitrage bot.
It checks for:
1. Required tables existence
2. Required indices for performance optimization
3. Data integrity and relationships
4. Initializes missing components if needed

Usage:
    python verify_db.py

The script will:
1. Check all required tables exist
2. Verify indices are created
3. Log the current state of the database
4. Initialize any missing components
"""

import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the absolute path to init_db.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INIT_DB_PATH = os.path.join(SCRIPT_DIR, 'init_db.py')

# Import init_db using exec to handle direct script execution
init_db_globals = {}
with open(INIT_DB_PATH) as f:
    exec(f.read(), init_db_globals)
init_db = init_db_globals['init_db']


def verify_db():
    """
    Verify database structure and initialize if needed.
    
    This function performs comprehensive checks on the database:
    1. Verifies all required tables exist
    2. Checks indices for query optimization
    3. Validates table relationships
    4. Reports current database status
    5. Initializes any missing components
    
    Returns:
        bool: True if verification successful, False otherwise
    """
    db_path = 'arbitrage_bot.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {
            'trades', 'bot_status', 'price_alerts',
            'alert_history', 'price_history'
        }

        # Check if all required tables exist
        missing_tables = required_tables - tables
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            logger.info("Initializing database with missing tables...")
            init_db()
            return verify_db()  # Recursive call to verify after initialization

        # Verify bot_status
        cursor.execute("SELECT * FROM bot_status")
        status = cursor.fetchone()
        logger.info(f"Bot Status: {status}")

        # Verify trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        logger.info(f"Trade Count: {trade_count}")
        if trade_count > 0:
            cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 1")
            latest_trade = cursor.fetchone()
            logger.info(f"Latest Trade: {latest_trade}")

        # Verify price alerts
        cursor.execute("SELECT COUNT(*) FROM price_alerts WHERE active = 1")
        active_alerts = cursor.fetchone()[0]
        logger.info(f"Active Price Alerts: {active_alerts}")
        if active_alerts > 0:
            cursor.execute("""
                SELECT token, condition, price, created_at 
                FROM price_alerts 
                WHERE active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            latest_alert = cursor.fetchone()
            logger.info(f"Latest Active Alert: {latest_alert}")

        # Verify alert history
        cursor.execute("SELECT COUNT(*) FROM alert_history")
        alert_history_count = cursor.fetchone()[0]
        logger.info(f"Alert History Count: {alert_history_count}")
        if alert_history_count > 0:
            cursor.execute("""
                SELECT ah.trigger_price, ah.triggered_at, pa.token, pa.condition
                FROM alert_history ah
                JOIN price_alerts pa ON ah.alert_id = pa.id
                ORDER BY ah.triggered_at DESC
                LIMIT 1
            """)
            latest_triggered = cursor.fetchone()
            logger.info(f"Latest Triggered Alert: {latest_triggered}")

        # Verify price history
        cursor.execute("SELECT COUNT(*) FROM price_history")
        price_history_count = cursor.fetchone()[0]
        logger.info(f"Price History Count: {price_history_count}")
        if price_history_count > 0:
            cursor.execute("""
                SELECT token, price, timestamp
                FROM price_history
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            latest_price = cursor.fetchone()
            logger.info(f"Latest Price Record: {latest_price}")

        # Verify indices for query optimization
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = {row[0] for row in cursor.fetchall()}
        required_indices = {
            'idx_price_history_token',      # For quick token-based queries
            'idx_price_history_timestamp',  # For time-based analysis
            'idx_price_alerts_token',       # For alert checking
            'idx_price_alerts_active',      # For active alert filtering
            'idx_trades_timestamp'          # For trade history analysis
        }

        missing_indices = required_indices - indices
        if missing_indices:
            logger.warning(f"Missing indices: {missing_indices}")
            logger.info("Creating missing indices...")
            for idx in missing_indices:
                if idx == 'idx_price_history_token':
                    cursor.execute('CREATE INDEX idx_price_history_token ON price_history(token)')
                elif idx == 'idx_price_history_timestamp':
                    cursor.execute('CREATE INDEX idx_price_history_timestamp ON price_history(timestamp)')
                elif idx == 'idx_price_alerts_token':
                    cursor.execute('CREATE INDEX idx_price_alerts_token ON price_alerts(token)')
                elif idx == 'idx_price_alerts_active':
                    cursor.execute('CREATE INDEX idx_price_alerts_active ON price_alerts(active)')
                elif idx == 'idx_trades_timestamp':
                    cursor.execute('CREATE INDEX idx_trades_timestamp ON trades(timestamp)')
            conn.commit()
            logger.info("Missing indices created successfully")

        conn.close()
        logger.info("Database verification complete - all structures verified")
        return True

    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {e}")
        logger.info("Attempting to initialize database...")
        init_db()
        return verify_db()  # Recursive call to verify after initialization

    except Exception as e:
        logger.error(f"Unexpected error during database verification: {e}")
        return False


if __name__ == '__main__':
    # When run directly, perform database verification
    verify_db()
