/* Sergak AI - Frontend auth state + guards */

const AUTH_TOKEN_KEY = 'sergak_token';
const AUTH_USER_KEY = 'sergak_user';

const SergakAuth = {
  getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null');
    } catch { return null; }
  },
  setSession(token, user) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  isAdmin() {
    const u = this.getUser();
    return u && u.role === 'admin';
  },

  /* Redirect to login if not authenticated */
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  },

  /* Redirect non-admin away */
  requireAdmin() {
    if (!this.requireAuth()) return false;
    if (!this.isAdmin()) {
      alert("Bu sahifaga faqat administrator kirishi mumkin");
      window.location.href = 'index.html';
      return false;
    }
    return true;
  },

  logout() {
    this.clear();
    window.location.href = 'login.html';
  },

  /* Authenticated fetch wrapper */
  async fetch(url, options = {}) {
    const token = this.getToken();
    const headers = options.headers || {};
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    options.headers = headers;
    const r = await fetch(url, options);
    if (r.status === 401) {
      this.clear();
      window.location.href = 'login.html';
      throw new Error('Unauthorized');
    }
    return r;
  }
};

window.SergakAuth = SergakAuth;

/* Auto-guard pages (except public ones) */
(function autoGuard() {
  const path = location.pathname;
  const publicPages = ['login.html', 'register.html'];
  if (publicPages.some(p => path.endsWith(p))) return;
  if (!SergakAuth.isAuthenticated()) {
    window.location.href = 'login.html';
  }
})();

/* Update user card in sidebar with real logged-in user info */
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const u = SergakAuth.getUser();
    if (!u) return;
    const nameEl = document.querySelector('.user-name');
    const roleEl = document.querySelector('.user-role');
    const avatarEl = document.querySelector('.user-avatar');
    if (nameEl) nameEl.textContent = u.full_name || u.email;
    if (roleEl) {
      const roleName = {admin: 'Administrator', manager: 'Menejer',
                        operator: 'Operator', auditor: 'Auditor'}[u.role] || u.role;
      roleEl.textContent = roleName;
    }
    if (avatarEl) {
      const initials = (u.full_name || u.email).split(/\s+/).map(p => p[0]).slice(0, 2).join('').toUpperCase();
      avatarEl.textContent = initials;
    }
    // Make user card clickable -> logout
    const card = document.querySelector('.user-card');
    if (card) {
      card.title = 'Tizimdan chiqish';
      card.addEventListener('click', () => {
        if (confirm('Tizimdan chiqishni xohlaysizmi?')) SergakAuth.logout();
      });
    }
    // Hide admin-only menu items if not admin
    if (u.role !== 'admin') {
      document.querySelectorAll('[data-admin-only]').forEach(el => el.style.display = 'none');
    }
  }, 100);
});
