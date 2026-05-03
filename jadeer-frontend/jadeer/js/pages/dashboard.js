(function(){
  const { el } = window.JadeerUI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  register('/dashboard', (_p, root) => {
    if(!requireAuth()) return;
    root.innerHTML = '';

    /*
     * heroContent renders inside .hero-area — a full-width slot that sits
     * OUTSIDE the padded .content div, so the hero spans the entire viewport.
     */
    const heroContent = el(`
      <section class="hero">
        <div class="hero-bg"></div>
        <div class="hero-dots"></div>
        <div class="hero-content">
          <span class="hero-title-ar">كفاءتك حقيقية</span>
          <p class="hero-title-en">Your merit is real &middot; who can see it?</p>
          <div class="hero-divider"></div>
          <div class="hero-cta">
            <a class="btn btn-primary btn-lg" href="#/recommendations" data-i18n="get_recs">Get Recommendations</a>
            <a class="btn btn-outline btn-lg" href="#/profile/edit" data-i18n="complete_profile">Complete Profile</a>
          </div>
        </div>
      </section>
    `);

    /* Dashboard cards — text-only, no icons */
    const content = el(`
      <div>
        <p class="section-label">Your Space</p>
        <div class="grid grid-3">

          <a class="card card-hover" href="#/profile">
            <h3 data-i18n="view_profile">View Profile</h3>
            <p class="muted mt-sm" data-i18n="update_info">Update your personal information</p>
          </a>

          <a class="card card-hover" href="#/skills">
            <h3 data-i18n="manage_skills">Manage Skills</h3>
            <p class="muted mt-sm" data-i18n="add_assess_skills">Add and assess your skills</p>
          </a>

          <a class="card card-hover" href="#/cvs">
            <h3 data-i18n="my_cvs">My CVs</h3>
            <p class="muted mt-sm" data-i18n="view_manage_cvs">View and manage your CVs</p>
          </a>

          <a class="card card-hover" href="#/certificates">
            <h3 data-i18n="certificates">Certificates</h3>
            <p class="muted mt-sm" data-i18n="manage_certs">Manage your certifications</p>
          </a>

          <a class="card card-hover" href="#/recommendations">
            <h3 data-i18n="nav_recs">Recommendations</h3>
            <p class="muted mt-sm">Get tailored CV recommendations</p>
          </a>

          <a class="card card-hover" href="#/chats">
            <h3 data-i18n="messages">Messages</h3>
            <p class="muted mt-sm" data-i18n="check_emp_msgs">Check employer messages</p>
          </a>

        </div>
      </div>
    `);

    root.appendChild(shell({ heroContent, content }));
  });
})();
