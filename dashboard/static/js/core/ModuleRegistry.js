/**
 * Core module registry for managing dashboard features
 * @class ModuleRegistry
 */
class ModuleRegistry {
    constructor() {
        this.modules = new Map();
        this.dependencies = new Map();
        this.initialized = new Set();
        this.eventBus = new EventEmitter();
    }

    /**
     * Register a new module
     * @param {string} name - Module name
     * @param {Object} module - Module instance
     * @param {Array} dependencies - Array of dependency module names
     */
    register(name, module, dependencies = []) {
        if (this.modules.has(name)) {
            throw new Error(`Module ${name} already registered`);
        }
        
        this.modules.set(name, module);
        this.dependencies.set(name, dependencies);
        
        // Log registration for debugging
        console.log(`Registered module: ${name}`);
    }

    /**
     * Initialize modules in dependency order
     * @returns {Promise} - Resolves when all modules are initialized
     */
    async initialize() {
        const initOrder = this.resolveDependencies();
        
        for (const moduleName of initOrder) {
            if (!this.initialized.has(moduleName)) {
                const module = this.modules.get(moduleName);
                await module.initialize();
                this.initialized.add(moduleName);
                console.log(`Initialized module: ${moduleName}`);
            }
        }
    }

    /**
     * Resolve module dependencies
     * @returns {Array} - Array of module names in initialization order
     */
    resolveDependencies() {
        const visited = new Set();
        const initOrder = [];

        const visit = (name) => {
            if (visited.has(name)) return;
            visited.add(name);

            const deps = this.dependencies.get(name) || [];
            for (const dep of deps) {
                if (!this.modules.has(dep)) {
                    throw new Error(`Missing dependency: ${dep} for module ${name}`);
                }
                visit(dep);
            }

            initOrder.push(name);
        };

        for (const name of this.modules.keys()) {
            visit(name);
        }

        return initOrder;
    }

    /**
     * Get a module instance
     * @param {string} name - Module name
     * @returns {Object} - Module instance
     */
    getModule(name) {
        if (!this.modules.has(name)) {
            throw new Error(`Module ${name} not found`);
        }
        return this.modules.get(name);
    }

    /**
     * Subscribe to module events
     * @param {string} eventName - Event name
     * @param {Function} handler - Event handler
     */
    subscribe(eventName, handler) {
        this.eventBus.on(eventName, handler);
    }

    /**
     * Publish module event
     * @param {string} eventName - Event name
     * @param {*} data - Event data
     */
    publish(eventName, data) {
        this.eventBus.emit(eventName, data);
    }
}

// Export for use in other modules
window.ModuleRegistry = ModuleRegistry;
