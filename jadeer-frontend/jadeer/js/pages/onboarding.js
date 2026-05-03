(function(){
  const { el, toast } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { go, register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  const MAJORS = ['Computer Science','Information Systems','Information Technology','Software Engineering',
    'Data Science','Cybersecurity','Business Administration','Marketing','Finance','Accounting',
    'Engineering','Design','Other'];
  const EXP_LEVELS = ['Entry level (0–1 years)','Junior (1–3 years)','Mid-level (3–5 years)',
    'Senior (5–10 years)','Lead / Principal (10+ years)'];
  const JOB_TYPES = ['Full-time','Part-time','Contract','Internship','Freelance','Remote'];

  register('/onboarding', (_p, root)=>{
    if(!requireAuth()) return;
    const u = window.JadeerAPI.getUser() || {};

    const opts = (arr)=>arr.map(v=>`<option value="${v}">${v}</option>`).join('');
    const form = el(`
      <div class="auth-shell" style="align-items:flex-start;padding-top:40px">
        <div class="auth-card" style="max-width:560px">
          <div class="auth-header">
            <h1 data-i18n="complete_your_profile">Complete Your Profile</h1>
            <p data-i18n="ob_sub">Let's set up your candidate profile to help employers find you</p>
          </div>
          <form id="ob-form">
            <div class="field">
              <label data-i18n="full_name">Full Name</label>
              <input class="input" name="full_name" value="${u.full_name||''}" required>
            </div>
            <div class="field">
              <label><span data-i18n="professional_headline">Professional Headline</span> *</label>
              <input class="input" name="headline" data-i18n-ph="headline_ph" required>
            </div>
            <div class="field">
              <label><span data-i18n="location">Location</span> *</label>
              <input class="input" name="location" data-i18n-ph="location_ph" required>
            </div>
            <div class="field">
              <label><span data-i18n="major">Major / Specialization</span> *</label>
              <select class="select" name="major" required>
                <option value="" data-i18n="select_major">Select your specialization</option>
                ${opts(MAJORS)}
              </select>
            </div>
            <div class="field">
              <label><span data-i18n="graduation_year">Graduation Year</span> *</label>
              <input class="input" type="number" min="1970" max="2035" name="graduation_year" data-i18n-ph="year_ph" required>
            </div>
            <div class="field">
              <label><span data-i18n="years_experience">Years of Experience</span> *</label>
              <select class="select" name="experience" required>
                <option value="" data-i18n="select_level">Select experience level</option>
                ${opts(EXP_LEVELS)}
              </select>
            </div>
            <div class="field">
              <label><span data-i18n="preferred_job">Preferred Job Type</span> *</label>
              <select class="select" name="job_type" required>
                <option value="" data-i18n="select_job_type">Select job type</option>
                ${opts(JOB_TYPES)}
              </select>
            </div>
            <div class="field">
              <label data-i18n="short_bio">Short Bio / About Me</label>
              <textarea class="textarea" name="bio" data-i18n-ph="bio_ph"></textarea>
            </div>
            <button type="submit" class="btn btn-primary btn-block btn-lg" data-i18n="complete_profile">Complete Profile</button>
          </form>
        </div>
      </div>
    `);
    root.innerHTML='';
    root.appendChild(form);

    form.querySelector('#ob-form').onsubmit = async (e)=>{
      e.preventDefault();
      const fd = new FormData(e.target);
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true; const orig = btn.textContent;
      btn.innerHTML = '<span class="spinner"></span>';
      try {
        // Compose bio to include onboarding-only fields (major/grad_year/exp/job_type)
        // since the profile schema only supports a subset of fields.
        const extra = [
          fd.get('headline') && `Headline: ${fd.get('headline')}`,
          fd.get('major') && `Major: ${fd.get('major')}`,
          fd.get('graduation_year') && `Graduation: ${fd.get('graduation_year')}`,
          fd.get('experience') && `Experience: ${fd.get('experience')}`,
          fd.get('job_type') && `Preferred: ${fd.get('job_type')}`,
        ].filter(Boolean).join(' • ');
        const bio = [fd.get('bio')?.trim(), extra].filter(Boolean).join('\n\n');

        await api('/profile/me', {
          method:'PATCH',
          body:{
            full_name: fd.get('full_name')?.trim() || null,
            location: fd.get('location')?.trim() || null,
            bio: bio || null,
          }
        });
        // Also update local cached user name
        const u2 = window.JadeerAPI.getUser() || {};
        u2.full_name = fd.get('full_name')?.trim() || u2.full_name;
        window.JadeerAPI.setUser(u2);
        toast('Profile saved','success');
        go('/dashboard');
      } catch(err){
        toast(err.message || 'Could not save profile','error');
        btn.disabled = false; btn.textContent = orig;
      }
    };
  });
})();
