"""Database cleanup and maintenance module"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseCleaner:
    """Handles cleanup of old data from the database"""
    
    def __init__(self, db_path: str = 'arbitrage_bot.db'):
        self.db_path = db_path
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def cleanup_old_data(self, 
                        price_retention_days: int = 7,
                        metrics_retention_days: int = 30,
                        logs_retention_days: int = 14) -> None:
        """Clean up old data from various tables"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Calculate cutoff timestamps
            price_cutoff = datetime.now() - timedelta(days=price_retention_days)
            metrics_cutoff = datetime.now() - timedelta(days=metrics_retention_days)
            logs_cutoff = datetime.now() - timedelta(days=logs_retention_days)
            
            # Clean up price data
            cursor.execute('''
                DELETE FROM dex_prices 
                WHERE timestamp < ?
            ''', (price_cutoff,))
            
            cursor.execute('''
                DELETE FROM price_history 
                WHERE timestamp < ?
            ''', (int(price_cutoff.timestamp()),))
            
            # Clean up metrics
            cursor.execute('''
                DELETE FROM system_metrics 
                WHERE timestamp < ?
            ''', (metrics_cutoff,))
            
            cursor.execute('''
                DELETE FROM model_metrics 
                WHERE timestamp < ?
            ''', (metrics_cutoff,))
            
            cursor.execute('''
                DELETE FROM risk_metrics 
                WHERE timestamp < ?
            ''', (metrics_cutoff,))
            
            # Clean up logs
            cursor.execute('''
                DELETE FROM system_logs 
                WHERE timestamp < ?
            ''', (logs_cutoff,))
            
            # Clean up opportunity data
            cursor.execute('''
                DELETE FROM opportunity_scores 
                WHERE timestamp < ?
            ''', (price_cutoff,))
            
            cursor.execute('''
                DELETE FROM opportunity_history 
                WHERE timestamp < ?
            ''', (int(price_cutoff.timestamp()),))
            
            # Clean up correlation data
            cursor.execute('''
                DELETE FROM dex_correlations 
                WHERE timestamp < ?
            ''', (metrics_cutoff,))
            
            # Clean up prediction data
            cursor.execute('''
                DELETE FROM prediction_confidence 
                WHERE timestamp < ?
            ''', (metrics_cutoff,))
            
            # Optimize database
            cursor.execute('VACUUM')
            
            # Commit changes
            conn.commit()
            
            logger.info(f"""Cleanup completed:
                - Removed price data older than {price_retention_days} days
                - Removed metrics older than {metrics_retention_days} days
                - Removed logs older than {logs_retention_days} days
            """)
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def analyze_database_size(self) -> dict:
        """Analyze database table sizes and row counts"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            analysis = {}
            for table in tables:
                table_name = table['name']
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = cursor.fetchone()['count']
                
                # Get approximate size
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                analysis[table_name] = {
                    'row_count': row_count,
                    'column_count': len(columns)
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing database: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def optimize_database(self) -> None:
        """Optimize database by rebuilding indices and vacuuming"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Reindex
            cursor.execute("REINDEX")
            
            # Vacuum to reclaim space and defragment
            cursor.execute("VACUUM")
            
            # Analyze to update statistics
            cursor.execute("ANALYZE")
            
            conn.commit()
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
        finally:
            if conn:
                conn.close()

def main():
    """Run database maintenance"""
    try:
        cleaner = DatabaseCleaner()
        
        # Analyze current state
        analysis = cleaner.analyze_database_size()
        logger.info("Database analysis before cleanup:")
        for table, stats in analysis.items():
            logger.info(f"{table}: {stats['row_count']} rows")
        
        # Perform cleanup
        cleaner.cleanup_old_data()
        
        # Optimize
        cleaner.optimize_database()
        
        # Analyze after cleanup
        analysis = cleaner.analyze_database_size()
        logger.info("Database analysis after cleanup:")
        for table, stats in analysis.items():
            logger.info(f"{table}: {stats['row_count']} rows")
            
    except Exception as e:
        logger.error(f"Error in database maintenance: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
