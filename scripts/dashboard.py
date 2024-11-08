from flask import Flask, render_template, jsonify
from arbitrage_bot import ArbitrageBot
import threading
import time

app = Flask(__name__)

# Create a global bot instance
bot = ArbitrageBot()

# Create a thread to run the bot
bot_thread = None

# Store bot statistics
bot_stats = {
    'total_trades': 0,
    'successful_trades': 0,
    'failed_trades': 0,
    'total_profit': 0,
    'total_gas_cost': 0,
    'net_profit': 0,
    'current_balance': 0,
    'initial_balance': 0,
    'last_update': None,
}


def update_stats():
    global bot_stats
    while True:
        bot_stats['total_trades'] = bot.total_trades
        bot_stats['successful_trades'] = bot.successful_trades
        bot_stats['failed_trades'] = bot.failed_trades
        bot_stats['total_profit'] = bot.total_profit
        bot_stats['total_gas_cost'] = bot.total_gas_cost
        bot_stats['net_profit'] = bot.total_profit - bot.total_gas_cost
        bot_stats['current_balance'] = bot.get_eth_balance()
        bot_stats['initial_balance'] = bot.initial_balance
        bot_stats['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(10)  # Update every 10 seconds


@app.route('/')
def index():
    return render_template('dashboard.html', stats=bot_stats)


@app.route('/api/stats')
def get_stats():
    return jsonify(bot_stats)


@app.route('/start')
def start_bot():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=bot.run)
        bot_thread.start()
        return "Bot started"
    return "Bot is already running"


@app.route('/stop')
def stop_bot():
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        bot.stop_flag = True
        bot_thread.join()
        return "Bot stopped"
    return "Bot is not running"


if __name__ == '__main__':
    # Start the stats update thread
    stats_thread = threading.Thread(target=update_stats)
    stats_thread.start()

    # Run the Flask app
    app.run(debug=True, use_reloader=False)
