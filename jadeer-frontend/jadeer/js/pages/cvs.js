(function(){
  const { el, toast, modal, confirmDialog } = window.JadeerUI;
  const { api, getToken } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;
  const CFG = window.JADEER_CONFIG;

  // ── Utilities ──────────────────────────────────────────────────────────────

  const toArr = (v) => Array.isArray(v) ? v
    : (v && (v.items || v.data || v.history || v.cvs || v.results ||
             v.experiences || v.education || v.certificates || v.skills)) || [];

  const fmtDate = (d) => d ? new Date(d).toLocaleString(undefined, {
    year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit',
  }) : '';
  const fmtShort = (d) => d ? new Date(d).toLocaleDateString(undefined, {
    year:'numeric', month:'short',
  }) : '';

  // ── CV Builder Styles ──────────────────────────────────────────────────────

  const CSS = `
    .cvb-name-row { margin-bottom:16px; }

    .cvb-identity {
      display:flex; align-items:center; gap:16px;
      padding:16px 18px;
      background:linear-gradient(135deg,rgba(124,92,252,.08),rgba(192,132,252,.04));
      border:1px solid rgba(124,92,252,.22);
      border-radius:var(--radius); margin-bottom:16px;
    }
    .cvb-identity-info { flex:1; min-width:0; }
    .cvb-identity-name { font-size:17px; font-weight:700; margin:0 0 5px; color:var(--text); }
    .cvb-identity-meta { font-size:12px; color:var(--text2); display:flex; flex-wrap:wrap; gap:10px; margin-bottom:5px; }
    .cvb-identity-lock { font-size:11px; color:var(--text3); display:flex; align-items:center; gap:4px; }

    .cvb-sections { display:flex; flex-direction:column; gap:8px; margin-bottom:16px; }

    .cvb-section {
      border:1px solid var(--border); border-radius:var(--radius);
      overflow:hidden; background:var(--surface);
      transition:opacity .15s, box-shadow .15s, border-color .15s;
    }
    .cvb-section.dragging { opacity:.4; box-shadow:var(--shadow-lg); }
    .cvb-section.drag-over { border-color:var(--accent); box-shadow:0 0 0 2px var(--accent-glow); }

    .cvb-section-header {
      display:flex; align-items:center; gap:10px;
      padding:11px 14px; background:var(--surface2);
      border-bottom:1px solid var(--border);
      cursor:grab; user-select:none; transition:background .12s;
    }
    .cvb-section-header:hover { background:var(--surface3); }
    .cvb-section-header:active { cursor:grabbing; }

    .cvb-drag-handle {
      color:var(--text3); font-size:16px; flex-shrink:0;
      letter-spacing:-2px; line-height:1; opacity:.6;
    }
    .cvb-section-toggle {
      display:flex; align-items:center; gap:8px;
      cursor:pointer; font-weight:600; font-size:13px; flex:1; color:var(--text);
    }
    .cvb-section-toggle input[type="checkbox"] {
      width:15px; height:15px; accent-color:var(--accent); flex-shrink:0;
    }

    .cvb-section-body { padding:12px 14px; display:flex; flex-direction:column; gap:6px; }
    .cvb-section.section-off .cvb-section-body { opacity:.4; pointer-events:none; }
    .cvb-section.section-off .cvb-section-header { opacity:.65; }

    .cvb-item {
      display:flex; align-items:flex-start; gap:10px;
      padding:8px 10px; border-radius:var(--radius-sm);
      border:1px solid var(--border); background:var(--surface2);
      cursor:pointer; transition:border-color .12s, background .12s;
    }
    .cvb-item:hover { border-color:var(--border2); }
    .cvb-item.item-on {
      border-color:rgba(124,92,252,.3);
      background:rgba(124,92,252,.05);
    }
    .cvb-item input[type="checkbox"] {
      width:15px; height:15px; accent-color:var(--accent);
      margin-top:2px; flex-shrink:0;
    }
    .cvb-item-label { flex:1; min-width:0; }
    .cvb-item-title {
      font-weight:600; font-size:13px; color:var(--text);
      display:flex; align-items:center; justify-content:space-between; gap:8px;
    }
    .cvb-item-sub { font-size:12px; color:var(--text2); margin-top:2px; }
    .cvb-item-badge {
      font-size:11px; color:var(--accent2); font-family:var(--mono);
      font-weight:700; flex-shrink:0;
    }
    .cvb-item-verified {
      font-size:10px; color:var(--success); font-weight:600;
      background:var(--success-bg); padding:1px 6px; border-radius:20px; flex-shrink:0;
    }

    .cvb-bio-area { resize:vertical; min-height:72px; }
    .cvb-desc-wrap { margin-top:6px; width:100%; }
    .cvb-item-desc { width:100%; box-sizing:border-box; font-size:12px !important; resize:vertical; min-height:48px; }
    .cvb-footer-row {
      display:flex; align-items:center; gap:10px;
      padding-top:12px; border-top:1px solid var(--border);
    }
    .cvb-footer-row label {
      display:flex; align-items:center; gap:8px;
      font-size:13px; cursor:pointer; color:var(--text);
    }
    .cvb-footer-row label input { accent-color:var(--accent); }

    .cvb-drag-hint {
      font-size:11px; color:var(--text3); text-align:center;
      padding:4px 0; letter-spacing:.02em;
    }

    @media(max-width:520px){
      .cvb-identity { flex-direction:column; gap:12px; }
    }
  `;

  function injectStyles() {
    if (document.getElementById('cvb-styles')) return;
    const s = document.createElement('style');
    s.id = 'cvb-styles'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ── Profile data ───────────────────────────────────────────────────────────

  async function fetchProfileData() {
    const norm = (v) => Array.isArray(v) ? v
      : (v && (v.items || v.data || v.experiences || v.education ||
               v.certificates || v.skills || v.results)) || [];

    const [me, expsRaw, edusRaw, certsRaw, skillsRaw, catalogRaw] = await Promise.all([
      api('/profile/me').catch(() => ({})),
      api('/profile/me/experiences').catch(() => []),
      api('/profile/me/education').catch(() => []),
      api('/profile/me/certificates').catch(() => []),
      api('/profile/me/skills').catch(() => []),
      api('/profile/skills-catalog').catch(() => ({ items: [] })),
    ]);

    const catalogMap = new Map();
    norm(catalogRaw).forEach(r => {
      const id = r.id ?? r.skill_id;
      const name = (r.name || r.skill_name || '').trim();
      if (id != null && name) catalogMap.set(id, name);
    });

    return {
      me: me || {},
      user: window.JadeerAPI.getUser() || {},
      exps:   norm(expsRaw),
      edus:   norm(edusRaw),
      certs:  norm(certsRaw),
      skills: norm(skillsRaw),
      catalogMap,
    };
  }

  // ── Preselect matching ─────────────────────────────────────────────────────

  function shouldCheck(type, item, pre, catalogMap) {
    if (!pre) return true;
    const lc = (s) => (s || '').toLowerCase().trim();
    if (type === 'skill') {
      const name = item.custom_skill_name
        || catalogMap.get(item.skill_id)
        || item.name || item.skill_name || '';
      return (pre.skills || []).some(s => lc(s) === lc(name));
    }
    if (type === 'experience') {
      return (pre.experiences || []).some(e =>
        (lc(e.job_title) && lc(e.job_title) === lc(item.job_title)) ||
        (lc(e.company)   && lc(e.company)   === lc(item.company))
      );
    }
    if (type === 'certificate') {
      return (pre.certs || []).some(c => lc(c) === lc(item.certificate_name));
    }
    return true; // education always checked
  }

  // ── Item row builders ──────────────────────────────────────────────────────

  function makeItemRow(dataId, checked, titleHtml, subHtml) {
    const label = document.createElement('label');
    label.className = `cvb-item ${checked ? 'item-on' : ''}`;
    if (dataId) label.dataset.id = dataId;
    label.innerHTML = `
      <input type="checkbox" ${checked ? 'checked' : ''}>
      <div class="cvb-item-label">
        <div class="cvb-item-title">${titleHtml}</div>
        ${subHtml ? `<div class="cvb-item-sub">${subHtml}</div>` : ''}
      </div>
    `;
    const chk = label.querySelector('input');
    chk.addEventListener('change', () => label.classList.toggle('item-on', chk.checked));
    return label;
  }

  function expRow(x, checked) {
    const id = x.exp_id || '';
    const dates = `${fmtShort(x.start_date)||'—'} – ${x.end_date ? fmtShort(x.end_date) : 'Present'}`;
    const label = makeItemRow(
      String(id),
      checked,
      `<span>${x.job_title||'—'}</span>`,
      `${x.company||''} · ${dates}`
    );

    // Inline description editor — visible when item is checked
    const descWrap = document.createElement('div');
    descWrap.className = 'cvb-desc-wrap';
    descWrap.style.display = checked ? '' : 'none';
    const ta = document.createElement('textarea');
    ta.className = 'textarea cvb-item-desc';
    ta.rows = 2;
    ta.placeholder = 'Override description for this CV…';
    ta.value = x.description || '';
    // Prevent textarea clicks from bubbling to the label and toggling the checkbox
    ta.addEventListener('click', e => e.stopPropagation());
    descWrap.appendChild(ta);
    label.querySelector('.cvb-item-label').appendChild(descWrap);

    const chk = label.querySelector('input[type="checkbox"]');
    chk.addEventListener('change', () => { descWrap.style.display = chk.checked ? '' : 'none'; });

    return label;
  }

  function eduRow(x, checked) {
    const field = x.field_of_study ? ` in ${x.field_of_study}` : '';
    const dates = `${fmtShort(x.start_date)||'—'} – ${x.end_date ? fmtShort(x.end_date) : 'Present'}`;
    return makeItemRow(
      x.edu_id || '',
      checked,
      `<span>${(x.degree||'—') + field}</span>`,
      `${x.institution||''} · ${dates}`
    );
  }

  function certRow(x, checked) {
    const verified = x.supported_cert_id || x.verified
      || /^verif/i.test(x.status || x.verification_status || '');
    const issuer = x.issuer_name || x.issuer || '';
    return makeItemRow(
      String(x.certificate_id || x.cert_id || x.id || ''),
      checked,
      `<span>${x.certificate_name||'—'}</span>${verified ? '<span class="cvb-item-verified">✓ Verified</span>' : ''}`,
      issuer
    );
  }

  function skillRow(x, checked, catalogMap) {
    const name = x.custom_skill_name
      || catalogMap.get(x.skill_id)
      || x.name || x.skill_name || 'Skill';
    const hasSc = x.score != null && x.score > 0;
    const pct = hasSc ? `<span class="cvb-item-badge">${Math.round(x.score)}%</span>` : '';
    return makeItemRow(
      x.user_skill_id || x.id || '',
      checked,
      `<span>${name}</span>${pct}`,
      null
    );
  }

  // ── Section factory ────────────────────────────────────────────────────────

  function makeSection(sectionKey, icon, title, items, buildRow) {
    const wrap = document.createElement('div');
    wrap.className = 'cvb-section';
    wrap.dataset.section = sectionKey;
    wrap.draggable = true;
    wrap.innerHTML = `
      <div class="cvb-section-header">
        <span class="cvb-drag-handle" aria-hidden="true">⠿⠿</span>
        <label class="cvb-section-toggle" onclick="event.stopPropagation()">
          <input type="checkbox" class="section-chk" checked>
          <span>${icon} ${title}</span>
        </label>
      </div>
      <div class="cvb-section-body"></div>
    `;
    const body = wrap.querySelector('.cvb-section-body');

    if (!items.length) {
      body.innerHTML = `<p class="muted" style="font-size:12px;padding:2px 0">No ${title.toLowerCase()} in your profile yet.</p>`;
    } else {
      items.forEach(item => body.appendChild(buildRow(item)));
    }

    // Toggle disabled state
    const chk = wrap.querySelector('.section-chk');
    const applyOff = () => wrap.classList.toggle('section-off', !chk.checked);
    applyOff();
    chk.addEventListener('change', applyOff);

    return wrap;
  }

  function makeBioSection() {
    const wrap = document.createElement('div');
    wrap.className = 'cvb-section';
    wrap.dataset.section = 'bio';
    wrap.draggable = true;
    wrap.innerHTML = `
      <div class="cvb-section-header">
        <span class="cvb-drag-handle" aria-hidden="true">⠿⠿</span>
        <label class="cvb-section-toggle" onclick="event.stopPropagation()">
          <input type="checkbox" class="section-chk" checked>
          <span>Bio</span>
        </label>
      </div>
      <div class="cvb-section-body">
        <textarea class="textarea cvb-bio-area" id="cvb-bio" rows="3"
          placeholder="Write a custom bio for this CV (leave empty to use your profile bio)…"></textarea>
      </div>
    `;
    const chk = wrap.querySelector('.section-chk');
    const applyOff = () => wrap.classList.toggle('section-off', !chk.checked);
    applyOff();
    chk.addEventListener('change', applyOff);
    return wrap;
  }

  // ── Drag-and-drop ──────────────────────────────────────────────────────────

  function initDragDrop(container) {
    let dragSrc = null;

    container.querySelectorAll('.cvb-section').forEach(sec => {
      sec.addEventListener('dragstart', e => {
        // Don't initiate drag from inside the body (inputs, textareas, checkboxes)
        if (e.target.closest('.cvb-section-body') || e.target.closest('.cvb-section-toggle')) {
          e.preventDefault(); return;
        }
        dragSrc = sec;
        e.dataTransfer.effectAllowed = 'move';
        // Defer class to avoid Chrome flicker
        requestAnimationFrame(() => sec.classList.add('dragging'));
      });
      sec.addEventListener('dragend', () => {
        sec.classList.remove('dragging');
        container.querySelectorAll('.cvb-section').forEach(s => s.classList.remove('drag-over'));
        dragSrc = null;
      });
      sec.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        if (sec !== dragSrc) sec.classList.add('drag-over');
      });
      sec.addEventListener('dragleave', e => {
        if (!sec.contains(e.relatedTarget)) sec.classList.remove('drag-over');
      });
      sec.addEventListener('drop', e => {
        e.preventDefault();
        sec.classList.remove('drag-over');
        if (!dragSrc || sec === dragSrc) return;
        const all = [...container.querySelectorAll('.cvb-section')];
        const si = all.indexOf(dragSrc), ti = all.indexOf(sec);
        container.insertBefore(dragSrc, si < ti ? sec.nextSibling : sec);
      });
    });
  }

  // ── Collect generate payload ───────────────────────────────────────────────

  function collectPayload(wrap) {
    const sectionOrder = [];
    const incl = {};
    const ids = { experience:[], education:[], certificates:[], skills:[] };
    const expDescOverrides = {};

    wrap.querySelectorAll('.cvb-section').forEach(sec => {
      const key = sec.dataset.section;
      sectionOrder.push(key);
      const chk = sec.querySelector('.section-chk');
      incl[key] = chk ? chk.checked : true;

      if (ids[key] !== undefined) {
        sec.querySelectorAll('.cvb-item input[type="checkbox"]').forEach(cb => {
          if (cb.checked) {
            const row = cb.closest('.cvb-item');
            if (row?.dataset.id) {
              ids[key].push(row.dataset.id);
              if (key === 'experience') {
                const ta = row.querySelector('.cvb-item-desc');
                if (ta) {
                  const v = ta.value.trim();
                  if (v) expDescOverrides[row.dataset.id] = v;
                }
              }
            }
          }
        });
      }
    });

    const bio    = wrap.querySelector('#cvb-bio')?.value.trim() || '';
    const cvName = wrap.querySelector('#cvb-cv-name')?.value.trim() || '';
    const save   = wrap.querySelector('#cvb-save-hist')?.checked ?? true;

    const payload = {
      save_to_history:         save,
      include_experience:      !!incl.experience,
      include_education:       !!incl.education,
      include_certificates:    !!incl.certificates,
      include_skills:          !!incl.skills,
      include_scores:          true,
      include_verified_badges: true,
      section_order:           sectionOrder,
    };
    if (bio)    payload.custom_bio = bio;
    if (cvName) payload.cv_name    = cvName;
    if (Object.keys(expDescOverrides).length) payload.experience_desc_overrides = expDescOverrides;

    // Always send selected ID arrays for included sections so the backend
    // filters correctly — an empty array means "user deselected all items".
    if (incl.experience)   payload.selected_experience_ids   = ids.experience;
    if (incl.education)    payload.selected_education_ids    = ids.education;
    if (incl.certificates) payload.selected_certificate_ids  = ids.certificates;
    if (incl.skills)       payload.selected_skill_ids        = ids.skills;

    return payload;
  }

  // ── Main open function ─────────────────────────────────────────────────────

  async function openCustomizeModal({ preselect = null, onDone } = {}) {
    injectStyles();

    // Immediately show a loading modal so the user sees instant feedback
    const loadBody = el(`
      <div style="padding:52px 24px;text-align:center">
        <div class="spinner" style="width:24px;height:24px;border-width:3px;margin:0 auto 14px"></div>
        <p class="muted" style="font-size:13px">Loading your profile…</p>
      </div>
    `);
    const loadFoot = el(`
      <div style="display:flex;justify-content:flex-end">
        <button class="btn btn-ghost" id="cvb-cancel-early">Cancel</button>
      </div>
    `);
    const m = modal({ title:'Customize CV', body:loadBody, footer:loadFoot, size:'lg' });
    loadFoot.querySelector('#cvb-cancel-early').onclick = () => m.close();

    let profile;
    try {
      profile = await fetchProfileData();
    } catch(e) {
      m.close();
      toast('Could not load profile data', 'error');
      return;
    }

    const { me, user, exps, edus, certs, skills, catalogMap } = profile;
    const fullName = me.full_name || user.full_name || user.email || 'You';

    // ── Identity block (read-only) ──────────────────────────────────────────
    const identityEl = document.createElement('div');
    identityEl.className = 'cvb-identity';
    const metaHtml = [
      user.email    && `<span>✉️ ${user.email}</span>`,
      me.phone      && `<span>📞 ${me.phone}</span>`,
      me.location   && `<span>📍 ${me.location}</span>`,
    ].filter(Boolean).join('');
    identityEl.innerHTML = `
      <div class="avatar avatar-lg">${window.JadeerUI.initials(fullName)}</div>
      <div class="cvb-identity-info">
        <p class="cvb-identity-name">${fullName}</p>
        <div class="cvb-identity-meta">${metaHtml || '<span style="color:var(--text3)">No contact info</span>'}</div>
        <div class="cvb-identity-lock">🔒 Pulled from your profile — edit in Profile Settings</div>
      </div>
    `;

    // ── Sections ────────────────────────────────────────────────────────────
    const sectionsEl = document.createElement('div');
    sectionsEl.className = 'cvb-sections';

    sectionsEl.appendChild(makeBioSection());
    sectionsEl.appendChild(makeSection('experience',   '💼', 'Work Experience', exps,
      x => expRow(x,  shouldCheck('experience',   x, preselect, catalogMap))));
    sectionsEl.appendChild(makeSection('education',    '🎓', 'Education',       edus,
      x => eduRow(x,  true)));
    sectionsEl.appendChild(makeSection('skills',       '🎯', 'Skills',          skills,
      x => skillRow(x, shouldCheck('skill',        x, preselect, catalogMap), catalogMap)));
    sectionsEl.appendChild(makeSection('certificates', '🏆', 'Certificates',    certs,
      x => certRow(x, shouldCheck('certificate',   x, preselect, catalogMap))));

    initDragDrop(sectionsEl);

    // ── Assemble body ───────────────────────────────────────────────────────
    const bodyWrap = document.createElement('div');
    bodyWrap.innerHTML = `
      <div class="cvb-name-row">
        <div class="field" style="margin-bottom:0">
          <label style="font-size:12px;color:var(--text2)">CV Name <span style="color:var(--text3)">(optional)</span></label>
          <input class="input" id="cvb-cv-name" placeholder="e.g., Frontend Role – Company X">
        </div>
      </div>
    `;
    bodyWrap.appendChild(identityEl);

    const hint = document.createElement('p');
    hint.className = 'cvb-drag-hint';
    hint.innerHTML = '⠿ Drag sections to reorder them in your CV';
    bodyWrap.appendChild(hint);

    bodyWrap.appendChild(sectionsEl);

    const footerRow = document.createElement('div');
    footerRow.className = 'cvb-footer-row';
    footerRow.innerHTML = `<label><input type="checkbox" id="cvb-save-hist" checked> Save a copy in My CVs</label>`;
    bodyWrap.appendChild(footerRow);

    // ── Footer buttons ──────────────────────────────────────────────────────
    const footBtns = el(`
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button class="btn btn-ghost" id="cvb-cancel">Cancel</button>
        <button class="btn btn-primary" id="cvb-gen">📄 Generate PDF</button>
      </div>
    `);

    // Replace loading content with the real UI
    m.body.innerHTML = '';
    m.body.appendChild(bodyWrap);

    const footerEl = m.root.querySelector('.modal-footer');
    if (footerEl) { footerEl.innerHTML = ''; footerEl.appendChild(footBtns); }

    footBtns.querySelector('#cvb-cancel').onclick = () => m.close();

    footBtns.querySelector('#cvb-gen').onclick = async () => {
      const payload = collectPayload(bodyWrap);
      const genBtn = footBtns.querySelector('#cvb-gen');
      genBtn.disabled = true;
      genBtn.innerHTML = '<span class="spinner"></span> Generating…';

      try {
        const token = getToken();
        const res = await fetch(`${CFG.API_GATEWAY}/cv/me.pdf`, {
          method: 'POST',
          headers: { 'Content-Type':'application/json', Authorization:`Bearer ${token}` },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          let msg = `${res.status} ${res.statusText}`;
          try { const err = await res.json(); msg = err.detail || err.error || msg; } catch(_) {}
          throw new Error(msg);
        }
        const blob = await res.blob();
        const fname = ((payload.cv_name || 'jadeer-cv').replace(/[^a-z0-9\-_ ]/gi,'') || 'jadeer-cv') + '.pdf';
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = fname;
        document.body.appendChild(a); a.click();
        setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
        toast('CV generated', 'success');
        m.close();
        if (onDone) onDone();
      } catch(e) {
        toast(e.message || 'Could not generate CV', 'error');
        genBtn.disabled = false;
        genBtn.innerHTML = '📄 Generate PDF';
      }
    };
  }

  // Expose for cross-module use (called from recommendations page)
  window.JadeerCV = { openCustomize: (opts) => openCustomizeModal(opts || {}) };

  // ── CV History helpers ─────────────────────────────────────────────────────

  async function downloadHistoryCv(cv) {
    try {
      const data = await api(`/cv/history/${cv.id || cv.cv_id}`);
      const url = data?.download_url;
      if (!url) throw new Error('No download URL returned');
      window.open(url, '_blank');
    } catch(e) {
      toast(e.message || 'Could not download CV', 'error');
    }
  }

  // ── CV History page ────────────────────────────────────────────────────────

  async function loadPage() {
    const content = document.getElementById('cvs-content');
    if (!content) return;
    content.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
    try {
      const raw = await api('/cv/history').catch(() => []);
      const cvs = toArr(raw);
      content.innerHTML = `
        <div class="page-header">
          <div>
            <h1 data-i18n="my_cvs">My CVs</h1>
            <p class="sub" data-i18n="my_cvs_sub">Generate tailored CVs from your profile.</p>
          </div>
          <button class="btn btn-primary" id="gen-cv-btn">+ Generate CV</button>
        </div>
        <div id="cv-list"></div>
      `;
      const list = content.querySelector('#cv-list');
      if (!cvs.length) {
        list.innerHTML = `<div class="empty"><div class="empty-icon">📄</div><p class="muted" data-i18n="no_cvs">No CVs yet.</p></div>`;
      } else {
        cvs.forEach(c => {
          const row = el(`
            <div class="card" style="margin-bottom:12px">
              <div class="row-between" style="align-items:flex-start;gap:12px">
                <div style="flex:1;min-width:0">
                  <div class="row gap-sm" style="margin-bottom:6px">
                    <span style="font-size:20px">📄</span>
                    <strong>${c.name || c.cv_name || 'CV'}</strong>
                  </div>
                  <div class="muted" style="font-size:12px">
                    <span data-i18n="generated_on">Generated on</span> ${fmtDate(c.created_at || c.generated_at)}
                  </div>
                </div>
                <div class="row gap-sm">
                  <button class="btn btn-sm btn-primary" data-dl>⬇ Download</button>
                  <button class="btn btn-sm btn-danger" data-del aria-label="Delete">🗑</button>
                </div>
              </div>
            </div>
          `);
          row.querySelector('[data-dl]').onclick = () => downloadHistoryCv(c);
          row.querySelector('[data-del]').onclick = async () => {
            const ok = await confirmDialog({
              title:'Delete CV', message: c.name || c.cv_name || 'CV',
              danger:true, confirmText:'Delete',
            });
            if (!ok) return;
            try {
              await api(`/cv/history/${c.id || c.cv_id}`, { method:'DELETE' });
              toast('CV deleted', 'success');
              loadPage();
            } catch(e) {
              toast(e.message || 'Could not delete CV', 'error');
            }
          };
          list.appendChild(row);
        });
      }
      content.querySelector('#gen-cv-btn').onclick = () => openCustomizeModal({ onDone: loadPage });
      window.JadeerI18n.applyTranslations(content);
    } catch(e) {
      content.innerHTML = `<div class="empty"><h3>Could not load</h3><p class="muted">${e.message}</p></div>`;
    }
  }

  register('/cvs', (_p, root) => {
    if (!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`<div id="cvs-content"></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));
    loadPage();
  });
})();
