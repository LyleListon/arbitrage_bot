"""Token Usage Optimization System"""
import sqlite3
from typing import Optional, Dict, Any
import json
import zlib
from datetime import datetime

class TokenOptimizer:
    def __init__(self, db_path: str = 'arbitrage_bot.db'):
        self.db_path = db_path
        self._init_database()
        self.cache: Dict[str, Any] = {}
        
    def _init_database(self) -> None:
        """Initialize the token optimization database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store compressed code snippets and responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_cache (
                key TEXT PRIMARY KEY,
                compressed_data BLOB,
                timestamp INTEGER,
                access_count INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()

    def store(self, key: str, data: Any) -> None:
        """Store data in compressed format"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compress the data
        json_data = json.dumps(data)
        compressed = zlib.compress(json_data.encode())
        
        timestamp = int(datetime.now().timestamp())
        
        cursor.execute('''
            INSERT OR REPLACE INTO token_cache 
            (key, compressed_data, timestamp, access_count)
            VALUES (?, ?, ?, 
                COALESCE((SELECT access_count + 1 FROM token_cache WHERE key = ?), 1)
            )
        ''', (key, compressed, timestamp, key))
        
        conn.commit()
        conn.close()

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve and decompress data"""
        # Check memory cache first
        if key in self.cache:
            return self.cache[key]
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT compressed_data FROM token_cache WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        if result:
            compressed_data = result[0]
            json_str = zlib.decompress(compressed_data).decode()
            data = json.loads(json_str)
            
            # Update access count
            cursor.execute('''
                UPDATE token_cache 
                SET access_count = access_count + 1 
                WHERE key = ?
            ''', (key,))
            
            conn.commit()
            
            # Cache frequently accessed items in memory
            cursor.execute('SELECT access_count FROM token_cache WHERE key = ?', (key,))
            access_count = cursor.fetchone()[0]
            if access_count > 10:  # Cache items accessed more than 10 times
                self.cache[key] = data
                
            return data
            
        return None

    def clear_old_cache(self, days: int = 7) -> None:
        """Clear old cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = int((datetime.now().timestamp()) - (days * 24 * 60 * 60))
        cursor.execute('DELETE FROM token_cache WHERE timestamp < ?', (cutoff,))
        
        conn.commit()
        conn.close()
        self.cache.clear()
