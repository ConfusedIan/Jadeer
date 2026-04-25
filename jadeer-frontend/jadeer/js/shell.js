(function(){
  const { el, initials } = window.JadeerUI;
  const { signOut, currentRole } = window.JadeerAuth;
  const { getUser } = window.JadeerAPI;

  function getTheme(){ return document.documentElement.dataset.theme || 'dark'; }
  function setTheme(t){
    document.documentElement.dataset.theme = t;
    localStorage.setItem('jadeer-theme', t);
  }

  /*
   * Navigation definitions — [href, i18nKey | null, label]
   * A null i18nKey means no data-i18n is set; the label text is used as-is
   * (prevents the i18n system from replacing it with the raw key string).
   */
  const CAND_NAV = [
    ['#/dashboard',       null,          'Home'],
    ['#/profile',         'nav_profile', 'Profile'],
    ['#/skills',          'nav_skills',  'Skills'],
    ['#/certificates',    'nav_certs',   'Certificates'],
    ['#/recommendations', 'nav_recs',    'Recommendations'],
    ['#/cvs',             'nav_cvs',     'My CVs'],
    ['#/chats',           'nav_chats',   'Chats'],
  ];
  const EMP_NAV = [
    ['#/employer',         null,          'Home'],
    ['#/employer/profile', 'nav_profile', 'Profile'],
    ['#/employer/search',  'nav_search',  'Search'],
    ['#/chats',            'nav_chats',   'Chats'],
  ];

  /* Jadeer logo — uses the official SVG file */
  const LOGO = `<img src="icons/Jadeer_Logo.png" alt="Jadeer" class="brand-logo">`;

  /*
   * shell({ content, heroContent })
   *
   * heroContent — optional DOM node / HTML string placed in .hero-area,
   *   which is outside the padded .content div → naturally full-width.
   * content     — DOM node / HTML string inside .content (padded).
   */
  function shell({ title = 'Jadeer', content, heroContent }){
    const u        = getUser() || {};
    const role     = currentRole();
    const nav      = role === 'employer' ? EMP_NAV : CAND_NAV;
    const cur      = location.hash.split('?')[0] || '#/';
    const homeHref = role === 'employer' ? '#/employer' : '#/dashboard';
    const name     = u.full_name || u.email || '';

    /* Build nav links, skipping data-i18n when key is null */
    const buildLinks = (itemClass) =>
      nav.map(([href, key, label]) => {
        const active  = cur === href || (cur.startsWith(href) && href !== '#/');
        const i18nAttr = key ? ` data-i18n="${key}"` : '';
        return `<a class="${itemClass}${active ? ' active' : ''}" href="${href}"${i18nAttr}>${label}</a>`;
      }).join('');

    const node = el(`
      <div class="app">

        <!-- Mobile backdrop -->
        <div class="sidebar-backdrop" id="sb-backdrop"></div>

        <!-- Mobile slide-in sidebar -->
        <aside class="sidebar" id="sidebar">
          <div class="sidebar-header">
            <a class="navbar-brand" href="${homeHref}">${LOGO}</a>
            <button class="sidebar-close" id="sb-close" aria-label="Close menu">&#x2715;</button>
          </div>
          <nav class="sidebar-nav">
            ${buildLinks('sidebar-nav-item')}
          </nav>
          <div class="sidebar-footer">
            <button class="sidebar-nav-item danger" id="logout-btn">
              <span data-i18n="logout">Log out</span>
            </button>
          </div>
        </aside>

        <!-- Main column -->
        <div class="main">

          <!-- Sticky top navbar -->
          <header class="navbar">
            <button class="hamburger" id="menu-tgl" aria-label="Open menu">&#9776;</button>
            <a class="navbar-brand" href="${homeHref}">${LOGO}</a>

            <nav class="navbar-nav">
              ${buildLinks('nav-link')}
            </nav>

            <div class="navbar-actions">

              <!-- Theme icon toggle: PNG switches based on active mode -->
              <button class="theme-icon-btn" id="theme-tgl" aria-label="Toggle theme">
                <img id="theme-icon" class="theme-icon-img" src="" alt="Toggle theme">
              </button>

              <!-- Language toggle with icon -->
              <button class="lang-toggle" id="lang-toggle">
                <img id="lang-icon" src="icons/language.png" alt="" class="lang-icon" aria-hidden="true">
                <span id="lang-label"></span>
              </button>

              <!-- Avatar with dropdown -->
              <div class="avatar-menu" id="avatar-menu">
                <button class="avatar" id="avatar-btn" aria-haspopup="true" aria-expanded="false" title="${name}">
                  ${initials(name || '?')}
                </button>
                <div class="avatar-dropdown" id="avatar-dropdown" role="menu">
                  <div class="avatar-dropdown-header">
                    <div class="avatar" style="width:34px;height:34px;font-size:12px;flex-shrink:0">
                      ${initials(name || '?')}
                    </div>
                    <div style="min-width:0">
                      <div class="avatar-user-name">${u.full_name || ''}</div>
                      <div class="avatar-user-email">${u.email || ''}</div>
                    </div>
                  </div>
                  <div class="avatar-dropdown-divider"></div>
                  <a class="avatar-dropdown-item" href="${role === 'employer' ? '#/employer/profile' : '#/profile'}" data-i18n="nav_profile">Profile</a>
                  <div class="avatar-dropdown-divider"></div>
                  <button class="avatar-dropdown-item danger" id="dropdown-logout">
                    <span data-i18n="logout">Log out</span>
                  </button>
                </div>
              </div>

            </div>
          </header>

          <!-- Full-width hero slot (only rendered when heroContent provided) -->
          ${heroContent ? '<div class="hero-area" id="hero-area"></div>' : ''}

          <!-- Padded page content -->
          <div class="content" id="page-content"></div>

        </div>
      </div>
    `);

    /* ── Populate slots ── */
    if(heroContent){
      const heroEl = node.querySelector('#hero-area');
      if(typeof heroContent === 'string') heroEl.innerHTML = heroContent;
      else heroEl.appendChild(heroContent);
    }
    const contentEl = node.querySelector('#page-content');
    if(typeof content === 'string') contentEl.innerHTML = content;
    else if(content) contentEl.appendChild(content);

    /* ── Logout (sidebar + dropdown) ── */
    node.querySelector('#logout-btn').onclick    = () => signOut();
    node.querySelector('#dropdown-logout').onclick = () => signOut();

    /* ── Mobile sidebar ── */
    const sb = node.querySelector('#sidebar');
    const bd = node.querySelector('#sb-backdrop');
    const closeSidebar = () => { sb.classList.remove('open'); bd.classList.remove('open'); };
    node.querySelector('#menu-tgl').onclick = () => { sb.classList.toggle('open'); bd.classList.toggle('open'); };
    node.querySelector('#sb-close').onclick = closeSidebar;
    bd.onclick = closeSidebar;
    sb.querySelectorAll('.sidebar-nav-item:not(#logout-btn)').forEach(a => {
      a.addEventListener('click', closeSidebar);
    });

    /* ── Language toggle ── */
    const ll = node.querySelector('#lang-label');
    const syncLang = () => { ll.textContent = window.JadeerI18n.getLang() === 'en' ? 'ع' : 'EN'; };
    syncLang();
    node.querySelector('#lang-toggle').onclick = () => { window.JadeerI18n.toggleLang(); syncLang(); };

    /* ── Theme toggle — PNG reflects current mode ──
         Dark mode  → show Light_Mode.png (sun, "click to go light")
         Light mode → show Dark_Mode.png  (moon, "click to go dark") */
    const themeIcon = node.querySelector('#theme-icon');
    const langIcon  = node.querySelector('#lang-icon');
    const logoImgs  = node.querySelectorAll('.brand-logo');
    const syncTheme = () => {
      const dark = getTheme() === 'dark';
      themeIcon.src = dark ? 'icons/Light_Mode.png' : 'icons/Dark_Mode.png';
      themeIcon.alt = dark ? 'Switch to light mode' : 'Switch to dark mode';
      langIcon.src  = dark ? 'icons/Language_Light.png' : 'icons/Language.png';
      logoImgs.forEach(img => {
        img.src = dark ? 'icons/Jadeer_Logo_light.png' : 'icons/Jadeer_Logo.png';
      });
    };
    syncTheme();
    node.querySelector('#theme-tgl').onclick = () => {
      setTheme(getTheme() === 'dark' ? 'light' : 'dark');
      syncTheme();
    };

    /* ── Avatar dropdown ── */
    const avatarBtn      = node.querySelector('#avatar-btn');
    const avatarDropdown = node.querySelector('#avatar-dropdown');
    const closeDropdown  = () => {
      avatarDropdown.classList.remove('open');
      avatarBtn.setAttribute('aria-expanded', 'false');
    };
    avatarBtn.onclick = (e) => {
      e.stopPropagation();
      const willOpen = !avatarDropdown.classList.contains('open');
      closeDropdown();
      if(willOpen){
        avatarDropdown.classList.add('open');
        avatarBtn.setAttribute('aria-expanded', 'true');
        /* Close on next outside click */
        const outsideClick = () => { closeDropdown(); document.removeEventListener('click', outsideClick); };
        document.addEventListener('click', outsideClick);
      }
    };
    /* Prevent clicks inside dropdown from bubbling to the outside-click handler */
    avatarDropdown.addEventListener('click', e => e.stopPropagation());

    return node;
  }

  window.JadeerShell = { render: shell };
})();
