/**
 * Base module class that all feature modules will extend
 * @class BaseModule
 */
class BaseModule {
    /**
     * @param {string} name - Module name
     * @param {Object} config - Module configuration
     * @param {ModuleRegistry} registry - Reference to the module registry
     */
    constructor(name, config = {}, registry) {
        this.name = name;
        this.config = config;
        this.registry = registry;
        this.initialized = false;
        this.dependencies = [];
        this._eventHandlers = new Map();
    }

    /**
     * Initialize the module
     * @returns {Promise<void>}
     */
    async initialize() {
        if (this.initialized) return;
        
        // Wait for dependencies to initialize
        for (const dep of this.dependencies) {
            const module = this.registry.getModule(dep);
            if (!module.initialized) {
                await module.initialize();
            }
        }

        await this._initialize();
        this.initialized = true;
        console.log(`Module ${this.name} initialized`);
    }

    /**
     * Internal initialization - to be implemented by child classes
     * @protected
     * @returns {Promise<void>}
     */
    async _initialize() {
        // Implementation in child classes
    }

    /**
     * Clean up module resources
     * @returns {Promise<void>}
     */
    async destroy() {
        if (!this.initialized) return;

        await this._destroy();
        this.initialized = false;
        this._eventHandlers.clear();
        console.log(`Module ${this.name} destroyed`);
    }

    /**
     * Internal cleanup - to be implemented by child classes
     * @protected
     * @returns {Promise<void>}
     */
    async _destroy() {
        // Implementation in child classes
    }

    /**
     * Subscribe to an event
     * @param {string} eventName - Name of the event
     * @param {Function} handler - Event handler function
     */
    subscribe(eventName, handler) {
        if (!this._eventHandlers.has(eventName)) {
            this._eventHandlers.set(eventName, new Set());
        }
        this._eventHandlers.get(eventName).add(handler);
        this.registry.subscribe(eventName, handler);
    }

    /**
     * Unsubscribe from an event
     * @param {string} eventName - Name of the event
     * @param {Function} handler - Event handler function
     */
    unsubscribe(eventName, handler) {
        const handlers = this._eventHandlers.get(eventName);
        if (handlers) {
            handlers.delete(handler);
        }
    }

    /**
     * Publish an event
     * @param {string} eventName - Name of the event
     * @param {*} data - Event data
     */
    publish(eventName, data) {
        this.registry.publish(eventName, {
            source: this.name,
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Update module configuration
     * @param {Object} newConfig - New configuration object
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.publish('config_updated', { module: this.name, config: this.config });
    }

    /**
     * Get module state
     * @returns {Object} Current module state
     */
    getState() {
        return {
            name: this.name,
            initialized: this.initialized,
            config: this.config
        };
    }

    /**
     * Add a dependency
     * @param {string} moduleName - Name of the dependent module
     */
    addDependency(moduleName) {
        if (!this.dependencies.includes(moduleName)) {
            this.dependencies.push(moduleName);
        }
    }
}

// Export for use in other modules
window.BaseModule = BaseModule;
