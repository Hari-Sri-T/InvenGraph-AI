// API client module for AI-First Logistics Management System

const API = {
    baseUrl: '/api/ai/procurement/',
    
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (token) return token;
        
        // Try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    },
    
    // Pipeline endpoints
    async triggerPipeline(partId) {
        return this.request('pipeline/trigger/', {
            method: 'POST',
            body: JSON.stringify({ part_id: partId }),
        });
    },
    
    async getPipelineStatus(pipelineId) {
        return this.request(`pipeline/status/${pipelineId}/`);
    },
    
    async getPipelinesByPart(partId) {
        return this.request(`pipeline/status/?part_id=${partId}`);
    },
    
    // Approval endpoints
    async getApprovals(status = 'pending') {
        return this.request(`approvals/?status=${status}`);
    },
    
    async processApproval(requestId, action, userData = {}) {
        return this.request(`approvals/${requestId}/action/`, {
            method: 'POST',
            body: JSON.stringify({
                action,
                ...userData,
            }),
        });
    },
};

// Export for use in other modules
window.API = API;
