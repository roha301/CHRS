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
            throw new Error(data.message || 'Something went wrong');
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
        })
    },

    halls: {
        getAll: () => api.fetch('/halls'),
        getOne: (id) => api.fetch(`/halls/${id}`),
        create: (data) => api.fetch('/halls', { method: 'POST', body: JSON.stringify(data) }),
        update: (id, data) => api.fetch(`/halls/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
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
        getPoster: (id) => api.fetch(`/bookings/${id}/poster`)
    },

    events: {
        create: (data) => api.fetch('/events', { method: 'POST', body: JSON.stringify(data) }),
        getAll: () => api.fetch('/events'),
        getMine: () => api.fetch('/events/mine'),
        getOne: (id) => api.fetch(`/events/${id}`),
        register: (id, data) => api.fetch(`/events/${id}/register`, { method: 'POST', body: JSON.stringify(data) }),
        getAnalytics: (id) => api.fetch(`/events/${id}/analytics`),
        delete: (id) => api.fetch(`/events/${id}`, { method: 'DELETE' })
    }
};

function getStoredUserSafe() {
    try {
        return JSON.parse(localStorage.getItem('user') || 'null');
    } catch {
        return null;
    }
}

function syncRoleAwareNavbar() {
    const nav = document.querySelector('nav.glass-card');
    if (!nav) return;

    const linksDivs = Array.from(nav.children).filter((child) => child.tagName === 'DIV');
    const links = linksDivs.find(div => div.querySelector('.fa-sign-out-alt')) || linksDivs[linksDivs.length - 1];
    if (!links) return;

    nav.style.flexWrap = 'wrap';
    if (!nav.style.gap) {
        nav.style.gap = '1rem';
    }
    links.style.flexWrap = 'wrap';

    const user = getStoredUserSafe();
    const existingLink = links.querySelector('[data-admin-nav-link="true"], a[href="admin.html"]');

    if (!user || user.role !== 'admin') {
        if (existingLink) existingLink.remove();
        return;
    }

    const isAdminPage = window.location.pathname.endsWith('/admin.html') || window.location.pathname.endsWith('admin.html');
    const adminLink = existingLink || document.createElement('a');
    adminLink.setAttribute('data-admin-nav-link', 'true');
    adminLink.href = 'admin.html';
    adminLink.textContent = 'Admin Panel';
    adminLink.style.textDecoration = 'none';
    adminLink.style.color = isAdminPage ? 'white' : 'rgba(255,255,255,0.8)';
    adminLink.style.fontWeight = isAdminPage ? '700' : '500';

    if (!existingLink) {
        const logoutLink = Array.from(links.querySelectorAll('a')).find((link) =>
            link.querySelector('.fa-sign-out-alt')
        );
        if (logoutLink) {
            links.insertBefore(adminLink, logoutLink);
        } else {
            links.appendChild(adminLink);
        }
    }
}

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
    syncRoleAwareNavbar();
    return true;
}

document.addEventListener('DOMContentLoaded', syncRoleAwareNavbar);
window.addEventListener('pageshow', syncRoleAwareNavbar);
