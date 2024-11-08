import os
import logging
import socket
from gevent import monkey
monkey.patch_all()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_port=5100):
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    raise RuntimeError("No available ports found")

def main():
    """Main entry point for the dashboard application"""
    logger.info("Installing required packages...")

    # Install required packages
    try:
        os.system("pip install -r requirements.txt")
        logger.info("Requirements installed successfully")
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return

    # Install dashboard package
    logger.info("Installing dashboard package...")
    try:
        os.system("pip install -e .")
        logger.info("Dashboard package installed successfully")
    except Exception as e:
        logger.error(f"Error installing dashboard package: {e}")
        return

    # Import and run dashboard
    try:
        from dashboard.app import app, socketio
        port = find_available_port()
        logger.info(f"Starting server on port {port}")
        socketio.run(app, debug=True, host='127.0.0.1', port=port, use_reloader=False)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        return

if __name__ == '__main__':
    main()
