/* Cameras page logic — list + wizard + REAL network scan */

let DETECTED_SUBNET = '';
let LAST_SCAN_RESULTS = [];
let DB_CAMERAS = [];  // Real DB dan keluvchi kameralar
let ALL_MODULES = [];  // Barcha mavjud AI modullar (modules API'dan)
let EDITING_CAM_ID = null;  // Modul tahrirlash modali uchun

const ROLE_DEPT_ICONS = {
  eritish: 'flame', pechka: 'thermometer', ombor: 'package',
  quyish: 'droplet', mexanik: 'wrench', ofis: 'briefcase'
};
const DEPT_COLORS = {
  eritish: '#ef4444', pechka: '#f97316', ombor: '#3b82f6',
  quyish: '#ec4899', mexanik: '#8b5cf6', ofis: '#10b981'
};
const MODULE_ICONS = {
  helmet: 'hard-hat', phone: 'smartphone', smoking: 'cigarette-off',
  fall: 'user-x', fire: 'flame', smoke: 'cloud-fog', zone: 'shield-x',
  twoperson: 'users-2', mask: 'venetian-mask', glove: 'hand', vest: 'shirt',
};

function escapeHtml(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

async function initCameras(){
  document.getElementById('camerasContainer').innerHTML =
    '<div style="padding:40px;text-align:center;color:var(--text-muted)">' +
    '<i data-lucide="loader-2" style="width:30px;height:30px;animation:spin 1.2s linear infinite"></i>' +
    '<div style="margin-top:8px">Kameralar yuklanmoqda...</div></div>';
  renderModuleToggles();
  fetchSubnet();
  if(window.lucide) lucide.createIcons();
  await loadCamerasFromDB();
}

async function loadCamerasFromDB(){
  try {
    // Modullarni va kameralarni parallel yuklash
    const [rCams, rMods] = await Promise.all([
      SergakAuth.fetch('/api/cameras'),
      SergakAuth.fetch('/api/modules')
    ]);
    if (!rCams.ok) throw new Error('Cameras HTTP ' + rCams.status);
    DB_CAMERAS = await rCams.json();
    if (rMods.ok) ALL_MODULES = await rMods.json();
    renderRealCameras();
    startSnapshotPoller();
  } catch (e) {
    document.getElementById('camerasContainer').innerHTML =
      '<div style="padding:40px;text-align:center;color:var(--danger)">Kameralarni yuklab bo\'lmadi: ' + e.message + '</div>';
  }
}

let _snapshotTimer = null;
function startSnapshotPoller(){
  if (_snapshotTimer) clearInterval(_snapshotTimer);
  _snapshotTimer = setInterval(() => {
    DB_CAMERAS.forEach(c => {
      const img = document.getElementById('snap-' + c.id);
      if (img) {
        img.style.display = 'block';  // qayta ko'rsatish (agar onerror yashirgan bo'lsa)
        if (img.nextElementSibling) img.nextElementSibling.style.display = 'none';
        img.src = '/api/cameras/' + c.id + '/snapshot.jpg?t=' + Date.now();
      }
    });
  }, 3000);  // har 3 soniyada yangilash
}
window.addEventListener('beforeunload', () => {
  if (_snapshotTimer) clearInterval(_snapshotTimer);
});

function renderRealCameras(){
  if (!DB_CAMERAS.length) {
    document.getElementById('camerasContainer').innerHTML =
      '<div style="padding:60px;text-align:center;color:var(--text-muted)">' +
      '<i data-lucide="video-off" style="width:48px;height:48px"></i>' +
      '<div style="margin-top:12px;font-size:16px;font-weight:600">Hech qanday kamera qo\'shilmagan</div>' +
      '<div style="margin-top:6px;font-size:13px">"Tarmoqni skanerlash" yoki "Yangi kamera" tugmasini bosing</div>' +
      '</div>';
    if(window.lucide) lucide.createIcons();
    return;
  }

  // Bo'limlar bo'yicha guruhlash
  const grouped = {};
  DB_CAMERAS.forEach(c => {
    const key = c.department_key || 'boshqa';
    (grouped[key] = grouped[key] || []).push(c);
  });

  const groupNames = {
    eritish: "Eritish bo'limi", pechka: "Pechkaxona", ombor: "Ombor",
    quyish: "Quyish bo'limi", mexanik: "Mexanik ustaxona", ofis: "Ofis",
    boshqa: "Boshqa"
  };

  let html = '';
  for (const [deptKey, cams] of Object.entries(grouped)) {
    const color = DEPT_COLORS[deptKey] || '#6b7280';
    html += `
      <div class="dept-section" style="margin-bottom:30px">
        <div class="dept-section-header" style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
          <div style="width:4px;height:32px;background:${color};border-radius:2px"></div>
          <div style="font-size:18px;font-weight:700;color:var(--text);flex:1">${groupNames[deptKey] || deptKey}</div>
          <div style="font-size:13px;color:var(--text-muted)">${cams.length} ta kamera</div>
        </div>
        <div class="cam-cards-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px">
          ${cams.map(renderRealCamCard).join('')}
        </div>
      </div>`;
  }
  document.getElementById('camerasContainer').innerHTML = html;
  if(window.lucide) lucide.createIcons();
}

function renderRealCamCard(c) {
  // Barcha mavjud modullarni ko'rsatish — klik bilan toggle qilinadi
  const enabledSet = new Set(c.modules_enabled || []);
  const moduleIcons = ALL_MODULES.map(m => {
    const icon = MODULE_ICONS[m.key] || m.icon || 'boxes';
    const isActive = enabledSet.has(m.key);
    const hasModel = m.model_path && m.model_path.length > 0;
    const bgColor = isActive ? m.color : 'var(--surface-2)';
    const iconColor = isActive ? '#fff' : 'var(--text-dim)';
    const opacity = isActive ? '1' : (hasModel ? '0.55' : '0.25');
    const border = isActive ? `2px solid ${m.color}` : '2px solid transparent';
    const cursor = hasModel ? 'pointer' : 'not-allowed';
    const tooltip = !hasModel
      ? `${m.name} — .pt yo'q`
      : `${m.name}: ${isActive ? 'YOQILGAN (o\'chirish uchun bosing)' : "O'CHIRILGAN (yoqish uchun bosing)"}`;
    const onclick = hasModel
      ? `event.stopPropagation();quickToggleModule(${c.id},'${m.key}',this)`
      : 'event.stopPropagation()';
    return `<div title="${escapeHtml(tooltip)}"
                 onclick="${onclick}"
                 data-mod-key="${m.key}" data-cam-id="${c.id}"
                 style="background:${bgColor};width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;opacity:${opacity};transition:all .15s;cursor:${cursor};border:${border}"
                 onmouseover="if(this.style.cursor!=='not-allowed') this.style.transform='scale(1.1)'"
                 onmouseout="this.style.transform='scale(1)'">
              <i data-lucide="${icon}" style="width:16px;height:16px;color:${iconColor};pointer-events:none"></i>
           </div>`;
  }).join('');
  const enabledCount = (c.modules_enabled || []).length;

  // RTSP'dan IP va kanal raqamini ajratish
  const ipMatch = (c.rtsp_url || '').match(/@(\d+\.\d+\.\d+\.\d+)/);
  const ip = ipMatch ? ipMatch[1] : c.ip;
  const chMatch = (c.rtsp_url || '').match(/Channels\/(\d+)/);
  const channel = chMatch ? chMatch[1] : '';

  const onlineDot = c.online
    ? '<span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;box-shadow:0 0 6px var(--success)"></span>'
    : '<span style="width:8px;height:8px;border-radius:50%;background:var(--text-dim);display:inline-block"></span>';
  const onlineText = c.online ? 'Onlayn' : 'Ofllayn';
  // Live snapshot - har 3 sekundda yangilanadi (img tag avto-refresh orqali)
  const snapshotUrl = `/api/cameras/${c.id}/snapshot.jpg?t=${Date.now()}`;

  return `
  <div class="cam-card" style="background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:all .15s" data-cam-id="${c.id}">
    <div style="background:#0a0e1a;height:180px;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden">
      <img id="snap-${c.id}" src="${snapshotUrl}" alt=""
           style="width:100%;height:100%;object-fit:cover;display:block"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
      <div style="display:none;width:100%;height:100%;align-items:center;justify-content:center;flex-direction:column;color:var(--text-muted)">
        <i data-lucide="video-off" style="width:42px;height:42px;opacity:.4"></i>
        <div style="margin-top:8px;font-size:11px">Tasvir mavjud emas</div>
      </div>
      <div style="position:absolute;top:10px;left:10px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,.55);backdrop-filter:blur(8px);padding:5px 10px;border-radius:6px;font-size:11px;color:#fff">
        ${onlineDot} ${onlineText}
      </div>
      ${channel ? `<div style="position:absolute;top:10px;right:10px;background:rgba(59,130,246,.85);color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px">CH ${channel}</div>` : ''}
      <div style="position:absolute;bottom:8px;right:10px;background:rgba(239,68,68,.85);color:#fff;font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;display:flex;align-items:center;gap:4px">
        <span style="width:6px;height:6px;border-radius:50%;background:#fff;animation:pulse 1.5s infinite"></span>LIVE
      </div>
    </div>
    <div style="padding:14px">
      <div style="font-weight:700;font-size:14px;color:var(--text);margin-bottom:4px">${escapeHtml(c.name)}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px"><i data-lucide="map-pin" style="width:11px;height:11px;display:inline;vertical-align:middle"></i> ${escapeHtml(c.location || ip)}</div>
      <div style="font-size:10px;color:var(--text-dim);margin-bottom:10px;font-family:'JetBrains Mono',monospace;background:var(--surface-2);padding:4px 8px;border-radius:4px">${ip}${channel ? ':554/CH'+channel : ''}</div>
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:6px;display:flex;align-items:center;gap:6px">
        <i data-lucide="cpu" style="width:11px;height:11px"></i>
        <span>AI modullar: <b style="color:var(--text)">${enabledCount}/${ALL_MODULES.length}</b> faol</span>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">${moduleIcons}</div>
    </div>
    <div style="display:flex;gap:6px;padding:10px 14px;border-top:1px solid var(--border);background:var(--surface-2)">
      <button class="btn btn-primary" style="flex:1;padding:6px 10px;font-size:11px" onclick="event.stopPropagation();openModulesModal(${c.id})">
        <i data-lucide="settings-2" style="width:12px;height:12px"></i>Modullar (${enabledCount})
      </button>
      <button class="btn btn-secondary" style="flex:1;padding:6px 10px;font-size:11px" onclick="event.stopPropagation();window.location='events.html?camera_id=${c.id}'">
        <i data-lucide="activity" style="width:12px;height:12px"></i>Hodisalar
      </button>
      <button class="btn btn-secondary" style="padding:6px 10px;font-size:11px;color:var(--danger)" onclick="event.stopPropagation();deleteCameraDB(${c.id})" title="O'chirish">
        <i data-lucide="trash-2" style="width:12px;height:12px"></i>
      </button>
    </div>
  </div>`;
}

/* ============ Tezkor (klik) toggle ============ */

async function quickToggleModule(camId, modKey, iconEl) {
  const cam = DB_CAMERAS.find(c => c.id === camId);
  if (!cam) return;
  const enabled = new Set(cam.modules_enabled || []);
  const wasOn = enabled.has(modKey);
  if (wasOn) enabled.delete(modKey);
  else enabled.add(modKey);
  const newList = Array.from(enabled);

  // Visual feedback (avval UI'ni yangilash, keyin saqlash)
  const mod = ALL_MODULES.find(m => m.key === modKey);
  const modColor = mod ? mod.color : '#3b82f6';
  if (iconEl) {
    if (!wasOn) {
      iconEl.style.background = modColor;
      iconEl.style.opacity = '1';
      iconEl.style.border = `2px solid ${modColor}`;
      const i = iconEl.querySelector('i');
      if (i) i.style.color = '#fff';
    } else {
      iconEl.style.background = 'var(--surface-2)';
      iconEl.style.opacity = '0.55';
      iconEl.style.border = '2px solid transparent';
      const i = iconEl.querySelector('i');
      if (i) i.style.color = 'var(--text-dim)';
    }
  }

  try {
    const r = await SergakAuth.fetch(`/api/cameras/${camId}/modules`, {
      method: 'PATCH',
      body: { modules: newList }
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    // DB cache yangilash
    cam.modules_enabled = newList;
    // Action toast
    const action = wasOn ? "o'chirildi" : "yoqildi";
    SergakApp.showToast('success', mod ? mod.name : modKey, action);
    // Hisoblovchi yangilash (Modullar (N) tugmasi)
    const card = iconEl.closest('.cam-card');
    if (card) {
      const btn = card.querySelector('button[onclick*="openModulesModal"]');
      if (btn) btn.innerHTML = btn.innerHTML.replace(/\(\d+\)/, `(${newList.length})`);
      const counter = card.querySelector('b');
      if (counter) counter.innerText = `${newList.length}/${ALL_MODULES.length}`;
    }
  } catch (e) {
    // Xato — qaytarish
    SergakApp.showToast('error', 'Xato', 'Saqlanmadi: ' + e.message);
    // UI ni qaytarish
    if (iconEl) {
      if (wasOn) {
        iconEl.style.background = modColor;
        iconEl.style.opacity = '1';
        iconEl.style.border = `2px solid ${modColor}`;
      } else {
        iconEl.style.background = 'var(--surface-2)';
        iconEl.style.opacity = '0.55';
        iconEl.style.border = '2px solid transparent';
      }
    }
  }
}

/* ============ Modullarni tahrirlash modali ============ */

function openModulesModal(camId) {
  EDITING_CAM_ID = camId;
  const cam = DB_CAMERAS.find(c => c.id === camId);
  if (!cam) return;

  const enabledSet = new Set(cam.modules_enabled || []);

  // Modal yaratish (har gal qaytadan)
  let modal = document.getElementById('modalCameraModules');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'modalCameraModules';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  const moduleItems = ALL_MODULES.map(m => {
    const isActive = enabledSet.has(m.key);
    const icon = MODULE_ICONS[m.key] || m.icon || 'boxes';
    const hasModel = m.model_path && m.model_path.length > 0;
    const disabled = !hasModel || !m.enabled;
    const disabledNote = !hasModel ? "(.pt fayl yo'q)" : (!m.enabled ? "(modul o'chirilgan)" : "");

    return `
    <label style="display:flex;align-items:center;gap:14px;padding:14px;background:var(--surface-2);border:2px solid ${isActive?m.color:'var(--border)'};border-radius:12px;cursor:${disabled?'not-allowed':'pointer'};margin-bottom:10px;transition:all .15s;opacity:${disabled?'0.5':'1'}">
      <div style="width:44px;height:44px;border-radius:10px;background:${m.color};display:flex;align-items:center;justify-content:center;flex-shrink:0">
        <i data-lucide="${icon}" style="width:22px;height:22px;color:#fff"></i>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:700;font-size:14px;color:var(--text)">${escapeHtml(m.name)} ${disabledNote ? `<span style="font-size:10px;color:var(--warning);font-weight:500">${disabledNote}</span>` : ''}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:3px">${escapeHtml(m.description || '')}</div>
        ${m.model_filename ? `<div style="font-size:10px;color:var(--text-dim);font-family:monospace;margin-top:3px">${escapeHtml(m.model_filename)} - ${m.file_size_mb.toFixed(1)} MB</div>` : ''}
      </div>
      <input type="checkbox" data-mod-key="${m.key}" ${isActive?'checked':''} ${disabled?'disabled':''}
             style="width:48px;height:26px;cursor:${disabled?'not-allowed':'pointer'};accent-color:${m.color}"
             onchange="event.stopPropagation()">
    </label>`;
  }).join('');

  modal.innerHTML = `
    <div class="modal" style="max-width:600px;max-height:85vh;display:flex;flex-direction:column">
      <div class="modal-header">
        <div>
          <div class="modal-title">Modullar boshqaruvi</div>
          <div class="modal-subtitle">${escapeHtml(cam.name)}</div>
        </div>
        <button class="modal-close" onclick="closeModulesModal()"><i data-lucide="x"></i></button>
      </div>
      <div class="modal-body" style="overflow-y:auto;flex:1">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:14px;padding:10px;background:rgba(59,130,246,.08);border-radius:8px;border-left:3px solid var(--primary)">
          <i data-lucide="info" style="width:13px;height:13px;display:inline;vertical-align:middle"></i>
          Yoqilgan modullar bu kamerada ishlaydi. O'zgartirishlar 30 soniya ichida kuchga kiradi.
        </div>
        ${moduleItems}
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="toggleAllModules(true)">
          <i data-lucide="check-circle"></i>Hammasi
        </button>
        <button class="btn btn-secondary" onclick="toggleAllModules(false)">
          <i data-lucide="circle"></i>Hech qaysi
        </button>
        <div style="flex:1"></div>
        <button class="btn btn-secondary" onclick="closeModulesModal()">Bekor</button>
        <button class="btn btn-primary" onclick="saveModulesForCamera()">
          <i data-lucide="save"></i>Saqlash
        </button>
      </div>
    </div>`;

  modal.classList.add('show');
  if (window.lucide) lucide.createIcons();
}

function closeModulesModal() {
  const modal = document.getElementById('modalCameraModules');
  if (modal) modal.classList.remove('show');
  EDITING_CAM_ID = null;
}

function toggleAllModules(state) {
  document.querySelectorAll('#modalCameraModules input[data-mod-key]').forEach(cb => {
    if (!cb.disabled) cb.checked = state;
  });
}

async function saveModulesForCamera() {
  if (!EDITING_CAM_ID) return;
  const checked = Array.from(
    document.querySelectorAll('#modalCameraModules input[data-mod-key]:checked')
  ).map(cb => cb.dataset.modKey);

  try {
    const r = await SergakAuth.fetch(`/api/cameras/${EDITING_CAM_ID}/modules`, {
      method: 'PATCH',
      body: { modules: checked }
    });
    if (!r.ok) {
      const err = await r.json().catch(()=>({}));
      SergakApp.showToast('error', 'Xato', err.detail || "Saqlab bo'lmadi");
      return;
    }
    closeModulesModal();
    SergakApp.showToast('success', 'OK', `${checked.length} ta modul biriktirildi`);
    await loadCamerasFromDB();
  } catch (e) {
    SergakApp.showToast('error', 'Xato', 'Tarmoq xatosi');
  }
}

async function testCameraConn(id) {
  try {
    const r = await SergakAuth.fetch('/api/cameras/' + id + '/test', {method:'POST'});
    if (!r.ok) { SergakApp.showToast('error', 'Xato', 'Ulanib bo\'lmadi'); return; }
    const data = await r.json();
    SergakApp.showToast('success', 'OK', `Kamera ulandi - FPS ${data.fps}, ${data.resolution}`);
  } catch (e) {
    SergakApp.showToast('error', 'Xato', 'Tarmoq xatosi');
  }
}

async function deleteCameraDB(id) {
  const c = DB_CAMERAS.find(x => x.id === id);
  if (!c) return;
  if (!confirm(`"${c.name}" kamerasini o'chirmoqchimisiz?\nBu amal qaytarilmaydi.`)) return;
  try {
    const r = await SergakAuth.fetch('/api/cameras/' + id, {method:'DELETE'});
    if (!r.ok && r.status !== 204) { SergakApp.showToast('error', 'Xato', "O'chirib bo'lmadi"); return; }
    SergakApp.showToast('success', 'OK', "Kamera o'chirildi");
    await loadCamerasFromDB();
  } catch (e) {
    SergakApp.showToast('error', 'Xato', 'Tarmoq xatosi');
  }
}

async function fetchSubnet(){
  try {
    const r = await SergakAuth.fetch('/api/discovery/subnet');
    if (!r.ok) return;
    const data = await r.json();
    DETECTED_SUBNET = data.subnet || '192.168.1.0/24';
    // Show on initial scan-meta labels
    const m1 = document.getElementById('scanProgressText');
    const m2 = document.getElementById('quickScanMeta');
    if (m1) m1.textContent = DETECTED_SUBNET + ' — tayyorlanmoqda...';
    if (m2) m2.textContent = DETECTED_SUBNET + ' — tayyorlanmoqda...';
  } catch (e) {}
}

function renderModuleToggles(){
  const grid = document.getElementById('moduleTogglesGrid');
  if(!grid) return;
  const items = [
    {k:'helmet', name:'Kaska Aniqlash', desc:'PPE — kaska kiyimi nazorati', icon:'hard-hat', on:true},
    {k:'phone', name:'Telefon Aniqlash', desc:"Ish vaqtida telefon ishlatish", icon:'smartphone', on:false},
    {k:'smoking', name:'Chekish Aniqlash', desc:"Yong'in xavfini oldini olish", icon:'cigarette-off', on:false},
    {k:'fall', name:'Yiqilish Aniqlash', desc:'Favqulodda hodisalar', icon:'user-x', on:true},
    {k:'fire', name:"Yong'in & Tutun", desc:'Dastlabki bosqichda aniqlash', icon:'flame', on:true},
    {k:'zone', name:'Cheklangan Zona', desc:'Polygon — taqiqlangan hudud', icon:'shield-x', on:true},
    {k:'twoperson', name:'Two-Person Rule', desc:"Yolg'iz ishlash taqiq", icon:'users-2', on:false}
  ];
  grid.innerHTML = items.map(i=>`
    <div class="module-toggle ${i.on?'active':''}" onclick="toggleModuleCard(this)">
      <div class="module-toggle-icon"><i data-lucide="${i.icon}"></i></div>
      <div class="module-toggle-info">
        <div class="module-toggle-name">${i.name}</div>
        <div class="module-toggle-desc">${i.desc}</div>
      </div>
      <div class="toggle-switch ${i.on?'on':''}"></div>
    </div>`).join('');
}

/* Wizard */
let wizardStep = 1;
function goToWizard(step){
  if(step==='next'){
    if(wizardStep===1) wizardStep=2;
    else if(wizardStep===2) wizardStep=3;
    else if(wizardStep===3){ saveCameraFromWizard(); return; }
  } else wizardStep = step;
  updateWizard();
  if(wizardStep===2) startScan();
}
function updateWizard(){
  ['1','2','3'].forEach((s,i)=>{
    const el = document.getElementById('wizStep'+s);
    el.className = 'wizard-step';
    if(i+1 < wizardStep) el.classList.add('completed');
    else if(i+1===wizardStep) el.classList.add('active');
    document.getElementById('wizardPanel'+s).style.display = i+1===wizardStep?'block':'none';
  });
  document.getElementById('wizBack').style.display = wizardStep>1?'inline-flex':'none';
  document.getElementById('wizNextText').textContent = wizardStep===3?'Saqlash':'Davom etish';
  const subs = {1:"Qaysi yo'l bilan qo'shamiz?",2:'Tarmoqdagi kameralarni topamiz',3:'Kamera sozlamalarini sozlash'};
  document.getElementById('addCamSubtitle').textContent = subs[wizardStep];
  if(window.lucide) lucide.createIcons();
}
window.onOpen_modalAddCamera = function(){ wizardStep=1; updateWizard(); };

/* ============ REAL SCAN ============ */

async function runRealScan(progressId, completeCallback){
  // The backend scan blocks until done. We start a fake progress
  // animation so the user sees motion, but the real results come from the API call.
  let pct = 0;
  let progressTimer = null;
  const startTime = Date.now();
  if (progressId) {
    const el = document.getElementById(progressId);
    progressTimer = setInterval(() => {
      // Simulate progressing — most of the time is WS-Discovery + port scan (~6-10s)
      const elapsed = (Date.now() - startTime) / 1000;
      // Ease towards 95% over ~10 seconds
      pct = Math.min(95, Math.floor((1 - Math.exp(-elapsed/3.5)) * 100));
      if (el) el.textContent = (DETECTED_SUBNET || 'tarmoq') + ' — ' + pct + '% (' + elapsed.toFixed(1) + 's)';
    }, 200);
  }

  try {
    const r = await SergakAuth.fetch('/api/discovery/scan', {
      method: 'POST',
      body: {subnet: DETECTED_SUBNET || null, deep: true}
    });
    if (progressTimer) clearInterval(progressTimer);
    if (!r.ok) {
      SergakApp.showToast('error', 'Skanerlash xato', "Server javob bermadi");
      completeCallback({cameras: [], error: true});
      return;
    }
    const data = await r.json();
    DETECTED_SUBNET = data.subnet_scanned;
    LAST_SCAN_RESULTS = data.cameras || [];
    completeCallback(data);
  } catch (e) {
    if (progressTimer) clearInterval(progressTimer);
    SergakApp.showToast('error', 'Tarmoq xatosi', e.message || 'Aloqa yoq');
    completeCallback({cameras: [], error: true});
  }
}

/* Wizard scan view */
function startScan(){
  document.getElementById('scanRunningView').style.display='block';
  document.getElementById('scanResultsView').style.display='none';
  runRealScan('scanProgressText', (data) => {
    document.getElementById('scanRunningView').style.display='none';
    document.getElementById('scanResultsView').style.display='block';
    renderFoundCameras(data);
  });
}

function badgeForCamera(f){
  if (f.already_added) return '<span class="found-camera-status status-ok"><i data-lucide="check-circle-2" style="width:11px;height:11px"></i>Qo\'shilgan</span>';
  if (f.status === 'onvif') return '<span class="found-camera-status status-ok"><i data-lucide="zap" style="width:11px;height:11px"></i>ONVIF</span>';
  if (f.status === 'rtsp') return '<span class="found-camera-status status-ok"><i data-lucide="video" style="width:11px;height:11px"></i>RTSP</span>';
  if (f.status === 'http') return '<span class="found-camera-status status-auth"><i data-lucide="globe" style="width:11px;height:11px"></i>HTTP</span>';
  return '<span class="found-camera-status status-auth"><i data-lucide="help-circle" style="width:11px;height:11px"></i>Topildi</span>';
}

function camDisplayName(f){
  if (f.manufacturer && f.model) return f.manufacturer + ' ' + f.model;
  if (f.manufacturer) return f.manufacturer + ' kamera';
  if (f.model) return f.model;
  if (f.server_banner) return f.server_banner;
  return "Aniqlanmagan qurilma";
}

function renderFoundCameras(data){
  const cameras = (data && data.cameras) || [];
  document.getElementById('foundCount').textContent = cameras.length;

  if (!cameras.length) {
    document.getElementById('foundCamerasList').innerHTML =
      `<div style="padding:30px;text-align:center;color:var(--text-muted);font-size:13px">
         <i data-lucide="search-x" style="width:36px;height:36px;display:block;margin:0 auto 10px;color:var(--text-dim)"></i>
         <div style="font-weight:600;margin-bottom:4px;color:var(--text)">Tarmoqda kamera topilmadi</div>
         <div>${DETECTED_SUBNET} tarmog'i tekshirildi · ${(data.duration_ms||0)/1000}s</div>
         <div style="margin-top:12px;font-size:11px">Tekshirilgan: ONVIF multicast (port 3702), RTSP (554), HTTP (80/8080/8000).<br>Agar kamera bor bo'lsa, ehtimol u boshqa tarmoqda yoki firewall bloklab turibdi.</div>
       </div>`;
    if(window.lucide) lucide.createIcons();
    return;
  }

  // Mark already-added cameras (by IP match in stored cameras list)
  const existingIPs = new Set();
  if (window.SergakData && Array.isArray(SergakData.CAMERAS)) {
    SergakData.CAMERAS.forEach(c => {
      const m = (c.rtsp_url || c.ip || '').match(/(\d+\.\d+\.\d+\.\d+)/);
      if (m) existingIPs.add(m[1]);
    });
  }
  cameras.forEach(c => { c.already_added = existingIPs.has(c.ip); });

  document.getElementById('foundCamerasList').innerHTML = cameras.map(f => {
    const ports = (f.ports || []).join(', ');
    const portsText = ports ? `Portlar: ${ports}` : '';
    const macText = f.mac ? ` · MAC ${f.mac}` : '';
    const bannerText = f.server_banner ? ` · ${escapeHtml(f.server_banner.slice(0,40))}` : '';
    const btn = f.already_added
      ? '<button class="btn btn-secondary" disabled style="opacity:.5">Qo\'shilgan</button>'
      : `<button class="btn btn-primary" onclick="useFoundCamera('${f.ip}')" style="padding:7px 14px;font-size:12px"><i data-lucide="plus"></i>Qo'shish</button>`;
    return `
    <div class="found-camera ${f.already_added?'added':''}">
      <div class="found-camera-thumb"><i data-lucide="video"></i></div>
      <div class="found-camera-info">
        <div class="found-camera-name">${escapeHtml(camDisplayName(f))} ${badgeForCamera(f)}</div>
        <div class="found-camera-meta">${f.ip}${macText}</div>
        <div class="found-camera-meta" style="font-size:10px;color:var(--text-dim);margin-top:2px;font-family:'JetBrains Mono',monospace">${portsText}${bannerText}</div>
      </div>${btn}
    </div>`;
  }).join('');
  if(window.lucide) lucide.createIcons();
}

function escapeHtml(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

function useFoundCamera(ip){
  // Pre-fill the wizard step 3 with this camera's details
  const cam = LAST_SCAN_RESULTS.find(c => c.ip === ip);
  if (!cam) return;
  // Switch to step 3
  wizardStep = 3;
  updateWizard();
  // Pre-fill RTSP URL
  setTimeout(() => {
    const inputs = document.querySelectorAll('#wizardPanel3 .form-input');
    if (inputs.length >= 4) {
      // [name, location, RTSP URL]  — depends on layout
      // The RTSP is the 4th input in our HTML
    }
    // Find the RTSP input by checking value pattern
    document.querySelectorAll('#wizardPanel3 .form-input').forEach(inp => {
      if (inp.value && inp.value.startsWith('rtsp://')) {
        inp.value = cam.rtsp_url || `rtsp://${cam.ip}:554/Streaming/Channels/101`;
      }
    });
    // Update camera name suggestion if it has manufacturer info
    if (cam.manufacturer || cam.model) {
      const nameInput = document.querySelector('#wizardPanel3 .form-input');
      if (nameInput && nameInput.placeholder.toLowerCase().includes('eritish')) {
        nameInput.value = camDisplayName(cam) + ' (' + cam.ip + ')';
      }
    }
  }, 100);
}

/* Quick scan modal (top-right "Tarmoqni skanerlash" button) */
function startQuickScan(){
  document.getElementById('quickScanRunning').style.display='block';
  document.getElementById('quickScanResults').style.display='none';
  runRealScan('quickScanMeta', (data) => {
    document.getElementById('quickScanRunning').style.display='none';
    document.getElementById('quickScanResults').style.display='block';
    renderQuickFound(data);
  });
}

function renderQuickFound(data){
  const cameras = (data && data.cameras) || [];
  const existingIPs = new Set();
  if (window.SergakData && Array.isArray(SergakData.CAMERAS)) {
    SergakData.CAMERAS.forEach(c => {
      const m = (c.rtsp_url || c.ip || '').match(/(\d+\.\d+\.\d+\.\d+)/);
      if (m) existingIPs.add(m[1]);
    });
  }
  cameras.forEach(c => { c.already_added = existingIPs.has(c.ip); });

  const newCams = cameras.filter(c => !c.already_added);
  const existing = cameras.filter(c => c.already_added);
  document.getElementById('qsFound').textContent = newCams.length;
  document.getElementById('qsExisting').textContent = existing.length;

  if (!cameras.length) {
    document.getElementById('quickFoundList').innerHTML =
      `<div style="padding:30px;text-align:center;color:var(--text-muted);font-size:13px">
        <i data-lucide="search-x" style="width:36px;height:36px;display:block;margin:0 auto 10px;color:var(--text-dim)"></i>
        <div style="font-weight:600;margin-bottom:4px;color:var(--text)">Tarmoqda hech narsa topilmadi</div>
        <div>${data.subnet_scanned||DETECTED_SUBNET} · ${data.hosts_scanned||0} ta IP · ${(data.duration_ms||0)/1000}s</div>
        <div style="margin-top:14px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);padding:12px;border-radius:8px;text-align:left;font-size:11px;line-height:1.6">
          <b style="color:var(--warning)">Maslahatlar:</b><br>
          • Kompyuter va kamera bir tarmoqda ekanligini tekshiring<br>
          • Windows Defender Firewall <code>python.exe</code> uchun keluvchi UDP/TCP ga ruxsat berishi kerak<br>
          • Kamera quvvati yoqilganligini va tarmoq kabeli ulanganligini tekshiring<br>
          • Sozlamalar bo'limida boshqa subnet (masalan, 10.0.0.0/24) kiriting va qaytadan urinib ko'ring
        </div>
      </div>`;
    if(window.lucide) lucide.createIcons();
    return;
  }

  document.getElementById('quickFoundList').innerHTML = cameras.map(f => {
    const macText = f.mac ? ` · MAC ${f.mac}` : '';
    const cb = f.already_added
      ? '<div style="width:18px"></div>'
      : `<input type="checkbox" data-ip="${f.ip}" checked style="width:18px;height:18px;accent-color:var(--primary)">`;
    return `
    <div class="found-camera ${f.already_added?'added':''}">${cb}
      <div class="found-camera-thumb"><i data-lucide="video"></i></div>
      <div class="found-camera-info">
        <div class="found-camera-name">${escapeHtml(camDisplayName(f))} ${badgeForCamera(f)}</div>
        <div class="found-camera-meta">${f.ip}${macText}</div>
        ${f.server_banner ? `<div class="found-camera-meta" style="font-size:10px;color:var(--text-dim);margin-top:2px">${escapeHtml(f.server_banner.slice(0,50))}</div>` : ''}
      </div>
      <button class="btn btn-ghost" style="padding:6px 8px" onclick="window.open('${f.http_url || ('http://' + f.ip)}', '_blank')" title="Brauzerda ochish"><i data-lucide="external-link"></i></button>
    </div>`;
  }).join('');
  if(window.lucide) lucide.createIcons();
}

window.onOpen_modalScan = function(){ startQuickScan(); };

function saveCameraFromWizard(){
  SergakApp.closeModal('modalAddCamera');
  SergakApp.showToast('success',"Kamera qo'shildi","Kamera bo'limga qo'shildi");
}
