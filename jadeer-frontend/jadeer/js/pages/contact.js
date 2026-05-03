(function(){
  const { el } = window.JadeerUI;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { getUser } = window.JadeerAPI;

  register('/contact', (_p, root) => {
    root.innerHTML = '';

    const user  = getUser() || {};
    const email = user.email || '';

    const content = el(`
      <div>
        <div class="page-header">
          <h1 class="page-title" data-i18n="contact_title">Contact Us</h1>
          <p class="muted" data-i18n="contact_sub">Have a question or feedback? We'd love to hear from you.</p>
        </div>

        <div style="max-width:600px;margin:0 auto;">
          <div class="card">

            <div id="contact-success" style="display:none;text-align:center;padding:2rem 0;">
              <div style="font-size:2.5rem;margin-bottom:1rem;">&#10003;</div>
              <h3 data-i18n="contact_success_title">Message sent!</h3>
              <p class="muted mt-sm" data-i18n="contact_success_sub">Thank you for reaching out. We'll get back to you soon.</p>
            </div>

            <form id="contact-form" novalidate>
              <div class="field">
                <label for="contact-title" data-i18n="contact_subject">Title</label>
                <input id="contact-title" class="input" type="text"
                       placeholder="What's this about?" required>
                <span id="err-title" style="display:none;color:var(--danger);font-size:.8rem;margin-top:.25rem;"></span>
              </div>

              <div class="field mt-md">
                <label for="contact-body" data-i18n="contact_body">Message</label>
                <textarea id="contact-body" class="input" rows="6"
                          placeholder="Write your message here…"
                          style="resize:vertical;min-height:140px;" required></textarea>
                <span id="err-body" style="display:none;color:var(--danger);font-size:.8rem;margin-top:.25rem;"></span>
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
    const titleEl   = root.querySelector('#contact-title');
    const bodyEl    = root.querySelector('#contact-body');
    const submitBtn = root.querySelector('#contact-submit');
    const successEl = root.querySelector('#contact-success');
    const serverErr = root.querySelector('#contact-server-error');

    function showErr(id, msg){
      const span = root.querySelector(`#${id}`);
      span.textContent = msg;
      span.style.display = 'block';
    }
    function clearErr(id){
      const span = root.querySelector(`#${id}`);
      span.textContent = '';
      span.style.display = 'none';
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      serverErr.style.display = 'none';
      clearErr('err-title');
      clearErr('err-body');

      const title   = titleEl.value.trim();
      const message = bodyEl.value.trim();
      let valid = true;

      if (!title)   { showErr('err-title', 'Please enter a title.'); valid = false; }
      if (!message) { showErr('err-body',  'Please enter a message.'); valid = false; }
      if (!valid) return;

      submitBtn.disabled = true;
      submitBtn.querySelector('span').textContent = 'Sending…';

      try {
        const base = (window.JADEER_CONFIG && window.JADEER_CONFIG.API_GATEWAY) || 'http://localhost:8000';
        const res = await fetch(base + '/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, title, message }),
        });

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
