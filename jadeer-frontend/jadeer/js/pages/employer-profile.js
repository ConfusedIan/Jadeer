(function(){
  const { el, toast, modal } = window.JadeerUI;
  const { api, getUser } = window.JadeerAPI;
  const { requireAuth, currentRole } = window.JadeerAuth;
  const { register, go } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const INDUSTRIES = [
    'Technology','Finance & Banking','Healthcare','Education','Retail & E-commerce',
    'Manufacturing','Construction','Media & Entertainment','Logistics & Supply Chain',
    'Government & Public Sector','Consulting','Telecommunications','Energy','Other',
  ];

  const CSS = `
    .epp-outer {
      display: flex;
      justify-content: center;
      padding: 32px 24px;
      width: 100%;
      box-sizing: border-box;
    }
    .epp-wrap { width: 100%; max-width: 740px; }

    /* Hero */
    .epp-hero {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 28px 32px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 14px;
    }
    .epp-hero-left { display: flex; align-items: flex-start; gap: 20px; flex: 1; min-width: 0; }

    /* Avatar — employer initials */
    .epp-avatar {
      width: 60px; height: 60px; border-radius: 50%; flex-shrink: 0;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; font-weight: 800; color: #fff; letter-spacing: -.5px;
    }

    .epp-identity { flex: 1; min-width: 0; }

    /* Employer name — primary */
    .epp-employer-name {
      font-size: 19px; font-weight: 700; color: var(--text);
      margin: 0 0 3px; line-height: 1.2;
    }

    /* Job title + company — secondary */
    .epp-role-line {
      font-size: 13px; color: var(--text2); margin: 0 0 14px;
    }
    .epp-role-line .company-name {
      color: var(--accent2); font-weight: 500;
    }

    /* Contact info rows */
    .epp-meta { display: flex; flex-direction: column; gap: 7px; }
    .epp-meta-row {
      display: flex; align-items: center; gap: 8px;
      font-size: 13px; color: var(--text2);
    }
    .epp-meta-row svg { flex-shrink: 0; color: var(--text3); }
    .epp-meta-link { color: var(--accent2); text-decoration: none; font-size: 13px; }
    .epp-meta-link:hover { text-decoration: underline; }

    /* Edit button */
    .epp-edit-btn {
      flex-shrink: 0; align-self: flex-start;
      background: none; border: 1px solid var(--border);
      border-radius: var(--radius-sm); color: var(--text2);
      font-size: 12px; padding: 8px 14px; cursor: pointer;
      transition: all .15s; font-family: var(--font);
      display: flex; align-items: center; gap: 6px; white-space: nowrap;
    }
    .epp-edit-btn:hover { border-color: var(--accent); color: var(--text); background: var(--accent-glow); }

    /* Cards */
    .epp-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 22px 28px; margin-bottom: 14px;
    }
    .epp-card-title {
      font-size: 10px; font-weight: 700; letter-spacing: .08em;
      text-transform: uppercase; color: var(--text3);
      margin: 0 0 14px; padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }
    .epp-about-text {
      font-size: 14px; line-height: 1.8; color: var(--text2);
      white-space: pre-line; margin: 0;
    }
    .epp-no-content { font-size: 13px; color: var(--text3); font-style: italic; margin: 0; }

    /* Company details grid */
    .epp-details-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px 24px; }
    .epp-detail-label {
      font-size: 10px; font-weight: 700; letter-spacing: .06em;
      text-transform: uppercase; color: var(--text3); margin: 0 0 4px;
    }
    .epp-detail-value { font-size: 13px; color: var(--text); font-weight: 500; margin: 0; }
    .epp-detail-value.empty { color: var(--text3); font-weight: 400; font-style: italic; }
    .epp-detail-link {
      font-size: 13px; color: var(--accent2); text-decoration: none; font-weight: 500;
      display: inline-flex; align-items: center; gap: 4px;
    }
    .epp-detail-link:hover { text-decoration: underline; }

    @media(max-width:640px){
      .epp-outer { padding: 16px; }
      .epp-hero { flex-direction: column; }
      .epp-details-grid { grid-template-columns: 1fr 1fr; }
    }
  `;

  const ico = {
    briefcase: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
    building:  `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    mail:      `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`,
    phone:     `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.21 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9a16 16 0 0 0 6.91 6.91l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>`,
    linkedin:  `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>`,
    external:  `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`,
    edit:      `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  };

  function injectStyles(){
    if(document.getElementById('epp-styles')) return;
    const s = document.createElement('style');
    s.id = 'epp-styles'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ── Employer Dashboard ─────────────────────────────────────────────────────
  register('/employer', async (_p, root) => {
    if(!requireAuth()) return;
    if(currentRole() !== 'employer'){ go('/dashboard'); return; }
    injectStyles();
    root.innerHTML = '';
    const content = el(`<div><div class="page-loader"><div class="spinner"></div></div></div>`);
    root.appendChild(shell({ title: 'Dashboard', content }));
    try {
      const me = await api('/profile/me').catch(() => ({}));
      const u  = getUser() || {};
      const employerName = me.full_name || u.full_name || 'Recruiter';
      const company = me.company_name || '';

      content.innerHTML = '';
      const outer = document.createElement('div');
      outer.className = 'epp-outer';
      outer.innerHTML = `
        <div class="epp-wrap">
          <div style="margin-bottom:24px">
            <h2 style="font-size:20px;font-weight:700;margin:0 0 3px">${employerName}</h2>
            <p style="font-size:13px;color:var(--text2);margin:0">
              ${[me.job_title, company].filter(Boolean).join(' · ') || 'Complete your profile to get started'}
            </p>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
            <a href="#/employer/search" style="text-decoration:none">
              <div class="epp-card" style="margin-bottom:0;cursor:pointer;transition:border-color .15s"
                onmouseenter="this.style.borderColor='var(--border2)'" onmouseleave="this.style.borderColor='var(--border)'">
                <div style="font-size:24px;margin-bottom:10px">🔍</div>
                <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px">Find Candidates</div>
                <div style="font-size:12px;color:var(--text3)">Search and rank by skills</div>
              </div>
            </a>
            <a href="#/employer/profile" style="text-decoration:none">
              <div class="epp-card" style="margin-bottom:0;cursor:pointer;transition:border-color .15s"
                onmouseenter="this.style.borderColor='var(--border2)'" onmouseleave="this.style.borderColor='var(--border)'">
                <div style="font-size:24px;margin-bottom:10px">👤</div>
                <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px">My Profile</div>
                <div style="font-size:12px;color:var(--text3)">${company || 'Manage your details'}</div>
              </div>
            </a>
            <a href="#/chats" style="text-decoration:none">
              <div class="epp-card" style="margin-bottom:0;cursor:pointer;transition:border-color .15s"
                onmouseenter="this.style.borderColor='var(--border2)'" onmouseleave="this.style.borderColor='var(--border)'">
                <div style="font-size:24px;margin-bottom:10px">💬</div>
                <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px">Messages</div>
                <div style="font-size:12px;color:var(--text3)">Coming soon</div>
              </div>
            </a>
          </div>
        </div>`;
      content.appendChild(outer);
    } catch(e){
      content.innerHTML = `<div class="empty"><p class="muted">${e.message||'Could not load'}</p></div>`;
    }
  });

  // ── Employer Profile ───────────────────────────────────────────────────────
  register('/employer/profile', async (_p, root) => {
    if(!requireAuth()) return;
    if(currentRole() !== 'employer'){ go('/dashboard'); return; }
    injectStyles();
    root.innerHTML = '';
    const content = el(`<div><div class="page-loader"><div class="spinner"></div></div></div>`);
    root.appendChild(shell({ title: 'My Profile', content }));

    async function loadPage(){
      content.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
      try {
        const me = await api('/profile/me', { noCache: true });
        const u  = getUser() || {};

        const employerName = me.full_name || u.full_name || 'Recruiter';
        const initials = employerName.split(' ').map(w=>w[0]||'').slice(0,2).join('').toUpperCase() || 'R';

        const roleParts = [
          me.job_title,
          me.company_name && `<span class="company-name">${me.company_name}</span>`,
        ].filter(Boolean).join(' · ');

        const metaRows = [
          me.job_title && me.company_name
            ? `<div class="epp-meta-row">${ico.briefcase} <span>${me.job_title} · <span style="color:var(--accent2)">${me.company_name}</span></span></div>`
            : me.company_name
              ? `<div class="epp-meta-row">${ico.building} <span style="color:var(--accent2)">${me.company_name}</span></div>`
              : me.job_title
                ? `<div class="epp-meta-row">${ico.briefcase} <span>${me.job_title}</span></div>`
                : '',
          u.email       ? `<div class="epp-meta-row">${ico.mail} <a class="epp-meta-link" href="mailto:${u.email}">${u.email}</a></div>` : '',
          me.phone      ? `<div class="epp-meta-row">${ico.phone} <span>${me.phone}</span></div>` : '',
          me.linkedin_url ? `<div class="epp-meta-row">${ico.linkedin} <a class="epp-meta-link" href="${me.linkedin_url}" target="_blank" rel="noopener">${me.linkedin_url.replace(/https?:\/\/(www\.)?linkedin\.com\/in\//,'').replace(/\/$/,'')}</a></div>` : '',
        ].filter(Boolean).join('');

        content.innerHTML = '';
        const outer = document.createElement('div');
        outer.className = 'epp-outer';
        outer.innerHTML = `
          <div class="epp-wrap">

            <!-- Hero: employer is primary -->
            <div class="epp-hero">
              <div class="epp-hero-left">
                <div class="epp-avatar">${initials}</div>
                <div class="epp-identity">
                  <p class="epp-employer-name">${employerName}</p>
                  ${roleParts ? `<p class="epp-role-line">${roleParts}</p>` : ''}
                  ${metaRows ? `<div class="epp-meta">${metaRows}</div>` : `<p style="font-size:13px;color:var(--text3);margin:0">No contact details yet — edit your profile to add them.</p>`}
                </div>
              </div>
              <button class="epp-edit-btn" id="edit-profile-btn">
                ${ico.edit} Edit Profile
              </button>
            </div>

            <!-- About -->
            <div class="epp-card">
              <p class="epp-card-title">About</p>
              ${me.bio
                ? `<p class="epp-about-text">${me.bio}</p>`
                : `<p class="epp-no-content">No bio added yet. Edit your profile to introduce yourself.</p>`}
            </div>

            <!-- Company details -->
            <div class="epp-card">
              <p class="epp-card-title">Company Information</p>
              <div class="epp-details-grid">
                <div>
                  <p class="epp-detail-label">Company</p>
                  <p class="epp-detail-value ${!me.company_name?'empty':''}">${me.company_name||'Not specified'}</p>
                </div>
                <div>
                  <p class="epp-detail-label">Industry</p>
                  <p class="epp-detail-value ${!me.industry?'empty':''}">${me.industry||'Not specified'}</p>
                </div>
                <div>
                  <p class="epp-detail-label">Location</p>
                  <p class="epp-detail-value ${!me.location?'empty':''}">${me.location||'Not specified'}</p>
                </div>
                <div>
                  <p class="epp-detail-label">Website</p>
                  ${me.website_url
                    ? `<a href="${me.website_url}" target="_blank" rel="noopener" class="epp-detail-link">${ico.external} ${me.website_url.replace('https://','').replace(/\/$/,'')}</a>`
                    : `<p class="epp-detail-value empty">Not specified</p>`}
                </div>
              </div>
            </div>

          </div>`;

        content.appendChild(outer);
        outer.querySelector('#edit-profile-btn').addEventListener('click', () => openEditModal(me, u, loadPage));
      } catch(e){
        content.innerHTML = `<div class="empty"><p class="muted">${e.message||'Could not load profile'}</p></div>`;
      }
    }
    loadPage();
  });

  // ── Edit Modal ─────────────────────────────────────────────────────────────
  function openEditModal(me, u, onSaved){
    const opts = (arr, sel) => arr.map(v => `<option value="${v}" ${v===sel?'selected':''}>${v}</option>`).join('');
    const body = el(`
      <div>
        <!-- Employer identity -->
        <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text3);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)">Your Details</div>
        <div class="grid grid-2">
          <div class="field">
            <label>Full Name *</label>
            <input class="input" id="ep-fullname" value="${me.full_name||''}">
          </div>
          <div class="field">
            <label>Job Title</label>
            <input class="input" id="ep-jobtitle" placeholder="e.g. HR Manager" value="${me.job_title||''}">
          </div>
        </div>
        <div class="grid grid-2">
          <div class="field">
            <label>Phone Number</label>
            <input class="input" id="ep-phone" placeholder="e.g. +966 5X XXX XXXX" value="${me.phone||''}">
          </div>
          <div class="field">
            <label>Email</label>
            <input class="input" id="ep-email-display" value="${u.email||''}" disabled>
            <div class="hint" style="font-size:11px">🔒 Email cannot be changed here.</div>
          </div>
        </div>
        <div class="field">
          <label>LinkedIn Profile</label>
          <input class="input" id="ep-linkedin" placeholder="https://linkedin.com/in/yourname" value="${me.linkedin_url||''}">
        </div>
        <div class="field">
          <label>About / Bio</label>
          <textarea class="textarea" id="ep-bio" rows="3" placeholder="Introduce yourself to candidates…">${me.bio||''}</textarea>
        </div>

        <!-- Company info -->
        <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--text3);margin:16px 0 12px;padding-top:16px;border-top:1px solid var(--border)">Company Information</div>
        <div class="grid grid-2">
          <div class="field">
            <label>Company Name</label>
            <input class="input" id="ep-company" placeholder="e.g. Acme Corp" value="${me.company_name||''}">
          </div>
          <div class="field">
            <label>Industry</label>
            <select class="select" id="ep-industry">
              <option value="">Select industry</option>
              ${opts(INDUSTRIES, me.industry)}
            </select>
          </div>
        </div>
        <div class="grid grid-2">
          <div class="field">
            <label>Location</label>
            <input class="input" id="ep-location" value="${me.location||''}">
          </div>
        </div>
        <div class="field">
          <label>Website</label>
          <input class="input" type="url" id="ep-website" placeholder="https://" value="${me.website_url||''}">
        </div>
      </div>
    `);

    const foot = document.createElement('div');
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.textContent = 'Cancel';
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.textContent = 'Save Changes';
    foot.appendChild(cancelBtn);
    foot.appendChild(saveBtn);

    const m = modal({ title: 'Edit Profile', body, footer: foot });
    cancelBtn.addEventListener('click', () => m.close());

    saveBtn.addEventListener('click', async () => {
      const fullName = body.querySelector('#ep-fullname').value.trim();
      const jobTitle = body.querySelector('#ep-jobtitle').value.trim();
      const phone    = body.querySelector('#ep-phone').value.trim();
      const linkedin = body.querySelector('#ep-linkedin').value.trim();
      const bio      = body.querySelector('#ep-bio').value.trim();
      const company  = body.querySelector('#ep-company').value.trim();
      const industry = body.querySelector('#ep-industry').value;
      const location = body.querySelector('#ep-location').value.trim();
      const website  = body.querySelector('#ep-website').value.trim();

      if(!fullName){ toast('Full name is required.','error'); return; }
      if(website  && !website.startsWith('https://')){ toast('Website must start with https://','error'); return; }
      if(linkedin && !linkedin.startsWith('https://')){ toast('LinkedIn URL must start with https://','error'); return; }

      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner"></span>';

      try {
        await api('/profile/me', {
          method: 'PATCH',
          body: {
            full_name:    fullName  || null,
            job_title:    jobTitle  || null,
            phone:        phone     || null,
            linkedin_url: linkedin  || null,
            bio:          bio       || null,
            company_name: company   || null,
            industry:     industry  || null,
            website_url:  website   || null,
            location:     location  || null,
          },
        });
        const u2 = window.JadeerAPI.getUser() || {};
        u2.full_name = fullName || u2.full_name;
        window.JadeerAPI.setUser(u2);
        toast('Profile saved','success');
        m.close();
        setTimeout(onSaved, 400);
      } catch(e){
        toast(e.message||'Could not save','error');
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Changes';
      }
    });
  }

})();
