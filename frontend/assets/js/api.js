/* Sergak AI — REST API client
   Loads data from backend if available; falls back to mock data otherwise. */

const API_BASE = (() => {
  // If served by FastAPI on same host, use same origin
  if (location.protocol.startsWith('http') && location.port) return '';
  // Otherwise (file:// or no port), use default backend
  return 'http://localhost:5000';
})();

async function apiGet(path) {
  try {
    const r = await fetch(API_BASE + path, { method: 'GET' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e) {
    console.warn('[API]', path, 'failed:', e.message, '— using mock');
    return null;
  }
}

async function apiPost(path, body) {
  try {
    const r = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e) {
    console.warn('[API]', path, 'failed:', e.message);
    return null;
  }
}

async function apiPut(path, body) {
  try {
    const r = await fetch(API_BASE + path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e) {
    console.warn('[API]', path, 'failed:', e.message);
    return null;
  }
}

async function apiDelete(path) {
  try {
    const r = await fetch(API_BASE + path, { method: 'DELETE' });
    return r.ok;
  } catch (e) {
    console.warn('[API]', path, 'failed:', e.message);
    return false;
  }
}

/* High-level data loaders — try backend, fall back to mock */
async function loadCameras() {
  const data = await apiGet('/api/cameras');
  if (data && Array.isArray(data) && data.length) {
    // Map backend shape to frontend shape
    return data.map((c, i) => ({
      id: c.id,
      name: c.name,
      dept: _deptKeyById(c.department_id),
      loc: c.location || '',
      online: c.online,
      modules: c.modules_enabled || [],
      alerts: 0,
      img: SergakData.CAM_IMAGES[i % SergakData.CAM_IMAGES.length],
    }));
  }
  return SergakData.CAMERAS;
}

async function loadDepartments() {
  const data = await apiGet('/api/departments');
  if (data && Array.isArray(data) && data.length) {
    SergakData._deptIdMap = {};
    data.forEach(d => SergakData._deptIdMap[d.id] = d.key);
    return data;
  }
  return SergakData.DEPARTMENTS;
}

async function loadEvents(limit = 50) {
  const data = await apiGet('/api/events?limit=' + limit);
  if (data && Array.isArray(data) && data.length) {
    return data.map(e => ({
      id: e.id,
      dept: 'eritish',  // would need to join via camera_id
      cam: 'Camera #' + e.camera_id,
      module: e.module_name,
      msg: e.message,
      time: new Date(e.timestamp).toLocaleTimeString('en-GB', { hour12: false }),
      critical: e.critical,
      confidence: e.confidence,
    }));
  }
  return SergakData.RECENT_ALERTS;
}

async function loadStats() {
  return await apiGet('/api/events/stats/summary') || {
    today_total: 23, yesterday_total: 26, today_critical: 3, trend_percent: -12,
  };
}

function _deptKeyById(id) {
  if (SergakData._deptIdMap && SergakData._deptIdMap[id]) return SergakData._deptIdMap[id];
  return 'eritish';
}

window.SergakAPI = {
  apiGet, apiPost, apiPut, apiDelete,
  loadCameras, loadDepartments, loadEvents, loadStats,
};
