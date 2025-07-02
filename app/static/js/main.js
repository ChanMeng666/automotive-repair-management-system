// 汽车维修管理系统 - 主要JavaScript文件

// 全局配置
const AppConfig = {
    apiBaseUrl: '/api',
    loadingClass: 'loading-overlay',
    alertTimeout: 5000,
    debounceDelay: 300,
    defaultPageSize: 10
};

// 实用工具类
class Utils {
    // 防抖函数
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 格式化货币
    static formatCurrency(amount) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'CNY',
            minimumFractionDigits: 2
        }).format(amount || 0);
    }

    // 格式化日期
    static formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };
        return new Intl.DateTimeFormat('zh-CN', { ...defaultOptions, ...options }).format(new Date(date));
    }

    // 显示Toast消息
    static showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        const toast = this.createToast(message, type);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // 创建Toast容器
    static createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    // 创建Toast元素
    static createToast(message, type) {
        const iconMap = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        const colorMap = {
            success: 'text-success',
            error: 'text-danger',
            warning: 'text-warning',
            info: 'text-info'
        };

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi ${iconMap[type]} ${colorMap[type]} me-2"></i>
                <strong class="me-auto">系统消息</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        return toast;
    }

    // 显示加载动画
    static showLoading(target = document.body) {
        const loading = document.createElement('div');
        loading.className = AppConfig.loadingClass;
        loading.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary spinner-border-xl" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <div class="mt-3">
                    <h6 class="text-muted">正在加载数据...</h6>
                </div>
            </div>
        `;
        target.appendChild(loading);
        return loading;
    }

    // 隐藏加载动画
    static hideLoading(target = document.body) {
        const loading = target.querySelector(`.${AppConfig.loadingClass}`);
        if (loading) {
            loading.remove();
        }
    }

    // 确认对话框
    static confirm(message, title = '确认操作') {
        return new Promise((resolve) => {
            const modal = this.createConfirmModal(message, title, resolve);
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        });
    }

    // 创建确认模态框
    static createConfirmModal(message, title, callback) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-question-circle text-warning me-2"></i>
                            ${title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="confirmBtn">确认</button>
                    </div>
                </div>
            </div>
        `;

        modal.querySelector('#confirmBtn').addEventListener('click', () => {
            callback(true);
            bootstrap.Modal.getInstance(modal).hide();
        });

        modal.addEventListener('hidden.bs.modal', () => {
            callback(false);
        });

        return modal;
    }
}

// API请求类
class ApiClient {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        try {
            const response = await fetch(AppConfig.apiBaseUrl + url, {
                ...defaultOptions,
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('API请求失败:', error);
            return { success: false, error: error.message };
        }
    }

    static async get(url) {
        return this.request(url, { method: 'GET' });
    }

    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// 表单处理类
class FormHandler {
    constructor(formElement) {
        this.form = formElement;
        this.init();
    }

    init() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.setupValidation();
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        if (!this.validateForm()) {
            return;
        }

        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            this.setSubmitState(submitBtn, true);
            
            const formData = new FormData(this.form);
            const response = await fetch(this.form.action, {
                method: this.form.method,
                body: formData
            });

            if (response.ok) {
                Utils.showToast('操作成功完成', 'success');
                this.handleSuccess(response);
            } else {
                throw new Error('服务器响应错误');
            }
        } catch (error) {
            Utils.showToast('操作失败：' + error.message, 'error');
            this.handleError(error);
        } finally {
            this.setSubmitState(submitBtn, false, originalText);
        }
    }

    setSubmitState(button, loading, originalText = '提交') {
        if (loading) {
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2"></span>
                处理中...
            `;
        } else {
            button.disabled = false;
            button.textContent = originalText;
        }
    }

    setupValidation() {
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', this.validateField.bind(this, input));
            input.addEventListener('input', this.clearFieldError.bind(this, input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        // 必填验证
        if (field.required && !value) {
            isValid = false;
            message = '此字段为必填项';
        }
        
        // 邮箱验证
        if (field.type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            message = '请输入有效的邮箱地址';
        }
        
        // 电话验证
        if (field.type === 'tel' && value && !this.isValidPhone(value)) {
            isValid = false;
            message = '请输入有效的电话号码';
        }

        this.setFieldState(field, isValid, message);
        return isValid;
    }

    validateForm() {
        const inputs = this.form.querySelectorAll('input, select, textarea');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    setFieldState(field, isValid, message = '') {
        const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                        this.createFeedbackElement(field);

        field.classList.remove('is-valid', 'is-invalid');
        
        if (isValid) {
            field.classList.add('is-valid');
            feedback.style.display = 'none';
        } else {
            field.classList.add('is-invalid');
            feedback.textContent = message;
            feedback.style.display = 'block';
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    }

    createFeedbackElement(field) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
        return feedback;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPhone(phone) {
        const phoneRegex = /^1[3-9]\d{9}$|^0\d{2,3}-?\d{7,8}$/;
        return phoneRegex.test(phone.replace(/\s+/g, ''));
    }

    handleSuccess(response) {
        // 子类可以重写此方法
        console.log('表单提交成功');
    }

    handleError(error) {
        // 子类可以重写此方法
        console.error('表单提交失败:', error);
    }
}

// 搜索功能类
class SearchHandler {
    constructor(searchInput, resultsContainer, searchFunction) {
        this.searchInput = searchInput;
        this.resultsContainer = resultsContainer;
        this.searchFunction = searchFunction;
        this.init();
    }

    init() {
        const debouncedSearch = Utils.debounce(this.performSearch.bind(this), AppConfig.debounceDelay);
        this.searchInput.addEventListener('input', debouncedSearch);
        this.searchInput.addEventListener('focus', this.showResults.bind(this));
        document.addEventListener('click', this.hideResults.bind(this));
    }

    async performSearch() {
        const query = this.searchInput.value.trim();
        
        if (query.length < 2) {
            this.hideResults();
            return;
        }

        try {
            this.showLoading();
            const results = await this.searchFunction(query);
            this.displayResults(results);
        } catch (error) {
            console.error('搜索失败:', error);
            this.displayError('搜索失败，请稍后重试');
        }
    }

    showLoading() {
        this.resultsContainer.innerHTML = `
            <div class="text-center p-3">
                <div class="spinner-border spinner-border-sm text-primary"></div>
                <small class="ms-2 text-muted">搜索中...</small>
            </div>
        `;
        this.showResults();
    }

    displayResults(results) {
        if (results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-search"></i>
                    <div>未找到匹配结果</div>
                </div>
            `;
        } else {
            this.resultsContainer.innerHTML = results.map(this.renderResultItem).join('');
        }
        this.showResults();
    }

    displayError(message) {
        this.resultsContainer.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <div>${message}</div>
            </div>
        `;
        this.showResults();
    }

    renderResultItem(item) {
        // 子类应该重写此方法
        return `<div class="p-2">${JSON.stringify(item)}</div>`;
    }

    showResults() {
        this.resultsContainer.style.display = 'block';
    }

    hideResults(event) {
        if (event && (this.searchInput.contains(event.target) || 
                     this.resultsContainer.contains(event.target))) {
            return;
        }
        this.resultsContainer.style.display = 'none';
    }
}

// 数据表格处理类
class DataTable {
    constructor(tableElement, options = {}) {
        this.table = tableElement;
        this.options = {
            pageSize: AppConfig.defaultPageSize,
            sortable: true,
            filterable: true,
            ...options
        };
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.filters = {};
        this.init();
    }

    init() {
        this.setupSorting();
        this.setupPagination();
        this.setupFiltering();
    }

    setupSorting() {
        if (!this.options.sortable) return;

        const headers = this.table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const column = header.dataset.sortable;
                this.sort(column);
            });
        });
    }

    sort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        this.render();
    }

    setupPagination() {
        // 分页逻辑实现
    }

    setupFiltering() {
        if (!this.options.filterable) return;
        
        const filterInputs = document.querySelectorAll('[data-filter]');
        filterInputs.forEach(input => {
            const debouncedFilter = Utils.debounce(() => {
                this.filters[input.dataset.filter] = input.value;
                this.render();
            }, AppConfig.debounceDelay);
            
            input.addEventListener('input', debouncedFilter);
        });
    }

    render() {
        // 表格渲染逻辑
        console.log('表格渲染:', {
            page: this.currentPage,
            sort: this.sortColumn,
            direction: this.sortDirection,
            filters: this.filters
        });
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有表单
    const forms = document.querySelectorAll('form[data-enhanced]');
    forms.forEach(form => new FormHandler(form));

    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 自动关闭警告框
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, AppConfig.alertTimeout);

    // 页面加载动画
    const pageLoading = document.getElementById('page-loading');
    if (pageLoading) {
        pageLoading.style.display = 'none';
    }

    // 添加页面淡入效果
    document.body.classList.add('fade-in');
});

// 导出全局对象
window.App = {
    Utils,
    ApiClient,
    FormHandler,
    SearchHandler,
    DataTable,
    config: AppConfig
}; 