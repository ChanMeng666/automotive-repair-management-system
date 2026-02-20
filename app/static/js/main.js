// AutoRepair Pro - Main JavaScript
// ================================
// Precision Industrial Theme

// Design System Colors
const DesignColors = {
    primary: '#1e3a5f',
    primaryHover: '#152a45',
    accent: '#e85d04',
    success: '#2d6a4f',
    warning: '#e9c46a',
    error: '#c1121f',
    info: '#219ebc',
    gray500: '#64748b'
};

// Global application state
const AutoRepairApp = {
    currentUser: null,
    notifications: [],
    settings: {},

    init() {
        this.initializeLucideIcons();
        this.setupEventListeners();
        this.loadUserPreferences();
        this.initializeComponents();
        this.setupNotifications();
    },

    // Initialize Lucide Icons
    initializeLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    },
    
    setupEventListeners() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMLoaded();
        });
        
        // Handle form submissions with loading states
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
        
        // Setup search functionality
        this.setupGlobalSearch();
        
        // Setup tooltips and popovers
        this.initializeBootstrapComponents();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    },
    
    onDOMLoaded() {
        // Add loading animations
        this.addLoadingAnimations();
        
        // Setup auto-save for forms
        this.setupAutoSave();
        
        // Initialize data tables
        this.initializeDataTables();
        
        // Setup live updates
        this.setupLiveUpdates();

        // Initialize charts
        this.initializeCharts();
    },
    
    // Form handling with enhanced UX
    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (submitBtn && !form.dataset.noLoadingState) {
            this.showFormLoading(submitBtn);
            this.showLoadingIndicator(); // Show global loading indicator
            
            // Reset loading state after timeout (fallback)
            setTimeout(() => {
                this.hideFormLoading(submitBtn);
                this.hideLoadingIndicator(); // Hide global loading indicator
            }, 10000);
        }
        
        // Validate form before submission
        if (!this.validateForm(form)) {
            event.preventDefault();
            this.hideFormLoading(submitBtn);
            this.hideLoadingIndicator(); // Hide global loading indicator if validation fails
        }
    },
    
    showFormLoading(button) {
        if (!button) return;
        
        button.disabled = true;
        button.classList.add('loading');
        
        const originalText = button.innerHTML;
        button.dataset.originalText = originalText;
        
        const icon = button.querySelector('i');
        if (icon) {
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        } else {
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + button.textContent;
        }
    },
    
    hideFormLoading(button) {
        if (!button) return;
        
        button.disabled = false;
        button.classList.remove('loading');
        
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    },
    
    validateForm(form) {
        const inputs = form.querySelectorAll('[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                this.showFieldError(input, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(input);
                
                // Additional validation based on input type
                if (input.type === 'email' && !this.isValidEmail(input.value)) {
                    this.showFieldError(input, 'Please enter a valid email address');
                    isValid = false;
                }
                
                if (input.type === 'tel' && !this.isValidPhone(input.value)) {
                    this.showFieldError(input, 'Please enter a valid phone number');
                    isValid = false;
                }
            }
        });

        return isValid;
    },
    
    showFieldError(input, message) {
        input.classList.add('is-invalid');
        
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    },
    
    clearFieldError(input) {
        input.classList.remove('is-invalid');
        const feedback = input.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = '';
        }
    },
    
    // Global search functionality
    setupGlobalSearch() {
        const searchInput = document.getElementById('globalSearch');
        if (!searchInput) return;
        
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            
            searchTimeout = setTimeout(() => {
                this.performGlobalSearch(e.target.value);
            }, 300);
        });
        
        // Setup search results dropdown
        this.createSearchDropdown(searchInput);
    },
    
    createSearchDropdown(searchInput) {
        const dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
            display: none;
        `;
        
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(dropdown);
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.parentNode.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    },
    
    async performGlobalSearch(query) {
        if (!query || query.length < 2) {
            this.hideSearchResults();
            return;
        }

        try {
            this.showSearchLoading();

            const response = await fetch(`/api/search/customers?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`Search request failed: ${response.status}`);
            }

            const customers = await response.json();
            const results = customers.map(c => ({
                type: 'customer',
                id: c.customer_id,
                title: c.full_name,
                subtitle: [c.email, c.phone].filter(Boolean).join(' | ')
            }));

            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError();
        }
    },
    
    displaySearchResults(results) {
        const dropdown = document.querySelector('.search-dropdown');
        if (!dropdown) return;

        if (results.length === 0) {
            dropdown.innerHTML = `
                <div class="p-3 text-center text-muted">
                    <i data-lucide="search" style="width: 16px; height: 16px; vertical-align: text-bottom;"></i>
                    No results found
                </div>
            `;
        } else {
            dropdown.innerHTML = results.map(result => `
                <div class="search-result-item p-3 border-bottom" data-type="${result.type}" data-id="${result.id}">
                    <div class="d-flex align-items-center">
                        <i data-lucide="${result.type === 'customer' ? 'user' : 'wrench'}" class="me-3 text-primary" style="width: 20px; height: 20px;"></i>
                        <div>
                            <div class="fw-semibold">${result.title}</div>
                            <small class="text-muted">${result.subtitle}</small>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Add click handlers
            dropdown.querySelectorAll('.search-result-item').forEach(item => {
                item.style.cursor = 'pointer';
                item.addEventListener('click', () => {
                    this.handleSearchResultClick(item.dataset.type, item.dataset.id);
                });
                
                item.addEventListener('mouseenter', () => {
                    item.style.backgroundColor = '#f8fafc';
                });
                
                item.addEventListener('mouseleave', () => {
                    item.style.backgroundColor = 'white';
                });
            });
        }
        
        dropdown.style.display = 'block';
    },
    
    handleSearchResultClick(type, id) {
        // Navigate to the appropriate page
        if (type === 'customer') {
            window.location.href = `/customers/${id}`;
        } else if (type === 'job') {
            window.location.href = `/jobs/${id}`;
        }

        this.hideSearchResults();
    },
    
    showSearchLoading() {
        const dropdown = document.querySelector('.search-dropdown');
        if (dropdown) {
            dropdown.innerHTML = `
                <div class="p-3 text-center">
                    <div class="spinner-border spinner-border-sm me-2"></div>
                    Searching...
                </div>
            `;
            dropdown.style.display = 'block';
        }
    },

    showSearchError() {
        const dropdown = document.querySelector('.search-dropdown');
        if (dropdown) {
            dropdown.innerHTML = `
                <div class="p-3 text-center text-danger">
                    <i data-lucide="alert-triangle" style="width: 16px; height: 16px; vertical-align: text-bottom;"></i>
                    Search error occurred
                </div>
            `;
            // Re-initialize Lucide icons for the new content
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    },
    
    hideSearchResults() {
        const dropdown = document.querySelector('.search-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    },

    // Global Loading Indicator
    showLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.classList.remove('d-none');
        }
    },

    hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.classList.add('d-none');
        }
    },
    
    // Auto-save functionality
    setupAutoSave() {
        const forms = document.querySelectorAll('[data-autosave]');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    this.autoSaveForm(form);
                });
            });
        });
    },
    
    autoSaveForm(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Save to localStorage
        const formId = form.id || 'auto-save-form';
        localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
        
        this.showAutoSaveIndicator();
    },
    
    showAutoSaveIndicator() {
        // Create or update auto-save indicator
        let indicator = document.getElementById('autosave-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'autosave-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${DesignColors.success};
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 1050;
                opacity: 0;
                transition: opacity 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            document.body.appendChild(indicator);
        }

        indicator.innerHTML = '<i data-lucide="check" style="width: 16px; height: 16px;"></i>Auto-saved';
        indicator.style.opacity = '1';

        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    },
    
    // Notification system
    setupNotifications() {
        this.loadNotifications();
        this.updateNotificationBadge();
        
        // Setup notification dropdown
        const notificationDropdown = document.querySelector('[data-bs-toggle="dropdown"]');
        if (notificationDropdown) {
            notificationDropdown.addEventListener('click', () => {
                this.markNotificationsAsRead();
            });
        }
    },
    
    loadNotifications() {
        // In a real app, this would fetch from an API
        this.notifications = [
            {
                id: 1,
                title: 'Overdue Payment',
                message: 'Customer #1234 payment is overdue',
                type: 'warning',
                timestamp: new Date(),
                read: false
            },
            {
                id: 2,
                title: 'Job Completed',
                message: 'Job #5678 has been marked as complete',
                type: 'success',
                timestamp: new Date(),
                read: false
            }
        ];
    },
    
    updateNotificationBadge() {
        const badge = document.querySelector('.navbar .badge');
        if (badge) {
            const unreadCount = this.notifications.filter(n => !n.read).length;
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'inline' : 'none';
        }
    },
    
    markNotificationsAsRead() {
        this.notifications.forEach(notification => {
            notification.read = true;
        });
        this.updateNotificationBadge();
    },
    
    // Initialize Bootstrap components
    initializeBootstrapComponents() {
        // Initialize tooltips
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
        
        // Initialize popovers
        const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(popover => {
            new bootstrap.Popover(popover);
        });
    },
    
    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('globalSearch');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape to close modals and dropdowns
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.show');
                if (activeModal) {
                    const modal = bootstrap.Modal.getInstance(activeModal);
                    if (modal) modal.hide();
                }
                
                this.hideSearchResults();
            }
        });
    },
    
    // Add loading animations to elements
    addLoadingAnimations() {
        const animatedElements = document.querySelectorAll('.stat-card, .action-card, .card');
        
        animatedElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });
    },
    
    // Data table initialization
    initializeDataTables() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            // Add hover effects
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                row.addEventListener('mouseenter', () => {
                    row.style.transform = 'translateX(4px)';
                    row.style.transition = 'transform 0.2s ease';
                });
                
                row.addEventListener('mouseleave', () => {
                    row.style.transform = 'translateX(0)';
                });
            });
        });
    },

    // Chart initialization with Precision Industrial colors
    initializeCharts() {
        const isDashboard = window.location.pathname.includes('dashboard');
        const monthlyRevenueCtx = document.getElementById('monthlyRevenueChart');
        const jobStatusCtx = document.getElementById('jobStatusChart');

        if (!monthlyRevenueCtx && !jobStatusCtx) return;

        if (isDashboard) {
            // Determine API URL - check if we're in an org-scoped route
            const pathParts = window.location.pathname.split('/');
            const orgIndex = pathParts.indexOf('org');
            let apiUrl = '/administrator/api/dashboard/summary';
            if (orgIndex !== -1 && pathParts[orgIndex + 1]) {
                const slug = pathParts[orgIndex + 1];
                apiUrl = `/org/${slug}/administrator/api/dashboard/summary`;
            }

            fetch(apiUrl)
                .then(res => res.ok ? res.json() : Promise.reject(res.status))
                .then(data => {
                    this._renderJobStatusChart(jobStatusCtx, data.jobs);
                    this._renderRevenueChart(monthlyRevenueCtx);
                })
                .catch(err => {
                    console.warn('Dashboard API unavailable, using fallback data:', err);
                    this._renderJobStatusChart(jobStatusCtx, null);
                    this._renderRevenueChart(monthlyRevenueCtx);
                });
        } else {
            this._renderJobStatusChart(jobStatusCtx, null);
            this._renderRevenueChart(monthlyRevenueCtx);
        }
    },

    _renderRevenueChart(ctx) {
        if (!ctx) return;
        // TODO: Connect to a monthly revenue API endpoint when available
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Monthly Revenue',
                    data: [12000, 19000, 30000, 50000, 20000, 30000, 45000, 35000, 40000, 55000, 60000, 70000],
                    borderColor: DesignColors.primary,
                    backgroundColor: 'rgba(30, 58, 95, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: DesignColors.accent,
                    pointBorderColor: DesignColors.accent,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: DesignColors.accent,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(30, 58, 95, 0.08)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    },

    _renderJobStatusChart(ctx, jobsData) {
        if (!ctx) return;

        let completed = 300, pending = 50, inProgress = 150, cancelled = 20;
        if (jobsData) {
            completed = jobsData.completed_jobs || 0;
            pending = jobsData.pending_jobs || 0;
            inProgress = (jobsData.total_jobs || 0) - completed - pending;
            if (inProgress < 0) inProgress = 0;
            cancelled = 0;
        }

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Pending', 'Cancelled'],
                datasets: [{
                    label: 'Job Status',
                    data: [completed, inProgress, pending, cancelled],
                    backgroundColor: [
                        DesignColors.success,
                        DesignColors.info,
                        DesignColors.warning,
                        DesignColors.error
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 20, usePointStyle: true, pointStyle: 'circle' }
                    }
                },
                cutout: '60%'
            }
        });
    },
    
    // Live updates simulation
    setupLiveUpdates() {
        // In a real application, this would use WebSockets or Server-Sent Events
        if (window.location.pathname.includes('dashboard') || 
            window.location.pathname.includes('current-jobs')) {
            
            setInterval(() => {
                this.checkForUpdates();
            }, 30000); // Check every 30 seconds
        }
    },
    
    async checkForUpdates() {
        try {
            // Simulate checking for updates
            const hasUpdates = Math.random() > 0.8;
            
            if (hasUpdates) {
                this.showUpdateNotification();
            }
        } catch (error) {
            console.error('Update check failed:', error);
        }
    },
    
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-dismissible fade show position-fixed';
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 1050;
            max-width: 300px;
            background: ${DesignColors.info};
            color: white;
            border: none;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;

        notification.innerHTML = `
            <i data-lucide="info" style="width: 18px; height: 18px;"></i>
            New updates available
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },
    
    // User preferences
    loadUserPreferences() {
        const savedPrefs = localStorage.getItem('autorepair_preferences');
        if (savedPrefs) {
            this.settings = JSON.parse(savedPrefs);
            this.applyUserPreferences();
        }
    },
    
    saveUserPreferences() {
        localStorage.setItem('autorepair_preferences', JSON.stringify(this.settings));
    },
    
    applyUserPreferences() {
        // Apply theme preferences
        if (this.settings.theme === 'dark') {
            document.body.classList.add('dark-theme');
        }
        
        // Apply other preferences
        if (this.settings.animations === false) {
            document.body.classList.add('no-animations');
        }
    },
    
    // Utility functions
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    },
    
    showToast(message, type = 'info') {
        const iconMap = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        const colorMap = {
            success: DesignColors.success,
            error: DesignColors.error,
            warning: DesignColors.warning,
            info: DesignColors.info
        };

        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white border-0';
        toast.style.backgroundColor = colorMap[type] || colorMap.info;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i data-lucide="${iconMap[type] || 'info'}" style="width: 18px; height: 18px;"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Re-initialize Lucide icons for the new content
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Re-initialize Lucide icons (useful after dynamic content updates)
    refreshIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
};

// Initialize the application
AutoRepairApp.init();

// Expose to global scope for debugging
window.AutoRepairApp = AutoRepairApp; 