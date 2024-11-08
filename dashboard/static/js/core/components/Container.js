/**
 * Core container component for flexible layouts
 * Provides grid-based layout system for organizing dashboard components
 */
class Container {
    constructor(id, columns = 12) {
        this.id = id;
        this.columns = columns;
        this.items = new Map();
        this.gaps = {
            row: '1rem',
            column: '1rem'
        };
    }

    /**
     * Add a component to the container
     * @param {BaseComponent} component - Component to add
     * @param {Object} options - Layout options
     * @param {number} options.columnSpan - Number of columns to span (1-12)
     * @param {number} options.rowSpan - Number of rows to span
     * @param {string} options.minWidth - Minimum width of the component
     */
    addComponent(component, options = {}) {
        const defaultOptions = {
            columnSpan: 12,
            rowSpan: 1,
            minWidth: '200px'
        };
        
        this.items.set(component, { ...defaultOptions, ...options });
        this.render();
    }

    /**
     * Remove a component from the container
     * @param {BaseComponent} component - Component to remove
     */
    removeComponent(component) {
        this.items.delete(component);
        this.render();
    }

    /**
     * Set the gap between components
     * @param {string} rowGap - Gap between rows
     * @param {string} columnGap - Gap between columns
     */
    setGap(rowGap, columnGap) {
        this.gaps.row = rowGap;
        this.gaps.column = columnGap;
        this.render();
    }

    /**
     * Generate CSS Grid template
     * @private
     */
    _generateGridTemplate() {
        return `
            display: grid;
            grid-template-columns: repeat(${this.columns}, 1fr);
            gap: ${this.gaps.row} ${this.gaps.column};
            padding: 1rem;
        `;
    }

    /**
     * Generate component styles
     * @private
     * @param {Object} options - Component layout options
     */
    _generateComponentStyle(options) {
        return `
            grid-column: span ${options.columnSpan};
            grid-row: span ${options.rowSpan};
            min-width: ${options.minWidth};
        `;
    }

    /**
     * Render the container and all its components
     */
    render() {
        const container = document.getElementById(this.id);
        if (!container) {
            console.error(`Container with id "${this.id}" not found`);
            return;
        }

        // Set container styles
        container.style.cssText = this._generateGridTemplate();

        // Clear existing content
        container.innerHTML = '';

        // Render components
        for (const [component, options] of this.items) {
            const wrapper = document.createElement('div');
            wrapper.style.cssText = this._generateComponentStyle(options);
            wrapper.appendChild(component.render());
            container.appendChild(wrapper);
        }
    }

    /**
     * Update the layout when window resizes
     */
    handleResize() {
        this.render();
    }
}

/**
 * Base component class that all UI components should extend
 */
class BaseComponent {
    constructor(title = '') {
        this.title = title;
        this.element = null;
    }

    /**
     * Create the component's DOM element
     * @protected
     */
    createElement() {
        const element = document.createElement('div');
        element.className = 'component';
        
        if (this.title) {
            const header = document.createElement('div');
            header.className = 'component-header';
            header.textContent = this.title;
            element.appendChild(header);
        }

        return element;
    }

    /**
     * Render the component
     * @returns {HTMLElement}
     */
    render() {
        if (!this.element) {
            this.element = this.createElement();
        }
        return this.element;
    }

    /**
     * Update the component's content
     * @param {*} data - New data to display
     */
    update(data) {
        // Implementation in child classes
    }

    /**
     * Clean up the component
     */
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

// Export for use in other modules
window.Container = Container;
window.BaseComponent = BaseComponent;
