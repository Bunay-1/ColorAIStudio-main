/**
 * ICAP Enterprise JavaScript Client SDK
 * =====================================
 * JavaScript SDK for interacting with ICAP Enterprise API.
 */

class ICAPConfig {
    constructor(baseUrl, options = {}) {
        this.baseUrl = baseUrl;
        this.apiKey = options.apiKey || null;
        this.username = options.username || null;
        this.password = options.password || null;
        this.tenantId = options.tenantId || null;
        this.timeout = options.timeout || 30000;
        this.verifySSL = options.verifySSL !== false;
    }
}

class ICAPClient {
    constructor(config) {
        this.config = config;
        this.token = null;
        this.authenticate();
    }

    async authenticate() {
        if (this.config.apiKey) {
            this.token = this.config.apiKey;
        } else if (this.config.username && this.config.password) {
            await this.login(this.config.username, this.config.password);
        }
    }

    async request(method, endpoint, options = {}) {
        const url = `${this.config.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (this.config.tenantId) {
            headers['X-Tenant-ID'] = this.config.tenantId;
        }

        const fetchOptions = {
            method,
            headers,
            ...options
        };

        try {
            const response = await fetch(url, fetchOptions);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    // Authentication
    async login(username, password) {
        const data = await this.request('POST', '/auth/login', {
            body: JSON.stringify({ username, password })
        });
        this.token = data.access_token;
        return data;
    }

    async refreshToken(refreshToken) {
        const data = await this.request('POST', '/auth/refresh', {
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        this.token = data.access_token;
        return data;
    }

    async logout() {
        return await this.request('POST', '/auth/logout');
    }

    // Color Analysis
    async analyzeColor(labValues, method = 'delta_e_2000') {
        return await this.request('POST', '/color/analyze', {
            body: JSON.stringify({
                lab_values: labValues,
                method: method
            })
        });
    }

    async predictTrend(historicalData) {
        return await this.request('POST', '/color/trend', {
            body: JSON.stringify({
                historical_data: historicalData
            })
        });
    }

    // Vision Analysis
    async detectDefects(imageFile) {
        const formData = new FormData();
        formData.append('file', imageFile);
        
        const response = await fetch(`${this.config.baseUrl}/vision/detect`, {
            method: 'POST',
            headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async multiViewFusion(imageFiles) {
        const formData = new FormData();
        imageFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch(`${this.config.baseUrl}/vision/fusion`, {
            method: 'POST',
            headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    // RAG System
    async indexDocument(documentFile, metadata = null) {
        const formData = new FormData();
        formData.append('file', documentFile);
        if (metadata) {
            formData.append('metadata', JSON.stringify(metadata));
        }
        
        const response = await fetch(`${this.config.baseUrl}/rag/index`, {
            method: 'POST',
            headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async queryRAG(query, topK = 5) {
        return await this.request('POST', '/rag/query', {
            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        });
    }

    // Notifications
    async createNotification(notification) {
        return await this.request('POST', '/notifications', {
            body: JSON.stringify(notification)
        });
    }

    async listNotifications(limit = 50) {
        return await this.request('GET', `/notifications?limit=${limit}`);
    }

    async createAlert(alert) {
        return await this.request('POST', '/notifications/alerts', {
            body: JSON.stringify(alert)
        });
    }

    // Analytics
    async getMetrics(metricType, period = '24h') {
        return await this.request('GET', `/analytics/metrics/${metricType}?period=${period}`);
    }

    async generateReport(reportType, params) {
        return await this.request('POST', '/analytics/reports', {
            body: JSON.stringify({
                report_type: reportType,
                params: params
            })
        });
    }

    // Webhooks
    async createWebhook(webhook) {
        return await this.request('POST', '/webhooks', {
            body: JSON.stringify(webhook)
        });
    }

    async listWebhooks() {
        return await this.request('GET', '/webhooks');
    }

    async triggerWebhookEvent(event, payload) {
        return await this.request('POST', '/webhooks/trigger', {
            body: JSON.stringify({
                event: event,
                payload: payload
            })
        });
    }

    // Compliance
    async generateComplianceReport(standard, title, description) {
        const now = new Date().toISOString();
        return await this.request('POST', '/compliance/reports', {
            body: JSON.stringify({
                standard: standard,
                title: title,
                description: description,
                period_start: now,
                period_end: now
            })
        });
    }

    async listComplianceReports() {
        return await this.request('GET', '/compliance/reports');
    }

    // Export/Import
    async exportData(dataType, format = 'json', filters = {}) {
        return await this.request('POST', '/export-import/export', {
            body: JSON.stringify({
                data_type: dataType,
                format: format,
                filters: filters
            })
        });
    }

    async importData(dataType, data, format = 'json', overwrite = false) {
        return await this.request('POST', '/export-import/import', {
            body: JSON.stringify({
                data_type: dataType,
                format: format,
                data: data,
                overwrite: overwrite
            })
        });
    }

    // Multi-Factor Authentication
    async setupMFA() {
        return await this.request('POST', '/mfa/setup');
    }

    async enableMFA(secret, verificationCode) {
        return await this.request('POST', '/mfa/enable', {
            body: JSON.stringify({
                secret: secret,
                verification_code: verificationCode
            })
        });
    }

    async verifyMFA(code, method = 'totp') {
        return await this.request('POST', '/mfa/verify', {
            body: JSON.stringify({
                code: code,
                method: method
            })
        });
    }

    async disableMFA() {
        return await this.request('POST', '/mfa/disable');
    }

    // Cache Management
    async getCacheStatistics() {
        return await this.request('GET', '/cache/statistics');
    }

    async clearCache(level = 'memory') {
        return await this.request('POST', `/cache/clear?level=${level}`);
    }

    async invalidateCachePattern(pattern) {
        return await this.request('DELETE', `/cache/invalidate?pattern=${pattern}`);
    }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ICAPConfig, ICAPClient };
}

// Export for browser
if (typeof window !== 'undefined') {
    window.ICAPConfig = ICAPConfig;
    window.ICAPClient = ICAPClient;
}
