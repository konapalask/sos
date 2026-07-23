// Configuration
const API_BASE_URL = window.location.origin; // Dynamically binds to host address
let refreshInterval = null;
const REFRESH_RATE_MS = 5000;

// DOM Elements
const serverStatusEl = document.querySelector('#server-status');
const whatsappStatusEl = document.querySelector('#whatsapp-status');
const wifiStatusEl = document.querySelector('#wifi-status');

const totalAlertsEl = document.getElementById('stat-total-alerts');
const todayAlertsEl = document.getElementById('stat-today-alerts');
const deviceIdEl = document.getElementById('stat-device-id');
const lastTimeEl = document.getElementById('stat-last-time');

const searchInput = document.getElementById('search-input');
const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
const manualRefreshBtn = document.getElementById('btn-manual-refresh');
const alertsTableBody = document.getElementById('alerts-table-body');

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    setupEventListeners();
    startAutoRefresh();
});

// Setup Action Listeners
function setupEventListeners() {
    // Manual Refresh
    manualRefreshBtn.addEventListener('click', () => {
        // Animate spin on refresh icon
        const icon = manualRefreshBtn.querySelector('i');
        icon.classList.add('bi-spin');
        
        fetchDashboardData().finally(() => {
            setTimeout(() => {
                icon.classList.remove('bi-spin');
            }, 600);
        });
    });

    // Auto Refresh Toggle
    autoRefreshToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // Real-time Search with Debounce
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchAlerts(searchInput.value.trim());
        }, 300); // Wait 300ms before calling API
    });
}

// Start Auto Refresh Interval
function startAutoRefresh() {
    stopAutoRefresh();
    refreshInterval = setInterval(() => {
        fetchDashboardData();
    }, REFRESH_RATE_MS);
}

// Stop Auto Refresh
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Fetch all stats and table logs
async function fetchDashboardData() {
    const searchVal = searchInput.value.trim();
    await Promise.all([
        fetchSystemStatus(),
        fetchAlerts(searchVal)
    ]);
}

// Fetch Server and Services Status
async function fetchSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        if (!response.ok) throw new Error('Status endpoint failure');
        
        const data = await response.json();
        
        // 1. Update Header Status Badges
        updateStatusBadge(serverStatusEl, 'Online', 'text-success', 'bi-cpu-fill');
        
        const wsStatusText = formatWhatsAppStatus(data.whatsapp_status);
        const wsColorClass = getWhatsAppColorClass(data.whatsapp_status);
        updateStatusBadge(whatsappStatusEl, wsStatusText, wsColorClass, 'bi-whatsapp');
        
        const wifiStatusText = data.internet_connected ? 'Connected' : 'Offline';
        const wifiColorClass = data.internet_connected ? 'text-success' : 'text-danger';
        updateStatusBadge(wifiStatusEl, wifiStatusText, wifiColorClass, 'bi-wifi');

        // 2. Update Stats Panel Cards
        totalAlertsEl.innerText = data.metrics.total_alerts;
        todayAlertsEl.innerText = data.metrics.today_alerts;
        
    } catch (error) {
        console.error('Failed to fetch system status:', error);
        // Set offline states
        updateStatusBadge(serverStatusEl, 'Offline', 'text-danger', 'bi-cpu-fill');
        updateStatusBadge(whatsappStatusEl, 'Unknown', 'text-muted', 'bi-whatsapp');
        updateStatusBadge(wifiStatusEl, 'Disconnected', 'text-danger', 'bi-wifi');
    }
}

// Fetch Logged Alerts from SQLite
async function fetchAlerts(searchVal = '') {
    try {
        const url = searchVal 
            ? `${API_BASE_URL}/alerts?search=${encodeURIComponent(searchVal)}`
            : `${API_BASE_URL}/alerts`;
            
        const response = await fetch(url);
        if (!response.ok) throw new Error('Alerts fetch failure');
        
        const alerts = await response.json();
        renderAlertsTable(alerts);
        
        // Update dashboard metrics based on latest item
        if (alerts.length > 0) {
            deviceIdEl.innerText = alerts[0].device || 'SOS001';
            lastTimeEl.innerText = formatTimeString(alerts[0].timestamp);
            lastTimeEl.title = alerts[0].timestamp; // Full time tooltip
        } else if (!searchVal) {
            deviceIdEl.innerText = 'None';
            lastTimeEl.innerText = '--:--:--';
        }
    } catch (error) {
        console.error('Failed to fetch alerts list:', error);
        alertsTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i> Failed to sync with server logs.
                </td>
            </tr>
        `;
    }
}

// Render SQLite data to DOM
function renderAlertsTable(alerts) {
    if (alerts.length === 0) {
        alertsTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5 text-muted">
                    <i class="bi bi-folder2-open fs-3 d-block mb-2"></i> No records found
                </td>
            </tr>
        `;
        return;
    }

    let rowsHTML = '';
    alerts.forEach(alert => {
        const batteryHTML = getBatteryMarkup(alert.battery);
        rowsHTML += `
            <tr>
                <td><strong>#${alert.id}</strong></td>
                <td><span class="font-outfit text-white">${escapeHTML(alert.device)}</span></td>
                <td><span class="status-pill emergency">${escapeHTML(alert.status)}</span></td>
                <td>${batteryHTML}</td>
                <td><code>${escapeHTML(alert.ip_address)}</code></td>
                <td>${escapeHTML(alert.timestamp)}</td>
            </tr>
        `;
    });
    alertsTableBody.innerHTML = rowsHTML;
}

// Helper to escape HTML characters (security)
function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Helper to format timestamps for display
function formatTimeString(isoString) {
    try {
        // Splits standard 'YYYY-MM-DD HH:MM:SS' to extract the time part
        const parts = isoString.split(' ');
        if (parts.length === 2) return parts[1];
        return isoString;
    } catch {
        return isoString;
    }
}

// Helper to compute Battery Level icons and CSS formatting
function getBatteryMarkup(batteryPercentage) {
    const pct = parseInt(batteryPercentage) || 0;
    let iconClass = 'bi-battery-full';
    let colorClass = 'text-success';

    if (pct <= 20) {
        iconClass = 'bi-battery-charge text-danger animate-pulse';
        colorClass = 'text-danger font-bold';
    } else if (pct <= 50) {
        iconClass = 'bi-battery-half';
        colorClass = 'text-warning';
    } else if (pct <= 85) {
        iconClass = 'bi-battery-half';
        colorClass = 'text-success';
    }

    return `
        <span class="d-inline-flex align-items-center ${colorClass}">
            <i class="bi ${iconClass} me-2 fs-5"></i> ${pct}%
        </span>
    `;
}

// Format the WhatsApp login state string
function formatWhatsAppStatus(status) {
    switch (status) {
        case 'logged_in': return 'Connected';
        case 'waiting_for_qr': return 'Scan QR Code';
        case 'loading': return 'Initializing...';
        case 'disconnected': return 'Disconnected';
        default: return 'Unknown';
    }
}

// Get the WhatsApp badge color formatting
function getWhatsAppColorClass(status) {
    switch (status) {
        case 'logged_in': return 'text-success';
        case 'waiting_for_qr': return 'text-warning animate-pulse';
        case 'loading': return 'text-info';
        case 'disconnected': return 'text-danger';
        default: return 'text-muted';
    }
}

// Update the badge UI state
function updateStatusBadge(badgeEl, value, colorClass, defaultIcon) {
    const badgeValEl = badgeEl.querySelector('.badge-val');
    
    // Clear old color classes
    badgeValEl.className = 'badge-val';
    badgeValEl.classList.add(colorClass);
    badgeValEl.innerText = value;
    
    // Update icon color if matching status
    const iconEl = badgeEl.querySelector('i');
    iconEl.className = `bi ${defaultIcon} ${colorClass}`;
}

// Custom CSS Inject for refresh icon animation rotation
const style = document.createElement('style');
style.innerHTML = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .bi-spin {
        display: inline-block;
        animation: spin 0.6s linear infinite;
    }
`;
document.head.appendChild(style);
