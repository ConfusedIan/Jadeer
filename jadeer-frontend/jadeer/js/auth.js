(function(){
  const { supabase, setToken, setRefreshToken, setUser, getUser, getToken } = window.JadeerAPI;

  function _storeSession(data, fallbackName, fallbackRole){
    setToken(data.access_token);
    if(data.refresh_token) setRefreshToken(data.refresh_token);
    const meta = (data.user && data.user.user_metadata) || {};
    setUser({
      id: data.user.id,
      email: data.user.email,
      full_name: meta.full_name || fallbackName || '',
      role: meta.role || fallbackRole || 'candidate',
    });
  }

  async function signUp({ email, password, full_name, role }){
    const data = await supabase('/auth/v1/signup', {
      body: { email, password, data: { full_name, role } }
    });
    // Supabase may return session directly, or require email confirm
    if(data.access_token){
      _storeSession(data, full_name, role);
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
    _storeSession(data, _afterSignupName, _afterSignupRole);
    return data;
  }

  function signOut(){
    setToken(null); setRefreshToken(null); setUser(null);
    location.hash = '#/login';
  }

  function requireAuth(){
    if(!getToken()){ location.hash = '#/login'; return false; }
    return true;
  }

  function currentRole(){ return (getUser()||{}).role || 'candidate'; }

  window.JadeerAuth = { signUp, signIn, signOut, requireAuth, currentRole };
})();
