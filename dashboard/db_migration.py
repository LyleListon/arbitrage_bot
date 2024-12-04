"""Database migration and optimization script"""

import logging
import sqlite3
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handle database migrations and optimizations"""
    
    def __init__(self, db_path: str = 'arbitrage_bot.db'):
        self.db_path = db_path
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def migrate(self) -> None:
        """Run all migrations"""
        try:
            self._create_indices()
            self._standardize_timestamps()
            self._add_constraints()
            self._optimize_tables()
            logger.info("Database migration completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def _create_indices(self) -> None:
        """Create necessary indices for performance"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create indices for frequently queried columns
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_dex_prices_timestamp ON dex_prices(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_dex_prices_token_pair ON dex_prices(token_pair)",
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_trades_token_pair ON trades(token_pair)",
                "CREATE INDEX IF NOT EXISTS idx_opportunity_scores_timestamp ON opportunity_scores(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON model_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_prediction_confidence_timestamp ON prediction_confidence(timestamp)"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            conn.commit()
            logger.info("Created performance indices")
            
        except Exception as e:
            logger.error(f"Error creating indices: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _standardize_timestamps(self) -> None:
        """Standardize timestamp columns to INTEGER (Unix timestamp)"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table['name']
                
                # Get columns for this table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Find timestamp columns
                timestamp_columns = [
                    col['name'] for col in columns 
                    if 'timestamp' in col['name'].lower() and col['type'] != 'INTEGER'
                ]
                
                # Convert DATETIME timestamps to INTEGER
                for col in timestamp_columns:
                    # Create temporary column
                    temp_col = f"{col}_temp"
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {temp_col} INTEGER")
                    
                    # Convert and copy data
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET {temp_col} = strftime('%s', {col})
                        WHERE {col} IS NOT NULL
                    """)
                    
                    # Drop old column and rename new one
                    cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {col}")
                    cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {temp_col} TO {col}")
            
            conn.commit()
            logger.info("Standardized timestamp columns")
            
        except Exception as e:
            logger.error(f"Error standardizing timestamps: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _add_constraints(self) -> None:
        """Add necessary constraints to tables"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Add foreign key constraints
            constraints = [
                """
                CREATE TABLE IF NOT EXISTS new_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    token_pair TEXT NOT NULL,
                    exchange_from TEXT NOT NULL,
                    exchange_to TEXT NOT NULL,
                    amount_in REAL NOT NULL CHECK (amount_in > 0),
                    amount_out REAL NOT NULL CHECK (amount_out > 0),
                    profit REAL NOT NULL,
                    FOREIGN KEY (token_pair) REFERENCES tokens(symbol)
                )
                """
            ]
            
            for constraint in constraints:
                cursor.execute(constraint)
            
            conn.commit()
            logger.info("Added database constraints")
            
        except Exception as e:
            logger.error(f"Error adding constraints: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def _optimize_tables(self) -> None:
        """Optimize database tables"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Analyze tables for query optimization
            cursor.execute("ANALYZE")
            
            # Vacuum database to reclaim space
            cursor.execute("VACUUM")
            
            conn.commit()
            logger.info("Optimized database tables")
            
        except Exception as e:
            logger.error(f"Error optimizing tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

def main():
    """Run database migration"""
    logging.basicConfig(level=logging.INFO)
    try:
        migration = DatabaseMigration()
        migration.migrate()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
