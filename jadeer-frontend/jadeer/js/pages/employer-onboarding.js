(function(){
  const { el, toast } = window.JadeerUI;
  const { api, getUser } = window.JadeerAPI;
  const { requireAuth, currentRole } = window.JadeerAuth;
  const { go, register } = window.JadeerRouter;
  const { t } = window.JadeerI18n;

  const INDUSTRIES = [
    'Technology','Finance & Banking','Healthcare','Education','Retail & E-commerce',
    'Manufacturing','Construction','Media & Entertainment','Logistics & Supply Chain',
    'Government & Public Sector','Consulting','Telecommunications','Energy','Other',
  ];


  register('/employer/onboarding', (_p, root) => {
    if(!requireAuth()) return;
    if(currentRole() !== 'employer'){ go('/dashboard'); return; }

    const opts = (arr) => arr.map(v => `<option value="${v}">${v}</option>`).join('');
    const u = getUser() || {};

    const form = el(`
      <div class="auth-shell" style="align-items:flex-start;padding-top:40px">
        <div class="auth-card" style="max-width:560px">
          <div class="auth-header">
            <h1 data-i18n="emp_ob_title">Set Up Your Company</h1>
            <p class="muted" data-i18n="emp_ob_sub">Tell us about your company so candidates can find you</p>
          </div>

          <div class="field">
            <label><span data-i18n="full_name">Full Name</span> *</label>
            <input class="input" id="ob-fullname" value="${u.full_name||''}" required>
          </div>

          <div class="field">
            <label><span data-i18n="company_name">Company Name</span> *</label>
            <input class="input" id="ob-company" placeholder="${t('company_name_ph')||'e.g. Acme Corp'}" required>
          </div>

          <div class="field">
            <label><span data-i18n="industry">Industry</span> *</label>
            <select class="select" id="ob-industry" required>
              <option value="" data-i18n="select_industry">Select industry</option>
              ${opts(INDUSTRIES)}
            </select>
          </div>


          <div class="field">
            <label><span data-i18n="company_location">Company Location</span> *</label>
            <input class="input" id="ob-location" placeholder="${t('company_location_ph')||'e.g. Riyadh, Saudi Arabia'}" required>
          </div>

          <div class="field">
            <label><span data-i18n="company_website">Company Website</span></label>
            <input class="input" id="ob-website" type="url" placeholder="${t('company_website_ph')||'https://yourcompany.com'}">
          </div>

          <div class="field">
            <label data-i18n="company_bio">About the Company</label>
            <textarea class="textarea" id="ob-bio" rows="4" placeholder="${t('company_bio_ph')||'Briefly describe what your company does...'}"></textarea>
          </div>

          <button class="btn btn-primary btn-block btn-lg" id="ob-submit">
            <span data-i18n="complete_company_profile">Complete Company Profile</span>
          </button>
        </div>
      </div>
    `);

    root.innerHTML = '';
    root.appendChild(form);
    window.JadeerI18n.applyTranslations(form);

    const submitBtn = form.querySelector('#ob-submit');

    submitBtn.addEventListener('click', async (ev) => {
      ev.preventDefault();

      const fullName   = form.querySelector('#ob-fullname').value.trim();
      const company    = form.querySelector('#ob-company').value.trim();
      const industry   = form.querySelector('#ob-industry').value;
      const location   = form.querySelector('#ob-location').value.trim();
      const website    = form.querySelector('#ob-website').value.trim();
      const bio        = form.querySelector('#ob-bio').value.trim();

      if(!fullName){ toast(t('err_name_required')||'Please enter your full name.','error'); return; }
      if(!company){ toast(t('err_company_required')||'Company name is required.','error'); return; }
      if(!industry){ toast(t('err_industry_required')||'Please select an industry.','error'); return; }
      if(!location){ toast(t('err_location_required')||'Company location is required.','error'); return; }
      if(website && !website.startsWith('https://')){
        toast(t('err_url_https')||'Website must start with https://','error'); return;
      }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>';

      try {
        await api('/profile/me', {
          method: 'PATCH',
          body: {
            full_name:    fullName  || null,
            location:     location  || null,
            bio:          bio       || null,
            company_name: company   || null,
            industry:     industry  || null,
            website_url:  website   || null,
          },
        });
        const u2 = window.JadeerAPI.getUser() || {};
        u2.full_name = fullName || u2.full_name;
        window.JadeerAPI.setUser(u2);
        toast(t('profile_saved')||'Profile saved','success');
        go('/employer');
      } catch(err){
        toast(err.message || 'Could not save profile','error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span data-i18n="complete_company_profile">Complete Company Profile</span>`;
      }
    });
  });
})();
