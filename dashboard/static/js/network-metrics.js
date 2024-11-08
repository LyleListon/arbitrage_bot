// Network Metrics Visualization
// @LAST_POINT: 2024-01-31 - Updated to use ES modules and improved threshold handling
// @CONTEXT: Handles real-time network metrics visualization, updates, and threshold monitoring

import { socket, showNotification } from './dashboard.js';
import { networkChartConfig } from './chart-config.js';

class NetworkMetricsManager {
    constructor() {
        this.chart = null;
        this.dataHistory = {
            sent: [],
            received: [],
            timestamps: [],
            maxPoints: 50
        };
        this.peakRates = {
            sent: 0,
            received: 0
        };
        this.totalTransfer = {
            sent: 0,
            received: 0
        };
        this.lastUpdate = {
            sent: 0,
            received: 0,
            timestamp: Date.now()
        };
        this.thresholds = {
            bytesSent: localStorage.getItem('threshold_bytesSent') || 1048576, // 1MB/s default
            bytesReceived: localStorage.getItem('threshold_bytesReceived') || 1048576,
            connections: localStorage.getItem('threshold_connections') || 100,
            latency: localStorage.getItem('threshold_latency') || 1000, // 1s default
            notificationsEnabled: localStorage.getItem('threshold_notifications') === 'true'
        };
        this.initializeChart();
        this.initializeThresholdListeners();
    }

    initializeChart() {
        const ctx = document.getElementById('networkChart').getContext('2d');
        const config = {
            ...networkChartConfig,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Bytes Sent/s',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        data: [],
                        fill: true
                    },
                    {
                        label: 'Bytes Received/s',
                        borderColor: 'rgba(153, 102, 255, 1)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        data: [],
                        fill: true
                    }
                ]
            }
        };
        this.chart = new Chart(ctx, config);
    }

    initializeThresholdListeners() {
        // Initialize threshold input values
        document.getElementById('bytesSentThresholdInput').value = this.thresholds.bytesSent;
        document.getElementById('bytesReceivedThresholdInput').value = this.thresholds.bytesReceived;
        document.getElementById('connectionsThresholdInput').value = this.thresholds.connections;
        document.getElementById('latencyThresholdInput').value = this.thresholds.latency;
        document.getElementById('enableNotifications').checked = this.thresholds.notificationsEnabled;

        // Save threshold settings
        document.getElementById('saveThresholds').addEventListener('click', () => {
            this.thresholds = {
                bytesSent: parseInt(document.getElementById('bytesSentThresholdInput').value),
                bytesReceived: parseInt(document.getElementById('bytesReceivedThresholdInput').value),
                connections: parseInt(document.getElementById('connectionsThresholdInput').value),
                latency: parseInt(document.getElementById('latencyThresholdInput').value),
                notificationsEnabled: document.getElementById('enableNotifications').checked
            };

            // Save to localStorage
            localStorage.setItem('threshold_bytesSent', this.thresholds.bytesSent);
            localStorage.setItem('threshold_bytesReceived', this.thresholds.bytesReceived);
            localStorage.setItem('threshold_connections', this.thresholds.connections);
            localStorage.setItem('threshold_latency', this.thresholds.latency);
            localStorage.setItem('threshold_notifications', this.thresholds.notificationsEnabled);

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('thresholdModal'));
            modal.hide();

            showNotification('Threshold settings saved successfully', 'success');
        });
    }

    checkThresholds(data, rates) {
        const thresholdChecks = [
            {
                value: rates.sent,
                threshold: this.thresholds.bytesSent,
                message: `Bytes sent rate (${this.formatBytes(rates.sent)}) exceeded threshold`,
                indicator: 'bytesSentThreshold'
            },
            {
                value: rates.received,
                threshold: this.thresholds.bytesReceived,
                message: `Bytes received rate (${this.formatBytes(rates.received)}) exceeded threshold`,
                indicator: 'bytesReceivedThreshold'
            },
            {
                value: data.active_connections,
                threshold: this.thresholds.connections,
                message: `Active connections (${data.active_connections}) exceeded threshold`,
                indicator: 'connectionsThreshold'
            },
            {
                value: data.latency || 0,
                threshold: this.thresholds.latency,
                message: `Network latency (${data.latency}ms) exceeded threshold`,
                indicator: 'latencyThreshold'
            }
        ];

        thresholdChecks.forEach(check => {
            const indicator = document.getElementById(check.indicator);
            if (check.value > check.threshold) {
                indicator.className = 'threshold-indicator warning';
                if (this.thresholds.notificationsEnabled) {
                    showNotification(check.message, 'warning');
                }
            } else {
                indicator.className = 'threshold-indicator';
            }
        });
    }

    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i] + '/s';
    }

    formatTotalBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    calculateRate(current, last, timeElapsed) {
        return (current - last) / (timeElapsed / 1000);
    }

    updateTrendIndicator(elementId, currentValue, lastValue) {
        const element = document.getElementById(elementId);
        if (currentValue > lastValue) {
            element.className = 'trend-indicator up';
            element.innerHTML = '↑';
        } else if (currentValue < lastValue) {
            element.className = 'trend-indicator down';
            element.innerHTML = '↓';
        } else {
            element.className = 'trend-indicator stable';
            element.innerHTML = '→';
        }
    }

    updateMetrics(data) {
        const now = Date.now();
        const timeElapsed = now - this.lastUpdate.timestamp;

        // Calculate rates
        const sentRate = this.calculateRate(data.bytes_sent, this.lastUpdate.sent, timeElapsed);
        const receivedRate = this.calculateRate(data.bytes_recv, this.lastUpdate.received, timeElapsed);

        // Check thresholds
        this.checkThresholds(data, { sent: sentRate, received: receivedRate });

        // Update peak rates
        this.peakRates.sent = Math.max(this.peakRates.sent, sentRate);
        this.peakRates.received = Math.max(this.peakRates.received, receivedRate);

        // Update total transfer
        this.totalTransfer.sent = data.bytes_sent;
        this.totalTransfer.received = data.bytes_recv;

        // Update trend indicators
        this.updateTrendIndicator('bytesSentTrend', sentRate, this.lastUpdate.sent);
        this.updateTrendIndicator('bytesReceivedTrend', receivedRate, this.lastUpdate.received);

        // Update display values
        document.getElementById('bytesSent').textContent = this.formatBytes(sentRate);
        document.getElementById('bytesReceived').textContent = this.formatBytes(receivedRate);
        document.getElementById('activeConnections').textContent = data.active_connections;
        document.getElementById('maxSendRate').textContent = this.formatBytes(this.peakRates.sent);
        document.getElementById('maxReceiveRate').textContent = this.formatBytes(this.peakRates.received);
        document.getElementById('totalSent').textContent = this.formatTotalBytes(this.totalTransfer.sent);
        document.getElementById('totalReceived').textContent = this.formatTotalBytes(this.totalTransfer.received);

        // Update chart data
        this.dataHistory.sent.push(sentRate);
        this.dataHistory.received.push(receivedRate);
        this.dataHistory.timestamps.push(now);

        // Maintain history length
        if (this.dataHistory.sent.length > this.dataHistory.maxPoints) {
            this.dataHistory.sent.shift();
            this.dataHistory.received.shift();
            this.dataHistory.timestamps.shift();
        }

        // Update chart
        this.chart.data.labels = this.dataHistory.timestamps;
        this.chart.data.datasets[0].data = this.dataHistory.sent;
        this.chart.data.datasets[1].data = this.dataHistory.received;
        this.chart.update('none');

        // Store current values for next update
        this.lastUpdate = {
            sent: data.bytes_sent,
            received: data.bytes_recv,
            timestamp: now
        };
    }
}

// Initialize network metrics manager
const networkMetrics = new NetworkMetricsManager();

// Listen for network metric updates from WebSocket
socket.on('network_metrics', (data) => {
    networkMetrics.updateMetrics(data);
});
