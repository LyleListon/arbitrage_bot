"""
Enhanced monitoring module for arbitrage bot
"""
import logging
import time
import smtplib
from email.mime.text import MIMEText
from typing import Dict
from web3 import Web3
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit: float
    total_gas_cost: float
    avg_profit_per_trade: float
    success_rate: float
    timestamp: int


class ArbitrageBotMonitor:
    def __init__(
        self,
        w3: Web3,
        config: Dict,
        email_config: Dict[str, str]
    ):
        self.w3 = w3
        self.config = config
        self.email_config = email_config
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Performance thresholds
        self.min_success_rate = config['monitoring']['min_success_rate']
        self.min_daily_profit = config['monitoring']['min_daily_profit']
        self.profit_window = config['monitoring']['profit_window']
        self.max_gas_cost_ratio = config['monitoring']['max_gas_cost_ratio']
        
        # Health check thresholds
        self.max_block_delay = config['monitoring']['health_check']['max_block_delay']
        self.max_pending_tx = config['monitoring']['health_check']['max_pending_tx']
        self.min_peer_count = config['monitoring']['health_check']['min_peer_count']
        
        # Alert cooldown
        self.last_alert_time = {}
        self.alert_cooldown = config['monitoring']['alerts'].get('cooldown', 300)  # 5 minutes default
        self.max_daily_alerts = config['monitoring']['alerts'].get('max_daily_alerts', 10)
        self.daily_alert_count = 0
        self.alert_count_reset_time = int(time.time())
        
        # Initialize SMTP connection if email alerts are enabled
        self.smtp_connection = None
        if email_config.get('enabled', False):
            try:
                self.smtp_connection = smtplib.SMTP(
                    email_config['smtp_server'],
                    email_config['smtp_port']
                )
                self.smtp_connection.starttls()
                self.smtp_connection.login(
                    email_config['username'],
                    email_config['password']
                )
                self.logger.info("SMTP connection established successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize SMTP connection: {str(e)}")

    def monitor_system_health(self) -> bool:
        """Monitor overall system health"""
        try:
            # Check block delay
            latest_block = self.w3.eth.get_block('latest')
            block_delay = int(time.time()) - latest_block.timestamp
            if block_delay > self.max_block_delay:
                self.send_alert(
                    "Block Delay Alert",
                    f"Block delay of {block_delay}s exceeds maximum of {self.max_block_delay}s",
                    "warning"
                )
                return False
            
            # Check pending transactions
            pending_tx_count = self.w3.eth.get_block_transaction_count('pending')
            if pending_tx_count > self.max_pending_tx:
                self.send_alert(
                    "High Mempool Load",
                    f"Pending transactions ({pending_tx_count}) exceed maximum of {self.max_pending_tx}",
                    "warning"
                )
                return False
            
            # Check peer count
            peer_count = self.w3.net.peer_count
            if peer_count < self.min_peer_count:
                self.send_alert(
                    "Low Peer Count",
                    f"Connected peers ({peer_count}) below minimum of {self.min_peer_count}",
                    "warning"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error monitoring system health: {str(e)}")
            return False

    def update_performance_metrics(self, metrics: PerformanceMetrics):
        """Update and check performance metrics"""
        try:
            # Check success rate
            if metrics.success_rate < self.min_success_rate:
                self.send_alert(
                    "Low Success Rate",
                    f"Success rate ({metrics.success_rate:.2%}) below minimum of {self.min_success_rate:.2%}",
                    "warning"
                )
            
            # Check daily profit
            profit_eth = Web3.from_wei(metrics.total_profit, 'ether')
            if profit_eth < self.min_daily_profit:
                self.send_alert(
                    "Low Daily Profit",
                    f"Daily profit ({profit_eth:.4f} ETH) below minimum of {self.min_daily_profit} ETH",
                    "warning"
                )
            
            # Check gas costs
            if metrics.total_trades > 0:
                gas_cost_ratio = metrics.total_gas_cost / metrics.total_profit
                if gas_cost_ratio > self.max_gas_cost_ratio:
                    self.send_alert(
                        "High Gas Costs",
                        f"Gas cost ratio ({gas_cost_ratio:.2%}) exceeds maximum of {self.max_gas_cost_ratio:.2%}",
                        "warning"
                    )
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")

    def send_alert(
        self,
        subject: str,
        message: str,
        severity: str = "info"
    ) -> bool:
        """Send alert through configured channels"""
        try:
            # Check alert cooldown
            current_time = int(time.time())
            if subject in self.last_alert_time:
                time_since_last = current_time - self.last_alert_time[subject]
                if time_since_last < self.alert_cooldown:
                    return False
            
            # Reset daily alert count if needed
            if current_time - self.alert_count_reset_time > 86400:  # 24 hours
                self.daily_alert_count = 0
                self.alert_count_reset_time = current_time
            
            # Check daily alert limit
            if self.daily_alert_count >= self.max_daily_alerts:
                self.logger.warning("Daily alert limit reached")
                return False
            
            # Send email alert if enabled
            if self.email_config.get('enabled', False) and self.smtp_connection:
                try:
                    msg = MIMEText(message)
                    msg['Subject'] = f"[{severity.upper()}] {subject}"
                    msg['From'] = self.email_config['sender']
                    msg['To'] = self.email_config['recipient']
                    
                    self.smtp_connection.send_message(msg)
                    self.logger.info(f"Alert email sent: {subject}")
                except Exception as e:
                    self.logger.error(f"Failed to send email alert: {str(e)}")
                    # Try to reconnect
                    self._reconnect_smtp()
            
            # Update alert tracking
            self.last_alert_time[subject] = current_time
            self.daily_alert_count += 1
            
            # Log alert
            log_message = f"[{severity.upper()}] {subject}: {message}"
            if severity == "critical":
                self.logger.critical(log_message)
            elif severity == "warning":
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {str(e)}")
            return False

    def _reconnect_smtp(self):
        """Attempt to reconnect SMTP connection"""
        try:
            if self.smtp_connection:
                self.smtp_connection.quit()
            
            self.smtp_connection = smtplib.SMTP(
                self.email_config['smtp_server'],
                self.email_config['smtp_port']
            )
            self.smtp_connection.starttls()
            self.smtp_connection.login(
                self.email_config['username'],
                self.email_config['password']
            )
            self.logger.info("SMTP connection re-established")
        except Exception as e:
            self.logger.error(f"Failed to reconnect SMTP: {str(e)}")
            self.smtp_connection = None

    def __del__(self):
        """Cleanup SMTP connection"""
        if hasattr(self, 'smtp_connection') and self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except Exception as e:
                self.logger.error(f"Error closing SMTP connection: {str(e)}")
