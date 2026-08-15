/* SERGAK AI — Reusable component renderers */

function renderLiveCameraTile(c, opts={}){
  const dept = SergakApp.deptByKey(c.dept);
  const moduleIcons = c.modules.slice(0,4).map(m=>{
    const md = SergakData.MODULE_DEFS[m];
    const isAlert = c.hasAlert && (m==='fire' || m==='helmet');
    return `<div class="module-mini ${isAlert?'alert':'active'}"><i data-lucide="${md.icon}"></i></div>`;
  }).join('');
  const detections = c.hasAlert ? `
    <div class="detection-box violation" style="top:35%;left:20%;width:25%;height:50%">
      <div class="detection-label">${c.modules.includes('fire')?"🔥 OLOV — 87%":"KASKA YO'Q — 91%"}</div>
    </div>
    <div class="detection-box helmet" style="top:30%;left:60%;width:18%;height:45%">
      <div class="detection-label">PERSON — 96%</div>
    </div>` : `
    <div class="detection-box helmet" style="top:30%;left:30%;width:18%;height:50%">
      <div class="detection-label">OK — 94%</div>
    </div>
    <div class="detection-box helmet" style="top:35%;left:55%;width:18%;height:45%">
      <div class="detection-label">OK — 92%</div>
    </div>`;
  return `
  <div class="camera-tile">
    <div class="camera-feed">
      <div class="camera-feed-content">
        <img class="camera-img" src="${c.img}" alt="" loading="lazy" onerror="this.style.display='none'">
        ${detections}
      </div>
    </div>
    <div class="camera-overlay-top">
      <span class="dept-badge ${c.dept}">${dept.name.split(' ')[0]}</span>
      <span class="camera-rec"><span class="camera-rec-dot"></span>LIVE</span>
    </div>
    <div class="camera-overlay-bottom">
      <div class="camera-name">${c.name}</div>
      <div class="camera-modules-mini">${moduleIcons}</div>
    </div>
  </div>`;
}

function renderAlertItem(a){
  const dept = SergakApp.deptByKey(a.dept);
  const md = SergakData.MODULE_DEFS[a.module];
  return `
  <div class="alert-item ${a.critical?'critical':''}">
    <div class="alert-thumb">
      <i data-lucide="image"></i>
      <div class="alert-thumb-icon-overlay" style="background:${md.color}"><i data-lucide="${md.icon}"></i></div>
    </div>
    <div class="alert-content">
      <div class="alert-title">${a.msg}${a.critical?' <span style="color:var(--danger);font-size:10px">●</span>':''}</div>
      <div class="alert-meta">
        <span class="dept-badge ${a.dept}" style="font-size:9px;padding:2px 6px">${dept.name.split(' ')[0]}</span>
        <span>${a.cam}</span>
      </div>
      <div class="alert-time">${a.time}</div>
    </div>
  </div>`;
}

function renderCamCard(c){
  const dept = SergakApp.deptByKey(c.dept);
  const moduleChips = Object.keys(SergakData.MODULE_DEFS).map(m=>{
    const active = c.modules.includes(m);
    const md = SergakData.MODULE_DEFS[m];
    return `<div class="module-chip ${active?'active':''}" title="${md.name}"><i data-lucide="${md.icon}"></i>${md.name}</div>`;
  }).join('');
  const detections = c.online && (c.id % 2 === 0) ? `
    <div class="detection-box ${c.hasAlert?'violation':'helmet'}" style="top:30%;left:25%;width:22%;height:55%">
      <div class="detection-label">${c.hasAlert?'⚠️ ALERT':'OK'}</div>
    </div>` : '';
  return `
  <div class="cam-card">
    <div class="cam-card-preview">
      <div class="camera-feed">
        <div class="camera-feed-content">
          <img class="camera-img" src="${c.img}" alt="" loading="lazy" onerror="this.style.display='none'">
          ${detections}
        </div>
      </div>
      <div class="cam-card-status ${c.online?'online':'offline'}">
        <span class="cam-card-status-dot"></span>${c.online?'Onlayn':'Ofllayn'}
      </div>
      <button class="cam-card-menu" onclick="event.stopPropagation();window.SergakApp.showCamMenu(event,${c.id})">
        <i data-lucide="more-vertical"></i>
      </button>
      ${c.hasAlert?`<div style="position:absolute;bottom:10px;left:10px;background:var(--danger);color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:99px;display:flex;align-items:center;gap:5px;z-index:5" class="critical-indicator"><i data-lucide="alert-triangle" style="width:11px;height:11px"></i>${c.alerts} ALERT</div>`:''}
    </div>
    <div class="cam-card-info">
      <div class="cam-card-name">
        <span class="dept-badge ${c.dept}" style="font-size:9px">${dept.name.split(' ')[0]}</span>
        ${c.name}
      </div>
      <div class="cam-card-location"><i data-lucide="map-pin"></i>${c.loc}</div>
      <div class="cam-card-modules">${moduleChips}</div>
    </div>
  </div>`;
}

/* Cameras grouped by department */
function renderCamerasGroupedByDept(){
  const grouped = {};
  SergakData.CAMERAS.forEach(c=>{(grouped[c.dept]=grouped[c.dept]||[]).push(c)});
  return SergakData.DEPARTMENTS.filter(d=>grouped[d.key]).map(d=>`
    <div class="dept-section">
      <div class="dept-section-header">
        <div class="dept-color-bar" style="background:${d.color}"></div>
        <div class="dept-section-title">${d.name}</div>
        <div class="dept-count">${grouped[d.key].length} ta kamera</div>
      </div>
      <div class="cam-cards-grid">
        ${grouped[d.key].map(renderCamCard).join('')}
      </div>
    </div>
  `).join('');
}

/* Camera kebab menu */
SergakApp.showCamMenu = function(e, id){
  let dd = document.getElementById('camDropdown');
  if(!dd){
    dd = document.createElement('div');
    dd.id = 'camDropdown';
    dd.className = 'dropdown';
    dd.innerHTML = `
      <button class="dropdown-item" onclick="window.location='cameras.html#edit-${id}'"><i data-lucide="edit-2"></i>Tahrirlash</button>
      <button class="dropdown-item"><i data-lucide="boxes"></i>Modullarni boshqarish</button>
      <button class="dropdown-item"><i data-lucide="pen-tool"></i>Polygon zonalar</button>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item"><i data-lucide="play"></i>Live ko'rish</button>
      <button class="dropdown-item"><i data-lucide="activity"></i>Test ulanish</button>
      <button class="dropdown-item"><i data-lucide="map-pin"></i>Joylashuvni o'zgartirish</button>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item"><i data-lucide="power"></i>Vaqtincha o'chirish</button>
      <button class="dropdown-item danger"><i data-lucide="trash-2"></i>Olib tashlash</button>
    `;
    document.body.appendChild(dd);
    if(window.lucide) lucide.createIcons();
  }
  dd.style.left = (e.clientX-180)+'px';
  dd.style.top = (e.clientY+10)+'px';
  dd.classList.add('show');
  e.stopPropagation();
};
document.addEventListener('click', ()=>{
  const dd = document.getElementById('camDropdown');
  if(dd) dd.classList.remove('show');
});

/* Module toggle helper */
function toggleModuleCard(card){
  const sw = card.querySelector('.toggle-switch');
  card.classList.toggle('active');
  if(sw) sw.classList.toggle('on');
}
window.toggleModuleCard = toggleModuleCard;
