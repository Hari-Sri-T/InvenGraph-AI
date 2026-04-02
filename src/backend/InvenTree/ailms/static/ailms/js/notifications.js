// Notification toast system for AI-First Logistics Management System

const Notifications = {
    container: null,
    
    init() {
        this.container = document.getElementById('notification-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(this.container);
        }
    },
    
    show(severity, message, duration = 5000) {
        const id = `notification-${Date.now()}`;
        const notification = this.createNotification(id, severity, message);
        
        this.container.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            this.remove(id);
        }, duration);
        
        return id;
    },
    
    createNotification(id, severity, message) {
        const div = document.createElement('div');
        div.id = id;
        div.className = `notification-toast ${this.getSeverityClass(severity)} p-4 rounded-lg shadow-lg max-w-md`;
        
        div.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    ${this.getSeverityIcon(severity)}
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button 
                    onclick="Notifications.remove('${id}')"
                    class="ml-4 flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-600">
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;
        
        return div;
    },
    
    getSeverityClass(severity) {
        const classes = {
            'success': 'bg-green-50 border border-green-200 text-green-800',
            'error': 'bg-red-50 border border-red-200 text-red-800',
            'warning': 'bg-orange-50 border border-orange-200 text-orange-800',
            'info': 'bg-blue-50 border border-blue-200 text-blue-800',
        };
        return classes[severity] || classes.info;
    },
    
    getSeverityIcon(severity) {
        const icons = {
            'success': '<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
            'error': '<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            'warning': '<svg class="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
            'info': '<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>',
        };
        return icons[severity] || icons.info;
    },
    
    remove(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    },
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    Notifications.init();
});

// Global function for easy access
function showNotification(severity, message, duration) {
    return Notifications.show(severity, message, duration);
}
