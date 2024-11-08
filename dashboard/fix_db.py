import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    try:
        # Connect to database
        conn = sqlite3.connect('arbitrage_bot.db')
        cursor = conn.cursor()
        
        # Check if success column exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = cursor.fetchall()
        has_success = any(col[1] == 'success' for col in columns)
        
        if not has_success:
            logger.info("Adding success column to trades table")
            cursor.execute("ALTER TABLE trades ADD COLUMN success BOOLEAN NOT NULL DEFAULT 0")
            conn.commit()
            logger.info("Successfully added success column")
        else:
            logger.info("Success column already exists")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error fixing database: {e}")
        raise

if __name__ == "__main__":
    fix_database()
