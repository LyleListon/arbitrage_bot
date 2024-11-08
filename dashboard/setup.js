/* Enhanced dashboard runner with proper process management

@CONTEXT: Script to run the enhanced dashboard with proper setup
@LAST_POINT: 2024-01-31 - Added network-specific initialization
*/

import os
import sys
import logging
import signal
import argparse
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Error: psutil package is required. Install with: pip install psutil")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the enhanced arbitrage dashboard')
    parser.add_argument(
        '--network',
        choices=['development', 'sepolia', 'mainnet'],
        default=os.getenv('NETWORK', 'development'),
        help='Network to run on (default: from NETWORK env var or "development")'
    )
    return parser.parse_args()


def cleanup_stale_processes():
    """Clean up any stale dashboard processes"""
    try:
        pid_file = Path(__file__).parent / 'dashboard.pid'
        if pid_file.exists():
            with open(pid_file) as f:
                old_pid = int(f.read().strip())
            try:
                process = psutil.Process(old_pid)
                if process.name().lower() in ['python', 'python.exe']:
                    cmdline = ' '.join(process.cmdline()).lower()
                    if 'dashboard' in cmdline:
                        process.terminate()
                        process.wait(timeout=5)
                        logger.info(f"Terminated stale process {old_pid}")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                pass
            pid_file.unlink()
            logger.info("Removed stale PID file")
    except Exception as e:
        logger.error(f"Error cleaning up stale processes: {e}")


def write_pid():
    """Write current process ID to file"""
    try:
        pid_file = Path(__file__).parent / 'dashboard.pid'
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Wrote PID {os.getpid()} to {pid_file}")
    except Exception as e:
        logger.error(f"Error writing PID file: {e}")


def cleanup():
    """Clean up resources"""
    try:
        pid_file = Path(__file__).parent / 'dashboard.pid'
        if pid_file.exists():
            pid_file.unlink()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup()
    sys.exit(0)


def run_dashboard(network: str):
    """
    Run the enhanced dashboard

    Args:
        network: Network to run on (development/sepolia/mainnet)
    """
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Clean up any stale processes first
        cleanup_stale_processes()

        # Run initialization with network
        from dashboard.init_dashboard import initialize_dashboard
        if not initialize_dashboard(network):
            logger.error(f"Dashboard initialization failed for network: {network}")
            return 1

        # Write PID file after initialization succeeds
        write_pid()

        # Import and run the dashboard
        from dashboard.enhanced_app import main
        logger.info(f"Starting enhanced dashboard on network: {network}")

        # Run the dashboard with network
        main(network=network)
        return 0

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        return 1
    finally:
        cleanup()


def main():
    """Main entry point"""
    try:
        # Parse command line arguments
        args = parse_args()

        # Validate network choice
        if args.network == "mainnet":
            logger.warning("""
            ⚠️ WARNING: Running on mainnet with real assets!
            Make sure you have:
            1. Verified all configurations
            2. Tested on testnet first
            3. Set appropriate gas limits
            4. Secured private keys
            """)
            confirm = input("Type 'yes' to confirm mainnet deployment: ")
            if confirm.lower() != 'yes':
                logger.info("Mainnet deployment cancelled")
                sys.exit(0)

        # Run dashboard with selected network
        sys.exit(run_dashboard(args.network))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
