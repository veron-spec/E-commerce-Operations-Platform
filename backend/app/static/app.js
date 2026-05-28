/* ============================================================
   鐢靛晢杩愯惀鑷姩鍖栧钩鍙?- App Core
   Toast, Dark Mode, Sidebar, Charts, Refresh, Loading
   ============================================================ */

/* ===== Toast System ===== */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-circle-fill', info: 'bi-info-circle-fill' };
    const el = document.createElement('div');
    el.className = `toast-item toast-${type}`;
    el.innerHTML = `<i class="bi ${icons[type] || icons.info} toast-icon"></i>
        <span class="toast-msg">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
    container.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(40px)'; el.style.transition = 'all 0.3s'; setTimeout(() => el.remove(), 300); }, duration);
}

/* ===== Loading Overlay ===== */
function showLoading(el) {
    if (!el) return;
    if (el.querySelector('.loading-overlay')) return;
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    el.style.position = 'relative';
    el.appendChild(overlay);
}

function hideLoading(el) {
    if (!el) return;
    const overlay = el.querySelector('.loading-overlay');
    if (overlay) overlay.remove();
}

/* ===== Dark Mode ===== */
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    updateThemeIcon(!isDark);
    showToast(isDark ? _t('宸插垏鎹负娴呰壊妯″紡') : _t('宸插垏鎹负娣辫壊妯″紡'), 'info');
}

function updateThemeIcon(isDark) {
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = isDark ? 'bi-sun' : 'bi-moon-stars';
}

// Always start in light mode (dark sidebar + light content).
// The toggleDarkMode() respects saved preference for manual toggles.
(function initTheme() {
    document.documentElement.setAttribute('data-theme', 'light');
    updateThemeIcon(false);
})();

/* ===== Modal System ===== */
function openModal(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.remove('show');
    document.body.style.overflow = '';
}

// Close modal on overlay click (outside modal-box)
document.addEventListener('click', (e) => {
    const overlay = e.target.closest('.modal-overlay');
    if (overlay && !e.target.closest('.modal-box')) {
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.show').forEach(el => {
            el.classList.remove('show');
        });
        document.body.style.overflow = '';
    }
});

/* ===== User Dropdown ===== */
function toggleUserMenu() {
    const menu = document.getElementById('userMenuDropdown');
    if (menu) menu.classList.toggle('show');
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('userMenuDropdown');
    if (menu && !e.target.closest('#userMenu')) {
        menu.classList.remove('show');
    }
});

/* ===== Sidebar ===== */
function toggleSidebar() {
    document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sidebarCollapsed', document.body.classList.contains('sidebar-collapsed'));
}

function toggleMobileSidebar() {
    document.getElementById('sidebar').classList.toggle('mobile-show');
    document.getElementById('mobileSidebarOverlay').classList.toggle('show');
}

document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('sidebarCollapsed') === 'true' && window.innerWidth > 768) {
        document.body.classList.add('sidebar-collapsed');
    }
    const overlay = document.getElementById('mobileSidebarOverlay');
    if (overlay) overlay.addEventListener('click', toggleMobileSidebar);
});

/* ===== Time ===== */
function updateTime() {
    const el = document.getElementById('updateTime');
    if (el) el.textContent = new Date().toLocaleString('zh-CN');
}

/* ===== Formatters ===== */
function formatMoney(v) { return '楼' + Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function formatNum(v) { return Number(v || 0).toLocaleString('zh-CN'); }
function formatPercent(v) { return (v || 0) + '%'; }
function formatDate(d) { if (!d) return '--'; const dt = new Date(d); return isNaN(dt) ? d : dt.toLocaleDateString('zh-CN'); }
function formatDateTime(d) { if (!d) return '--'; const dt = new Date(d); return isNaN(dt) ? d : dt.toLocaleString('zh-CN'); }

/* ===== Generic Refresh Trigger ===== */
const _pageRefreshMap = {
    dashboard: 'refreshDashboard',
    sales: 'refreshSales',
    inventory: 'refreshInventoryPage',
    stores: 'refreshStores',
    orders: 'refreshOrders',
    automation: 'refreshAutomation',
    'product-selections': 'refreshProductSelections',
    'auto-reply': 'refreshAutoReply',
    suggestions: 'refreshSuggestions',
    retrospectives: 'refreshRetrospectives',
};

function triggerRefresh() {
    const page = document.body.dataset.page || 'dashboard';
    showToast(_t('姝ｅ湪鍒锋柊鏁版嵁...'), 'info');
    const fnName = _pageRefreshMap[page];
    if (fnName && typeof window[fnName] === 'function') {
        window[fnName]();
    }
    setTimeout(updateTime, 100);
}

/* ===== Language Switcher ===== */
function switchLang() {
    const current = document.documentElement.lang || 'zh';
    const next = current === 'zh' ? 'en' : 'zh';
    document.cookie = `lang=${next};path=/;max-age=31536000`;
    location.reload();
}

/* ===== Charts Manager ===== */
let chartInstances = {};

function destroyChart(id) {
    if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

function renderLineChart(canvasId, label, labels, data, color) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || !labels.length) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    chartInstances[canvasId] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label,
                data,
                borderColor: color,
                backgroundColor: color + '15',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: color,
                pointHoverRadius: 5,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#fff',
                    titleColor: isDark ? '#f1f5f9' : '#1e293b',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: { label: ctx => label + ': 楼' + Number(ctx.parsed.y).toLocaleString() }
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor, callback: v => '楼' + v.toLocaleString() } },
                x: { grid: { display: false }, ticks: { color: textColor, maxTicksLimit: 15, font: { size: 11 } } }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

function renderDoughnut(canvasId, labels, data) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || !labels.length) {
        if (ctx) { const p = ctx.parentElement; if (p) p.innerHTML = '<div class="empty-state"><div class="empty-icon"><i class="bi bi-pie-chart"></i></div><div class="empty-title">' + _t('鏆傛棤鏁版嵁') + '</div></div>'; }
        return;
    }
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const colors = ['#b8945a','#5a8a6a','#5a7a9a','#c45a5a','#b88a4a','#8f8068','#a9977a','#334155','#64748b','#7a8a7a'];

    chartInstances[canvasId] = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors.slice(0, labels.length), borderWidth: 2, borderColor: isDark ? '#1e293b' : '#fff' }] },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '65%',
            plugins: {
                legend: { position: 'bottom', labels: { padding: 12, font: { size: 12 }, color: isDark ? '#94a3b8' : '#64748b' } },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#fff',
                    titleColor: isDark ? '#f1f5f9' : '#1e293b',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: { label: ctx => ' ' + ctx.label + ': ' + ctx.parsed + ' 浠? }
                }
            }
        }
    });
}

function renderBarChart(canvasId, label, labels, data, color) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx || !labels || !labels.length) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    chartInstances[canvasId] = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: { labels, datasets: [{ label, data, backgroundColor: color + '80', borderColor: color, borderWidth: 1, borderRadius: 4, barPercentage: 0.6 }] },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#fff',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    cornerRadius: 8
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor } },
                x: { grid: { display: false }, ticks: { color: textColor } }
            }
        }
    });
}

/* ===== Dashboard ===== */
async function refreshDashboard() {
    try {
        const [summary, sales, inventory, topProducts, trends] = await Promise.all([
            fetch('/api/v1/dashboard/summary?days=30').then(r => r.json()),
            fetch('/api/v1/analytics/sales?days=30&granularity=day').then(r => r.json()),
            fetch('/api/v1/analytics/inventory').then(r => r.json()),
            fetch('/api/v1/analytics/products/top?days=30&limit=10').then(r => r.json()),
            fetch('/api/v1/analytics/trends?days=60').then(r => r.json()),
        ]);

        setStat('totalSales', formatMoney(summary.total_sales));
        setStat('orderCount', formatNum(summary.order_count));
        setStat('avgOrderValue', formatMoney(summary.avg_order_value));
        setStat('totalProducts', formatNum(summary.total_products));

        // Sales chart
        renderLineChart('salesChart', '閿€鍞 (楼)',
            (sales.revenue_by_day || []).map(d => d.period ? d.period.substring(5, 10) : ''),
            (sales.revenue_by_day || []).map(d => d.revenue || 0),
            '#b8945a');

        // Category chart
        renderDoughnut('categoryChart',
            (inventory.category_distribution || []).map(d => d.category || '鏈垎绫?),
            (inventory.category_distribution || []).map(d => d.count));

        // Top products table
        renderTopProducts(topProducts.top_products || []);

        // Low stock alerts
        renderInventoryAlerts(inventory.low_stock_items || []);

        // Growth indicators
        if (trends) {
            const gr = trends.growth_rates || {};
            setStat('salesGrowth', (gr.revenue_growth !== undefined ? (gr.revenue_growth >= 0 ? '+' : '') + gr.revenue_growth.toFixed(1) + '%' : '--'));
            const growthEl = document.getElementById('salesGrowth');
            if (growthEl && gr.revenue_growth !== undefined) {
                growthEl.className = gr.revenue_growth >= 0 ? 'stat-change up' : 'stat-change down';
            }
        }
    } catch (e) {
        console.error('鐪嬫澘鍔犺浇澶辫触:', e);
        showToast(_t('鐪嬫澘鏁版嵁鍔犺浇澶辫触'), 'error');
    }
}

function setStat(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function renderTopProducts(products) {
    const tbody = document.getElementById('topProductsBody');
    if (!tbody) return;
    if (!products.length) {
        tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('鏆傛棤鏁版嵁') + '</div></div></td></tr>';
        return;
    }
    tbody.innerHTML = products.map((p, i) => `<tr>
        <td class="fw-bold text-muted">${i+1}</td>
        <td><span class="truncate" style="display:inline-block;max-width:200px">${p.title || _t('鏈煡')}</span></td>
        <td>${formatNum(p.quantity)}</td>
        <td class="fw-bold">${formatMoney(p.revenue)}</td>
    </tr>`).join('');
}

function renderInventoryAlerts(items) {
    const tbody = document.getElementById('inventoryAlertBody');
    if (!tbody) return;
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('鏆傛棤棰勮锛屽簱瀛樻甯?) + '</div></div></td></tr>';
        return;
    }
    tbody.innerHTML = items.map(item => {
        const qty = item.quantity || 0;
        const cls = qty <= 0 ? 'tag-danger' : qty < 5 ? 'tag-warning' : 'tag-warning';
        const txt = qty <= 0 ? _t('缂鸿揣') : _t('鍋忎綆');
        return `<tr>
            <td>${item.title || _t('鏈煡')}</td>
            <td class="text-muted">${item.sku || '--'}</td>
            <td class="fw-medium">${qty}</td>
            <td><span class="tag ${cls}">${txt}</span></td>
        </tr>`;
    }).join('');
}

/* ===== Sales Page ===== */
async function refreshSales() {
    try {
        const days = document.getElementById('salesDays')?.value || 30;
        const [salesData, trendsData] = await Promise.all([
            fetch(`/api/v1/analytics/sales?days=${days}&granularity=day`).then(r => r.json()),
            fetch(`/api/v1/analytics/trends?days=${days * 2}`).then(r => r.json()),
        ]);

        renderLineChart('salesTrendChart', '閿€鍞 (楼)',
            (salesData.revenue_by_day || []).map(d => d.period ? d.period.substring(5, 10) : ''),
            (salesData.revenue_by_day || []).map(d => d.revenue || 0),
            '#5a8a6a');

        const total = (salesData.revenue_by_day || []).reduce((s, d) => s + (d.revenue || 0), 0);
        const count = (salesData.revenue_by_day || []).reduce((s, d) => s + (d.order_count || 0), 0);
        setStat('salesTotalRevenue', formatMoney(total));
        setStat('salesTotalOrders', formatNum(count));
        setStat('salesAvgOrder', formatMoney(count ? total / count : 0));

        if (trendsData && trendsData.growth_rates) {
            setStat('salesRevenueGrowth', (trendsData.growth_rates.revenue_growth !== undefined
                ? (trendsData.growth_rates.revenue_growth >= 0 ? '+' : '') + trendsData.growth_rates.revenue_growth.toFixed(1) + '%' : '--'));
        }

        // Table
        const tbody = document.getElementById('salesTableBody');
        if (tbody) {
            const rows = salesData.revenue_by_day || [];
            if (!rows.length) {
                tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('鏆傛棤鏁版嵁') + '</div></div></td></tr>';
            } else {
                tbody.innerHTML = rows.slice().reverse().map(d => `<tr>
                    <td>${d.period || '--'}</td>
                    <td class="fw-medium">${formatMoney(d.revenue)}</td>
                    <td>${formatNum(d.order_count)}</td>
                    <td class="text-muted">${formatMoney(d.discounts)}</td>
                </tr>`).join('');
            }
        }
    } catch (e) {
        console.error('閿€鍞垎鏋愬姞杞藉け璐?', e);
        showToast(_t('閿€鍞暟鎹姞杞藉け璐?), 'error');
    }
}

/* ===== Inventory Page ===== */
async function refreshInventoryPage() {
    try {
        const res = await fetch('/api/v1/analytics/inventory');
        const data = await res.json();

        setStat('invTotal', formatNum(data.total_products));
        setStat('invLowStock', formatNum(data.low_stock_count));
        setStat('invOutOfStock', formatNum(data.out_of_stock_count));

        renderDoughnut('invCategoryChart',
            (data.category_distribution || []).map(d => d.category || '鏈垎绫?),
            (data.category_distribution || []).map(d => d.count));

        const tbody = document.getElementById('invTableBody');
        if (tbody) {
            const items = data.low_stock_items || [];
            if (!items.length) {
                tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-title">' + _t('鎵€鏈夊晢鍝佸簱瀛樻甯?) + '</div></div></td></tr>';
            } else {
                tbody.innerHTML = items.map(item => {
                    const qty = item.quantity || 0;
                    const cls = qty <= 0 ? 'tag-danger' : qty < 5 ? 'tag-warning' : 'tag-warning';
                    const txt = qty <= 0 ? _t('缂鸿揣') : qty < 5 ? _t('绱ф€?) : _t('棰勮');
                    return `<tr>
                        <td>${item.title || _t('鏈煡')}</td>
                        <td class="text-muted">${item.sku || '--'}</td>
                        <td class="fw-medium">${qty}</td>
                        <td><span class="tag ${cls}">${txt}</span></td>
                        <td><button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('琛ヨ揣') + ' 鈥?' + _t('寮€鍙戜腑'), 'info')">${_t('琛ヨ揣')}</button></td>
                    </tr>`;
                }).join('');
            }
        }
    } catch (e) {
        console.error('搴撳瓨鍔犺浇澶辫触:', e);
        showToast(_t('搴撳瓨鏁版嵁鍔犺浇澶辫触'), 'error');
    }
}

/* ===== Stores Page ===== */
async function refreshStores() {
    try {
        const res = await fetch('/api/v1/stores');
        const stores = await res.json();
        const tbody = document.getElementById('storesTableBody');
        if (!tbody) return;

        if (!stores.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-title">' + _t('鏆傛棤搴楅摵') + '</div><div class="empty-desc">' + _t('鐐瑰嚮涓婃柟鎸夐挳娣诲姞浣犵殑绗竴涓簵閾?) + '</div></div></td></tr>';
            return;
        }
        tbody.innerHTML = stores.map(s => `<tr>
            <td class="fw-medium">${s.name}</td>
            <td><span class="tag tag-${s.platform_type === 'taobao' ? 'warning' : s.platform_type === 'shopify' || s.platform_type === 'shopee' || s.platform_type === 'lazada' ? 'info' : 'neutral'}">${s.platform_type === 'taobao' ? '娣樺疂' : s.platform_type === 'shopify' ? 'Shopify' : s.platform_type === 'shopee' ? 'Shopee' : s.platform_type === 'lazada' ? 'Lazada' : s.platform_type}</span></td>
            <td class="text-muted text-sm">${s.store_url}</td>
            <td><span class="tag ${s.is_active ? 'tag-success' : 'tag-neutral'}">${s.is_active ? _t('姝ｅ父') : _t('鍋滅敤')}</span></td>
            <td>
                <div class="cell-actions">
                    <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="syncStore(${s.id})"><i class="bi bi-arrow-repeat"></i></button>
                    ${s.platform_type === 'taobao' ? `<button class="btn-custom btn-custom-outline btn-custom-sm text-primary" onclick="authorizeTaobao(${s.id})" title="娣樺疂鎺堟潈">${_t('鎺堟潈')}</button>` : ''}    }
}

async function addStore() {
    const name = document.getElementById('storeName').value;
    const platform = document.getElementById('storePlatform').value;
    const url = document.getElementById('storeUrl').value;
    const key = document.getElementById('storeKey').value;
    const secret = document.getElementById('storeSecret').value;

    if (!name || !url || !key || !secret) {
        showToast(_t('璇峰～鍐欐墍鏈夊繀濉」'), 'warning');
        return;
    }

    try {
        const params = new URLSearchParams({ name, platform_type: platform, store_url: url, api_key: key, api_secret: secret });
        const res = await fetch('/api/v1/stores?' + params, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('搴楅摵娣诲姞鎴愬姛锛?), 'success');
        closeModal('addStoreModal');
        document.getElementById('addStoreForm').reset();
        refreshStores();
    } catch (e) {
        showToast(_t('娣诲姞澶辫触') + ': ' + e.message, 'error');
    }
}

/* ===== Orders Page ===== */
let orderPage = 1;
const orderPageSize = 20;

async function refreshOrders() {
    try {
        const status = document.getElementById('orderStatusFilter')?.value || '';
        const search = document.getElementById('orderSearch')?.value || '';
        let url = `/api/v1/orders?page=${orderPage}&page_size=${orderPageSize}`;
        if (status) url += `&status=${status}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url);
        const data = await res.json();
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        const orders = data.orders || data.items || [];
        if (!orders.length) {
            tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon"><i class="bi bi-receipt"></i></div><div class="empty-title">' + _t('鏆傛棤璁㈠崟') + '</div><div class="empty-desc">' + _t('鍚屾鏁版嵁鍚庤鍗曞皢鍦ㄦ鏄剧ず') + '</div></div></td></tr>';
        } else {
            tbody.innerHTML = orders.map(o => {
                const statusClass = o.financial_status === 'paid' ? 'tag-success' : o.financial_status === 'refunded' ? 'tag-danger' : 'tag-warning';
                const statusText = o.financial_status === 'paid' ? _t('宸蹭粯娆?) : o.financial_status === 'refunded' ? _t('宸查€€娆?) : o.financial_status || _t('鏈煡');
                const itemCount = (o.line_items || []).reduce((s, i) => s + (i.quantity || 0), 0);
                return `<tr>
                    <td class="fw-medium">${o.order_number || '--'}</td>
                    <td class="text-muted text-sm">${formatDateTime(o.created_at)}</td>
                    <td class="text-muted">${o.email || '--'}</td>
                    <td>${itemCount}</td>
                    <td class="fw-medium">${formatMoney(o.total_price)}</td>
                    <td><span class="tag ${statusClass}">${statusText}</span></td>
                    <td>
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('璁㈠崟璇︽儏寮€鍙戜腑'), 'info')">${_t('璇︽儏')}</button>
                    </td>
                </tr>`;
            }).join('');
        }

        // Pagination
        updatePagination(data.total || data.count || 0, data.page || orderPage, data.total_pages || 1);
    } catch (e) {
        console.error('璁㈠崟鍔犺浇澶辫触:', e);
        showToast(_t('璁㈠崟鏁版嵁鍔犺浇澶辫触'), 'error');
    }
}

function updatePagination(total, currentPage, totalPages) {
    const el = document.getElementById('pageInfo');
    if (el) el.textContent = _t('鍏?) + ' ' + total + _t('鏉★紝绗?) + ' ' + currentPage + '/' + totalPages + _t('椤?);
    const prev = document.getElementById('pagePrev');
    const next = document.getElementById('pageNext');
    if (prev) prev.disabled = currentPage <= 1;
    if (next) next.disabled = currentPage >= totalPages;
}

function changePage(delta) {
    orderPage = Math.max(1, orderPage + delta);
    refreshOrders();
}

/* ===== Automation Page ===== */
async function refreshAutomation() {
    try {
        const res = await fetch('/api/v1/automation/rules');
        const rules = await res.json();
        const tbody = document.getElementById('rulesTableBody');
        if (!tbody) return;

        const items = rules.rules || rules || [];
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon"><i class="bi bi-lightning-charge"></i></div><div class="empty-title">' + _t('鏆傛棤鑷姩鍖栬鍒?) + '</div><div class="empty-desc">' + _t('鍒涘缓瑙勫垯鏉ヨ嚜鍔ㄥ鐞嗗簱瀛橀璀︺€佷环鏍艰皟鏁寸瓑鎿嶄綔') + '</div></div></td></tr>';
            return;
        }
        tbody.innerHTML = items.map(r => {
            const triggerText = r.trigger_type === 'scheduled' ? _t('瀹氭椂') : r.trigger_type === 'event' ? _t('浜嬩欢') : r.trigger_type || '--';
            const cond = r.conditions || {};
            const condText = cond.field ? `${cond.field} ${cond.operator} ${cond.value}` : '--';
            return `<tr>
                <td class="fw-medium">${r.name}</td>
                <td><span class="tag tag-info">${triggerText}</span></td>
                <td class="text-sm text-muted">${condText}</td>
                <td><span class="tag ${r.is_enabled ? 'tag-success' : 'tag-neutral'}">${r.is_enabled ? _t('鍚敤') : _t('鍋滅敤')}</span></td>
                <td>
                    <div class="cell-actions">
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('缂栬緫鍔熻兘寮€鍙戜腑'), 'info')"><i class="bi bi-pencil"></i></button>
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="toggleRule(${r.id})"><i class="bi ${r.is_enabled ? 'bi-pause' : 'bi-play'}"></i></button>
                    </div>
                </td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error('鑷姩鍖栬鍒欏姞杞藉け璐?', e);
        showToast('瑙勫垯鏁版嵁鍔犺浇澶辫触', 'error');
    }
}

async function toggleRule(id) {
    try {
        const res = await fetch(`/api/v1/automation/rules/${id}/toggle`, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('瑙勫垯鐘舵€佸凡鏇存柊'), 'success');
        refreshAutomation();
    } catch (e) {
        showToast(_t('鎿嶄綔澶辫触') + ': ' + e.message, 'error');
    }
}

async function createRule() {
    const name = document.getElementById('ruleName').value;
    const field = document.getElementById('ruleField').value;
    const operator = document.getElementById('ruleOperator').value;
    const value = document.getElementById('ruleValue').value;

    if (!name || !field || !value) { showToast(_t('璇峰～鍐欏畬鏁翠俊鎭?), 'warning'); return; }

    try {
        const res = await fetch('/api/v1/automation/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name, trigger_type: 'scheduled',
                conditions: { field, operator, value: isNaN(value) ? value : Number(value) },
                actions: [{ type: 'notify', channel: 'email' }],
                is_enabled: true,
            }),
        });
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('瑙勫垯鍒涘缓鎴愬姛锛?), 'success');
        closeModal('addRuleModal');
        document.getElementById('addRuleForm').reset();
        refreshAutomation();
    } catch (e) {
        showToast(_t('鍒涘缓澶辫触') + ': ' + e.message, 'error');
    }
}

/* ===== Page Load ===== */
document.addEventListener('DOMContentLoaded', () => {
    updateTime();
    const page = document.body.dataset.page || 'dashboard';
    if (page === 'dashboard') refreshDashboard();
    else if (page === 'sales') refreshSales();
    else if (page === 'inventory') refreshInventoryPage();
    else if (page === 'stores') refreshStores();
    else if (page === 'orders') refreshOrders();
    else if (page === 'automation') refreshAutomation();
    else if (page === 'product-selections') refreshProductSelections();
    else if (page === 'auto-reply') refreshAutoReply();
    else if (page === 'suggestions') refreshSuggestions();
    else if (page === 'retrospectives') refreshRetrospectives();

    // Auto-refresh every 60s
    setInterval(() => {
        updateTime();
        const p = document.body.dataset.page || 'dashboard';
        if (p === 'dashboard') refreshDashboard();
    }, 60000);
});
