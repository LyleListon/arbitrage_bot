"""
Run script for the Arbitrage Bot Dashboard
"""

import os
import sys

# Add the parent directory to the path so we can import the dashboard package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from dashboard.price_analysis import PriceAnalyzer
from dashboard.price_alerts import PriceAlertSystem
from dashboard.app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
