(function(){
  const { el, initials } = window.JadeerUI;
  const { api, getUser } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const fmtDate = (d)=> d ? new Date(d).toLocaleDateString(undefined,{year:'numeric',month:'short'}) : '';
  const range = (s,e)=> `${fmtDate(s)||'—'} – ${e?fmtDate(e):t('present')}`;

  const profLevel = (score)=>{
    if(score==null || score<=0) return {cls:'beginner',label:'Unverified'};
    if(score>=90) return {cls:'expert',label:'Expert'};
    if(score>=75) return {cls:'advanced',label:'Advanced'};
    if(score>=60) return {cls:'intermediate',label:'Intermediate'};
    return {cls:'beginner',label:'Beginner'};
  };

  register('/profile', async (_p, root)=>{
    if(!requireAuth()) return;
    const user = getUser() || {};
    root.innerHTML = '';
    const content = el(`<div id="profile-content"><div class="page-loader"><div class="spinner"></div></div></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));

    try {
      const toArr = (v) => Array.isArray(v) ? v
        : (v && (v.items || v.data || v.experiences || v.education || v.certificates || v.skills || v.results)) || [];
      const [meRaw, expsRaw, edusRaw, certsRaw, skillsRaw, catalogRaw] = await Promise.all([
        api('/profile/me').catch(()=>({})),
        api('/profile/me/experiences').catch(()=>[]),
        api('/profile/me/education').catch(()=>[]),
        api('/profile/me/certificates').catch(()=>[]),
        api('/profile/me/skills').catch(()=>[]),
        api('/profile/skills-catalog').catch(()=>({items:[]})),
      ]);
      const cvsRaw = await api('/cv/history').catch(()=>[]);
      const me = meRaw || {};
      const exps = toArr(expsRaw);
      const edus = toArr(edusRaw);
      const certs = toArr(certsRaw);
      const skills = toArr(skillsRaw);
      const cvs = toArr(cvsRaw);

      // Build skill_id → name map so skills saved via skill_id (assessment
      // flow) display their proper name even though the GET endpoint doesn't
      // JOIN with standard_skills.
      const catalogIdToName = new Map();
      toArr(catalogRaw).forEach(row=>{
        const id = row.id ?? row.skill_id;
        const name = (row.name || row.skill_name || '').trim();
        if(id != null && name) catalogIdToName.set(id, name);
      });

      const fullName = me.full_name || user.full_name || user.email || '';
      const headline = (me.bio||'').split('\n')[0]?.replace(/^Headline:\s*/,'') || '';

      const expHtml = (exps||[]).length ? exps.map(x=>`
        <div style="padding:14px 0;border-top:1px solid var(--border)">
          <div class="row-between">
            <div><strong>${x.job_title||''}</strong> <span class="muted">· ${x.company||''}</span></div>
            <div class="muted" style="font-size:13px">${range(x.start_date,x.end_date)}</div>
          </div>
          ${x.description?`<p class="muted mt-sm" style="font-size:13px">${x.description}</p>`:''}
        </div>
      `).join('') : `<p class="muted" data-i18n="no_experience">No work experience yet.</p>`;

      const eduHtml = (edus||[]).length ? edus.map(x=>`
        <div style="padding:14px 0;border-top:1px solid var(--border)">
          <div><strong>${x.degree||''}${x.field_of_study?` in ${x.field_of_study}`:''}</strong></div>
          <div class="muted" style="font-size:13px">${x.institution||''} · ${range(x.start_date,x.end_date)}</div>
        </div>
      `).join('') : `<p class="muted" data-i18n="no_education">No education entries yet.</p>`;

      const certHtml = (certs||[]).length ? certs.slice(0,6).map(c=>{
        const verified = c.supported_cert_id || c.verified;
        return `<span class="pill ${verified?'pill-accent':''}">${c.certificate_name}${verified?' <span class="badge-success" style="color:var(--success)">✓</span>':''}</span>`;
      }).join(' ') : `<p class="muted" data-i18n="no_certs">No certificates yet.</p>`;

      const topSkills = (skills||[]).slice().sort((a,b)=>(b.score||0)-(a.score||0)).slice(0,8);
      const skillHtml = topSkills.length ? topSkills.map(s=>{
        const p = profLevel(s.score);
        const label = s.custom_skill_name || catalogIdToName.get(s.skill_id) || s.name || s.skill_name || 'Skill';
        return `<span class="pill">${label}${(s.score!=null && s.score>0)?` <span class="mono" style="color:var(--text2)">(${Math.round(s.score)})</span>`:''}</span>`;
      }).join(' ') : `<p class="muted" data-i18n="no_skills">No skills added yet.</p>`;

      const cvHtml = (cvs||[]).length ? cvs.slice(0,3).map(c=>`
        <div class="row-between" style="padding:10px 0;border-top:1px solid var(--border)">
          <div>📄 ${c.name || c.cv_name || 'CV'}</div>
          <div class="muted" style="font-size:12px">${c.created_at ? fmtDate(c.created_at):''}</div>
        </div>
      `).join('') : `<p class="muted" data-i18n="no_cvs">No CVs generated yet.</p>`;

      content.innerHTML = `
        <div class="page-header">
          <div>
            <h1 data-i18n="candidate_profile">Candidate Profile</h1>
            <p class="sub" data-i18n="manage_profile_info">Manage your profile information</p>
          </div>
          <a class="btn btn-primary" href="#/profile/edit"><span>✏️</span> <span data-i18n="edit_profile">Edit Profile</span></a>
        </div>

        <div class="card">
          <div class="row" style="gap:20px;align-items:flex-start">
            <div class="avatar avatar-xl">${initials(fullName)}</div>
            <div style="flex:1;min-width:0">
              <h2>${fullName}</h2>
              ${headline?`<p class="muted mt-sm">${headline}</p>`:''}
              <div class="row mt" style="gap:18px;flex-wrap:wrap;font-size:13px;color:var(--text2)">
                ${user.email?`<span>✉️ ${user.email}</span>`:''}
                ${me.phone?`<span>📞 ${me.phone}</span>`:''}
                ${me.location?`<span>📍 ${me.location}</span>`:''}
                ${me.linkedin_url?`<a href="${me.linkedin_url}" target="_blank" rel="noopener">🔗 LinkedIn</a>`:''}
              </div>
            </div>
          </div>
        </div>

        <div class="card mt-lg">
          <div class="card-title"><h3>🏢 <span data-i18n="work_experience">Work Experience</span></h3></div>
          ${expHtml}
        </div>

        <div class="card mt-lg">
          <div class="card-title"><h3>🎓 <span data-i18n="education">Education</span></h3></div>
          ${eduHtml}
        </div>

        <div class="card mt-lg">
          <div class="card-title">
            <h3>🏆 <span data-i18n="certificates">Certificates</span></h3>
            <a class="btn btn-sm btn-ghost" href="#/certificates" data-i18n="view_all_certs">View All Certificates</a>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">${certHtml}</div>
        </div>

        <div class="card mt-lg">
          <div class="card-title">
            <h3>🎯 <span data-i18n="top_skills">Top Skills</span></h3>
            <a class="btn btn-sm btn-ghost" href="#/skills" data-i18n="view_all_skills">View All Skills</a>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px">${skillHtml}</div>
        </div>

        <div class="card mt-lg">
          <div class="card-title">
            <h3>📄 <span data-i18n="recent_cvs">Recent CVs</span></h3>
            <a class="btn btn-sm btn-ghost" href="#/cvs" data-i18n="view_all_cvs">View All CVs</a>
          </div>
          ${cvHtml}
        </div>
      `;
      window.JadeerI18n.applyTranslations(content);
    } catch(e){
      content.innerHTML = `<div class="empty"><h3>Could not load profile</h3><p class="muted">${e.message}</p></div>`;
    }
  });
})();
