(function(){
  const { el, initials } = window.JadeerUI;
  const { signOut, currentRole } = window.JadeerAuth;
  const { getUser } = window.JadeerAPI;

  const CAND_NAV = [
    ['#/dashboard','🏠','Dashboard','dashboard'],
    ['#/profile','👤','nav_profile','Profile'],
    ['#/skills','🎯','nav_skills','Skills'],
    ['#/certificates','🏆','nav_certs','Certificates'],
    ['#/recommendations','✨','nav_recs','Recommendations'],
    ['#/cvs','📄','nav_cvs','My CVs'],
    ['#/chats','💬','nav_chats','Chats'],
  ];
  const EMP_NAV = [
    ['#/employer','🏠','Dashboard','dashboard'],
    ['#/employer/profile','👤','nav_profile','Profile'],
    ['#/employer/search','🔍','nav_search','Search'],
    ['#/chats','💬','nav_chats','Chats'],
  ];

  function shell({ title='Jadeer', content }){
    const u = getUser() || {};
    const role = currentRole();
    const nav = role==='employer'?EMP_NAV:CAND_NAV;
    const cur = location.hash.split('?')[0] || '#/';
    const navHtml = nav.map(([h,ic,key,fb])=>{
      const active = cur===h || (cur.startsWith(h) && h!=='#/');
      return `<a class="nav-item ${active?'active':''}" href="${h}">
        <span class="ic">${ic}</span><span data-i18n="${key}">${fb}</span></a>`;
    }).join('');
    const node = el(`
      <div class="app">
        <div class="sidebar-backdrop" id="sb-backdrop"></div>
        <aside class="sidebar" id="sidebar">
          <div class="logo" data-i18n="brand">Jadeer</div>
          ${navHtml}
          <div class="sidebar-footer">
            <button class="nav-item" id="logout-btn" style="width:100%">
              <span class="ic">🚪</span><span data-i18n="logout">Log out</span>
            </button>
          </div>
        </aside>
        <div class="main">
          <header class="topbar">
            <div class="row">
              <button class="menu-toggle icon-btn" id="menu-tgl" aria-label="Menu">☰</button>
              <div class="title">${title}</div>
            </div>
            <div class="actions">
              <button class="lang-toggle" id="lang-toggle"><span>🌐</span><span id="lang-label"></span></button>
              <button class="icon-btn" aria-label="Notifications">🔔</button>
              <div class="avatar" style="width:36px;height:36px;font-size:13px" title="${u.full_name||u.email||''}">
                ${initials(u.full_name||u.email||'?')}
              </div>
            </div>
          </header>
          <div class="content" id="page-content"></div>
        </div>
      </div>
    `);
    const contentEl = node.querySelector('#page-content');
    if(typeof content==='string') contentEl.innerHTML = content;
    else if(content) contentEl.appendChild(content);

    // Wire controls
    node.querySelector('#logout-btn').onclick = ()=>signOut();
    const sb = node.querySelector('#sidebar'), bd = node.querySelector('#sb-backdrop');
    node.querySelector('#menu-tgl').onclick = ()=>{ sb.classList.toggle('open'); bd.classList.toggle('open'); };
    bd.onclick = ()=>{ sb.classList.remove('open'); bd.classList.remove('open'); };

    const lt = node.querySelector('#lang-toggle'), ll = node.querySelector('#lang-label');
    const setLbl = ()=> ll.textContent = window.JadeerI18n.getLang()==='en'?'عربي':'EN';
    setLbl();
    lt.onclick = ()=>window.JadeerI18n.toggleLang();

    return node;
  }

  window.JadeerShell = { render: shell };
})();
