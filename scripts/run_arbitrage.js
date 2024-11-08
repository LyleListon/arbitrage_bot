// Run arbitrage operations with monitoring and execution
const { spawn } = require('child_process');
const chalk = require('chalk');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
    logDir: path.join(__dirname, '../logs'),
    pidFile: path.join(__dirname, '../bot.pid'),
    performance: {
        logInterval: 300000, // 5 minutes
        summaryInterval: 3600000 // 1 hour
    },
    monitoring: {
        restartDelay: 5000, // 5 seconds
        maxRestarts: 3
    }
};

// Global state
let state = {
    startTime: Date.now(),
    trades: [],
    errors: [],
    restarts: {
        monitor: 0,
        executor: 0
    },
    isShuttingDown: false
};

async function main() {
    console.log(chalk.blue("\nStarting arbitrage operations..."));
    
    // Create log directory if it doesn't exist
    if (!fs.existsSync(CONFIG.logDir)) {
        fs.mkdirSync(CONFIG.logDir, { recursive: true });
    }
    
    // Write PID file
    fs.writeFileSync(CONFIG.pidFile, process.pid.toString());
    
    try {
        // Start components
        const monitor = startMonitor();
        const executor = startExecutor();
        
        // Start performance tracking
        const performanceInterval = setInterval(() => logPerformance(), CONFIG.performance.logInterval);
        const summaryInterval = setInterval(() => logSummary(), CONFIG.performance.summaryInterval);
        
        // Handle process termination
        setupProcessHandlers(monitor, executor, performanceInterval, summaryInterval);
        
        // Wait for components
        await Promise.all([
            handleComponent(monitor, 'monitor'),
            handleComponent(executor, 'executor')
        ]);
        
    } catch (error) {
        console.error(chalk.red("\nFatal error:"), error);
        await shutdown();
        process.exit(1);
    }
}

function startMonitor() {
    console.log(chalk.yellow("\nStarting opportunity monitor..."));
    
    const monitor = spawn('node', ['monitor_opportunities.js'], {
        cwd: __dirname,
        stdio: ['inherit', 'pipe', 'pipe']
    });
    
    setupComponentLogging(monitor, 'monitor');
    
    return monitor;
}

function startExecutor() {
    console.log(chalk.yellow("\nStarting trade executor..."));
    
    const executor = spawn('node', ['execute_arbitrage.js'], {
        cwd: __dirname,
        stdio: ['inherit', 'pipe', 'pipe']
    });
    
    setupComponentLogging(executor, 'executor');
    
    return executor;
}

function setupComponentLogging(process, name) {
    // Create log streams
    const logStream = fs.createWriteStream(
        path.join(CONFIG.logDir, `${name}.log`),
        { flags: 'a' }
    );
    
    const errorStream = fs.createWriteStream(
        path.join(CONFIG.logDir, `${name}.error.log`),
        { flags: 'a' }
    );
    
    // Pipe output to logs
    process.stdout.pipe(logStream);
    process.stderr.pipe(errorStream);
    
    // Log to console
    process.stdout.on('data', (data) => {
        console.log(chalk.gray(`[${name}] ${data.toString().trim()}`));
    });
    
    process.stderr.on('data', (data) => {
        console.error(chalk.red(`[${name}] ${data.toString().trim()}`));
        state.errors.push({
            component: name,
            error: data.toString().trim(),
            timestamp: Date.now()
        });
    });
}

async function handleComponent(process, name) {
    return new Promise((resolve, reject) => {
        process.on('exit', async (code) => {
            if (state.isShuttingDown) {
                console.log(chalk.gray(`${name} shut down`));
                resolve();
                return;
            }
            
            console.error(chalk.red(`${name} exited with code ${code}`));
            
            // Attempt restart if not max restarts
            if (state.restarts[name] < CONFIG.monitoring.maxRestarts) {
                state.restarts[name]++;
                console.log(chalk.yellow(`Restarting ${name} (attempt ${state.restarts[name]})...`));
                
                await new Promise(resolve => setTimeout(resolve, CONFIG.monitoring.restartDelay));
                
                const newProcess = name === 'monitor' ? startMonitor() : startExecutor();
                handleComponent(newProcess, name).catch(reject);
            } else {
                console.error(chalk.red(`${name} failed to restart, shutting down...`));
                await shutdown();
                reject(new Error(`${name} failed to restart`));
            }
        });
    });
}

function setupProcessHandlers(monitor, executor, performanceInterval, summaryInterval) {
    const cleanup = async () => {
        if (state.isShuttingDown) return;
        await shutdown(monitor, executor, performanceInterval, summaryInterval);
    };
    
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    process.on('uncaughtException', async (error) => {
        console.error(chalk.red("\nUncaught exception:"), error);
        await cleanup();
        process.exit(1);
    });
}

async function shutdown(monitor, executor, performanceInterval, summaryInterval) {
    console.log(chalk.yellow("\nShutting down..."));
    state.isShuttingDown = true;
    
    // Clear intervals
    if (performanceInterval) clearInterval(performanceInterval);
    if (summaryInterval) clearInterval(summaryInterval);
    
    // Stop components
    if (monitor) monitor.kill();
    if (executor) executor.kill();
    
    // Final performance log
    await logPerformance();
    await logSummary();
    
    // Remove PID file
    if (fs.existsSync(CONFIG.pidFile)) {
        fs.unlinkSync(CONFIG.pidFile);
    }
    
    console.log(chalk.green("\nShutdown complete"));
}

function logPerformance() {
    const performance = {
        uptime: Date.now() - state.startTime,
        trades: state.trades.length,
        errors: state.errors.length,
        restarts: state.restarts,
        timestamp: Date.now()
    };
    
    fs.appendFileSync(
        path.join(CONFIG.logDir, 'performance.log'),
        JSON.stringify(performance) + '\n'
    );
}

function logSummary() {
    const runtime = Date.now() - state.startTime;
    const hours = runtime / 3600000;
    
    const summary = {
        runtime: {
            hours,
            uptime: `${Math.floor(hours)}h ${Math.floor((hours % 1) * 60)}m`
        },
        trades: {
            total: state.trades.length,
            perHour: state.trades.length / hours
        },
        errors: {
            total: state.errors.length,
            perHour: state.errors.length / hours
        },
        restarts: state.restarts,
        timestamp: Date.now()
    };
    
    fs.writeFileSync(
        path.join(CONFIG.logDir, 'summary.json'),
        JSON.stringify(summary, null, 2)
    );
    
    console.log(chalk.cyan("\nOperation Summary:"));
    console.log(chalk.gray(JSON.stringify(summary, null, 2)));
}

// Run operations
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = { main };
