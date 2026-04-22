(function(){
  const { el, toast, modal, confirmDialog } = window.JadeerUI;
  const { api, getToken } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;
  const CFG = window.JADEER_CONFIG;

  const toArr = (v) => Array.isArray(v) ? v
    : (v && (v.items || v.data || v.history || v.cvs || v.results)) || [];
  const fmtDate = (d)=> d ? new Date(d).toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';

  async function downloadCvFromBlob(blob, filename){
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(()=>{ document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
  }

  async function downloadHistoryCv(cv){
    try {
      const data = await api(`/cv/history/${cv.id || cv.cv_id}`);
      const url = data?.download_url;
      if(!url) throw new Error('No download URL returned');
      window.open(url, '_blank');
    } catch(e){
      toast(e.message || 'Could not download CV','error');
    }
  }

  function openGenerateModal(onDone){
    const b = el(`
      <div>
        <p class="muted" style="margin-bottom:14px">Customize which sections to include in your generated CV.</p>
        <div class="field">
          <label data-i18n="cv_name_label">CV Name (optional)</label>
          <input class="input" id="cv-name" data-i18n-ph="cv_name_ph" placeholder="e.g., Frontend Role - Company X">
        </div>
        <div class="card" style="background:var(--surface2);padding:14px;margin-bottom:14px">
          <strong style="display:block;margin-bottom:10px" data-i18n="cv_sections">CV Sections</strong>
          <div style="display:flex;flex-direction:column;gap:8px">
            <label class="row gap-sm"><input type="checkbox" id="inc-exp"   checked> <span data-i18n="include_experience">Include Work Experience</span></label>
            <label class="row gap-sm"><input type="checkbox" id="inc-edu"   checked> <span data-i18n="include_education">Include Education</span></label>
            <label class="row gap-sm"><input type="checkbox" id="inc-cert"  checked> <span data-i18n="include_certificates">Include Certificates</span></label>
            <label class="row gap-sm"><input type="checkbox" id="inc-sk"    checked> <span data-i18n="include_skills">Include Skills</span></label>
            <label class="row gap-sm"><input type="checkbox" id="inc-score" checked> <span data-i18n="include_scores">Show Skill Scores</span></label>
            <label class="row gap-sm"><input type="checkbox" id="inc-badge" checked> <span data-i18n="include_verified_badges">Show Verified Badges</span></label>
          </div>
        </div>
        <div class="field">
          <label><span data-i18n="skill_threshold">Only show skills with score ≥</span> <strong id="thr-val">70</strong></label>
          <input type="range" id="thr" min="0" max="100" step="5" value="70" style="width:100%">
        </div>
        <div class="field">
          <label data-i18n="custom_bio_label">Custom Bio (optional)</label>
          <textarea class="textarea" id="cv-bio" data-i18n-ph="custom_bio_ph" rows="3"></textarea>
        </div>
        <label class="row gap-sm" style="margin-top:8px">
          <input type="checkbox" id="save-hist" checked>
          <span data-i18n="save_to_history">Save a copy in My CVs</span>
        </label>
      </div>
    `);
    const foot = el(`
      <div class="row gap-sm" style="justify-content:flex-end">
        <button class="btn btn-ghost" id="cancel-btn" data-i18n="cancel">Cancel</button>
        <button class="btn btn-primary" id="gen-btn" data-i18n="generate">Generate</button>
      </div>
    `);
    const m = modal({ title:t('customize_cv'), body:b, footer:foot, size:'lg' });

    const thr = b.querySelector('#thr');
    const thrVal = b.querySelector('#thr-val');
    thr.oninput = ()=>{ thrVal.textContent = thr.value; };

    foot.querySelector('#cancel-btn').onclick = ()=>m.close();
    foot.querySelector('#gen-btn').onclick = async ()=>{
      const payload = {
        include_experience:       b.querySelector('#inc-exp').checked,
        include_education:        b.querySelector('#inc-edu').checked,
        include_certificates:     b.querySelector('#inc-cert').checked,
        include_skills:           b.querySelector('#inc-sk').checked,
        include_scores:           b.querySelector('#inc-score').checked,
        include_verified_badges:  b.querySelector('#inc-badge').checked,
        skill_threshold:          parseFloat(thr.value),
        save_to_history:          b.querySelector('#save-hist').checked,
      };
      const bio = b.querySelector('#cv-bio').value.trim();
      if(bio) payload.custom_bio = bio;
      const name = b.querySelector('#cv-name').value.trim();
      if(name) payload.cv_name = name;

      const btn = foot.querySelector('#gen-btn');
      btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
      try {
        // This returns a PDF blob (Gateway forwards the CV service response)
        const token = getToken();
        const res = await fetch(`${CFG.API_GATEWAY}/cv/me.pdf`, {
          method:'POST',
          headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${token}` },
          body: JSON.stringify(payload),
        });
        if(!res.ok){
          let msg = `${res.status} ${res.statusText}`;
          try { const e = await res.json(); msg = e.detail || e.error || msg; } catch(_){}
          throw new Error(msg);
        }
        const blob = await res.blob();
        const fname = (name || 'jadeer-cv').replace(/[^a-z0-9\-_ ]/gi,'') + '.pdf';
        await downloadCvFromBlob(blob, fname);
        toast('CV generated','success');
        m.close();
        if(onDone) onDone();
      } catch(e){
        toast(e.message || 'Could not generate CV','error');
        btn.disabled = false; btn.innerHTML = t('generate');
      }
    };
    window.JadeerI18n.applyTranslations(b);
    window.JadeerI18n.applyTranslations(foot);
  }

  async function loadPage(){
    const content = document.getElementById('cvs-content');
    if(!content) return;
    content.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
    try {
      const raw = await api('/cv/history').catch(()=>[]);
      const cvs = toArr(raw);
      content.innerHTML = `
        <div class="page-header">
          <div>
            <h1 data-i18n="my_cvs">My CVs</h1>
            <p class="sub" data-i18n="my_cvs_sub">Generate tailored CVs…</p>
          </div>
          <button class="btn btn-primary" id="gen-cv-btn" data-i18n="generate_cv">+ Generate CV</button>
        </div>
        <div id="cv-list"></div>
      `;
      const list = content.querySelector('#cv-list');
      if(!cvs.length){
        list.innerHTML = `<div class="empty"><div class="empty-icon">📄</div><p class="muted" data-i18n="no_cvs">No CVs yet.</p></div>`;
      } else {
        cvs.forEach(c=>{
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
                  <button class="btn btn-sm btn-primary" data-dl><span>⬇</span> <span data-i18n="download">Download</span></button>
                  <button class="btn btn-sm btn-danger" data-del aria-label="Delete">🗑</button>
                </div>
              </div>
            </div>
          `);
          row.querySelector('[data-dl]').onclick = ()=>downloadHistoryCv(c);
          row.querySelector('[data-del]').onclick = async ()=>{
            const ok = await confirmDialog({title:'Delete CV',message:c.name||c.cv_name||'CV',danger:true,confirmText:'Delete'});
            if(!ok) return;
            try {
              await api(`/cv/history/${c.id || c.cv_id}`, { method:'DELETE' });
              toast('CV deleted','success');
              loadPage();
            } catch(e){
              toast(e.message || 'Could not delete CV','error');
            }
          };
          list.appendChild(row);
        });
      }
      content.querySelector('#gen-cv-btn').onclick = ()=>openGenerateModal(loadPage);
      window.JadeerI18n.applyTranslations(content);
    } catch(e){
      content.innerHTML = `<div class="empty"><h3>Could not load</h3><p class="muted">${e.message}</p></div>`;
    }
  }

  register('/cvs', (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`<div id="cvs-content"></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));
    loadPage();
  });
})();
