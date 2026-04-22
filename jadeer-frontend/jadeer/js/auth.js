(function(){
  const { supabase, setToken, setUser, getUser, getToken } = window.JadeerAPI;

  async function signUp({ email, password, full_name, role }){
    const data = await supabase('/auth/v1/signup', {
      body: { email, password, data: { full_name, role } }
    });
    // Supabase may return session directly, or require email confirm
    if(data.access_token){
      setToken(data.access_token);
      setUser({ id:data.user.id, email, full_name, role });
    } else if(data.user){
      // No session yet (email confirm required) — try immediate login
      try { await signIn({ email, password, _afterSignupRole: role, _afterSignupName: full_name }); }
      catch(_){ /* user will need to confirm email */ }
    }
    return data;
  }

  async function signIn({ email, password, _afterSignupRole, _afterSignupName }){
    const data = await supabase('/auth/v1/token?grant_type=password', {
      body: { email, password }
    });
    setToken(data.access_token);
    const meta = (data.user && data.user.user_metadata) || {};
    setUser({
      id: data.user.id,
      email: data.user.email,
      full_name: meta.full_name || _afterSignupName || '',
      role: meta.role || _afterSignupRole || 'candidate',
    });
    return data;
  }

  function signOut(){
    setToken(null); setUser(null);
    location.hash = '#/login';
  }

  function requireAuth(){
    if(!getToken()){ location.hash = '#/login'; return false; }
    return true;
  }

  function currentRole(){ return (getUser()||{}).role || 'candidate'; }

  window.JadeerAuth = { signUp, signIn, signOut, requireAuth, currentRole };
})();
