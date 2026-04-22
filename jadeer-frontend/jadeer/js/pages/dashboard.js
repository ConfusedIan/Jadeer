(function(){
  const { el } = window.JadeerUI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  register('/dashboard', (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`
      <div>
        <div class="page-header">
          <div>
            <h1 data-i18n="welcome_back">Welcome back!</h1>
            <p class="sub" data-i18n="manage_sub">Manage your profile, skills, and career opportunities</p>
          </div>
        </div>
        <div class="grid grid-3">
          <a class="card card-hover" href="#/profile">
            <div class="row gap-sm" style="margin-bottom:8px"><span style="font-size:22px">👤</span><h3 data-i18n="view_profile">View Profile</h3></div>
            <p class="muted" data-i18n="update_info">Update your personal information</p>
          </a>
          <a class="card card-hover" href="#/skills">
            <div class="row gap-sm" style="margin-bottom:8px"><span style="font-size:22px">🎯</span><h3 data-i18n="manage_skills">Manage Skills</h3></div>
            <p class="muted" data-i18n="add_assess_skills">Add and assess your skills</p>
          </a>
          <a class="card card-hover" href="#/cvs">
            <div class="row gap-sm" style="margin-bottom:8px"><span style="font-size:22px">📄</span><h3 data-i18n="my_cvs">My CVs</h3></div>
            <p class="muted" data-i18n="view_manage_cvs">View and manage your CVs</p>
          </a>
          <a class="card card-hover" href="#/certificates">
            <div class="row gap-sm" style="margin-bottom:8px"><span style="font-size:22px">🏆</span><h3 data-i18n="certificates">Certificates</h3></div>
            <p class="muted" data-i18n="manage_certs">Manage your certifications</p>
          </a>
          <a class="card card-hover" href="#/chats">
            <div class="row gap-sm" style="margin-bottom:8px"><span style="font-size:22px">💬</span><h3 data-i18n="messages">Messages</h3></div>
            <p class="muted" data-i18n="check_emp_msgs">Check employer messages</p>
          </a>
        </div>
        <div class="card mt-lg" style="background:linear-gradient(135deg,rgba(124,92,252,.14),rgba(192,132,252,.08));border-color:rgba(124,92,252,.35)">
          <h3 data-i18n="ready_next">Ready to find your next opportunity?</h3>
          <p class="muted mt-sm" data-i18n="complete_and_generate">Complete your profile and generate tailored CVs to match with potential employers.</p>
          <div class="row mt" style="gap:10px;flex-wrap:wrap">
            <a class="btn btn-primary" href="#/recommendations" data-i18n="get_recs">Get Recommendations</a>
            <a class="btn btn-ghost" href="#/profile/edit" data-i18n="complete_profile">Complete Profile</a>
          </div>
        </div>
      </div>
    `);
    root.appendChild(shell({ title:'Jadeer', content }));
  });
})();
