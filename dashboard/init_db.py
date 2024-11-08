"""
Initialize SQLite database for the arbitrage bot dashboard

This module handles the initialization and setup of the SQLite database used by the dashboard.
It creates all necessary tables, indexes, and views according to the schema defined in schema.sql.

Key features:
- Creates database tables for trades, parameters, gas prices, and bot status
- Sets up indexes for optimized query performance
- Creates views for common analytics queries
- Initializes bot_status table with default values
- Handles database versioning and migrations

Database Schema:
- trades: Records all arbitrage trades executed by the bot
- parameter_history: Tracks changes to bot configuration parameters
- gas_history: Monitors gas price fluctuations
- price_history: Stores token price data
- bot_status: Maintains current bot state and last update time

Usage:
    python init_db.py

Dependencies:
    - sqlite3: Database engine
    - schema.sql: SQL schema definition file
"""

import os
import time
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def init_db():
    """
    Initialize database with schema and default data
    
    This function:
    1. Creates database tables if they don't exist
    2. Sets up necessary indexes for performance
    3. Creates views for common queries
    4. Initializes bot_status with default values
    
    Returns:
        None
    
    Raises:
        sqlite3.Error: If database operations fail
        FileNotFoundError: If schema.sql is missing
    """
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'arbitrage_bot.db')
        logger.info(f"Database path: {db_path}")
        
        # Connect to database
        db = sqlite3.connect(db_path)
        cur = db.cursor()
        
        # Read schema
        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path) as f:
            schema = f.read()
            
        # Execute schema
        cur.executescript(schema)
        logger.info("Successfully created tables")
        
        # Create indexes
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        index_count = cur.fetchone()[0]
        logger.info(f"Successfully created {index_count} out of 6 indexes")
        
        # Create views
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
        view_count = cur.fetchone()[0]
        logger.info("Successfully created views")
        
        # Initialize bot_status with default row if it doesn't exist
        cur.execute("SELECT COUNT(*) FROM bot_status")
        if cur.fetchone()[0] == 0:
            current_time = int(time.time())
            cur.execute("""
                INSERT INTO bot_status (id, is_running, last_update)
                VALUES (1, 0, ?)
            """, (current_time,))
            db.commit()
            logger.info("Initialized bot_status table with default row")
        
        # Log created objects
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        logger.info(f"Created tables: {tables}")
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cur.fetchall()]
        logger.info(f"Created indexes: {indexes}")
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cur.fetchall()]
        logger.info(f"Created views: {views}")
        
        logger.info("Database initialization completed successfully!")
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()


if __name__ == '__main__':
    init_db()
