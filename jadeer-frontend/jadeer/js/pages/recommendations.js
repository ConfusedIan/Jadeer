(function(){
  const { el, toast } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const toArr = (v) => Array.isArray(v) ? v : [];

  function section(title, iconEmoji, items, renderItem){
    if(!items.length) return '';
    return `
      <div class="card mt-lg">
        <div class="card-title">
          <h3><span style="margin-inline-end:6px">${iconEmoji}</span>${title}</h3>
        </div>
        <div style="display:flex;flex-direction:column;gap:10px">
          ${items.map(renderItem).join('')}
        </div>
      </div>
    `;
  }

  function renderResults(root, data){
    const relevant = toArr(data.relevant_skills);
    const exps     = toArr(data.matching_experiences);
    const certs    = toArr(data.recommended_certifications);
    const gaps     = toArr(data.areas_for_development);

    const any = relevant.length || exps.length || certs.length || gaps.length;
    if(!any){
      root.innerHTML = `<p class="muted" style="padding:20px;text-align:center" data-i18n="rec_no_results">No recommendations returned. Try a more detailed job description.</p>`;
      return;
    }

    const html = `
      ${section(t('relevant_skills'), '🎯', relevant, (s)=>`
        <div style="padding:12px 14px;background:var(--surface2);border-radius:var(--radius-sm);border-inline-start:3px solid var(--success)">
          <strong>${s.name||''}</strong>
          ${s.description?`<p class="muted mt-sm" style="font-size:13px">${s.description}</p>`:''}
        </div>
      `)}

      ${section(t('matching_experiences'), '💼', exps, (x)=>`
        <div style="padding:12px 14px;background:var(--surface2);border-radius:var(--radius-sm);border-inline-start:3px solid var(--info)">
          <div class="row-between">
            <strong>${x.job_title||''} <span class="muted" style="font-weight:400">· ${x.company||''}</span></strong>
            ${x.duration?`<span class="muted" style="font-size:12px">${x.duration}</span>`:''}
          </div>
          ${x.description?`<p class="muted mt-sm" style="font-size:13px">${x.description}</p>`:''}
        </div>
      `)}

      ${section(t('recommended_certifications'), '🏆', certs, (c)=>`
        <div style="padding:12px 14px;background:var(--surface2);border-radius:var(--radius-sm);border-inline-start:3px solid var(--accent)">
          <strong>${c.name||''}</strong>
          ${c.description?`<p class="muted mt-sm" style="font-size:13px">${c.description}</p>`:''}
        </div>
      `)}

      ${section(t('areas_for_development'), '📚', gaps, (g)=>`
        <div style="padding:12px 14px;background:var(--surface2);border-radius:var(--radius-sm);border-inline-start:3px solid var(--warning)">
          <strong>${g.skill||''}</strong>
          ${g.description?`<p class="muted mt-sm" style="font-size:13px">${g.description}</p>`:''}
        </div>
      `)}
    `;
    root.innerHTML = html;
    window.JadeerI18n.applyTranslations(root);

    const anyCv = relevant.length || exps.length || certs.length;
    if(anyCv){
      const cta = document.createElement('div');
      cta.className = 'card mt-lg';
      cta.style.cssText = 'background:linear-gradient(135deg,rgba(124,92,252,.1),rgba(192,132,252,.06));border-color:rgba(124,92,252,.3)';
      cta.innerHTML = `
        <div class="row-between" style="flex-wrap:wrap;gap:12px">
          <div>
            <h3>Ready to apply?</h3>
            <p class="muted mt-sm" style="font-size:13px">Build a tailored CV with these recommendations pre-selected as your starting point.</p>
          </div>
          <button class="btn btn-primary" id="create-cv-btn">📄 Create this CV</button>
        </div>
      `;
      root.appendChild(cta);
      cta.querySelector('#create-cv-btn').onclick = () => {
        if(!window.JadeerCV){ toast('CV module not available','error'); return; }
        window.location.hash = '#/cvs';
        requestAnimationFrame(() => {
          window.JadeerCV.openCustomize({
            preselect: {
              skills:      relevant.map(s => s.name),
              experiences: exps.map(e => ({ job_title: e.job_title, company: e.company })),
              certs:       certs.map(c => c.name),
            },
          });
        });
      };
    }
  }

  register('/recommendations', (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`
      <div>
        <div class="page-header">
          <div>
            <h1 data-i18n="recommendations">Get Recommendations</h1>
            <p class="sub" data-i18n="recommendations_sub">Paste a job description…</p>
          </div>
        </div>
        <div class="card">
          <div class="field">
            <label data-i18n="job_description">Job Description</label>
            <textarea class="textarea" id="jd-input" rows="8" data-i18n-ph="job_desc_ph" placeholder="Paste the full job description here…"></textarea>
          </div>
          <div class="row" style="justify-content:flex-end;gap:10px">
            <button class="btn btn-ghost" id="clear-btn" data-i18n="clear_analysis">Start Over</button>
            <button class="btn btn-primary" id="analyze-btn" data-i18n="analyze_btn">Analyze My Match</button>
          </div>
        </div>
        <div id="rec-results">
          <p class="muted" style="padding:30px;text-align:center" data-i18n="rec_empty">Your personalized recommendations will appear here once you paste a job description.</p>
        </div>
      </div>
    `);
    root.appendChild(shell({ title:'Jadeer', content }));

    const jd = content.querySelector('#jd-input');
    const resultsBox = content.querySelector('#rec-results');
    const analyzeBtn = content.querySelector('#analyze-btn');
    const clearBtn   = content.querySelector('#clear-btn');

    clearBtn.onclick = ()=>{
      jd.value = '';
      resultsBox.innerHTML = `<p class="muted" style="padding:30px;text-align:center" data-i18n="rec_empty">Your personalized recommendations will appear here once you paste a job description.</p>`;
      window.JadeerI18n.applyTranslations(resultsBox);
    };

    analyzeBtn.onclick = async ()=>{
      const text = jd.value.trim();
      if(text.length < 40){ toast('Please paste a longer job description (40+ characters).','error'); return; }
      analyzeBtn.disabled = true;
      const orig = analyzeBtn.textContent;
      analyzeBtn.innerHTML = '<span class="spinner"></span>';
      resultsBox.innerHTML = `<div class="page-loader"><div class="spinner"></div><span style="margin-inline-start:10px" data-i18n="analyzing">Analyzing…</span></div>`;
      window.JadeerI18n.applyTranslations(resultsBox);
      try {
        const res = await api('/recommendation/analyze', { method:'POST', body:{ job_description:text } });
        renderResults(resultsBox, res || {});
      } catch(e){
        // Backend returns a generic "Internal server error" for any exception
        // in the LLM pipeline (bad API key, LLM timeout, malformed JSON, etc.)
        // Translate common failure modes into helpful UI messages.
        const status = e.status;
        const raw = (e.message || '').toLowerCase();
        let friendly = e.message || 'Could not analyze';
        let retryable = true;
        if(status === 500 || raw.includes('internal server error')){
          friendly = 'The AI service couldn\'t complete your request. This usually means the LLM provider is unreachable or the service is cold-starting. Try again in 30–60 seconds.';
        } else if(status === 401){
          friendly = 'Session expired. Please sign in again.';
          retryable = false;
        } else if(status === 502 || status === 503 || status === 504){
          friendly = 'The recommendation service is waking up (Render free tier sleeps after inactivity). Please wait 30–60 seconds and try again.';
        } else if(raw.includes('unexpected response format')){
          friendly = 'The AI model returned an invalid response. Please try a more detailed job description or try again.';
        }
        toast(friendly,'error', 7000);
        resultsBox.innerHTML = `
          <div class="card" style="padding:24px;text-align:center">
            <div style="font-size:40px;margin-bottom:10px">⚠️</div>
            <h3 style="margin-bottom:6px">Could not analyze</h3>
            <p class="muted" style="max-width:520px;margin:0 auto">${friendly}</p>
            ${retryable ? `<button class="btn btn-primary mt-lg" id="rec-retry-btn">Try Again</button>` : ''}
          </div>
        `;
        const retryBtn = resultsBox.querySelector('#rec-retry-btn');
        if(retryBtn) retryBtn.onclick = ()=>analyzeBtn.click();
      } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = orig;
        window.JadeerI18n.applyTranslations(analyzeBtn);
      }
    };
  });
})();
