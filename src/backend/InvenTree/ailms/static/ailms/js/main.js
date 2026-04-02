// Main application initialization for AI-First Logistics Management System

const App = {
    config: {
        apiBaseUrl: '/api/ai/procurement/',
        refreshInterval: 30000,  // 30 seconds
    },
    
    state: {
        user: null,
        socket: null,
        notifications: [],
    },
    
    init() {
        this.loadUserData();
        this.setupGlobalEventListeners();
        
        // Initialize WebSocket if available
        if (typeof initializeWebSocket === 'function') {
            this.initializeWebSocket();
        }
    },
    
    loadUserData() {
        this.state.user = {
            id: document.body.dataset.userId,
            username: document.body.dataset.username,
            permissions: JSON.parse(document.body.dataset.permissions || '[]'),
        };
    },
    
    initializeWebSocket() {
        if (this.state.socket) return;
        if (this.state.user && this.state.user.id) {
            this.state.socket = initializeWebSocket(this.state.user.id);
        }
    },
    
    setupGlobalEventListeners() {
        // Handle HTMX events
        document.body.addEventListener('htmx:afterRequest', (event) => {
            if (event.detail.successful) {
                this.handleSuccessfulRequest(event);
            } else {
                this.handleFailedRequest(event);
            }
        });
    },
    
    handleSuccessfulRequest(event) {
        // Show success notification if response includes message
        try {
            const response = JSON.parse(event.detail.xhr.response);
            if (response && response.message) {
                showNotification('success', response.message);
            }
        } catch (e) {
            // Response might not be JSON
        }
    },
    
    handleFailedRequest(event) {
        // Show error notification
        try {
            const response = JSON.parse(event.detail.xhr.response);
            const message = response?.error || 'An error occurred. Please try again.';
            showNotification('error', message);
        } catch (e) {
            showNotification('error', 'An error occurred. Please try again.');
        }
    },
};

// Initialize app on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
