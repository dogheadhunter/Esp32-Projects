/**
 * API Client for Script Review
 */

class API {
    constructor() {
        this.baseURL = window.location.origin;
        this.token = localStorage.getItem('api_token') || '';
    }
    
    setToken(token) {
        this.token = token;
        localStorage.setItem('api_token', token);
    }
    
    getToken() {
        return this.token;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const config = {
            ...options,
            headers
        };
        
        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Token invalid or expired
                localStorage.removeItem('api_token');
                this.token = '';
                throw new Error('Authentication failed. Please log in again.');
            }
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({detail: 'Unknown error'}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async getScripts(djFilter = null) {
        const query = djFilter ? `?dj=${encodeURIComponent(djFilter)}` : '';
        return this.request(`/api/scripts${query}`);
    }
    
    async reviewScript(scriptId, status, reasonId = null, customComment = null) {
        const body = {
            script_id: scriptId,
            status: status
        };
        
        if (status === 'rejected') {
            body.reason_id = reasonId;
            if (customComment) {
                body.custom_comment = customComment;
            }
        }
        
        return this.request('/api/review', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }
    
    async getReasons() {
        return this.request('/api/reasons');
    }
    
    async getStats() {
        return this.request('/api/stats');
    }
}

const api = new API();
