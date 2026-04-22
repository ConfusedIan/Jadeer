(function(){
  const { el, toast } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth, currentRole } = window.JadeerAuth;
  const { register, go } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  const CSS = `
    .esp-wrap { padding: 28px 32px; max-width: 1100px; }
    .esp-header { margin-bottom: 28px; }
    .esp-header h2 { font-size: 22px; font-weight: 700; color: var(--text); margin: 0 0 4px; }
    .esp-header p { font-size: 13px; color: var(--text2); margin: 0; }

    .esp-filters {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 24px; margin-bottom: 24px;
    }
    .esp-filters-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px 20px; }
    .esp-field label {
      display: block; font-size: 11px; font-weight: 600;
      letter-spacing: .06em; text-transform: uppercase;
      color: var(--text2); margin-bottom: 6px;
    }
    .esp-field input, .esp-field select {
      width: 100%; background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius-sm); color: var(--text); font-size: 13px;
      padding: 9px 12px; outline: none; transition: border-color .15s;
      box-sizing: border-box; font-family: var(--font);
    }
    .esp-field input:focus, .esp-field select:focus {
      border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow);
    }
    .esp-field select { cursor: pointer; }

    .esp-skills-row {
      display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
      margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border);
    }
    .esp-skills-box {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius-sm); padding: 16px;
    }
    .esp-skills-box-header {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;
    }
    .esp-skills-box-header strong {
      font-size: 11px; font-weight: 600; letter-spacing: .05em;
      text-transform: uppercase; color: var(--text2);
    }
    .esp-add-btn {
      background: none; border: 1px dashed var(--border2); border-radius: 20px;
      color: var(--accent2); font-size: 12px; padding: 4px 12px; cursor: pointer;
      transition: all .15s; font-family: var(--font);
    }
    .esp-add-btn:hover { border-color: var(--accent); background: var(--accent-glow); }
    .esp-skill-tags { display: flex; flex-wrap: wrap; gap: 8px; min-height: 32px; }
    .esp-skill-tag {
      display: inline-flex; align-items: center; gap: 6px;
      background: var(--surface3); border: 1px solid var(--border);
      border-radius: 20px; padding: 4px 10px 4px 12px; font-size: 12px;
      color: var(--text); animation: tagIn .15s ease;
    }
    @keyframes tagIn { from { opacity:0; transform:scale(.88); } to { opacity:1; transform:scale(1); } }
    .esp-skill-tag input {
      background: none; border: none; outline: none;
      color: var(--text); font-size: 12px; width: 90px; font-family: var(--font);
    }
    .esp-skill-tag .score-in {
      width: 38px; background: none; border: none; outline: none;
      color: var(--accent2); font-size: 12px; text-align: center; font-family: var(--font);
    }
    .esp-skill-tag .sep { color: var(--border2); font-size: 11px; }
    .esp-skill-tag .rm {
      background: none; border: none; cursor: pointer;
      color: var(--text3); font-size: 15px; line-height: 1; padding: 0 2px; transition: color .1s;
    }
    .esp-skill-tag .rm:hover { color: var(--danger); }
    .esp-empty-tag { font-size: 12px; color: var(--text3); align-self: center; }

    .esp-actions {
      display: flex; align-items: center; justify-content: flex-end;
      gap: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border);
    }
    .esp-reset-btn {
      background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
      color: var(--text2); font-size: 13px; padding: 9px 18px; cursor: pointer;
      transition: all .15s; font-family: var(--font);
    }
    .esp-reset-btn:hover { border-color: var(--border2); color: var(--text); }
    .esp-search-btn {
      background: var(--accent); border: none; border-radius: var(--radius-sm);
      color: #fff; font-size: 13px; font-weight: 600; padding: 10px 28px; cursor: pointer;
      transition: opacity .15s, transform .1s; font-family: var(--font);
      letter-spacing: .02em; display: flex; align-items: center; gap: 8px;
    }
    .esp-search-btn:hover:not(:disabled) { opacity: .88; }
    .esp-search-btn:active:not(:disabled) { transform: scale(.97); }
    .esp-search-btn:disabled { opacity: .5; cursor: not-allowed; }

    .esp-results-header {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    }
    .esp-results-header h3 { font-size: 15px; font-weight: 600; margin: 0; }
    .esp-count {
      font-size: 12px; color: var(--text3); background: var(--surface2);
      border: 1px solid var(--border); border-radius: 20px; padding: 3px 12px;
    }

    .esp-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 20px 24px; margin-bottom: 12px;
      display: flex; align-items: flex-start; gap: 20px;
      transition: border-color .15s, box-shadow .15s;
    }
    .esp-card:hover { border-color: var(--border2); box-shadow: 0 4px 24px rgba(0,0,0,.25); }
    .esp-avatar {
      width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      display: flex; align-items: center; justify-content: center;
      font-size: 16px; font-weight: 700; color: #fff;
    }
    .esp-card-body { flex: 1; min-width: 0; }
    .esp-card-top {
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 12px; margin-bottom: 8px;
    }
    .esp-card-name { font-size: 15px; font-weight: 600; margin: 0 0 3px; }
    .esp-card-meta { font-size: 12px; color: var(--text2); }
    .esp-score-badge {
      flex-shrink: 0; text-align: center; background: var(--surface2);
      border: 1px solid var(--border); border-radius: var(--radius-sm);
      padding: 8px 14px; min-width: 64px;
    }
    .esp-score-badge .val { font-size: 20px; font-weight: 700; color: var(--accent2); line-height: 1; }
    .esp-score-badge .lbl { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing:.06em; margin-top:3px; }
    .esp-stat-chips { display: flex; gap: 10px; flex-wrap: wrap; }
    .esp-stat { font-size: 12px; color: var(--text3); }
    .esp-stat span { color: var(--text2); }
    .esp-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .esp-pill {
      font-size: 11px; padding: 3px 10px; border-radius: 20px;
      background: var(--surface2); border: 1px solid var(--border); color: var(--text2);
    }
    .esp-pill.verified { background:rgba(124,92,252,.12); border-color:rgba(124,92,252,.3); color:var(--accent2); }
    .esp-pill.cert { background:var(--success-bg); border-color:rgba(34,211,160,.25); color:var(--success); }

    .esp-empty { text-align:center; padding:60px 24px; color:var(--text3); font-size:14px; }
    .esp-empty-icon { font-size:38px; margin-bottom:12px; opacity:.45; }
    .esp-action-btn {
      display: inline-flex; align-items: center; gap: 5px;
      font-size: 12px; font-weight: 500; padding: 5px 12px;
      border-radius: 6px; border: 1px solid var(--border);
      cursor: pointer; text-decoration: none; transition: all .15s;
      font-family: var(--font);
    }
    .esp-action-primary {
      background: var(--accent); border-color: var(--accent); color: #fff;
    }
    .esp-action-primary:hover { opacity: .85; }
    .esp-action-ghost { background: none; color: var(--text2); }
    .esp-action-ghost:hover { border-color: var(--border2); color: var(--text); }
    .esp-catalog-select {
      width:100%; background:var(--surface3); border:1px solid var(--border);
      border-radius:var(--radius-sm); color:var(--text); font-size:12px;
      padding:7px 10px; outline:none; cursor:pointer; font-family:var(--font);
      transition: border-color .15s;
    }
    .esp-catalog-select:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-glow); }
    .esp-catalog-input {
      background:var(--surface3); border:1px solid var(--border);
      border-radius:var(--radius-sm); color:var(--text); font-size:12px;
      padding:7px 10px; outline:none; font-family:var(--font);
      transition: border-color .15s; box-sizing:border-box;
    }
    .esp-catalog-input:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-glow); }

    @media(max-width:768px){
      .esp-wrap{padding:16px;}
      .esp-filters-grid{grid-template-columns:1fr 1fr;}
      .esp-skills-row{grid-template-columns:1fr;}
    }
    @media(max-width:520px){ .esp-filters-grid{grid-template-columns:1fr;} }
  `;

  function injectStyles(){
    if(document.getElementById('esp-styles')) return;
    const s = document.createElement('style');
    s.id = 'esp-styles'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  register('/employer/search', (_p, root) => {
    if(!requireAuth()) return;
    if(currentRole() !== 'employer'){ go('/dashboard'); return; }

    injectStyles();
    root.innerHTML = '';

    let softSkills = [];
    let techSkills = [];

    const content = el(`<div></div>`);
    root.appendChild(shell({ title: 'Find Candidates', content }));

    const wrap = document.createElement('div');
    wrap.className = 'esp-wrap';
    wrap.innerHTML = `
      <div class="esp-header">
        <h2>Find Candidates</h2>
        <p>Search and rank verified candidates by skills, experience, and qualifications</p>
      </div>
      <div class="esp-filters">
        <div class="esp-filters-grid">
          <div class="esp-field"><label>Major / Field</label><input id="f-major" placeholder="e.g. Computer Science"></div>
          <div class="esp-field"><label>Location</label><input id="f-location" placeholder="e.g. Riyadh"></div>
          <div class="esp-field"><label>Graduation Year</label><input id="f-grad" type="number" min="1990" max="2035" placeholder="e.g. 2022"></div>
          <div class="esp-field"><label>Min. Years of Experience</label><input id="f-exp" type="number" min="0" max="30" placeholder="0"></div>
          <div class="esp-field"><label>Sort By</label>
            <select id="f-sort-by">
              <option value="score">Skill Score</option>
              <option value="years_experience">Years of Experience</option>
            </select>
          </div>
          <div class="esp-field"><label>Order</label>
            <select id="f-sort-order">
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
        <div class="esp-skills-row">
          <div class="esp-skills-box">
            <div class="esp-skills-box-header">
              <strong>Soft Skills</strong>
            </div>
            <!-- Standardized catalog -->
            <div id="soft-catalog-wrap" style="margin-bottom:12px">
              <div style="font-size:11px;color:var(--text3);margin-bottom:6px">From standardized catalog</div>
              <select id="soft-catalog-select" class="esp-catalog-select">
                <option value="">Loading skills…</option>
              </select>
            </div>
            <!-- Selected tags -->
            <div class="esp-skill-tags" id="soft-tags"><span class="esp-empty-tag">No requirements added</span></div>
            <!-- Manual entry -->
            <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
              <div style="font-size:11px;color:var(--text3);margin-bottom:6px">Non-standard / manual</div>
              <div class="row" style="gap:8px;align-items:center">
                <input id="soft-manual-name" class="esp-catalog-input" placeholder="Skill name" style="flex:1">
                <input id="soft-manual-score" class="esp-catalog-input" type="number" min="0" max="100" placeholder="Min %" style="width:72px">
                <button class="esp-add-btn" id="add-soft-manual-btn">+ Add</button>
              </div>
            </div>
          </div>
          <div class="esp-skills-box">
            <div class="esp-skills-box-header">
              <strong>Technical Skills</strong>
              <button class="esp-add-btn" id="add-tech-btn">+ Add</button>
            </div>
            <div class="esp-skill-tags" id="tech-tags"><span class="esp-empty-tag">No requirements added</span></div>
          </div>
        </div>
        <div class="esp-actions">
          <button class="esp-reset-btn" id="reset-btn">Clear filters</button>
          <button class="esp-search-btn" id="search-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            Search Candidates
          </button>
        </div>
      </div>
      <div id="results-section" style="display:none">
        <div class="esp-results-header">
          <h3>Results</h3>
          <span class="esp-count" id="results-count">0 found</span>
        </div>
        <div id="results-list"></div>
      </div>
    `;
    content.appendChild(wrap);

    // Load catalog into select
    (async ()=>{
      const sel = wrap.querySelector('#soft-catalog-select');
      try {
        const raw = await api('/profile/skills-catalog').catch(()=>({items:[]}));
        const items = Array.isArray(raw)?raw:(raw.items||raw.data||[]);
        const softItems = items.filter(s=>{
          const cat=(s.category||s.skill_category||'').toLowerCase();
          return !cat || cat==='soft';
        });
        if(softItems.length){
          sel.innerHTML = `<option value="">— Select a standardized skill —</option>` +
            softItems.map(s=>{
              const id = s.id??s.skill_id;
              const name = s.name||s.skill_name||'';
              return `<option value="${name}" data-id="${id}">${name}</option>`;
            }).join('');
        } else {
          sel.innerHTML = `<option value="">No catalog available</option>`;
        }
      } catch(_){
        sel.innerHTML = `<option value="">Could not load skills</option>`;
      }
    })();

    // Catalog select → add tag on change
    wrap.querySelector('#soft-catalog-select').addEventListener('change', (ev)=>{
      const name = ev.target.value.trim();
      if(!name) return;
      if(softSkills.find(s=>s.name.toLowerCase()===name.toLowerCase())){
        toast(`"${name}" already added`,'info'); ev.target.value=''; return;
      }
      softSkills.push({name, min_score:60});
      renderSoftTags();
      ev.target.value=''; // reset dropdown
    });

    // Manual add button
    wrap.querySelector('#add-soft-manual-btn').addEventListener('click', ()=>{
      const nameIn  = wrap.querySelector('#soft-manual-name');
      const scoreIn = wrap.querySelector('#soft-manual-score');
      const name    = nameIn.value.trim();
      if(!name){ toast('Enter a skill name','error'); return; }
      if(softSkills.find(s=>s.name.toLowerCase()===name.toLowerCase())){
        toast(`"${name}" already added`,'info'); return;
      }
      softSkills.push({name, min_score: parseInt(scoreIn.value)||60});
      renderSoftTags();
      nameIn.value=''; scoreIn.value='';
    });

    function renderSoftTags(){
      const box = wrap.querySelector('#soft-tags');
      box.innerHTML = '';
      if(!softSkills.length){ box.innerHTML = `<span class="esp-empty-tag">No requirements added</span>`; return; }
      softSkills.forEach((sk, idx) => {
        const tag = document.createElement('div');
        tag.className = 'esp-skill-tag';
        const label = document.createElement('span');
        label.style.cssText = 'font-size:12px;color:var(--text)';
        label.textContent = sk.name;
        const sep = document.createElement('span'); sep.className='sep'; sep.textContent='≥';
        const si = document.createElement('input'); si.className='score-in'; si.type='number'; si.min='0'; si.max='100'; si.placeholder='60'; si.value=sk.min_score||'';
        si.addEventListener('input', ()=>{ softSkills[idx].min_score=parseInt(si.value)||0; });
        const rm = document.createElement('button'); rm.className='rm'; rm.textContent='×';
        rm.addEventListener('click', ()=>{ softSkills.splice(idx,1); renderSoftTags(); });
        tag.append(label, sep, si, rm); box.appendChild(tag);
      });
    }

    function renderTechTags(){
      const box = wrap.querySelector('#tech-tags');
      box.innerHTML = '';
      if(!techSkills.length){ box.innerHTML = `<span class="esp-empty-tag">No requirements added</span>`; return; }
      techSkills.forEach((sk, idx) => {
        const tag = document.createElement('div'); tag.className='esp-skill-tag';
        const ni = document.createElement('input'); ni.placeholder='Skill name'; ni.value=sk; ni.style.width='110px';
        ni.addEventListener('input', ()=>{ techSkills[idx]=ni.value.trim(); });
        const rm = document.createElement('button'); rm.className='rm'; rm.textContent='×';
        rm.addEventListener('click', ()=>{ techSkills.splice(idx,1); renderTechTags(); });
        tag.append(ni, rm); box.appendChild(tag);
      });
    }
    wrap.querySelector('#add-tech-btn').addEventListener('click', ()=>{
      techSkills.push(''); renderTechTags();
      const ins = wrap.querySelectorAll('#tech-tags input'); if(ins.length) ins[ins.length-1]?.focus();
    });

    wrap.querySelector('#reset-btn').addEventListener('click', ()=>{
      ['f-major','f-location','f-grad','f-exp'].forEach(id => wrap.querySelector('#'+id).value='');
      wrap.querySelector('#f-sort-by').value='score'; wrap.querySelector('#f-sort-order').value='desc';
      softSkills=[]; techSkills=[]; renderSoftTags(); renderTechTags();
      wrap.querySelector('#soft-catalog-select').value='';
      wrap.querySelector('#soft-manual-name').value='';
      wrap.querySelector('#soft-manual-score').value='';
      wrap.querySelector('#results-section').style.display='none';
    });

    wrap.querySelector('#search-btn').addEventListener('click', async ()=>{
      const major    = wrap.querySelector('#f-major').value.trim();
      const location = wrap.querySelector('#f-location').value.trim();
      const expVal   = wrap.querySelector('#f-exp').value.trim();
      const gradVal  = wrap.querySelector('#f-grad').value.trim();
      const sortBy   = wrap.querySelector('#f-sort-by').value;
      const sortOrd  = wrap.querySelector('#f-sort-order').value;

      const payload = { sort_by:sortBy, sort_order:sortOrd };
      if(major)    payload.major=major;
      if(location) payload.location=location;
      if(expVal)   payload.min_years_experience=parseInt(expVal)||0;
      if(gradVal)  payload.graduation_year=parseInt(gradVal)||null;
      const vs = softSkills.filter(s=>s.name.trim());
      const vt = techSkills.filter(s=>s.trim());
      if(vs.length) payload.soft_skills=vs.map(s=>({name:s.name,min_score:s.min_score||0}));
      if(vt.length) payload.tech_skills=vt;

      const btn = wrap.querySelector('#search-btn');
      btn.disabled=true; btn.innerHTML=`<span class="spinner" style="width:14px;height:14px;border-width:2px"></span> Searching…`;

      const section = wrap.querySelector('#results-section');
      const list    = wrap.querySelector('#results-list');
      const count   = wrap.querySelector('#results-count');
      list.innerHTML=`<div style="padding:48px;text-align:center"><div class="spinner"></div></div>`;
      section.style.display='';

      try {
        const res = await api('/ranking/search',{method:'POST',body:payload});
        const candidates = Array.isArray(res)?res:(res.results||res.candidates||res.items||res.data||[]);
        count.textContent=`${candidates.length} candidate${candidates.length!==1?'s':''} found`;
        list.innerHTML='';
        if(!candidates.length){
          list.innerHTML=`<div class="esp-empty"><div class="esp-empty-icon">🔍</div><div>No candidates matched your criteria</div><div style="font-size:12px;margin-top:6px">Try adjusting your filters or removing skill requirements</div></div>`;
          return;
        }
        candidates.forEach(c=>list.appendChild(buildCard(c)));
      } catch(e){
        list.innerHTML=`<div class="esp-empty"><div class="esp-empty-icon">⚠️</div><div>${e.message||'Search failed — please try again'}</div></div>`;
        toast(e.message||'Search failed','error');
      } finally {
        btn.disabled=false;
        btn.innerHTML=`<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg> Search Candidates`;
      }
    });

    function buildCard(c){
      const profile  = c.profile || {};
      const name     = (profile.full_name || '').trim() || 'Candidate';
      const initials = name.split(' ').map(w=>w[0]||'').slice(0,2).join('').toUpperCase() || '?';
      const location = profile.location || null;
      const bioRaw   = profile.bio || '';
      const bioClean = bioRaw.split('\n\n').filter(p=>!p.startsWith('Company:')).join(' ').trim();
      const headline = bioClean ? (bioClean.length > 80 ? bioClean.slice(0,77)+'…' : bioClean) : null;

      const score  = c.avg_soft_skill_score != null ? Math.round(c.avg_soft_skill_score) : null;
      const exp    = c.years_of_experience  != null ? c.years_of_experience : null;
      const grad   = c.graduation_year || null;
      const major  = c.major || null;
      const email  = c.email || null;

      const latestJob = (c.experiences||[]).find(e => !e.end_date || e.is_current);
      const jobLine   = latestJob ? [latestJob.job_title, latestJob.company].filter(Boolean).join(' · ') : null;

      const allCerts  = (c.certificates || []).filter(cert => cert.certificate_name);
      const verCerts  = allCerts.filter(cert => /^verif/i.test(cert.status||cert.verification_status||''));
      const restCerts = allCerts.filter(cert => !/^verif/i.test(cert.status||cert.verification_status||''));
      const showCerts = [...verCerts, ...restCerts].slice(0, 3);
      const moreCerts = allCerts.length - showCerts.length;

      const scoreColor = score == null ? 'var(--text3)'
        : score >= 75 ? 'var(--success)'
        : score >= 50 ? 'var(--warning)'
        : 'var(--accent2)';
      const scoreLabel = score == null ? '—'
        : score >= 75 ? 'Strong'
        : score >= 50 ? 'Good'
        : 'Fair';
      const scoreBg    = score == null ? 'var(--surface2)'
        : score >= 75 ? 'var(--success-bg)'
        : score >= 50 ? 'var(--warning-bg)'
        : 'rgba(124,92,252,.12)';
      const scoreBorder = score == null ? 'var(--border)'
        : score >= 75 ? 'rgba(34,211,160,.25)'
        : score >= 50 ? 'rgba(251,191,36,.25)'
        : 'rgba(124,92,252,.25)';

      const metaParts = [
        major    && `🎓 ${major}`,
        grad     && `Class of ${grad}`,
        exp != null && `⏱ ${exp} yr${exp!==1?'s':''}`,
        location && `📍 ${location}`,
      ].filter(Boolean);

      const card = document.createElement('div');
      card.className = 'esp-card';

      card.innerHTML = `
        <div style="display:flex;gap:0;align-items:stretch">

          <!-- Left: main info -->
          <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:8px;padding-inline-end:16px">

            <!-- Identity -->
            <div style="display:flex;align-items:flex-start;gap:12px">
              <div class="esp-avatar" style="width:42px;height:42px;font-size:14px;border-radius:11px;flex-shrink:0">${initials}</div>
              <div style="min-width:0">
                <p style="font-size:14px;font-weight:700;color:var(--text);margin:0 0 1px">${name}</p>
                ${jobLine  ? `<p style="font-size:12px;color:var(--text2);margin:0">${jobLine}</p>` : ''}
                ${headline ? `<p style="font-size:12px;color:var(--text3);margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:340px">${headline}</p>` : ''}
              </div>
            </div>

            <!-- Meta -->
            ${metaParts.length ? `
            <div style="display:flex;flex-wrap:wrap;gap:4px">
              ${metaParts.map(m=>`<span class="esp-pill" style="font-size:11px;padding:2px 8px">${m}</span>`).join('')}
            </div>` : ''}

            <!-- Certificates -->
            ${showCerts.length ? `
            <div style="display:flex;flex-wrap:wrap;align-items:center;gap:4px">
              ${showCerts.map(cert=>{
                const ver=/^verif/i.test(cert.status||cert.verification_status||'');
                return `<span class="esp-pill ${ver?'cert':''}" style="font-size:11px">${ver?'✓ ':''}${cert.certificate_name}</span>`;
              }).join('')}
              ${moreCerts>0?`<span style="font-size:11px;color:var(--text3)">+${moreCerts}</span>`:''}
            </div>` : ''}

            <!-- Email -->
            ${email ? `
            <p style="font-size:11px;color:var(--text3);margin:0;display:flex;align-items:center;gap:4px">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              <a href="mailto:${email}" style="color:inherit;text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px">${email}</a>
            </p>` : ''}

          </div>

          <!-- Right: score + Chat -->
          <div style="flex-shrink:0;width:100px;border-inline-start:1px solid var(--border);padding-inline-start:16px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:10px">

            <!-- Score block -->
            <div style="text-align:center;width:100%">
              <div style="font-size:30px;font-weight:800;color:${scoreColor};line-height:1;margin-bottom:4px">
                ${score != null ? score : '—'}
              </div>
              <div style="font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--text3);margin-bottom:6px" title="Match score based on soft skills (60%), experience (20%), and technical skills (20%).">Match</div>
              <div style="display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;background:${scoreBg};color:${scoreColor};border:1px solid ${scoreBorder}">
                ${scoreLabel}
              </div>
            </div>

            <!-- Chat placeholder -->
            <button class="esp-chat-btn" title="Messaging coming soon" style="width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;padding:8px 4px;border-radius:var(--radius-sm);background:none;border:1px dashed var(--border);color:var(--text3);font-size:11px;cursor:pointer;transition:border-color .15s,color .15s;font-family:var(--font)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Chat
            </button>

          </div>
        </div>
      `;

      const chatBtn = card.querySelector('.esp-chat-btn');
      chatBtn.addEventListener('mouseenter', function(){ this.style.borderColor='var(--border2)'; this.style.color='var(--text2)'; });
      chatBtn.addEventListener('mouseleave', function(){ this.style.borderColor='var(--border)';  this.style.color='var(--text3)'; });
      chatBtn.addEventListener('click', ()=>{ toast('Employer messaging is coming soon.','info', 3000); });

      return card;
    }
  });
})();
