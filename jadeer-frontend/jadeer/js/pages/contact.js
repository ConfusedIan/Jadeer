(function(){
  const { el } = window.JadeerUI;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  register('/contact', (_p, root) => {
    root.innerHTML = '';

    const content = el(`
      <div>
        <div class="page-header">
          <h1 class="page-title" data-i18n="contact_title">Contact Us</h1>
          <p class="muted" data-i18n="contact_sub">Have a question or feedback? We'd love to hear from you.</p>
        </div>

        <div style="max-width:600px;margin:0 auto;">
          <div class="card" id="contact-card">

            <div id="contact-success" style="display:none;text-align:center;padding:2rem 0;">
              <div style="font-size:2.5rem;margin-bottom:1rem;">&#10003;</div>
              <h3 data-i18n="contact_success_title">Message sent!</h3>
              <p class="muted mt-sm" data-i18n="contact_success_sub">Thank you for reaching out. We'll get back to you soon.</p>
            </div>

            <form id="contact-form" novalidate>
              <div class="field">
                <label for="contact-name" data-i18n="contact_name">Name</label>
                <input id="contact-name" class="input" type="text" autocomplete="name"
                       placeholder="Your name" data-i18n-placeholder="contact_name_placeholder" required>
                <span class="field-error" id="err-name" style="display:none;color:var(--danger);font-size:.8rem;margin-top:.25rem;"></span>
              </div>

              <div class="field mt-md">
                <label for="contact-email" data-i18n="contact_email">Email</label>
                <input id="contact-email" class="input" type="email" autocomplete="email"
                       placeholder="you@example.com" required>
                <span class="field-error" id="err-email" style="display:none;color:var(--danger);font-size:.8rem;margin-top:.25rem;"></span>
              </div>

              <div class="field mt-md">
                <label for="contact-message" data-i18n="contact_message">Message</label>
                <textarea id="contact-message" class="textarea input" rows="6"
                          placeholder="Write your message here…" data-i18n-placeholder="contact_msg_placeholder"
                          style="resize:vertical;min-height:140px;" required></textarea>
                <span class="field-error" id="err-msg" style="display:none;color:var(--danger);font-size:.8rem;margin-top:.25rem;"></span>
              </div>

              <div id="contact-server-error" style="display:none;color:var(--danger);font-size:.875rem;margin-top:.75rem;"></div>

              <div class="mt-lg">
                <button type="submit" class="btn btn-primary btn-block" id="contact-submit">
                  <span data-i18n="contact_send">Send Message</span>
                </button>
              </div>
            </form>

          </div>
        </div>
      </div>
    `);

    root.appendChild(shell({ content }));

    const form      = root.querySelector('#contact-form');
    const nameEl    = root.querySelector('#contact-name');
    const emailEl   = root.querySelector('#contact-email');
    const msgEl     = root.querySelector('#contact-message');
    const submitBtn = root.querySelector('#contact-submit');
    const successEl = root.querySelector('#contact-success');
    const serverErr = root.querySelector('#contact-server-error');

    function showErr(id, msg){
      const el = root.querySelector(`#${id}`);
      el.textContent = msg;
      el.style.display = 'block';
    }
    function clearErr(id){
      const el = root.querySelector(`#${id}`);
      el.textContent = '';
      el.style.display = 'none';
    }

    function validateEmail(v){
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      serverErr.style.display = 'none';

      const name    = nameEl.value.trim();
      const email   = emailEl.value.trim();
      const message = msgEl.value.trim();
      let valid = true;

      clearErr('err-name');
      clearErr('err-email');
      clearErr('err-msg');

      if (!name) {
        showErr('err-name', 'Please enter your name.');
        valid = false;
      }
      if (!email) {
        showErr('err-email', 'Please enter your email.');
        valid = false;
      } else if (!validateEmail(email)) {
        showErr('err-email', 'Please enter a valid email address.');
        valid = false;
      }
      if (!message) {
        showErr('err-msg', 'Please enter a message.');
        valid = false;
      }
      if (!valid) return;

      submitBtn.disabled = true;
      submitBtn.querySelector('span').setAttribute('data-i18n', 'loading');
      submitBtn.querySelector('span').textContent = 'Sending…';

      try {
        const base = (window.JADEER_CONFIG && window.JADEER_CONFIG.API_GATEWAY) || 'http://localhost:8000';
        const res = await fetch(base + '/contact',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, message }),
          }
        );

        if (!res.ok) {
          let detail = 'Failed to send message. Please try again.';
          try { const data = await res.json(); detail = data.detail || detail; } catch(_){}
          throw new Error(detail);
        }

        form.style.display = 'none';
        successEl.style.display = 'block';
      } catch (err) {
        serverErr.textContent = err.message || 'Something went wrong. Please try again.';
        serverErr.style.display = 'block';
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Send Message';
      }
    });

    if (window.JadeerI18n) window.JadeerI18n.applyTranslations(root);
  });
})();
