/**
 * Main Application Logic
 */

class ScriptReviewApp {
    constructor() {
        this.scripts = [];
        this.currentIndex = 0;
        this.reasons = [];
        this.swipeHandler = null;
        this.pendingRejectScript = null;
        
        // Set up auth event listeners first (always needed)
        document.getElementById('loginBtn').addEventListener('click', () => this.handleLogin());
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        document.getElementById('apiToken').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        
        this.init();
    }
    
    async init() {
        // Check authentication
        if (!api.getToken()) {
            this.showAuthModal();
            return;
        }
        
        // Hide auth modal if token exists
        document.getElementById('authModal').classList.remove('active');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load data
        await this.loadReasons();
        await this.loadScripts();
        await this.updateStats();
    }
    
    setupEventListeners() {
        if (this.listenersAttached) return;
        this.listenersAttached = true;

        // Action buttons
        document.getElementById('approveBtn').addEventListener('click', () => this.approveCurrentScript());
        document.getElementById('rejectBtn').addEventListener('click', () => this.rejectCurrentScript());
        
        // Rejection modal
        document.getElementById('confirmReject').addEventListener('click', () => this.confirmReject());
        document.getElementById('cancelReject').addEventListener('click', () => this.cancelReject());
        document.getElementById('rejectionReason').addEventListener('change', (e) => {
            const customComment = document.getElementById('customComment');
            if (e.target.value === 'other') {
                customComment.classList.remove('hidden');
            } else {
                customComment.classList.add('hidden');
            }
        });
        
        // Filters
        document.getElementById('djFilter').addEventListener('change', () => this.loadScripts());
        document.getElementById('refreshBtn').addEventListener('click', () => this.refresh());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') {
                this.approveCurrentScript();
            } else if (e.key === 'ArrowLeft') {
                this.rejectCurrentScript();
            }
        });
    }
    
    showAuthModal() {
        document.getElementById('authModal').classList.add('active');
    }
    
    async handleLogin() {
        const token = document.getElementById('apiToken').value.trim();
        if (!token) {
            this.showToast('Please enter an API token', 'error');
            return;
        }
        
        api.setToken(token);
        
        try {
            // Test token by fetching stats
            await api.getStats();
            document.getElementById('authModal').classList.remove('active');
            
            // Setup listeners after login
            this.setupEventListeners();
            
            // Load data
            await this.loadReasons();
            await this.loadScripts();
            await this.updateStats();
        } catch (error) {
            this.showToast('Invalid API token', 'error');
            api.setToken('');
        }
    }
    
    async loadReasons() {
        try {
            this.reasons = await api.getReasons();
            this.populateReasonDropdown();
        } catch (error) {
            console.error('Error loading reasons:', error);
            this.showToast('Error loading rejection reasons', 'error');
        }
    }
    
    populateReasonDropdown() {
        const select = document.getElementById('rejectionReason');
        select.innerHTML = '<option value="">Select a reason...</option>';
        
        this.reasons.forEach(reason => {
            const option = document.createElement('option');
            option.value = reason.id;
            option.textContent = reason.label;
            select.appendChild(option);
        });
    }
    
    async loadScripts() {
        const djFilter = document.getElementById('djFilter').value;
        
        try {
            const response = await api.getScripts(djFilter || null, 1, 20);
            this.scripts = response.scripts;
            this.currentIndex = 0;
            this.totalPages = response.total_pages;
            this.currentPage = response.page;
            this.hasMore = response.has_more;
            
            // Populate DJ filter if empty
            this.populateDJFilter();
            
            if (this.scripts.length === 0) {
                this.showNoScripts();
            } else {
                this.showCurrentScript();
            }
        } catch (error) {
            console.error('Error loading scripts:', error);
            this.showToast('Error loading scripts: ' + error.message, 'error');
            
            if (error.message.includes('Authentication')) {
                this.showAuthModal();
            }
        }
    }
    
    populateDJFilter() {
        const select = document.getElementById('djFilter');
        const currentValue = select.value;
        
        // Get unique DJs from scripts
        const djs = [...new Set(this.scripts.map(s => s.metadata.dj))].sort();
        
        // Only update if we have new DJs
        if (djs.length > 0 && select.options.length === 1) {
            djs.forEach(dj => {
                const option = document.createElement('option');
                option.value = dj;
                option.textContent = dj;
                select.appendChild(option);
            });
        }
        
        select.value = currentValue;
    }
    
    showNoScripts() {
        const container = document.getElementById('cardContainer');
        container.innerHTML = `
            <div id="noScripts" class="text-center text-gray-400">
                <div class="text-6xl mb-4">✅</div>
                <p class="text-xl">All scripts reviewed!</p>
                <p class="mt-2">Great job! Click refresh to check for new scripts.</p>
            </div>
        `;
    }
    
    showCurrentScript() {
        if (this.currentIndex >= this.scripts.length) {
            this.showNoScripts();
            return;
        }
        
        const script = this.scripts[this.currentIndex];
        const container = document.getElementById('cardContainer');
        
        const card = document.createElement('div');
        card.className = 'review-card bg-gray-800 overflow-hidden';
        card.innerHTML = `
            <div class="approve-indicator">✓</div>
            <div class="reject-indicator">✗</div>
            
            <div class="h-full flex flex-col">
                <div class="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
                    <h2 class="text-xl font-bold">${this.escapeHtml(script.metadata.dj)}</h2>
                    <p class="text-sm opacity-90">${this.escapeHtml(script.metadata.content_type)}</p>
                    <p class="text-xs opacity-75 mt-1">
                        ${new Date(script.metadata.timestamp).toLocaleString()} | 
                        ${script.metadata.word_count} words
                    </p>
                </div>
                
                <div class="p-6">
                    <div class="prose prose-invert max-w-none">
                        <p class="whitespace-pre-wrap leading-relaxed">${this.escapeHtml(script.content)}</p>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = '';
        container.appendChild(card);
        
        // Swipe disabled - buttons work better on mobile with scrolling
        if (this.swipeHandler) {
            this.swipeHandler.destroy();
            this.swipeHandler = null;
        }
    }
    
    async approveCurrentScript() {
        if (this.currentIndex >= this.scripts.length) return;
        
        const script = this.scripts[this.currentIndex];
        const card = document.querySelector('.review-card');
        
        if (!card || card.classList.contains('approved') || card.classList.contains('rejected')) {
            return;
        }
        
        card.classList.add('approved');
        
        try {
            await api.reviewScript(script.metadata.script_id, 'approved');
            this.showToast('Script approved! ✓', 'success');
            
            setTimeout(() => {
                this.currentIndex++;
                this.showCurrentScript();
                this.updateStats();
            }, 300);
        } catch (error) {
            console.error('Error approving script:', error);
            this.showToast('Error approving script', 'error');
            card.classList.remove('approved');
        }
    }
    
    rejectCurrentScript() {
        if (this.currentIndex >= this.scripts.length) return;
        
        const script = this.scripts[this.currentIndex];
        const card = document.querySelector('.review-card');
        
        if (!card || card.classList.contains('approved') || card.classList.contains('rejected')) {
            return;
        }
        
        this.pendingRejectScript = script;
        document.getElementById('rejectionModal').classList.add('active');
    }
    
    async confirmReject() {
        const reasonId = document.getElementById('rejectionReason').value;
        const customComment = document.getElementById('customComment').value.trim();
        
        if (!reasonId) {
            this.showToast('Please select a rejection reason', 'error');
            return;
        }
        
        if (reasonId === 'other' && !customComment) {
            this.showToast('Please provide a custom comment', 'error');
            return;
        }
        
        const card = document.querySelector('.review-card');
        card.classList.add('rejected');
        
        try {
            await api.reviewScript(
                this.pendingRejectScript.metadata.script_id,
                'rejected',
                reasonId,
                customComment || null
            );
            
            this.showToast('Script rejected ✗', 'success');
            this.closeRejectionModal();
            
            setTimeout(() => {
                this.currentIndex++;
                this.showCurrentScript();
                this.updateStats();
            }, 300);
        } catch (error) {
            console.error('Error rejecting script:', error);
            this.showToast('Error rejecting script', 'error');
            card.classList.remove('rejected');
        }
    }
    
    cancelReject() {
        this.closeRejectionModal();
        
        // Reset card position
        const card = document.querySelector('.review-card');
        if (card) {
            card.style.transform = '';
        }
    }
    
    closeRejectionModal() {
        document.getElementById('rejectionModal').classList.remove('active');
        document.getElementById('rejectionReason').value = '';
        document.getElementById('customComment').value = '';
        document.getElementById('customComment').classList.add('hidden');
        this.pendingRejectScript = null;
    }
    
    async updateStats() {
        try {
            const stats = await api.getStats();
            const statsEl = document.getElementById('stats');
            statsEl.textContent = `Pending: ${stats.total_pending} | Approved: ${stats.total_approved} | Rejected: ${stats.total_rejected}`;
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }
    
    async refresh() {
        await this.loadScripts();
        await this.updateStats();
        this.showToast('Refreshed!', 'success');
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ScriptReviewApp());
} else {
    new ScriptReviewApp();
}
