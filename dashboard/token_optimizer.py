"""Token price optimization and caching"""

import time
from typing import Dict, Any, Optional, Union
import json

class TokenOptimizer:
    def __init__(self, db_path: str):
        self.cache: Dict[str, Dict[str, Union[Any, float]]] = {}
        self.cache_duration = 300  # 5 minutes
        
    def store(self, key: str, value: Any) -> None:
        """Store value in cache with timestamp"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if not expired"""
        if key in self.cache:
            cache_entry = self.cache[key]
            if time.time() - cache_entry['timestamp'] < self.cache_duration:
                return cache_entry['value']
            else:
                del self.cache[key]
        return None
