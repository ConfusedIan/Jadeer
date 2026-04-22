(function(){
  const { el, toast, modal, confirmDialog } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const toArr = (v) => Array.isArray(v) ? v
    : (v && (v.items || v.data || v.skills || v.results)) || [];
  const fmtDate = (d)=> d ? new Date(d).toLocaleDateString() : '';

  // Postgres enum `skill_category` members in the live DB: "Soft", "Technical".
  // We send these exact values on write, and normalize on read for robustness.
  const CAT = { SOFT: 'Soft', TECHNICAL: 'Technical' };
  function bucketOf(s){
    const c = ((s && s.category) || '').toString().toLowerCase();
    if (c.startsWith('tech')) return 'technical';
    return 'soft';
  }

  // A skill is "verified" only if it has a real passing score.
  // We use 0 to represent "explicitly unverified" on retakes (backend update
  // filters out null values), so treat 0 as unverified.
  const isVerified = (s)=> s && s.score != null && s.score > 0;

  // Cache of standardized O*NET soft-skill names. A skill row only shows
  // "Take Assessment Again" if its name appears in this set — that's how we
  // distinguish manually-added skills (no assessment available) from
  // assessment-library skills that the user just hasn't passed yet.
  let _stdSkillSet = null;     // lowercased Set, for membership test
  let _stdSkillList = null;    // original-case Array, for display
  async function getStdSkillSet(){
    // Only treat as cached if we actually got data — don't cache failures so
    // a cold-started /assessment/skills-list can recover on the next call.
    if(_stdSkillSet && _stdSkillSet.size > 0) return _stdSkillSet;
    try {
      const res = await api('/assessment/skills-list');
      const list = Array.isArray(res)
        ? res
        : (res && (res.all_skills || res.skills || [...(res.social_skills||[]), ...(res.thinking_skills||[])])) || [];
      _stdSkillList = list.map(s => typeof s === 'string' ? s : (s.name || s.skill_name || '')).filter(Boolean);
      _stdSkillSet = new Set(_stdSkillList.map(n => n.toLowerCase().trim()));
    } catch(e){
      console.warn('Could not load standardized skills list (will retry next time):', e);
      // IMPORTANT: leave _stdSkillSet as an EMPTY set (not null) so that
      // isAssessable() doesn't block, but next call will retry since we
      // check size > 0 above.
      _stdSkillList = _stdSkillList || [];
      _stdSkillSet = _stdSkillSet || new Set();
    }
    return _stdSkillSet;
  }
  function isAssessable(s){
    // Primary signal: the skill has a skill_id pointing to the standardized
    // catalog. Saved by the assessment flow → always assessable for reassess.
    if(s.skill_id != null && _catalogIdToName && _catalogIdToName.has(s.skill_id)){
      return true;
    }
    // Otherwise resolve the name and check if it's a known standardized skill.
    const resolvedName = s.custom_skill_name || lookupSkillName(s.skill_id) || s.name || s.skill_name || '';
    const lc = resolvedName.toLowerCase().trim();
    if(!lc) return false;
    // Prefer the catalog (loaded from Profile Service, very reliable).
    if(_catalogMap && _catalogMap.has(lc)) return true;
    // Fall back to the O*NET library set (may be empty if assessment service
    // is cold/unreachable — do NOT return false based solely on that).
    if(_stdSkillSet && _stdSkillSet.has(lc)) return true;
    return false;
  }

  // Cache of standardized skill catalog: lowercased name → integer skill_id.
  // The DB has a trigger that rejects custom_skill_name entries that collide
  // with standardized names, so the assessment flow must save by skill_id.
  let _catalogMap = null;       // name (lowercase) → skill_id
  let _catalogIdToName = null;  // skill_id → original-case name
  async function getCatalog(){
    if(_catalogMap && _catalogMap.size > 0) return _catalogMap;
    const mapN = new Map();
    const mapI = new Map();
    try {
      const res = await api('/profile/skills-catalog');
      const items = Array.isArray(res) ? res : (res && (res.items || res.data || res.skills)) || [];
      items.forEach(row => {
        const name = (row.name || row.skill_name || '').trim();
        const id = row.id ?? row.skill_id;
        if(name && id != null){
          mapN.set(name.toLowerCase(), id);
          mapI.set(id, name);
        }
      });
      _catalogMap = mapN;
      _catalogIdToName = mapI;
    } catch(e){
      console.warn('Could not load skills catalog (will retry next time):', e);
      _catalogMap = _catalogMap || new Map();
      _catalogIdToName = _catalogIdToName || new Map();
    }
    return _catalogMap;
  }
  function lookupSkillId(name){
    if(!_catalogMap) return null;
    return _catalogMap.get((name||'').toLowerCase().trim()) ?? null;
  }
  function lookupSkillName(skillId){
    if(!_catalogIdToName || skillId == null) return null;
    return _catalogIdToName.get(skillId) || null;
  }

  function profLevel(score){
    if(score==null || score<=0) return {cls:'beginner',label:t('unverified')};
    if(score>=90) return {cls:'expert',label:t('expert')};
    if(score>=75) return {cls:'advanced',label:t('advanced')};
    if(score>=60) return {cls:'intermediate',label:t('intermediate')};
    return {cls:'beginner',label:t('beginner')};
  }

  function skillRow(s){
    // Skills saved via skill_id (from assessment flow) come back from the
    // backend without a name — the GET endpoint doesn't JOIN with
    // standard_skills. Look up the name via our cached catalog.
    const name = s.custom_skill_name
              || lookupSkillName(s.skill_id)
              || s.name || s.skill_name || 'Skill';
    const verified = isVerified(s);
    const p = profLevel(s.score);
    const row = el(`
      <div class="card" style="background:var(--surface2);padding:14px 18px;margin-bottom:10px">
        <div class="row-between" style="margin-bottom:${verified?'10px':'0'}">
          <div class="row gap-sm" style="flex:1;min-width:0;flex-wrap:wrap">
            <strong style="font-size:15px">${name}</strong>
            ${verified
              ? `<span class="badge badge-accent">${p.label}</span><span class="mono" style="color:var(--text2);font-size:13px">${Math.round(s.score)} ✓</span>`
              : `<span class="badge badge-muted" data-i18n="unverified">Unverified</span>`}
          </div>
          <div class="row gap-sm">
            ${bucketOf(s)==='soft' && isAssessable(s)
              ? `<button class="btn btn-sm btn-ghost" data-assess data-i18n="${verified?'reassess':'take_assessment_again'}">${verified?'Reassess':'Take Assessment Again'}</button>`
              : ''}
            <button class="btn btn-sm btn-danger" data-del aria-label="Delete">🗑</button>
          </div>
        </div>
        ${verified ? `
          <div class="prof">
            <div class="prof-bar"><div class="prof-fill ${p.cls}" style="width:${Math.min(100,s.score)}%"></div></div>
            <span class="prof-score">${Math.round(s.score)}</span>
          </div>
          ${s.updated_at||s.created_at?`<div class="muted mt-sm" style="font-size:12px"><span data-i18n="assessed_on">Assessed on</span> ${fmtDate(s.updated_at||s.created_at)}</div>`:''}
        ` : `<div class="muted mt-sm" style="font-size:12px" data-i18n="not_assessed">Not yet assessed. Take an assessment to verify this skill.</div>`}
      </div>
    `);
    row.querySelector('[data-del]').onclick = async ()=>{
      const ok = await confirmDialog({title:'Delete skill',message:name,danger:true,confirmText:'Delete'});
      if(!ok) return;
      try { await api(`/profile/me/skills/${s.id}`,{method:'DELETE'}); toast('Deleted','success'); loadPage(); }
      catch(e){ toast(e.message,'error'); }
    };
    const assessBtn = row.querySelector('[data-assess]');
    if(assessBtn) assessBtn.onclick = ()=>startAssessment(name, s);
    return row;
  }

  async function startAssessment(skillName, existingSkill){
    let occupation = { code:'15-1252.00', title:'Software Developers' };
    try {
      const m = await api('/assessment/match-occupation',{method:'POST'});
      if(m && m.occupation_code){ occupation = { code:m.occupation_code, title:m.occupation_title||'' }; }
    } catch(_){}

    const loading = modal({
      title: `${t('assessing')}: ${skillName}`,
      body: `<div class="page-loader"><div class="spinner"></div></div>`,
    });
    let batch;
    try {
      batch = await api('/assessment/generate-assessment',{method:'POST',
        body:{ occupation_code: occupation.code, skill_name: skillName }});
    } catch(e){
      loading.close();
      toast(e.message || 'Could not load assessment','error');
      return;
    }
    loading.close();

    // Backend returns 5 deterministic questions per call. UI is strictly 5 Qs.
    const questions = toArr(batch.questions || batch);
    if(!questions.length){ toast('No questions returned','error'); return; }

    runQuestions(skillName, occupation, questions, existingSkill);
  }

  function runQuestions(skillName, occupation, questions, existingSkill){
    let idx = 0;
    const answers = {};
    const body = el('<div></div>');
    const m = modal({ title:`${t('assessing')}: ${skillName}`, body, size:'lg' });

    function renderQ(){
      const q = questions[idx];
      // Backend evaluates by position: answers[str(i)] for i in 0..N-1.
      // Using a per-question id (q.id or synthetic) here causes the backend
      // to see an empty user_answer for every question → score stays 0.
      const qKey = String(idx);
      const qText = q.text || q.question || q.prompt || '';
      const choices = q.choices || q.options || q.answers || [];
      body.innerHTML = `
        <div class="row-between mt-sm" style="margin-bottom:14px">
          <strong>${t('question')} ${idx+1} / ${questions.length}</strong>
          <span class="muted" style="font-size:12px">${occupation.title||''}</span>
        </div>
        <div class="prof-bar" style="margin-bottom:18px">
          <div class="prof-fill advanced" style="width:${(idx/questions.length)*100}%"></div>
        </div>
        <p style="margin-bottom:18px;line-height:1.6">${qText}</p>
        <div id="choices" style="display:flex;flex-direction:column;gap:10px"></div>
        <div class="row-between mt-lg">
          <button class="btn btn-ghost" id="cancel-btn" data-i18n="cancel">Cancel</button>
          <button class="btn btn-primary" id="next-btn" disabled>${idx===questions.length-1?t('submit'):t('next')}</button>
        </div>
      `;
      const cBox = body.querySelector('#choices');
      const letters = ['A','B','C','D','E','F'];
      const arr = Array.isArray(choices) ? choices : Object.entries(choices).map(([k,v])=>({key:k,text:v}));
      arr.forEach((c, i)=>{
        const key = c.key || c.id || c.letter || letters[i];
        const txt = c.text || c.label || (typeof c==='string'?c:'');
        // Preserve a selected answer if user is returning to this question.
        const isSelected = answers[qKey] === key;
        const btn = el(`<button class="card card-hover" style="text-align:start;padding:12px 16px;cursor:pointer;border:1px solid ${isSelected?'var(--accent)':'var(--border)'}" data-key="${key}">
          <strong style="color:var(--accent2);margin-inline-end:10px">${letters[i]}.</strong>${txt}</button>`);
        btn.onclick = ()=>{
          cBox.querySelectorAll('button').forEach(b=>b.style.borderColor='var(--border)');
          btn.style.borderColor = 'var(--accent)';
          answers[qKey] = key;
          body.querySelector('#next-btn').disabled = false;
        };
        cBox.appendChild(btn);
      });
      // Pre-enable Next if we already have an answer for this index.
      if(answers[qKey] !== undefined){
        body.querySelector('#next-btn').disabled = false;
      }
      body.querySelector('#cancel-btn').onclick = ()=>m.close();
      body.querySelector('#next-btn').onclick = ()=>{
        if(idx < questions.length-1){ idx++; renderQ(); }
        else submitAll();
      };
    }

    async function saveSkill({ verified, score }){
      // Assessment path uses standardized skills. The DB has a trigger that
      // rejects custom_skill_name entries colliding with the standardized
      // catalog (P0001), so we MUST submit by skill_id instead.
      // Backend rejects null/missing score (NOT NULL/CHECK on skills.score),
      // so unverified rows go in with score:0 and isVerified() treats 0 as
      // unverified at render time.
      const finalScore = verified ? score : 0;

      if(existingSkill && existingSkill.id){
        const body = { score: finalScore };
        await api(`/profile/me/skills/${existingSkill.id}`, { method:'PUT', body });
        return;
      }

      // New row from assessment flow → look up the standardized skill_id
      await getCatalog();
      const stdId = lookupSkillId(skillName);
      const body = { category: CAT.SOFT, score: finalScore };
      if(stdId != null){
        body.skill_id = stdId;
      } else {
        // Catalog miss → fall back to custom_skill_name. The trigger will
        // still reject if this name happens to be in the catalog under a
        // different spelling, but at least non-cataloged names succeed.
        body.custom_skill_name = skillName;
      }
      await api('/profile/me/skills', { method:'POST', body });
    }

    async function submitAll(){
      body.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
      try {
        const res = await api('/assessment/evaluate',{method:'POST',body:{
          occupation_code: occupation.code,
          occupation_title: occupation.title || '',
          skill_name: skillName, questions, answers,
        }});
        // Backend returns:
        //   score       = count of correct answers (e.g. 4 out of 5)
        //   percentage  = 0-100 (what we actually want as our score)
        //   passed      = boolean (pre-computed via per-occupation threshold)
        const score = res.percentage ?? res.total_score ?? 0;
        const passed = res.passed ?? score >= 70;
        m.close();
        if(passed){
          try { await saveSkill({ verified:true, score }); }
          catch(e){ console.warn('save skill failed',e); toast(e.message,'error'); }
          showPassed(skillName, score);
        } else {
          // Persist immediately as Unverified. If this fails, surface the error
          // and don't claim success — otherwise the modal lies to the user.
          let savedOk = true;
          try { await saveSkill({ verified:false }); }
          catch(e){
            console.warn('save unverified skill failed',e);
            toast(e.message || 'Could not save skill','error');
            savedOk = false;
          }
          showFailed(skillName, score,
            ()=>startAssessment(skillName, existingSkill),
            /*alreadySaved=*/savedOk);
        }
      } catch(e){
        body.innerHTML = `<p class="muted">${e.message}</p>`;
      }
    }

    renderQ();
    window.JadeerI18n.applyTranslations(body);
  }

  function showPassed(name, score){
    const foot = document.createElement('div');
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-primary';
    closeBtn.type = 'button';
    closeBtn.textContent = t('close') || 'Close';
    foot.appendChild(closeBtn);

    const b = el(`
      <div style="text-align:center;padding:10px 0">
        <div style="font-size:54px;margin-bottom:10px">🏅</div>
        <h3 style="margin-bottom:6px">${name}</h3>
        <div class="mono" style="font-size:34px;font-weight:700;color:var(--success);margin-bottom:10px">${Math.round(score)}</div>
        <p class="muted" data-i18n="assessment_passed_sub">Your skill has been added to your profile.</p>
      </div>
    `);
    const mm = modal({ title:t('assessment_passed'), body:b, footer:foot });
    closeBtn.addEventListener('click', (ev)=>{
      ev.preventDefault();
      mm.close();
      setTimeout(()=>{
        if(location.hash.startsWith('#/skills')) loadPage();
        else location.hash = '#/skills';
      }, 220);
    });
    window.JadeerI18n.applyTranslations(b);
  }

  function showFailed(name, score, retryFn, alreadySaved){
    // Build buttons as DOM nodes so handlers survive any render/i18n passes.
    const foot = document.createElement('div');
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-ghost';
    closeBtn.type = 'button';
    closeBtn.textContent = t('close') || 'Close';
    const retryBtn = document.createElement('button');
    retryBtn.className = 'btn btn-primary';
    retryBtn.type = 'button';
    retryBtn.textContent = t('retry_assessment') || 'Retry Assessment';
    foot.appendChild(closeBtn);
    foot.appendChild(retryBtn);

    const b = el(`
      <div style="text-align:center;padding:10px 0">
        <div style="font-size:54px;margin-bottom:10px">⚠️</div>
        <h3 style="margin-bottom:6px" data-i18n="score_below_threshold">Score Below Threshold</h3>
        <div class="mono" style="font-size:34px;font-weight:700;color:var(--danger);margin-bottom:10px">${Math.round(score)} / 100</div>
        <p class="muted" data-i18n="try_again">Your assessment score did not meet the required threshold of 70.</p>
        ${alreadySaved ? `<p class="muted mt-sm" style="font-size:13px" data-i18n="saved_in_soft_skills">The skill has been added to your Soft Skills list as Unverified. You can retake the assessment any time.</p>` : ''}
      </div>
    `);
    const mm = modal({ title:t('assessment_failed'), body:b, footer:foot });
    function dismissAndRefresh(){
      mm.close();
      setTimeout(()=>{
        if(location.hash.startsWith('#/skills')) loadPage();
        else location.hash = '#/skills';
      }, 220);
    }
    closeBtn.addEventListener('click', (ev)=>{ ev.preventDefault(); dismissAndRefresh(); });
    retryBtn.addEventListener('click', (ev)=>{ ev.preventDefault(); mm.close(); setTimeout(retryFn, 220); });
    window.JadeerI18n.applyTranslations(b);
  }

  async function openAddSkill(category){
    // `category` is 'soft' or 'technical' — determined by the entry button.
    const isSoft = category === 'soft';
    const b = el(`
      <div>
        <p class="muted" data-i18n="add_skill_sub" style="margin-bottom:16px">Choose a skill to add.</p>
        <div class="tabs">
          <button class="tab active" data-tab="assess" data-i18n="take_assessment">Take Assessment</button>
          <button class="tab" data-tab="man" data-i18n="add_manually_unverified">Add Manually</button>
        </div>

        <div id="tab-assess">
          ${isSoft ? `
            <p class="muted" style="font-size:13px;margin-bottom:12px" data-i18n="select_from">Select a skill from the standardized library to start a verified assessment.</p>
            <div id="skills-list" style="max-height:360px;overflow-y:auto;display:flex;flex-direction:column;gap:6px">
              <div class="page-loader"><div class="spinner"></div></div>
            </div>
          ` : `
            <div class="empty" style="padding:30px 10px">
              <div class="empty-icon">🚧</div>
              <h3 data-i18n="tech_assess_soon_title">Technical assessments coming soon</h3>
              <p class="muted mt-sm" data-i18n="tech_assess_soon_body">Verified technical skill assessments are not available yet. For now, add your technical skills manually from the tab above.</p>
            </div>
          `}
        </div>

        <div id="tab-man" class="hidden">
          <div class="field">
            <label data-i18n="custom_skill_name">Custom skill name</label>
            <input class="input" id="custom-name" placeholder="${isSoft?'e.g., Public Speaking':'e.g., React'}">
          </div>
          <p class="muted" style="font-size:12px;margin-bottom:8px">
            <span data-i18n="will_add_as">Will be added as:</span>
            <strong>${isSoft ? t('soft_skills') : t('technical_skills')}</strong>
            · <span data-i18n="unverified">Unverified</span>
          </p>
          <button class="btn btn-primary btn-block" id="add-unv-btn" data-i18n="add_as_unverified">Add as Unverified</button>
        </div>
      </div>
    `);
    const m = modal({ title:t('add_skill_title'), body:b, size:'lg' });

    b.querySelectorAll('.tab').forEach(tab=>{
      tab.onclick = ()=>{
        b.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
        tab.classList.add('active');
        b.querySelector('#tab-assess').classList.toggle('hidden', tab.dataset.tab!=='assess');
        b.querySelector('#tab-man').classList.toggle('hidden', tab.dataset.tab!=='man');
      };
    });

    // --- Assessment tab: load predefined soft-skill library (soft only) ---
    if(isSoft){
      await getStdSkillSet();
      await getCatalog();

      // Source-of-truth for the assessable list:
      //  1. Primary: the O*NET library (/assessment/skills-list) — exactly
      //     the 14 supported skills.
      //  2. Fallback: the DB catalog (/profile/skills-catalog) — if the
      //     assessment service is unreachable (cold start / timeout), we
      //     still have the catalog names so the user isn't stuck with an
      //     empty modal.
      let allSkills = _stdSkillList && _stdSkillList.length
        ? _stdSkillList.slice()
        : (_catalogIdToName ? Array.from(_catalogIdToName.values()) : []);

      // Load the user's existing skills so we can:
      //  - mark skills they've already added (different UI)
      //  - pass existingSkill to startAssessment so reassessment updates the
      //    same row (no duplicate, no DB trigger violation)
      let myRows = [];
      try {
        const raw = await api('/profile/me/skills').catch(()=>[]);
        myRows = toArr(raw);
      } catch(_){}

      // Index by resolved lowercased name
      const myByName = new Map();
      myRows.forEach(r=>{
        const nm = (r.custom_skill_name || lookupSkillName(r.skill_id) || r.name || r.skill_name || '').toLowerCase().trim();
        if(nm) myByName.set(nm, r);
      });

      function renderList(){
        const list = b.querySelector('#skills-list');
        list.innerHTML = '';
        if(!allSkills.length){
          list.innerHTML = '<p class="muted" style="padding:10px" data-i18n="no_std_skills">No standardized skills available.</p>';
          window.JadeerI18n.applyTranslations(list);
          return;
        }
        allSkills.forEach(name=>{
          if(!name) return;
          const existing = myByName.get(name.toLowerCase().trim());
          const verified = existing && isVerified(existing);
          const statusLabel = verified
            ? `<span class="badge badge-accent" style="margin-inline-start:8px">${Math.round(existing.score)}</span>`
            : existing
              ? `<span class="badge badge-muted" style="margin-inline-start:8px" data-i18n="unverified">Unverified</span>`
              : '';
          const actionHint = existing
            ? (verified ? (t('reassess')||'Reassess') : (t('take_assessment_again')||'Retake'))
            : (t('take_assessment')||'Take Assessment');
          const btn = el(`
            <button class="card card-hover" style="text-align:start;padding:12px 14px;cursor:pointer;background:var(--surface2);display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid var(--border)">
              <span style="display:flex;align-items:center;flex:1;min-width:0">
                <strong>${name}</strong>
                ${statusLabel}
              </span>
              <span class="muted" style="font-size:12px;white-space:nowrap">→ ${actionHint}</span>
            </button>
          `);
          btn.onclick = ()=>{
            m.close();
            // Pass existingSkill so the reassessment UPDATES the same row
            // (otherwise POST would violate the DB trigger or unique constraint).
            setTimeout(()=>startAssessment(name, existing), 220);
          };
          list.appendChild(btn);
        });
      }
      renderList();
    }

    // --- Manual tab: category is fixed by the entry path ---
    b.querySelector('#add-unv-btn').onclick = async ()=>{
      const name = b.querySelector('#custom-name').value.trim();
      if(!name){ toast('Enter a skill name','error'); return; }
      const dbCategory = category === 'technical' ? CAT.TECHNICAL : CAT.SOFT;

      // Check if the typed name matches a standardized skill — if so, save by
      // skill_id so the user can assess it later (also avoids the DB trigger
      // that rejects custom names colliding with the catalog).
      await getCatalog();
      const stdId = lookupSkillId(name);

      const body = { category: dbCategory };
      if(stdId != null && category === 'soft'){
        body.skill_id = stdId;
      } else {
        body.custom_skill_name = name;
      }
      try {
        await api('/profile/me/skills', { method:'POST', body });
        toast(stdId != null && category === 'soft'
          ? 'Added — you can take an assessment to verify it'
          : 'Skill added', 'success');
        m.close(); loadPage();
      } catch(e){ toast(e.message,'error'); }
    };
    window.JadeerI18n.applyTranslations(b);
  }

  async function loadPage(){
    const content = document.getElementById('skills-content');
    if(!content) return;
    content.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
    try {
      // Load skills, the standardized library, and the DB catalog in parallel.
      // Catalog gives us skill_id for assessment saves; library gates the
      // inline "Take Assessment Again" button (issue #4).
      const [raw] = await Promise.all([
        api('/profile/me/skills').catch(()=>[]),
        getStdSkillSet(),
        getCatalog(),
      ]);
      const all = toArr(raw);
      const soft = all.filter(s=>bucketOf(s)==='soft');
      const tech = all.filter(s=>bucketOf(s)==='technical');
      const scored = all.filter(isVerified);
      const avg = scored.length ? Math.round(scored.reduce((a,b)=>a+(b.score||0),0)/scored.length) : 0;
      const adv = scored.filter(s=>s.score>=75).length;

      content.innerHTML = `
        <div class="page-header">
          <div><h1 data-i18n="skills_title">Skills</h1><p class="sub" data-i18n="skills_sub"></p></div>
        </div>
        <div class="grid grid-4">
          <div class="stat"><span class="stat-label" data-i18n="total_skills">Total</span><span class="stat-value">${all.length}</span></div>
          <div class="stat"><span class="stat-label" data-i18n="verified_skills">Verified</span><span class="stat-value">${scored.length}</span></div>
          <div class="stat"><span class="stat-label" data-i18n="advanced_skills">Advanced</span><span class="stat-value">${adv}</span></div>
          <div class="stat"><span class="stat-label" data-i18n="avg_score">Avg</span><span class="stat-value">${avg}</span></div>
        </div>
        <div class="card mt-lg">
          <div class="card-title">
            <h3 data-i18n="soft_skills">Soft Skills</h3>
            <button class="btn btn-sm btn-primary" id="add-soft" data-i18n="add_skill">+ Add Skill</button>
          </div>
          <div id="soft-list"></div>
        </div>
        <div class="card mt-lg">
          <div class="card-title">
            <h3 data-i18n="technical_skills">Technical Skills</h3>
            <button class="btn btn-sm btn-primary" id="add-tech" data-i18n="add_skill">+ Add Skill</button>
          </div>
          <div id="tech-list"></div>
        </div>
      `;
      const softList = content.querySelector('#soft-list');
      const techList = content.querySelector('#tech-list');
      if(soft.length) soft.forEach(s=>softList.appendChild(skillRow(s)));
      else softList.innerHTML = `<p class="muted" style="padding:14px 0">No soft skills yet.</p>`;
      if(tech.length) tech.forEach(s=>techList.appendChild(skillRow(s)));
      else techList.innerHTML = `<p class="muted" style="padding:14px 0">No technical skills yet.</p>`;
      content.querySelector('#add-soft').onclick = ()=>openAddSkill('soft');
      content.querySelector('#add-tech').onclick = ()=>openAddSkill('technical');
      window.JadeerI18n.applyTranslations(content);
    } catch(e){
      content.innerHTML = `<div class="empty"><h3>Could not load</h3><p class="muted">${e.message}</p></div>`;
    }
  }

  register('/skills', (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`<div id="skills-content"></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));
    loadPage();
  });
})();
