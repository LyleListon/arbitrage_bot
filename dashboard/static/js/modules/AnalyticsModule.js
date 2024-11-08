/**
 * Analytics module for processing and visualizing trading data
 * @extends BaseModule
 */
class AnalyticsModule extends BaseModule {
    constructor(registry) {
        super('analytics', {
            refreshInterval: 5000,
            chartOptions: {
                responsive: true,
                animation: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        }, registry);

        // Initialize data structures
        this.priceHistory = new Map();
        this.volumeHistory = new Map();
        this.profitHistory = new Map();
        this.charts = new Map();
    }

    async _initialize() {
        // Subscribe to market updates
        this.subscribe('market_update', this._handleMarketUpdate.bind(this));
        this.subscribe('trade_executed', this._handleTradeExecuted.bind(this));
        
        // Initialize UI components
        this._initializeCharts();
        this._initializeMetrics();
        
        console.log('Analytics module initialized');
    }

    async _destroy() {
        // Cleanup charts
        for (const chart of this.charts.values()) {
            chart.destroy();
        }
        this.charts.clear();
        
        // Clear data
        this.priceHistory.clear();
        this.volumeHistory.clear();
        this.profitHistory.clear();
    }

    /**
     * Initialize chart components
     * @private
     */
    _initializeCharts() {
        // Price chart
        const priceCtx = document.getElementById('price-chart');
        if (priceCtx) {
            this.charts.set('price', new Chart(priceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Price',
                        data: [],
                        borderColor: '#007bff',
                        tension: 0.1
                    }]
                },
                options: this.config.chartOptions
            }));
        }

        // Volume chart
        const volumeCtx = document.getElementById('volume-chart');
        if (volumeCtx) {
            this.charts.set('volume', new Chart(volumeCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Volume',
                        data: [],
                        backgroundColor: '#28a745'
                    }]
                },
                options: this.config.chartOptions
            }));
        }

        // Profit chart
        const profitCtx = document.getElementById('profit-chart');
        if (profitCtx) {
            this.charts.set('profit', new Chart(profitCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Profit',
                        data: [],
                        borderColor: '#17a2b8',
                        fill: true,
                        backgroundColor: 'rgba(23, 162, 184, 0.1)'
                    }]
                },
                options: this.config.chartOptions
            }));
        }
    }

    /**
     * Initialize metrics display
     * @private
     */
    _initializeMetrics() {
        this.metrics = {
            totalTrades: 0,
            successRate: 0,
            avgProfit: 0,
            totalVolume: 0
        };

        this._updateMetricsDisplay();
    }

    /**
     * Handle market update events
     * @private
     * @param {Object} data Market update data
     */
    _handleMarketUpdate(data) {
        const timestamp = new Date().toLocaleTimeString();

        // Update price history
        if (data.price) {
            const prices = this.priceHistory.get(data.token) || [];
            prices.push({ time: timestamp, value: data.price });
            if (prices.length > 100) prices.shift();
            this.priceHistory.set(data.token, prices);
        }

        // Update volume history
        if (data.volume) {
            const volumes = this.volumeHistory.get(data.token) || [];
            volumes.push({ time: timestamp, value: data.volume });
            if (volumes.length > 100) volumes.shift();
            this.volumeHistory.set(data.token, volumes);
        }

        this._updateCharts();
    }

    /**
     * Handle trade execution events
     * @private
     * @param {Object} data Trade execution data
     */
    _handleTradeExecuted(data) {
        const timestamp = new Date().toLocaleTimeString();

        // Update profit history
        const profits = this.profitHistory.get(data.token) || [];
        profits.push({ time: timestamp, value: data.profit });
        if (profits.length > 100) profits.shift();
        this.profitHistory.set(data.token, profits);

        // Update metrics
        this.metrics.totalTrades++;
        this.metrics.totalVolume += data.volume;
        this.metrics.avgProfit = (this.metrics.avgProfit * (this.metrics.totalTrades - 1) + data.profit) / this.metrics.totalTrades;
        this.metrics.successRate = (data.profit > 0 ? this.metrics.successRate + 1 : this.metrics.successRate) / this.metrics.totalTrades * 100;

        this._updateCharts();
        this._updateMetricsDisplay();
    }

    /**
     * Update chart displays
     * @private
     */
    _updateCharts() {
        // Update price chart
        const priceChart = this.charts.get('price');
        if (priceChart && this.priceHistory.size > 0) {
            const [token] = this.priceHistory.keys();
            const prices = this.priceHistory.get(token);
            priceChart.data.labels = prices.map(p => p.time);
            priceChart.data.datasets[0].data = prices.map(p => p.value);
            priceChart.update('none');
        }

        // Update volume chart
        const volumeChart = this.charts.get('volume');
        if (volumeChart && this.volumeHistory.size > 0) {
            const [token] = this.volumeHistory.keys();
            const volumes = this.volumeHistory.get(token);
            volumeChart.data.labels = volumes.map(v => v.time);
            volumeChart.data.datasets[0].data = volumes.map(v => v.value);
            volumeChart.update('none');
        }

        // Update profit chart
        const profitChart = this.charts.get('profit');
        if (profitChart && this.profitHistory.size > 0) {
            const [token] = this.profitHistory.keys();
            const profits = this.profitHistory.get(token);
            profitChart.data.labels = profits.map(p => p.time);
            profitChart.data.datasets[0].data = profits.map(p => p.value);
            profitChart.update('none');
        }
    }

    /**
     * Update metrics display
     * @private
     */
    _updateMetricsDisplay() {
        const container = document.getElementById('metrics-container');
        if (!container) return;

        container.innerHTML = `
            <div class="metric">
                <h3>Total Trades</h3>
                <p>${this.metrics.totalTrades}</p>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <p>${this.metrics.successRate.toFixed(2)}%</p>
            </div>
            <div class="metric">
                <h3>Average Profit</h3>
                <p>${this.metrics.avgProfit.toFixed(4)} ETH</p>
            </div>
            <div class="metric">
                <h3>Total Volume</h3>
                <p>${this.metrics.totalVolume.toFixed(2)} ETH</p>
            </div>
        `;
    }
}

// Export for use in other modules
window.AnalyticsModule = AnalyticsModule;
