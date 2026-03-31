const BASE_URL = window.location.protocol === 'file:'
    ? 'http://localhost:5000/api'
    : `${window.location.origin}/api`;

const api = {
    async fetch(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        const response = await fetch(`${BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json();
        if (!response.ok) {
            const err = new Error(data.message || 'Something went wrong');
            err.clashing = data.clashing || null;
            err.suggestion = data.suggestion || null;
            throw err;
        }
        return data;
    },

    auth: {
        login: (credentials) => api.fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        }),
        register: (userData) => api.fetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        }),
        googleLogin: (idToken) => api.fetch('/auth/google', {
            method: 'POST',
            body: JSON.stringify({ idToken })
        }),
        getProfile: () => api.fetch('/auth/profile'),
        updateProfile: (data) => api.fetch('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        }),
        changePassword: (data) => api.fetch('/auth/password', {
            method: 'PUT',
            body: JSON.stringify(data)
        })
    },

    halls: {
        getAll: () => api.fetch('/halls'),
        getOne: (id) => api.fetch(`/halls/${id}`),
        getMaintenance: () => api.fetch('/halls/maintenance'),
        create: (data) => api.fetch('/halls', { method: 'POST', body: JSON.stringify(data) }),
        update: (id, data) => api.fetch(`/halls/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
        addMaintenance: (id, data) => api.fetch(`/halls/${id}/maintenance`, { method: 'POST', body: JSON.stringify(data) }),
        removeMaintenance: (id, windowId) => api.fetch(`/halls/${id}/maintenance/${windowId}`, { method: 'DELETE' }),
        delete: (id) => api.fetch(`/halls/${id}`, { method: 'DELETE' })
    },

    bookings: {
        create: (data) => api.fetch('/bookings', { method: 'POST', body: JSON.stringify(data) }),
        getUserBookings: () => api.fetch('/bookings'),
        getAll: () => api.fetch('/bookings/all'),
        getApproved: () => api.fetch('/bookings/approved'),
        updateStatus: (id, status) => api.fetch(`/bookings/${id}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        }),
        cancel: (id) => api.fetch(`/bookings/${id}/cancel`, { method: 'PUT' }),
        getRecommendations: (params) => {
            const query = new URLSearchParams(params).toString();
            return api.fetch(`/bookings/recommendations?${query}`);
        },
        getStats: () => api.fetch('/bookings/stats'),
        getPoster: (id) => api.fetch(`/bookings/${id}/poster`),
        getAvailability: (hallId, date) => api.fetch(`/bookings/availability?hallId=${encodeURIComponent(hallId)}&date=${encodeURIComponent(date)}`)
    },

    events: {
        create: (data) => api.fetch('/events', { method: 'POST', body: JSON.stringify(data) }),
        getAll: () => api.fetch('/events'),
        getMine: () => api.fetch('/events/mine'),
        getOne: (id) => api.fetch(`/events/${id}`),
        register: (id, data) => api.fetch(`/events/${id}/register`, { method: 'POST', body: JSON.stringify(data) }),
        getCheckInAccess: (id) => api.fetch(`/events/${id}/checkin/access`),
        getCheckInDesk: (id, token) => api.fetch(`/events/${id}/checkin${token ? `?token=${encodeURIComponent(token)}` : ''}`),
        setParticipantCheckIn: (eventId, participantId, data) => api.fetch(`/events/${eventId}/participants/${participantId}/checkin`, { method: 'PUT', body: JSON.stringify(data) }),
        getAnalytics: (id) => api.fetch(`/events/${id}/analytics`),
        delete: (id) => api.fetch(`/events/${id}`, { method: 'DELETE' })
    },

    notifications: {
        getAll: () => api.fetch('/notifications'),
        markAllRead: () => api.fetch('/notifications/read', { method: 'PUT' }),
        markRead: (id) => api.fetch(`/notifications/${id}/read`, { method: 'PUT' })
    }
};

function getStoredUserSafe() {
    try {
        return JSON.parse(localStorage.getItem('user') || 'null');
    } catch {
        return null;
    }
}

/* ───────── Navbar Builder ───────── */
function buildNavbar(activePage) {
    const nav = document.querySelector('nav.glass-card');
    if (!nav) return;

    const user = getStoredUserSafe();
    const isAdmin = user && user.role === 'admin';

    // Determine correct relative path prefix
    const isInPages = window.location.pathname.includes('/pages/');
    const pagesPrefix = isInPages ? '' : 'pages/';
    const rootPrefix = isInPages ? '../' : '';

    const links = [
        { href: `${pagesPrefix}dashboard.html`, label: 'Dashboard', id: 'dashboard' },
        { href: `${pagesPrefix}halls.html`, label: 'Reserve Hall', id: 'halls' },
        { href: `${pagesPrefix}bookings.html`, label: 'My Bookings', id: 'bookings' },
        { href: `${pagesPrefix}events.html`, label: 'Events', id: 'events' },
    ];

    if (isAdmin) {
        links.push({ href: `${pagesPrefix}admin.html`, label: 'Admin Panel', id: 'admin' });
    }

    const rightDiv = nav.querySelector('[data-nav-links]') || nav.children[1];
    if (!rightDiv) return;

    // Rebuild links
    let linksHtml = links.map(l => {
        const isActive = activePage === l.id;
        return `<a href="${l.href}" style="color: ${isActive ? 'white' : 'rgba(255,255,255,0.8)'}; text-decoration: none;${isActive ? ' font-weight: 600;' : ''}">${l.label}</a>`;
    }).join('');

    // Notification bell
    linksHtml += `
        <div class="notif-bell-wrapper" style="position: relative; cursor: pointer;" onclick="toggleNotifDropdown(event)">
            <i class="fas fa-bell" style="color: rgba(255,255,255,0.9); font-size: 1.1rem;"></i>
            <span id="notif-badge" class="notif-badge" style="display: none;">0</span>
            <div id="notif-dropdown" class="notif-dropdown" style="display: none;">
                <div class="notif-dropdown-header">
                    <strong>Notifications</strong>
                    <span onclick="markAllNotifRead(event)" style="font-size: 0.8rem; color: var(--primary); cursor: pointer;">Mark all read</span>
                </div>
                <div id="notif-list" class="notif-list">
                    <p style="padding: 1rem; color: var(--text-muted); text-align: center; font-size: 0.85rem;">No notifications</p>
                </div>
            </div>
        </div>
    `;

    // Profile icon
    const initial = user ? (user.name || 'U').charAt(0).toUpperCase() : 'U';
    linksHtml += `
        <a href="${pagesPrefix}profile.html" style="text-decoration: none;" title="Profile & Settings">
            <div class="nav-profile-avatar">${initial}</div>
        </a>
    `;

    // Logout
    linksHtml += `<a href="#" onclick="logout()" style="color: rgba(255,200,200,0.9); text-decoration: none;" title="Logout"><i class="fas fa-sign-out-alt"></i></a>`;

    rightDiv.innerHTML = linksHtml;
}

/* ───────── Notification System ───────── */
let _notifPollTimer = null;

function startNotificationPolling() {
    if (!localStorage.getItem('token')) return;
    fetchNotifications();
    _notifPollTimer = setInterval(fetchNotifications, 30000); // 30 seconds
}

function stopNotificationPolling() {
    if (_notifPollTimer) clearInterval(_notifPollTimer);
}

async function fetchNotifications() {
    try {
        const data = await api.notifications.getAll();
        const badge = document.getElementById('notif-badge');
        const list = document.getElementById('notif-list');

        if (badge) {
            if (data.unreadCount > 0) {
                badge.style.display = 'flex';
                badge.textContent = data.unreadCount > 99 ? '99+' : data.unreadCount;
            } else {
                badge.style.display = 'none';
            }
        }

        if (list && data.notifications.length > 0) {
            list.innerHTML = data.notifications.slice(0, 20).map(n => `
                <div class="notif-item ${n.read ? '' : 'notif-unread'}" onclick="handleNotifClick('${n._id}', '${n.link || ''}')">
                    <div class="notif-item-title">${n.title}</div>
                    <div class="notif-item-msg">${n.message}</div>
                    <div class="notif-item-time">${timeAgo(n.createdAt)}</div>
                </div>
            `).join('');
        } else if (list) {
            list.innerHTML = '<p style="padding: 1rem; color: var(--text-muted); text-align: center; font-size: 0.85rem;">No notifications yet</p>';
        }
    } catch {
        // silently ignore polling errors
    }
}

function toggleNotifDropdown(e) {
    e.stopPropagation();
    const dd = document.getElementById('notif-dropdown');
    if (dd) {
        dd.style.display = dd.style.display === 'none' ? 'block' : 'none';
    }
}

async function markAllNotifRead(e) {
    e.stopPropagation();
    try {
        await api.notifications.markAllRead();
        fetchNotifications();
    } catch { }
}

async function handleNotifClick(id, link) {
    try {
        await api.notifications.markRead(id);
    } catch { }
    if (link) {
        window.location.href = link;
    } else {
        fetchNotifications();
    }
}

function timeAgo(isoStr) {
    try {
        const now = Date.now();
        const then = new Date(isoStr + 'Z').getTime();
        const diffSec = Math.floor((now - then) / 1000);
        if (diffSec < 60) return 'Just now';
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
        if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
        return `${Math.floor(diffSec / 86400)}d ago`;
    } catch {
        return '';
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    const dd = document.getElementById('notif-dropdown');
    if (dd) dd.style.display = 'none';
});

/* ───────── Shared Utilities ───────── */
function showNotification(message, type = 'info') {
    const notify = document.getElementById('notification');
    if (!notify) return;
    
    notify.textContent = message;
    notify.style.display = 'block';
    
    if (type === 'success') notify.style.background = 'var(--success)';
    else if (type === 'error') notify.style.background = 'var(--error)';
    else notify.style.background = 'var(--accent)';

    setTimeout(() => {
        notify.style.display = 'none';
    }, 4000);
}

// Redirect if token missing
function checkAuth() {
    if (!localStorage.getItem('token')) {
        window.location.href = '/index.html';
        return false;
    }
    buildNavbar();
    startNotificationPolling();
    return true;
}

function logout() {
    stopNotificationPolling();
    localStorage.clear();
    window.location.href = '../index.html';
}
