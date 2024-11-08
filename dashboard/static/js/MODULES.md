# Dashboard Module System Documentation

## Overview

The dashboard uses a modular architecture to organize functionality into independent, reusable components. This system is built on three core concepts:

1. **Module Registry** - Central management of all modules
2. **Base Module** - Foundation class that all modules extend
3. **Feature Modules** - Individual functionality implementations

## Core Components

### ModuleRegistry

The ModuleRegistry (`ModuleRegistry.js`) manages module lifecycle and dependencies:

```javascript
const registry = new ModuleRegistry();
registry.register('analytics', new AnalyticsModule(registry));
```

Key features:
- Module registration and initialization
- Dependency resolution
- Event bus for inter-module communication
- State management

### BaseModule

The BaseModule (`BaseModule.js`) provides common functionality for all modules:

```javascript
class MyModule extends BaseModule {
    constructor(registry) {
        super('myModule', config, registry);
    }
}
```

Features:
- Lifecycle management (initialize, destroy)
- Event subscription/publishing
- Configuration management
- State handling

## Current Modules

### 1. Analytics Module

Location: `modules/AnalyticsModule.js`

Purpose:
- Real-time price and volume visualization
- Performance metrics tracking
- Historical data analysis
- Trading statistics

Events Published:
- `stats_update`: Updated performance metrics
- `chart_update`: New chart data available

Events Subscribed:
- `market_update`: New market data
- `trade_executed`: Trade completion

### 2. Trading Module (In Progress)

Location: `modules/TradingModule.js`

Purpose:
- Trading controls and parameters
- Order management
- Risk controls
- Emergency functions

Events Published:
- `trading_state_changed`: Bot status updates
- `parameters_updated`: Trading parameter changes
- `emergency_stop_triggered`: Emergency stop events

Events Subscribed:
- `market_update`: Market data updates
- `gas_price_update`: Gas price changes
- `trade_executed`: Trade execution updates

## Adding New Modules

1. Create a new module file in `modules/`:
```javascript
class NewModule extends BaseModule {
    constructor(registry) {
        super('moduleName', defaultConfig, registry);
    }

    async _initialize() {
        // Setup code
    }

    async _destroy() {
        // Cleanup code
    }
}
```

2. Register module dependencies:
```javascript
class NewModule extends BaseModule {
    constructor(registry) {
        super('moduleName', defaultConfig, registry);
        this.addDependency('analytics');  // If depends on analytics
    }
}
```

3. Subscribe to events:
```javascript
async _initialize() {
    this.subscribe('market_update', this._handleMarketUpdate.bind(this));
}
```

4. Publish events:
```javascript
_handleMarketUpdate(data) {
    // Process data
    this.publish('my_event', processedData);
}
```

## Best Practices

1. **Initialization**
   - Always call super() in constructor
   - Initialize state in constructor
   - Setup event handlers in _initialize()
   - Validate dependencies before use

2. **Event Handling**
   - Use descriptive event names
   - Document event data structures
   - Handle errors in event callbacks
   - Clean up subscriptions in _destroy()

3. **State Management**
   - Keep module state private
   - Use getters/setters for state access
   - Publish state changes as events
   - Validate state transitions

4. **Error Handling**
   - Catch and log errors
   - Provide meaningful error messages
   - Handle cleanup in error cases
   - Notify system of critical errors

## Module Communication

Modules communicate through the event system:

```javascript
// Publishing events
this.publish('event_name', {
    timestamp: Date.now(),
    data: someData
});

// Subscribing to events
this.subscribe('event_name', (data) => {
    // Handle event
});
```

Event naming convention:
- Use snake_case
- Include module name for specific events
- Use present tense for states
- Use past tense for actions

## Configuration

Modules can be configured through their constructor:

```javascript
const config = {
    refreshInterval: 5000,
    maxItems: 100,
    // etc
};

new MyModule(registry, config);
```

Configuration best practices:
- Provide sensible defaults
- Validate configuration values
- Document configuration options
- Allow runtime configuration updates

## Testing

Each module should include tests:

```javascript
describe('MyModule', () => {
    let module;
    let registry;
    
    beforeEach(() => {
        registry = new ModuleRegistry();
        module = new MyModule(registry);
    });
    
    test('initializes correctly', () => {
        // Test initialization
    });
    
    // More tests...
});
```

Test coverage should include:
- Initialization
- Event handling
- State management
- Error cases
- Configuration validation

## Future Improvements

1. **Planned Modules**
   - Risk Management Module
   - Portfolio Analysis Module
   - Alert System Module
   - Strategy Builder Module

2. **System Enhancements**
   - Hot module reloading
   - Module versioning
   - State persistence
   - Performance optimization

3. **Developer Tools**
   - Module debugging tools
   - Event monitoring
   - State inspection
   - Performance profiling
