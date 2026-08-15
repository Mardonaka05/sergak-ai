/* SERGAK AI - Shared application logic */

const NAV_ITEMS = [
  {section:'Asosiy', items:[
    {key:'dashboard', name:'Boshqaruv paneli', icon:'layout-dashboard', href:'index.html'},
    {key:'cameras', name:'Kameralar', icon:'camera', href:'cameras.html', badge:'14'},
    {key:'departments', name:"Bo'limlar", icon:'building-2', href:'departments.html'},
    {key:'events', name:'Hodisalar', icon:'alert-octagon', href:'events.html', badge:'7'},
    {key:'chat', name:'Xabarlar', icon:'message-circle', href:'chat.html', badgeId:'navUnreadBadge'}
  ]},
  {section:'Tahlil', items:[
    {key:'analytics', name:'Analitika', icon:'bar-chart-3', href:'analytics.html'},
    {key:'reports', name:'Hisobotlar', icon:'file-text', href:'reports.html'},
    {key:'floorplan', name:'Zavod xaritasi', icon:'map', href:'floorplan.html'}
  ]},
  {section:'Sozlamalar', items:[
    {key:'modules', name:'AI modullar', icon:'boxes', href:'modules.html'},
    {key:'users', name:'Foydalanuvchilar', icon:'users', href:'users.html', adminOnly:true},
    {key:'settings', name:'Sozlamalar', icon:'settings', href:'settings.html'}
  ]}
];

const PAGE_TITLES = {
  dashboard:['Boshqaruv paneli','Real-time xavfsizlik nazorati'],
  cameras:['Kameralar',"14 ta kamera, 6 ta bo'limda"],
  departments:["Bo'limlar","Bo'limlar va ularning sozlamalari"],
  events:['Hodisalar','Qoidabuzarliklar va alertlar'],
  analytics:['Analitika','Chuqur statistik tahlil'],
  reports:['Hisobotlar','Avtomatik hisobotlar'],
  floorplan:['Zavod xaritasi',"Top-down ko'rinish"],
  modules:['AI modullar','7 ta aniqlash moduli'],
  users:['Foydalanuvchilar','Rollar va huquqlar'],
  settings:['Sozlamalar','Tizim sozlamalari']
};

function renderSidebar(activeKey){
  const navHtml = NAV_ITEMS.map(s=>{
    const items = s.items.map(it=>{
      let badgeHtml = '';
      if (it.badgeId) {
        badgeHtml = '<span class="nav-badge nav-badge-unread" id="'+it.badgeId+'" style="display:none;background:var(--danger)">0</span>';
      } else if (it.badge) {
        badgeHtml = '<span class="nav-badge">'+it.badge+'</span>';
      }
      return '<a class="nav-item '+(it.key===activeKey?'active':'')+'" href="'+it.href+'"'+(it.adminOnly?' data-admin-only':'')+'>'+
        '<i data-lucide="'+it.icon+'"></i>'+it.name+badgeHtml+'</a>';
    }).join('');
    return '<div class="nav-section"><div class="nav-section-title">'+s.section+'</div>'+items+'</div>';
  }).join('');

  return `
    <aside class="sidebar">
      <div class="sidebar-header">
        <a href="index.html" class="brand">
          <div class="brand-logo"><i data-lucide="shield-check"></i></div>
          <div class="brand-text">
            <span class="brand-name">SERGAK AI</span>
            <span class="brand-tagline">Sanoat Xavfsizligi</span>
          </div>
        </a>
      </div>
      <nav class="nav">${navHtml}</nav>
      <div class="sidebar-footer">
        <div class="user-card">
          <div class="user-avatar">MS</div>
          <div class="user-info">
            <div class="user-name">Mardon Sulaymonqulov</div>
            <div class="user-role">Administrator</div>
          </div>
        </div>
      </div>
    </aside>
  `;
}

function renderTopbar(activeKey){
  const t = PAGE_TITLES[activeKey] || ['Sergak AI',''];
  return `
    <header class="topbar">
      <div>
        <div class="page-title">${t[0]}</div>
        <div class="page-subtitle">${t[1]}</div>
      </div>
      <div class="topbar-spacer"></div>
      <div class="topbar-search">
        <i data-lucide="search"></i>
        <input type="text" placeholder="Qidirish...">
        <kbd>Ctrl+K</kbd>
      </div>
      <div class="live-pill"><span class="live-dot"></span>Live</div>
      <div class="lang-switcher">
        <button class="active">UZ</button>
        <button>RU</button>
        <button>EN</button>
      </div>
      <button class="icon-btn"><i data-lucide="bell"></i><span class="badge">7</span></button>
      <button class="icon-btn"><i data-lucide="moon"></i></button>
    </header>
  `;
}

function mountShell(activeKey){
  const sb = document.getElementById('sidebarMount');
  if(sb) sb.outerHTML = renderSidebar(activeKey);
  const tb = document.getElementById('topbarMount');
  if(tb) tb.outerHTML = renderTopbar(activeKey);
  if(window.lucide) lucide.createIcons();
  // Inject user info into sidebar footer
  try {
    if (window.SergakAuth && SergakAuth.isAuthenticated()) {
      const me = SergakAuth.getUser();
      if (me) {
        const av = document.querySelector('.sidebar-footer .user-avatar');
        const nm = document.querySelector('.sidebar-footer .user-name');
        const rl = document.querySelector('.sidebar-footer .user-role');
        const initials = (me.full_name || me.username || '?').split(/\s+/).map(p=>p[0]).slice(0,2).join('').toUpperCase();
        if (av) {
          if (me.avatar_url) {
            av.innerHTML = '<img src="'+me.avatar_url+'" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';
            av.style.padding = '0';
            av.style.overflow = 'hidden';
          } else {
            av.textContent = initials;
          }
        }
        if (nm) nm.textContent = me.full_name || me.username;
        const roleMap = {admin:'Administrator', manager:'Menejer', operator:'Operator', auditor:'Auditor'};
        if (rl) rl.textContent = roleMap[me.role] || me.role;
      }
    }
  } catch (e) {}
  // Refresh /me in background so avatar/name updates propagate across pages
  try {
    if (window.SergakAuth && SergakAuth.isAuthenticated()) {
      SergakAuth.fetch('/api/auth/me').then(r => r.ok ? r.json() : null).then(u => {
        if (!u) return;
        const existing = SergakAuth.getUser() || {};
        const merged = {...existing, ...u};
        SergakAuth.setSession(SergakAuth.getToken(), merged);
      }).catch(()=>{});
    }
  } catch(e){}
  // Start unread badge poller
  startUnreadPoller();
}

let _unreadPollerStarted = false;
function startUnreadPoller(){
  if (_unreadPollerStarted) { refreshUnreadBadge(); return; }
  _unreadPollerStarted = true;
  refreshUnreadBadge();
  setInterval(refreshUnreadBadge, 5000);
}
async function refreshUnreadBadge(){
  try {
    if (!window.SergakAuth || !SergakAuth.isAuthenticated()) return;
    const r = await SergakAuth.fetch('/api/chat/unread-count');
    if (!r.ok) return;
    const data = await r.json();
    const badge = document.getElementById('navUnreadBadge');
    if (!badge) return;
    if (data.total > 0) {
      badge.textContent = data.total > 99 ? '99+' : data.total;
      badge.style.display = '';
    } else {
      badge.style.display = 'none';
    }
  } catch (e) {}
}
window.refreshUnreadBadge = refreshUnreadBadge;

function showToast(type, title, msg){
  let container = document.getElementById('toasts');
  if(!container){
    container = document.createElement('div');
    container.id = 'toasts';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = 'toast ' + (type==='error'?'error':'');
  t.innerHTML = '<i data-lucide="'+(type==='error'?'alert-circle':'check-circle-2')+'"></i>'+
    '<div class="toast-content"><div class="toast-title">'+title+'</div><div class="toast-msg">'+msg+'</div></div>';
  container.appendChild(t);
  if(window.lucide) lucide.createIcons();
  setTimeout(function(){t.style.opacity='0'},3500);
  setTimeout(function(){t.remove()},4000);
}

function openModal(id){
  const m = document.getElementById(id);
  if(m){
    m.classList.add('show');
    if(typeof window['onOpen_'+id]==='function') window['onOpen_'+id]();
  }
}
function closeModal(id){
  const m = document.getElementById(id);
  if(m) m.classList.remove('show');
}

function updateClock(){
  const now = new Date();
  const t = now.toLocaleTimeString('en-GB',{hour12:false});
  const d = now.toLocaleDateString('uz-UZ',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
  const ce = document.getElementById('liveClock');
  const de = document.getElementById('liveDate');
  if(ce) ce.textContent = t;
  if(de) de.textContent = d.charAt(0).toUpperCase()+d.slice(1);
}

function deptByKey(k){ return SergakData.DEPARTMENTS.find(function(d){return d.key===k}); }

document.addEventListener('click', function(e){
  if(e.target.classList && e.target.classList.contains('modal-overlay')){
    e.target.classList.remove('show');
  }
});

window.addEventListener('DOMContentLoaded', function(){
  updateClock();
  setInterval(updateClock,1000);
});

window.SergakApp = {
  mountShell: mountShell,
  showToast: showToast,
  openModal: openModal,
  closeModal: closeModal,
  deptByKey: deptByKey
};
