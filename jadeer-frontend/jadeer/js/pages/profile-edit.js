(function(){
  const { el, toast, confirmDialog } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register, go } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const toInputDate = (d)=> d ? String(d).slice(0,10) : '';

  function expRow(x={}){
    const row = el(`
      <div class="card experience-item" style="background:var(--surface2);padding:16px;margin-bottom:12px">
        <div class="row-between" style="margin-bottom:10px">
          <strong data-i18n="work_experience">Work Experience</strong>
          <button class="btn btn-sm btn-danger" data-del>✕</button>
        </div>
        <input type="hidden" data-id value="${x.exp_id||''}">
        <div class="grid grid-2">
          <div class="field"><label data-i18n="job_title">Job Title</label>
            <input class="input" name="job_title" value="${x.job_title||''}" required></div>
          <div class="field"><label data-i18n="company">Company</label>
            <input class="input" name="company" value="${x.company||''}" required></div>
          <div class="field"><label data-i18n="start_date">Start Date</label>
            <input class="input" type="date" name="start_date" value="${toInputDate(x.start_date)}" required></div>
          <div class="field"><label data-i18n="end_date">End Date</label>
            <input class="input" type="date" name="end_date" value="${toInputDate(x.end_date)}"></div>
        </div>
        <div class="field"><label data-i18n="description">Description</label>
          <textarea class="textarea" name="description" data-i18n-ph="desc_ph">${x.description||''}</textarea></div>
      </div>
    `);
    row.querySelector('[data-del]').onclick = async ()=>{
      const id = row.querySelector('[data-id]').value;
      if(id){
        const ok = await confirmDialog({title:'Delete experience',message:'This cannot be undone.',danger:true,confirmText:'Delete'});
        if(!ok) return;
        try { await api(`/profile/me/experiences/${id}`,{method:'DELETE'}); toast('Deleted','success'); }
        catch(e){ toast(e.message,'error'); return; }
      }
      row.remove();
    };
    return row;
  }

  function eduRow(x={}){
    const row = el(`
      <div class="card education-item" style="background:var(--surface2);padding:16px;margin-bottom:12px">
        <div class="row-between" style="margin-bottom:10px">
          <strong data-i18n="education">Education</strong>
          <button class="btn btn-sm btn-danger" data-del>✕</button>
        </div>
        <input type="hidden" data-id value="${x.edu_id||''}">
        <div class="grid grid-2">
          <div class="field"><label data-i18n="institution">Institution</label>
            <input class="input" name="institution" value="${x.institution||''}"></div>
          <div class="field"><label data-i18n="degree">Degree</label>
            <input class="input" name="degree" value="${x.degree||''}"></div>
          <div class="field"><label data-i18n="field_of_study">Field of Study</label>
            <input class="input" name="field_of_study" value="${x.field_of_study||''}"></div>
          <div></div>
          <div class="field"><label data-i18n="start_date">Start Date</label>
            <input class="input" type="date" name="start_date" value="${toInputDate(x.start_date)}"></div>
          <div class="field"><label data-i18n="end_date">End Date</label>
            <input class="input" type="date" name="end_date" value="${toInputDate(x.end_date)}"></div>
        </div>
      </div>
    `);
    row.querySelector('[data-del]').onclick = async ()=>{
      const id = row.querySelector('[data-id]').value;
      if(id){
        const ok = await confirmDialog({title:'Delete education',message:'This cannot be undone.',danger:true,confirmText:'Delete'});
        if(!ok) return;
        try { await api(`/profile/me/education/${id}`,{method:'DELETE'}); toast('Deleted','success'); }
        catch(e){ toast(e.message,'error'); return; }
      }
      row.remove();
    };
    return row;
  }

  function collect(row){
    const out = {};
    row.querySelectorAll('input[name],textarea[name]').forEach(inp=>{
      const v = inp.value.trim();
      out[inp.name] = v || null;
    });
    return out;
  }

  register('/profile/edit', async (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`<div id="edit-content"><div class="page-loader"><div class="spinner"></div></div></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));

    try {
      const toArr = (v) => Array.isArray(v) ? v : (v && (v.items || v.data || v.experiences || v.education || v.results)) || [];
      const [meRaw, expsRaw, edusRaw] = await Promise.all([
        api('/profile/me').catch(()=>({})),
        api('/profile/me/experiences').catch(()=>[]),
        api('/profile/me/education').catch(()=>[]),
      ]);
      const me = meRaw || {};
      const exps = toArr(expsRaw);
      const edus = toArr(edusRaw);

      content.innerHTML = `
        <div class="page-header">
          <div><h1 data-i18n="edit_your_profile">Edit Your Profile</h1></div>
          <div class="row" style="gap:8px">
            <a class="btn btn-ghost" href="#/profile" data-i18n="cancel">Cancel</a>
            <button class="btn btn-primary" id="save-btn"><span>💾</span> <span data-i18n="save_profile">Save Profile</span></button>
          </div>
        </div>
        <div class="card">
          <h3 data-i18n="personal_info">Personal Information</h3>
          <div class="grid grid-2 mt">
            <div class="field"><label data-i18n="full_name">Full Name</label><input class="input" id="f-name" value="${me.full_name||''}"></div>
            <div class="field"><label data-i18n="phone_number">Phone Number</label><input class="input" id="f-phone" value="${me.phone||''}"></div>
            <div class="field"><label data-i18n="location">Location</label><input class="input" id="f-loc" value="${me.location||''}"></div>
            <div class="field"><label data-i18n="linkedin">LinkedIn URL</label><input class="input" id="f-linkedin" value="${me.linkedin_url||''}" placeholder="https://…"></div>
          </div>
          <div class="field"><label data-i18n="professional_bio">Professional Bio</label><textarea class="textarea" id="f-bio" data-i18n-ph="bio_about_ph">${me.bio||''}</textarea></div>
        </div>
        <div class="card mt-lg">
          <div class="card-title"><h3 data-i18n="work_experience">Work Experience</h3><button class="btn btn-sm btn-ghost" id="add-exp" data-i18n="add_experience">+ Add Experience</button></div>
          <div id="exp-list"></div>
        </div>
        <div class="card mt-lg">
          <div class="card-title"><h3 data-i18n="education">Education</h3><button class="btn btn-sm btn-ghost" id="add-edu" data-i18n="add_education">+ Add Education</button></div>
          <div id="edu-list"></div>
        </div>
      `;

      const expList = content.querySelector('#exp-list');
      const eduList = content.querySelector('#edu-list');
      exps.forEach(x=>expList.appendChild(expRow(x)));
      edus.forEach(x=>eduList.appendChild(eduRow(x)));

      content.querySelector('#add-exp').onclick = ()=>{ const r=expRow(); expList.appendChild(r); window.JadeerI18n.applyTranslations(r); };
      content.querySelector('#add-edu').onclick = ()=>{ const r=eduRow(); eduList.appendChild(r); window.JadeerI18n.applyTranslations(r); };

      content.querySelector('#save-btn').onclick = async (e) => {
        const btn = e.currentTarget;
        if (btn.disabled) return; 

        btn.disabled = true;
        const orig = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span> <span data-i18n="saving">Saving…</span>';

        try {
          // 1. Save Personal Info (PATCH)
          await api('/profile/me', {
            method: 'PATCH',
            body: {
              full_name: content.querySelector('#f-name').value.trim() || null,
              phone: content.querySelector('#f-phone').value.trim() || null,
              location: content.querySelector('#f-loc').value.trim() || null,
              linkedin_url: content.querySelector('#f-linkedin').value.trim() || null,
              bio: content.querySelector('#f-bio').value.trim() || null,
            }
          });

          // 2. Save Experiences
          for (const row of expList.querySelectorAll('.experience-item')) {
            const idInput = row.querySelector('[data-id]');
            const data = collect(row);
            if (!data.job_title || !data.company) continue;

            if (idInput.value) {
              // Use exp_id for the URL
              await api(`/profile/me/experiences/${idInput.value}`, { method: 'PUT', body: data });
            } else {
              const res = await api('/profile/me/experiences', { method: 'POST', body: data });
              if (res && res.data && res.data[0]) idInput.value = res.data[0].exp_id || '';
            }
          }

          // 3. Save Education
          for (const row of eduList.querySelectorAll('.education-item')) {
            const idInput = row.querySelector('[data-id]');
            const data = collect(row);
            if (!data.institution && !data.degree) continue;

            if (idInput.value) {
              // Use edu_id for the URL
              await api(`/profile/me/education/${idInput.value}`, { method: 'PUT', body: data });
            } else {
              const res = await api('/profile/me/education', { method: 'POST', body: data });
              if (res && res.data && res.data[0]) idInput.value = res.data[0].edu_id || '';
            }
          }

          toast(t('saved'), 'success');
          setTimeout(() => { go('/profile'); }, 500);

        } catch (err) {
          toast(err.message || 'Error saving', 'error');
          btn.disabled = false;
          btn.innerHTML = orig;
        }
      };

      window.JadeerI18n.applyTranslations(content);
    } catch(e){
      content.innerHTML = `<div class="empty"><h3>Could not load</h3><p class="muted">${e.message}</p></div>`;
    }
  });
})();