import argparse
import time
import logging
import os
import signal
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.arbitrage_bot import ArbitrageBot

def start_bot(args):
    bot = ArbitrageBot(dry_run=args.dry_run)
    pid = os.getpid()
    with open('bot.pid', 'w') as f:
        f.write(str(pid))
    logging.info(f"Bot started with PID {pid}")
    bot.run()

def stop_bot(args):
    try:
        with open('bot.pid', 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        logging.info(f"Sent SIGTERM to bot process with PID {pid}")
    except FileNotFoundError:
        logging.error("Bot PID file not found. Is the bot running?")
    except ProcessLookupError:
        logging.error(f"No process found with PID {pid}")

def get_status(args):
    try:
        with open('bot.pid', 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)  # This will raise an exception if the process is not running
            print(f"Bot is running with PID {pid}")
        except ProcessLookupError:
            print(f"Bot process with PID {pid} is not running")
    except FileNotFoundError:
        print("Bot is not running")

def main():
    parser = argparse.ArgumentParser(description="Arbitrage Bot CLI")
    subparsers = parser.add_subparsers()

    # Start command
    start_parser = subparsers.add_parser('start', help='Start the arbitrage bot')
    start_parser.add_argument('--dry-run', action='store_true', help='Run the bot in dry run mode')
    start_parser.set_defaults(func=start_bot)

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop the arbitrage bot')
    stop_parser.set_defaults(func=stop_bot)

    # Status command
    status_parser = subparsers.add_parser('status', help='Get the status of the arbitrage bot')
    status_parser.set_defaults(func=get_status)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
