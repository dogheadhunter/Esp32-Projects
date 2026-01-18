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
        this.selectedDJ = '';
        this.selectedCategory = '';
        this.selectedStatus = 'pending';
        this.selectedWeatherType = '';
        this.dateFrom = '';
        this.dateTo = '';
        this.djs = [];
        
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
        await this.loadDJs();
        await this.loadReasons();
        await this.loadScripts();
        await this.updateStats();
    }
    
    setupEventListeners() {
        if (this.listenersAttached) return;
        this.listenersAttached = true;

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
        document.getElementById('djFilter').addEventListener('change', (e) => {
            this.selectedDJ = e.target.value;
            this.loadScripts();
        });
        
        // Category pills
        document.querySelectorAll('.category-pill').forEach(pill => {
            pill.addEventListener('click', (e) => {
                // Update active state
                document.querySelectorAll('.category-pill').forEach(p => {
                    p.classList.remove('active', 'bg-blue-600');
                    p.classList.add('bg-gray-700');
                });
                e.target.classList.add('active', 'bg-blue-600');
                e.target.classList.remove('bg-gray-700');
                
                // Update filter and reload
                this.selectedCategory = e.target.dataset.category;
                
                // Show/hide weather type filter based on category
                const weatherTypeContainer = document.getElementById('weatherTypeFilterContainer');
                if (this.selectedCategory === 'weather') {
                    weatherTypeContainer.classList.remove('hidden');
                } else {
                    weatherTypeContainer.classList.add('hidden');
                }
                
                this.loadScripts();
            });
        });
        
        // Advanced Filters
        document.getElementById('advancedFiltersToggle').addEventListener('click', () => this.toggleAdvancedFilters());
        document.getElementById('applyAdvFilters').addEventListener('click', () => this.applyAdvancedFilters());
        document.getElementById('resetAdvFilters').addEventListener('click', () => this.resetAdvancedFilters());
        
        document.getElementById('refreshBtn').addEventListener('click', () => this.refresh());
        
        // Stats dashboard
        document.getElementById('statsBtn').addEventListener('click', () => this.showStatsView());
        document.getElementById('closeStatsView').addEventListener('click', () => this.closeStatsView());
        
        // Timeline view
        document.getElementById('timelineViewBtn').addEventListener('click', () => this.showTimelineView());
        document.getElementById('closeTimelineView').addEventListener('click', () => this.closeTimelineView());
        
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
    
    async loadDJs() {
        try {
            const response = await api.getDJs();
            this.djs = response.djs || [];
            this.populateDJFilter();
        } catch (error) {
            console.error('Error loading DJs:', error);
            // Fallback - DJs will be populated from scripts
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
        const djFilter = this.selectedDJ || null;
        const categoryFilter = this.selectedCategory || null;
        const statusFilter = this.selectedStatus || null;
        const weatherTypeFilter = this.selectedWeatherType || null;
        const dateFrom = this.dateFrom || null;
        const dateTo = this.dateTo || null;
        
        // Show loading state
        const container = document.getElementById('cardContainer');
        container.innerHTML = '<div class="text-center text-gray-400 py-8">Loading scripts...</div>';
        
        try {
            const response = await api.getScripts(
                djFilter, 
                categoryFilter, 
                statusFilter, 
                weatherTypeFilter,
                dateFrom,
                dateTo,
                1, 
                20
            );
            this.scripts = response.scripts;
            this.currentIndex = 0;
            this.totalPages = response.total_pages;
            this.currentPage = response.page;
            this.hasMore = response.has_more;
            
            // Show/hide timeline view button based on story scripts
            const hasStoryScripts = this.scripts.some(s => 
                s.metadata.category === 'story' && s.metadata.story_info
            );
            const timelineBtn = document.getElementById('timelineViewBtn');
            if (hasStoryScripts) {
                timelineBtn.classList.remove('hidden');
            } else {
                timelineBtn.classList.add('hidden');
            }
            
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
        select.innerHTML = '<option value="">All DJs</option>';
        
        if (this.djs.length > 0) {
            this.djs.forEach(dj => {
                const option = document.createElement('option');
                option.value = dj.id;
                option.textContent = `${dj.name} - ${dj.region}`;
                select.appendChild(option);
            });
        }
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
        
        // Get category badge class
        const categoryClass = `badge-${script.metadata.category || 'general'}`;
        const categoryIcon = this.getCategoryIcon(script.metadata.category);
        
        // Build category-specific metadata section
        const categoryMetadata = this.buildCategoryMetadata(script);
        
        const card = document.createElement('div');
        card.className = 'review-card bg-gray-800 overflow-hidden';
        card.innerHTML = `
            <div class="approve-indicator">✓</div>
            <div class="reject-indicator">✗</div>
            
            <div class="h-full flex flex-col" style="max-height: 70vh;">
                <div class="bg-gradient-to-r from-blue-600 to-purple-600 p-4 flex-shrink-0">
                    <div class="flex items-center justify-between mb-2">
                        <h2 class="text-xl font-bold">${this.escapeHtml(script.metadata.dj)}</h2>
                        <span class="category-badge ${categoryClass}">
                            ${categoryIcon} ${script.metadata.category}
                        </span>
                    </div>
                    <p class="text-sm opacity-90">${this.escapeHtml(script.metadata.content_type)}</p>
                    <p class="text-xs opacity-75 mt-1">
                        ${new Date(script.metadata.timestamp).toLocaleString()} | 
                        ${script.metadata.word_count} words
                    </p>
                    ${categoryMetadata}
                </div>
                
                <div class="p-6 overflow-y-auto flex-1 scrollable-content" style="overscroll-behavior: contain; -webkit-overflow-scrolling: touch;">
                    <div class="prose prose-invert max-w-none">
                        <p class="whitespace-pre-wrap leading-relaxed">${this.escapeHtml(script.content)}</p>
                    </div>
                </div>
                
                <!-- Touch-friendly approve/reject buttons -->
                <div class="flex gap-3 p-4 bg-gray-900 flex-shrink-0 border-t border-gray-700">
                    <button id="rejectBtn" class="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-6 rounded-lg transition shadow-lg min-h-[56px]">
                        ✗ Reject
                    </button>
                    <button id="approveBtn" class="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-lg transition shadow-lg min-h-[56px]">
                        ✓ Approve
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = '';
        container.appendChild(card);
        
        // Add button event listeners
        const approveBtn = card.querySelector('#approveBtn');
        const rejectBtn = card.querySelector('#rejectBtn');
        
        if (approveBtn) {
            approveBtn.addEventListener('click', () => this.approveCurrentScript());
        }
        
        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => this.rejectCurrentScript());
        }
        
        // Initialize swipe handler
        if (this.swipeHandler) {
            this.swipeHandler.destroy();
        }
        
        this.swipeHandler = new SwipeHandler(card, {
            onApprove: () => this.approveCurrentScript(),
            onReject: () => this.rejectCurrentScript()
        });
    }
    
    buildCategoryMetadata(script) {
        const category = script.metadata.category;
        
        if (category === 'weather' && script.metadata.weather_state) {
            return this.buildWeatherMetadata(script.metadata.weather_state);
        } else if (category === 'story' && script.metadata.story_info) {
            return this.buildStoryMetadata(script.metadata.story_info);
        }
        
        return '';
    }
    
    buildWeatherMetadata(weatherState) {
        const parts = [];
        
        if (weatherState.current) {
            const emoji = this.getWeatherEmoji(weatherState.current.type);
            parts.push(`<span class="inline-flex items-center">
                <span class="text-xl mr-1">${emoji}</span>
                <span>${this.capitalize(weatherState.current.type)}, ${weatherState.current.temperature}°F</span>
            </span>`);
        }
        
        if (weatherState.is_emergency) {
            parts.push(`<span class="inline-flex items-center text-red-400 font-semibold">
                <span class="mr-1">⚠️</span> Emergency Alert
            </span>`);
        }
        
        if (weatherState.continuity) {
            parts.push(`<span class="text-xs opacity-80">Continuity: ${this.escapeHtml(weatherState.continuity)}</span>`);
        }
        
        if (parts.length === 0) return '';
        
        return `<div class="mt-2 pt-2 border-t border-white/20 space-y-1 text-xs">
            ${parts.join('<br>')}
        </div>`;
    }
    
    buildStoryMetadata(storyInfo) {
        const parts = [];
        
        if (storyInfo.timeline) {
            const tlEmoji = {
                'daily': '📅',
                'weekly': '📆',
                'monthly': '🗓️',
                'yearly': '📕'
            }[storyInfo.timeline.toLowerCase()] || '📖';
            parts.push(`<span class="inline-flex items-center">
                <span class="mr-1">${tlEmoji}</span>
                <span>${this.capitalize(storyInfo.timeline)} Story</span>
            </span>`);
        }
        
        if (storyInfo.act_position) {
            const actType = this.capitalize(storyInfo.act_position.type);
            const actNum = storyInfo.act_position.index + 1;
            const totalActs = storyInfo.act_position.total;
            parts.push(`<span class="inline-flex items-center">
                <span class="mr-1">🎬</span>
                <span>Act ${actNum}/${totalActs}: ${actType}</span>
            </span>`);
        }
        
        if (storyInfo.engagement_score !== undefined) {
            const score = Math.round(storyInfo.engagement_score * 100);
            const emoji = score >= 75 ? '🔥' : score >= 50 ? '👍' : '📊';
            parts.push(`<span class="inline-flex items-center">
                <span class="mr-1">${emoji}</span>
                <span>Engagement: ${score}%</span>
            </span>`);
        }
        
        if (parts.length === 0) return '';
        
        return `<div class="mt-2 pt-2 border-t border-white/20 space-y-1 text-xs">
            ${parts.join('<br>')}
        </div>`;
    }
    
    getWeatherEmoji(weatherType) {
        const emojis = {
            'sunny': '☀️',
            'cloudy': '☁️',
            'rainy': '🌧️',
            'rad_storm': '☢️',
            'dust_storm': '🌪️',
            'glowing_fog': '☁️',
            'foggy': '🌫️',
            'snowy': '❄️'
        };
        return emojis[weatherType] || '🌤️';
    }
    
    capitalize(str) {
        if (!str) return '';
        return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
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
    
    getCategoryIcon(category) {
        const icons = {
            'weather': '⛈️',
            'story': '📖',
            'news': '📰',
            'gossip': '💬',
            'music': '🎵',
            'general': '📄'
        };
        return icons[category] || '📄';
    }
    
    async showTimelineView() {
        const modal = document.getElementById('timelineModal');
        const content = document.getElementById('timelineContent');
        
        modal.classList.add('active');
        content.innerHTML = '<p class="text-gray-400 text-center py-8">Loading story timelines...</p>';
        
        try {
            // Group scripts by story timeline
            const storyScripts = this.scripts.filter(s => 
                s.metadata.category === 'story' && s.metadata.story_info
            );
            
            if (storyScripts.length === 0) {
                content.innerHTML = `
                    <div class="text-center text-gray-400 py-8">
                        <div class="text-6xl mb-4">📖</div>
                        <p class="text-xl">No story scripts found</p>
                        <p class="mt-2">Story scripts will appear here when available.</p>
                    </div>
                `;
                return;
            }
            
            // Group by timeline
            const byTimeline = {
                daily: [],
                weekly: [],
                monthly: [],
                yearly: []
            };
            
            storyScripts.forEach(script => {
                const timeline = (script.metadata.story_info.timeline || 'daily').toLowerCase();
                if (byTimeline[timeline]) {
                    byTimeline[timeline].push(script);
                }
            });
            
            // Build timeline view
            let html = '';
            const timelineOrder = ['daily', 'weekly', 'monthly', 'yearly'];
            const timelineEmojis = {
                daily: '📅',
                weekly: '📆',
                monthly: '🗓️',
                yearly: '📕'
            };
            
            timelineOrder.forEach(timeline => {
                const scripts = byTimeline[timeline];
                if (scripts.length === 0) return;
                
                html += `
                    <div class="bg-gray-900 rounded-lg p-4">
                        <h3 class="text-lg font-bold mb-3 flex items-center">
                            <span class="text-2xl mr-2">${timelineEmojis[timeline]}</span>
                            ${this.capitalize(timeline)} Timeline (${scripts.length} script${scripts.length > 1 ? 's' : ''})
                        </h3>
                        <div class="space-y-2">
                `;
                
                scripts.forEach(script => {
                    const actInfo = script.metadata.story_info.act_position;
                    const actLabel = actInfo ? 
                        `Act ${actInfo.index + 1}/${actInfo.total}: ${this.capitalize(actInfo.type)}` :
                        'Unknown Act';
                    
                    const engagement = script.metadata.story_info.engagement_score !== undefined ?
                        `${Math.round(script.metadata.story_info.engagement_score * 100)}%` :
                        'N/A';
                    
                    html += `
                        <div class="bg-gray-800 p-3 rounded border-l-4 border-purple-500">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <div class="font-semibold">${this.escapeHtml(script.metadata.content_type)}</div>
                                    <div class="text-sm text-gray-400 mt-1">
                                        🎬 ${actLabel} | 📊 Engagement: ${engagement}
                                    </div>
                                    <div class="text-xs text-gray-500 mt-1">
                                        ${new Date(script.metadata.timestamp).toLocaleString()}
                                    </div>
                                </div>
                                <div class="text-xs bg-gray-700 px-2 py-1 rounded">
                                    ${script.metadata.word_count} words
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            });
            
            content.innerHTML = html;
            
        } catch (error) {
            console.error('Error showing timeline view:', error);
            content.innerHTML = `
                <div class="text-center text-red-400 py-8">
                    <p class="text-xl">Error loading timeline</p>
                    <p class="mt-2 text-sm">${this.escapeHtml(error.message)}</p>
                </div>
            `;
        }
    }
    
    closeTimelineView() {
        document.getElementById('timelineModal').classList.remove('active');
    }
    
    toggleAdvancedFilters() {
        const panel = document.getElementById('advancedFiltersPanel');
        const toggle = document.getElementById('advancedFiltersToggle');
        
        if (panel.classList.contains('hidden')) {
            panel.classList.remove('hidden');
            toggle.textContent = '⚙️ Hide Advanced Filters';
        } else {
            panel.classList.add('hidden');
            toggle.textContent = '⚙️ Advanced Filters';
        }
    }
    
    applyAdvancedFilters() {
        // Get filter values
        this.selectedStatus = document.getElementById('statusFilter').value;
        this.selectedWeatherType = document.getElementById('weatherTypeFilter').value;
        this.dateFrom = document.getElementById('dateFromFilter').value;
        this.dateTo = document.getElementById('dateToFilter').value;
        
        // Update indicator
        const hasActiveFilters = this.selectedStatus || this.selectedWeatherType || this.dateFrom || this.dateTo;
        const indicator = document.getElementById('advFilterIndicator');
        
        if (hasActiveFilters) {
            indicator.classList.remove('hidden');
        } else {
            indicator.classList.add('hidden');
        }
        
        // Reload scripts with new filters
        this.loadScripts();
        
        this.showToast('Filters applied', 'success');
    }
    
    resetAdvancedFilters() {
        // Clear filter values
        document.getElementById('statusFilter').value = '';
        document.getElementById('weatherTypeFilter').value = '';
        document.getElementById('dateFromFilter').value = '';
        document.getElementById('dateToFilter').value = '';
        
        // Clear state
        this.selectedStatus = '';
        this.selectedWeatherType = '';
        this.dateFrom = '';
        this.dateTo = '';
        
        // Hide indicator
        document.getElementById('advFilterIndicator').classList.add('hidden');
        
        // Reload scripts
        this.loadScripts();
        
        this.showToast('Filters reset', 'success');
    }
    
    async showStatsView() {
        const modal = document.getElementById('statsModal');
        const content = document.getElementById('statsContent');
        
        modal.classList.add('active');
        content.innerHTML = '<p class="text-gray-400 text-center py-8">Loading statistics...</p>';
        
        try {
            const stats = await api.getDetailedStats();
            
            let html = `
                <!-- Overview Section -->
                <div class="bg-gray-700 rounded-lg p-6">
                    <h3 class="text-xl font-bold mb-4">📊 Overview</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-gray-800 p-4 rounded text-center">
                            <div class="text-3xl font-bold text-yellow-400">${stats.overview.total_pending}</div>
                            <div class="text-sm text-gray-400 mt-1">Pending</div>
                        </div>
                        <div class="bg-gray-800 p-4 rounded text-center">
                            <div class="text-3xl font-bold text-green-400">${stats.overview.total_approved}</div>
                            <div class="text-sm text-gray-400 mt-1">Approved</div>
                        </div>
                        <div class="bg-gray-800 p-4 rounded text-center">
                            <div class="text-3xl font-bold text-red-400">${stats.overview.total_rejected}</div>
                            <div class="text-sm text-gray-400 mt-1">Rejected</div>
                        </div>
                        <div class="bg-gray-800 p-4 rounded text-center">
                            <div class="text-3xl font-bold text-blue-400">${stats.overview.approval_rate}%</div>
                            <div class="text-sm text-gray-400 mt-1">Approval Rate</div>
                        </div>
                    </div>
                </div>
                
                <!-- Category Breakdown -->
                <div class="bg-gray-700 rounded-lg p-6">
                    <h3 class="text-xl font-bold mb-4">📂 By Category</h3>
                    <div class="space-y-3">
            `;
            
            Object.entries(stats.by_category).forEach(([category, counts]) => {
                const total = counts.pending + counts.approved + counts.rejected;
                const categoryIcon = this.getCategoryIcon(category);
                
                html += `
                    <div class="bg-gray-800 p-4 rounded">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium">${categoryIcon} ${this.capitalize(category)}</span>
                            <span class="text-gray-400 text-sm">Total: ${total}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-sm">
                            <div class="text-center">
                                <div class="text-yellow-400">${counts.pending}</div>
                                <div class="text-gray-500 text-xs">Pending</div>
                            </div>
                            <div class="text-center">
                                <div class="text-green-400">${counts.approved}</div>
                                <div class="text-gray-500 text-xs">Approved</div>
                            </div>
                            <div class="text-center">
                                <div class="text-red-400">${counts.rejected}</div>
                                <div class="text-gray-500 text-xs">Rejected</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
                
                <!-- DJ Breakdown -->
                <div class="bg-gray-700 rounded-lg p-6">
                    <h3 class="text-xl font-bold mb-4">🎙️ By DJ</h3>
                    <div class="space-y-3">
            `;
            
            Object.entries(stats.by_dj).forEach(([dj, counts]) => {
                const total = counts.pending + counts.approved + counts.rejected;
                const approvalRate = (counts.approved + counts.rejected) > 0 
                    ? Math.round((counts.approved / (counts.approved + counts.rejected)) * 100)
                    : 0;
                
                html += `
                    <div class="bg-gray-800 p-4 rounded">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium">${this.escapeHtml(dj)}</span>
                            <span class="text-gray-400 text-sm">Approval: ${approvalRate}%</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-sm">
                            <div class="text-center">
                                <div class="text-yellow-400">${counts.pending}</div>
                                <div class="text-gray-500 text-xs">Pending</div>
                            </div>
                            <div class="text-center">
                                <div class="text-green-400">${counts.approved}</div>
                                <div class="text-gray-500 text-xs">Approved</div>
                            </div>
                            <div class="text-center">
                                <div class="text-red-400">${counts.rejected}</div>
                                <div class="text-gray-500 text-xs">Rejected</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
            
            content.innerHTML = html;
            
        } catch (error) {
            console.error('Error showing stats:', error);
            content.innerHTML = `
                <div class="text-center text-red-400 py-8">
                    <p class="text-xl">Error loading statistics</p>
                    <p class="mt-2 text-sm">${this.escapeHtml(error.message)}</p>
                </div>
            `;
        }
    }
    
    closeStatsView() {
        document.getElementById('statsModal').classList.remove('active');
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ScriptReviewApp());
} else {
    new ScriptReviewApp();
}
