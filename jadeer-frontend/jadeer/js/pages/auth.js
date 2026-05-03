(function(){
  const { el, toast } = window.JadeerUI;
  const { signUp, signIn } = window.JadeerAuth;
  const { t } = window.JadeerI18n;
  const { go } = window.JadeerRouter;

  function validatePassword(pw){
    return {
      len:      pw.length >= 8,
      upper:    /[A-Z]/.test(pw),
      lower:    /[a-z]/.test(pw),
      num:      /[0-9]/.test(pw),
      special:  /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(pw),
      nospace:  !/\s/.test(pw) && pw.length>0,
    };
  }
  function allPwOk(v){ return Object.values(v).every(Boolean); }

  function shell(activeTab, inner){
    return el(`
      <div class="auth-shell">
        <div class="auth-card">
          <div class="auth-header">
            <h1 data-i18n="welcome">Welcome to Jadeer</h1>
            <p data-i18n="welcome_sub">Sign in to your account or create a new one</p>
          </div>
          <div class="auth-tabs" role="tablist">
            <button class="${activeTab==='login'?'active':''}" data-go="#/login" data-i18n="login">Login</button>
            <button class="${activeTab==='signup'?'active':''}" data-go="#/signup" data-i18n="signup">Sign Up</button>
          </div>
          <div class="auth-inner">${inner}</div>
          <div class="row" style="justify-content:center;margin-top:18px">
            <button class="lang-toggle" id="lang-toggle">🌐 <span id="lang-label"></span></button>
          </div>
        </div>
      </div>
    `);
  }

  function hookTabs(root){
    root.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go.replace('#','')));
    const lt = root.querySelector('#lang-toggle');
    const ll = root.querySelector('#lang-label');
    function setLbl(){ ll.textContent = window.JadeerI18n.getLang()==='en'?'عربي':'EN'; }
    setLbl();
    lt.onclick = ()=>window.JadeerI18n.toggleLang();
  }

  // ----- Login -----
  window.JadeerRouter.register('/login', (_p, root)=>{
    root.innerHTML = '';
    const inner = `
      <form id="login-form" novalidate>
        <div class="field">
          <label data-i18n="email">Email</label>
          <input class="input" type="email" name="email" required data-i18n-ph="email" placeholder="Email">
        </div>
        <div class="field">
          <label data-i18n="password">Password</label>
          <input class="input" type="password" name="password" required minlength="1" placeholder="••••••••">
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg" data-i18n="login">Login</button>
      </form>
    `;
    const node = shell('login', inner);
    root.appendChild(node);
    hookTabs(node);
    const form = node.querySelector('#login-form');
    form.onsubmit = async (e)=>{
      e.preventDefault();
      const btn = form.querySelector('button[type=submit]');
      const fd = new FormData(form);
      btn.disabled = true; const orig = btn.textContent; btn.innerHTML = `<span class="spinner"></span>`;
      try {
        await signIn({ email: fd.get('email').trim(), password: fd.get('password') });
        toast('Welcome back!','success');
        // Route by role
        const role = window.JadeerAuth.currentRole();
        go(role==='employer' ? '/employer' : '/dashboard');
      } catch(err){
        toast(err.message || t('err_generic'),'error');
        btn.disabled = false; btn.textContent = orig;
      }
    };
  });

  // ----- Sign Up -----
  window.JadeerRouter.register('/signup', (_p, root)=>{
    root.innerHTML = '';
    const inner = `
      <form id="signup-form" novalidate>
        <div class="field">
          <label data-i18n="full_name">Full Name</label>
          <input class="input" name="full_name" required placeholder="Name">
        </div>
        <div class="field">
          <label data-i18n="email">Email</label>
          <input class="input" type="email" name="email" required placeholder="your.email@example.com">
        </div>
        <div class="field">
          <label data-i18n="password">Password</label>
          <div class="input-icon">
            <input class="input" type="password" name="password" id="pw" required placeholder="••••••••">
            <button type="button" id="pw-toggle" aria-label="Show">👁</button>
          </div>
          <div class="password-rules" id="pw-rules">
            <div data-rule="len">• <span data-i18n="pw_rule_len"></span></div>
            <div data-rule="upper">• <span data-i18n="pw_rule_upper"></span></div>
            <div data-rule="lower">• <span data-i18n="pw_rule_lower"></span></div>
            <div data-rule="num">• <span data-i18n="pw_rule_num"></span></div>
            <div data-rule="special">• <span data-i18n="pw_rule_special"></span></div>
            <div data-rule="nospace">• <span data-i18n="pw_rule_space"></span></div>
          </div>
        </div>
        <div class="field">
          <label data-i18n="repeat_password">Repeat Password</label>
          <input class="input" type="password" name="password2" required placeholder="••••••••">
        </div>
        <div class="field">
          <label data-i18n="i_am_a">I am a:</label>
          <div class="role-picker" role="radiogroup">
            <div class="role-opt active" data-role="candidate">
              <span class="emoji">🎓</span><div class="lbl" data-i18n="candidate">Candidate</div>
            </div>
            <div class="role-opt" data-role="employer">
              <span class="emoji">🏢</span><div class="lbl" data-i18n="employer">Employer</div>
            </div>
          </div>
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg mt-sm" data-i18n="signup">Sign Up</button>
      </form>
    `;
    const node = shell('signup', inner);
    root.appendChild(node);
    hookTabs(node);

    const form = node.querySelector('#signup-form');
    const pw = form.querySelector('#pw');
    const rulesBox = form.querySelector('#pw-rules');
    pw.addEventListener('input',()=>{
      const v = validatePassword(pw.value);
      rulesBox.querySelectorAll('[data-rule]').forEach(d=>{
        d.classList.toggle('ok', !!v[d.dataset.rule]);
      });
    });
    form.querySelector('#pw-toggle').onclick = ()=>{
      pw.type = pw.type==='password'?'text':'password';
    };
    // Role picker
    let role = 'candidate';
    form.querySelectorAll('.role-opt').forEach(o=>{
      o.onclick = ()=>{
        form.querySelectorAll('.role-opt').forEach(x=>x.classList.remove('active'));
        o.classList.add('active'); role = o.dataset.role;
      };
    });

    form.onsubmit = async (e)=>{
      e.preventDefault();
      const fd = new FormData(form);
      const email = fd.get('email').trim();
      const full_name = fd.get('full_name').trim();
      const password = fd.get('password');
      const password2 = fd.get('password2');
      if(!email || !full_name){ toast(t('err_fill_all'),'error'); return; }
      if(!allPwOk(validatePassword(password))){ toast(t('err_pw_invalid'),'error'); return; }
      if(password!==password2){ toast(t('err_passwords_match'),'error'); return; }
      const btn = form.querySelector('button[type=submit]');
      btn.disabled = true; const orig = btn.textContent; btn.innerHTML = `<span class="spinner"></span>`;
      try {
        await signUp({ email, password, full_name, role });
        toast('Account created!','success');
        if(window.JadeerAPI.getToken()){
          go(role==='employer' ? '/employer/onboarding' : '/onboarding');
        } else {
          toast('Check your email to confirm, then log in.','info',5000);
          go('/login');
        }
      } catch(err){
        toast(err.message || t('err_generic'),'error');
        btn.disabled = false; btn.textContent = orig;
      }
    };
  });
})();
