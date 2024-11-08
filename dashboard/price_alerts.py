"""
Price Alert System
Monitors prices and triggers alerts based on user-defined conditions
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceAlertSystem:
    def __init__(self, db_path='arbitrage_bot.db'):
        """Initialize alert system with database connection"""
        self.db_path = db_path
        self.setup_database()
        
    def get_db_connection(self):
        """Create a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def setup_database(self):
        """Set up alerts database tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    price REAL NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    created_at INTEGER NOT NULL
                )
            ''')
            
            # Create alert history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER NOT NULL,
                    trigger_price REAL NOT NULL,
                    triggered_at INTEGER NOT NULL,
                    FOREIGN KEY (alert_id) REFERENCES price_alerts (id)
                )
            ''')
            
            conn.commit()
            logger.info("Alert tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up alert tables: {str(e)}")
        finally:
            conn.close()
            
    def add_alert(self, token, condition, price):
        """
        Add a new price alert
        condition: 'above' or 'below'
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_alerts (token, condition, price, created_at)
                VALUES (?, ?, ?, ?)
            ''', (token, condition, price, int(datetime.now().timestamp())))
            
            alert_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added new alert for {token} {condition} {price}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error adding alert: {str(e)}")
            return None
        finally:
            conn.close()
            
    def check_alerts(self, token, current_price):
        """Check if any alerts should be triggered for the current price"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get active alerts for token
            cursor.execute('''
                SELECT * FROM price_alerts 
                WHERE token = ? AND active = 1
            ''', (token,))
            
            alerts = cursor.fetchall()
            triggered = []
            
            for alert in alerts:
                should_trigger = False
                
                if alert['condition'] == 'above' and current_price >= alert['price']:
                    should_trigger = True
                elif alert['condition'] == 'below' and current_price <= alert['price']:
                    should_trigger = True
                    
                if should_trigger:
                    # Record trigger in history
                    cursor.execute('''
                        INSERT INTO alert_history (alert_id, trigger_price, triggered_at)
                        VALUES (?, ?, ?)
                    ''', (alert['id'], current_price, int(datetime.now().timestamp())))
                    
                    # Deactivate the alert
                    cursor.execute('''
                        UPDATE price_alerts SET active = 0
                        WHERE id = ?
                    ''', (alert['id'],))
                    
                    triggered.append({
                        'id': alert['id'],
                        'token': token,
                        'condition': alert['condition'],
                        'target_price': alert['price'],
                        'trigger_price': current_price
                    })
                    
            conn.commit()
            return triggered
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            return []
        finally:
            conn.close()
            
    def get_active_alerts(self):
        """Get all active alerts"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM price_alerts 
                WHERE active = 1
                ORDER BY created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []
        finally:
            conn.close()
            
    def get_alert_history(self, limit=50):
        """Get recent alert history"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    h.id,
                    a.token,
                    a.condition,
                    a.price as target_price,
                    h.trigger_price,
                    h.triggered_at
                FROM alert_history h
                JOIN price_alerts a ON h.alert_id = a.id
                ORDER BY h.triggered_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}")
            return []
        finally:
            conn.close()
            
    def delete_alert(self, alert_id):
        """Delete an alert"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM price_alerts
                WHERE id = ?
            ''', (alert_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting alert: {str(e)}")
            return False
        finally:
            conn.close()
