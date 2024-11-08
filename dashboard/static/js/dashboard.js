// Dashboard Core Functionality
// @LAST_POINT: 2024-01-31 - Added shared dashboard functionality

// Initialize Socket.io connection
const socket = io();

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-icon">${type === 'success' ? '✓' : '!'}</div>
        <div class="notification-message">${message}</div>
    `;

    const notificationArea = document.getElementById('notificationArea');
    notificationArea.appendChild(notification);

    // Remove notification after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Socket connection status
socket.on('connect', () => {
    console.log('Socket connected successfully');
    showNotification('Connected to server', 'success');
});

socket.on('disconnect', () => {
    console.log('Socket disconnected');
    showNotification('Lost connection to server', 'warning');
});

// Request updates from server
function requestUpdate(type) {
    socket.emit('request_update', { type });
}

// Set up periodic updates
setInterval(() => {
    requestUpdate('stats');
}, 5000);

// Make functions available globally
window.showNotification = showNotification;
window.socket = socket;
window.requestUpdate = requestUpdate;
