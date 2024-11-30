#!/usr/bin/env python3
import logging
from typing import NoReturn
from dashboard.app import app, socketio

def configure_logging() -> None:
    """Configure logging for the dashboard server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main() -> NoReturn:
    """
    Main entry point for the dashboard server
    Runs indefinitely until interrupted
    """
    logger = logging.getLogger('DashboardRunner')
    configure_logging()
    
    try:
        logger.info("Starting dashboard server...")
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting dashboard server: {e}")
        raise

if __name__ == '__main__':
    main()
