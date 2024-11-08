// Chart.js Configuration
// @LAST_POINT: 2024-01-31 - Fixed Chart.js configuration

// Network chart configuration
export const networkChartConfig = {
    type: 'line',
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
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 0
        },
        scales: {
            x: {
                type: 'time',
                adapters: {
                    date: {
                        locale: 'en'
                    }
                },
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Bytes/s'
                }
            }
        },
        plugins: {
            legend: {
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    }
};

// Performance chart configuration
export const performanceChartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: []
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: 'time',
                adapters: {
                    date: {
                        locale: 'en'
                    }
                },
                time: {
                    unit: 'hour',
                    displayFormats: {
                        hour: 'MMM d, HH:mm'
                    }
                },
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Performance'
                }
            }
        },
        plugins: {
            legend: {
                position: 'top'
            }
        }
    }
};
