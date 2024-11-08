const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const MONITOR_INTERVAL = 15 * 60 * 1000; // 15 minutes
const MONITORING_DURATION = 24 * 60 * 60 * 1000; // 24 hours
const LOG_FILE = path.join(__dirname, '../logs/monitoring.log');

// Ensure logs directory exists
if (!fs.existsSync(path.join(__dirname, '../logs'))) {
    fs.mkdirSync(path.join(__dirname, '../logs'));
}

function runMonitoring() {
    const command = 'npx hardhat run scripts/monitor_deployment.js --network sepolia';
    
    exec(command, (error, stdout, stderr) => {
        const timestamp = new Date().toISOString();
        const logEntry = `\n[${timestamp}]\n${stdout}\n${stderr ? `Errors:\n${stderr}\n` : ''}`;
        
        fs.appendFileSync(LOG_FILE, logEntry);
        
        if (error) {
            console.error(`Error: ${error}`);
            fs.appendFileSync(LOG_FILE, `Error: ${error}\n`);
        }
    });
}

console.log('Starting 24-hour monitoring schedule...');
console.log(`Monitoring interval: ${MONITOR_INTERVAL/1000/60} minutes`);
console.log(`Log file: ${LOG_FILE}`);

// Initial run
runMonitoring();

// Schedule regular monitoring
const interval = setInterval(runMonitoring, MONITOR_INTERVAL);

// Stop after 24 hours
setTimeout(() => {
    clearInterval(interval);
    console.log('24-hour monitoring period completed.');
    process.exit(0);
}, MONITORING_DURATION);
