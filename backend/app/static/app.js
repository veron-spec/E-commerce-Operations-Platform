/* ============================================================
   电商运营自动化平台 - App Core
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
    showToast(isDark ? _t('已切换为浅色模式') : _t('已切换为深色模式'), 'info');
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
function formatMoney(v) { return '¥' + Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
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
    showToast(_t('正在刷新数据...'), 'info');
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
                    callbacks: { label: ctx => label + ': ¥' + Number(ctx.parsed.y).toLocaleString() }
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor, callback: v => '¥' + v.toLocaleString() } },
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
        if (ctx) { const p = ctx.parentElement; if (p) p.innerHTML = '<div class="empty-state"><div class="empty-icon"><i class="bi bi-pie-chart"></i></div><div class="empty-title">' + _t('暂无数据') + '</div></div>'; }
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
                    callbacks: { label: ctx => ' ' + ctx.label + ': ' + ctx.parsed + ' 件' }
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
        renderLineChart('salesChart', '销售额 (¥)',
            (sales.revenue_by_day || []).map(d => d.period ? d.period.substring(5, 10) : ''),
            (sales.revenue_by_day || []).map(d => d.revenue || 0),
            '#b8945a');

        // Category chart
        renderDoughnut('categoryChart',
            (inventory.category_distribution || []).map(d => d.category || '未分类'),
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
        console.error('看板加载失败:', e);
        showToast(_t('看板数据加载失败'), 'error');
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
        tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('暂无数据') + '</div></div></td></tr>';
        return;
    }
    tbody.innerHTML = products.map((p, i) => `<tr>
        <td class="fw-bold text-muted">${i+1}</td>
        <td><span class="truncate" style="display:inline-block;max-width:200px">${p.title || _t('未知')}</span></td>
        <td>${formatNum(p.quantity)}</td>
        <td class="fw-bold">${formatMoney(p.revenue)}</td>
    </tr>`).join('');
}

function renderInventoryAlerts(items) {
    const tbody = document.getElementById('inventoryAlertBody');
    if (!tbody) return;
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('暂无预警，库存正常') + '</div></div></td></tr>';
        return;
    }
    tbody.innerHTML = items.map(item => {
        const qty = item.quantity || 0;
        const cls = qty <= 0 ? 'tag-danger' : qty < 5 ? 'tag-warning' : 'tag-warning';
        const txt = qty <= 0 ? _t('缺货') : _t('偏低');
        return `<tr>
            <td>${item.title || _t('未知')}</td>
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

        renderLineChart('salesTrendChart', '销售额 (¥)',
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
                tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state"><div class="empty-title">' + _t('暂无数据') + '</div></div></td></tr>';
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
        console.error('销售分析加载失败:', e);
        showToast(_t('销售数据加载失败'), 'error');
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
            (data.category_distribution || []).map(d => d.category || '未分类'),
            (data.category_distribution || []).map(d => d.count));

        const tbody = document.getElementById('invTableBody');
        if (tbody) {
            const items = data.low_stock_items || [];
            if (!items.length) {
                tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-title">' + _t('所有商品库存正常') + '</div></div></td></tr>';
            } else {
                tbody.innerHTML = items.map(item => {
                    const qty = item.quantity || 0;
                    const cls = qty <= 0 ? 'tag-danger' : qty < 5 ? 'tag-warning' : 'tag-warning';
                    const txt = qty <= 0 ? _t('缺货') : qty < 5 ? _t('紧急') : _t('预警');
                    return `<tr>
                        <td>${item.title || _t('未知')}</td>
                        <td class="text-muted">${item.sku || '--'}</td>
                        <td class="fw-medium">${qty}</td>
                        <td><span class="tag ${cls}">${txt}</span></td>
                        <td><button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('补货') + ' — ' + _t('开发中'), 'info')">${_t('补货')}</button></td>
                    </tr>`;
                }).join('');
            }
        }
    } catch (e) {
        console.error('库存加载失败:', e);
        showToast(_t('库存数据加载失败'), 'error');
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
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-title">' + _t('暂无店铺') + '</div><div class="empty-desc">' + _t('点击上方按钮添加你的第一个店铺') + '</div></div></td></tr>';
            return;
        }
        tbody.innerHTML = stores.map(s => `<tr>
            <td class="fw-medium">${s.name}</td>
            <td><span class="tag tag-${s.platform_type === 'taobao' ? 'warning' : s.platform_type === 'shopify' || s.platform_type === 'shopee' || s.platform_type === 'lazada' ? 'info' : 'neutral'}">${s.platform_type === 'taobao' ? '淘宝' : s.platform_type === 'shopify' ? 'Shopify' : s.platform_type === 'shopee' ? 'Shopee' : s.platform_type === 'lazada' ? 'Lazada' : s.platform_type}</span></td>
            <td class="text-muted text-sm">${s.store_url}</td>
            <td><span class="tag ${s.is_active ? 'tag-success' : 'tag-neutral'}">${s.is_active ? _t('正常') : _t('停用')}</span></td>
            <td>
                <div class="cell-actions">
                    <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="syncStore(${s.id})"><i class="bi bi-arrow-repeat"></i></button>
                    ${s.platform_type === 'taobao' ? `<button class="btn-custom btn-custom-outline btn-custom-sm text-primary" onclick="authorizeTaobao(${s.id})" title="淘宝授权">${_t('授权')}</button>` : ''}
                    <button class="btn-custom btn-custom-outline btn-custom-sm text-danger" onclick="showToast(_t('删除功能开发中'), 'info')"><i class="bi bi-trash"></i></button>
                </div>
            </td>
        </tr>`).join('');
        document.getElementById('orderBadge').textContent = stores.length;
    } catch (e) {
        console.error('店铺加载失败:', e);
        showToast(_t('店铺数据加载失败'), 'error');
    }
}

async function syncStore(id) {
    try {
        const res = await fetch(`/api/v1/stores/${id}/sync`);
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('同步任务已触发'), 'success');
    } catch (e) {
        showToast(_t('同步失败') + ': ' + e.message, 'error');
    }
}

async function authorizeTaobao(storeId) {
    try {
        const res = await fetch(`/api/v1/stores/${storeId}/taobao/auth-url`);
        if (!res.ok) {
            const body = await res.json();
            throw new Error(body.detail || '获取授权链接失败');
        }
        const data = await res.json();
        window.location.href = data.auth_url;
    } catch (e) {
        showToast(_t('授权失败') + ': ' + e.message, 'error');
    }
}

async function addStore() {
    const name = document.getElementById('storeName').value;
    const platform = document.getElementById('storePlatform').value;
    const url = document.getElementById('storeUrl').value;
    const key = document.getElementById('storeKey').value;
    const secret = document.getElementById('storeSecret').value;

    if (!name || !url || !key || !secret) {
        showToast(_t('请填写所有必填项'), 'warning');
        return;
    }

    try {
        const params = new URLSearchParams({ name, platform_type: platform, store_url: url, api_key: key, api_secret: secret });
        const res = await fetch('/api/v1/stores?' + params, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('店铺添加成功！'), 'success');
        closeModal('addStoreModal');
        document.getElementById('addStoreForm').reset();
        refreshStores();
    } catch (e) {
        showToast(_t('添加失败') + ': ' + e.message, 'error');
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
            tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon"><i class="bi bi-receipt"></i></div><div class="empty-title">' + _t('暂无订单') + '</div><div class="empty-desc">' + _t('同步数据后订单将在此显示') + '</div></div></td></tr>';
        } else {
            tbody.innerHTML = orders.map(o => {
                const statusClass = o.financial_status === 'paid' ? 'tag-success' : o.financial_status === 'refunded' ? 'tag-danger' : 'tag-warning';
                const statusText = o.financial_status === 'paid' ? _t('已付款') : o.financial_status === 'refunded' ? _t('已退款') : o.financial_status || _t('未知');
                const itemCount = (o.line_items || []).reduce((s, i) => s + (i.quantity || 0), 0);
                return `<tr>
                    <td class="fw-medium">${o.order_number || '--'}</td>
                    <td class="text-muted text-sm">${formatDateTime(o.created_at)}</td>
                    <td class="text-muted">${o.email || '--'}</td>
                    <td>${itemCount}</td>
                    <td class="fw-medium">${formatMoney(o.total_price)}</td>
                    <td><span class="tag ${statusClass}">${statusText}</span></td>
                    <td>
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('订单详情开发中'), 'info')">${_t('详情')}</button>
                    </td>
                </tr>`;
            }).join('');
        }

        // Pagination
        updatePagination(data.total || data.count || 0, data.page || orderPage, data.total_pages || 1);
    } catch (e) {
        console.error('订单加载失败:', e);
        showToast(_t('订单数据加载失败'), 'error');
    }
}

function updatePagination(total, currentPage, totalPages) {
    const el = document.getElementById('pageInfo');
    if (el) el.textContent = _t('共') + ' ' + total + _t('条，第') + ' ' + currentPage + '/' + totalPages + _t('页');
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
            tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon"><i class="bi bi-lightning-charge"></i></div><div class="empty-title">' + _t('暂无自动化规则') + '</div><div class="empty-desc">' + _t('创建规则来自动处理库存预警、价格调整等操作') + '</div></div></td></tr>';
            return;
        }
        tbody.innerHTML = items.map(r => {
            const triggerText = r.trigger_type === 'scheduled' ? _t('定时') : r.trigger_type === 'event' ? _t('事件') : r.trigger_type || '--';
            const cond = r.conditions || {};
            const condText = cond.field ? `${cond.field} ${cond.operator} ${cond.value}` : '--';
            return `<tr>
                <td class="fw-medium">${r.name}</td>
                <td><span class="tag tag-info">${triggerText}</span></td>
                <td class="text-sm text-muted">${condText}</td>
                <td><span class="tag ${r.is_enabled ? 'tag-success' : 'tag-neutral'}">${r.is_enabled ? _t('启用') : _t('停用')}</span></td>
                <td>
                    <div class="cell-actions">
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="showToast(_t('编辑功能开发中'), 'info')"><i class="bi bi-pencil"></i></button>
                        <button class="btn-custom btn-custom-outline btn-custom-sm" onclick="toggleRule(${r.id})"><i class="bi ${r.is_enabled ? 'bi-pause' : 'bi-play'}"></i></button>
                    </div>
                </td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error('自动化规则加载失败:', e);
        showToast('规则数据加载失败', 'error');
    }
}

async function toggleRule(id) {
    try {
        const res = await fetch(`/api/v1/automation/rules/${id}/toggle`, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        showToast(_t('规则状态已更新'), 'success');
        refreshAutomation();
    } catch (e) {
        showToast(_t('操作失败') + ': ' + e.message, 'error');
    }
}

async function createRule() {
    const name = document.getElementById('ruleName').value;
    const field = document.getElementById('ruleField').value;
    const operator = document.getElementById('ruleOperator').value;
    const value = document.getElementById('ruleValue').value;

    if (!name || !field || !value) { showToast(_t('请填写完整信息'), 'warning'); return; }

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
        showToast(_t('规则创建成功！'), 'success');
        closeModal('addRuleModal');
        document.getElementById('addRuleForm').reset();
        refreshAutomation();
    } catch (e) {
        showToast(_t('创建失败') + ': ' + e.message, 'error');
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
