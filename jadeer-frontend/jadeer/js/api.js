// Jadeer API client — wraps all fetch calls with JWT auth + error handling
(function(){
  const CFG = window.JADEER_CONFIG;
  const TOKEN_KEY   = 'jadeer.jwt';
  const REFRESH_KEY = 'jadeer.refresh';
  const USER_KEY    = 'jadeer.user';

  function getToken(){ return localStorage.getItem(TOKEN_KEY); }
  function setToken(t){ t ? localStorage.setItem(TOKEN_KEY,t) : localStorage.removeItem(TOKEN_KEY); }
  function getRefreshToken(){ return localStorage.getItem(REFRESH_KEY); }
  function setRefreshToken(t){ t ? localStorage.setItem(REFRESH_KEY,t) : localStorage.removeItem(REFRESH_KEY); }
  function getUser(){ try{ return JSON.parse(localStorage.getItem(USER_KEY)||'null'); }catch(e){ return null; } }
  function setUser(u){ u ? localStorage.setItem(USER_KEY,JSON.stringify(u)) : localStorage.removeItem(USER_KEY); }

  // Single in-flight refresh promise — prevents parallel refresh races
  let _refreshPromise = null;

  async function _attemptRefresh(){
    const refreshToken = getRefreshToken();
    if(!refreshToken) return false;

    try {
      const res = await fetch(`${CFG.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
        method: 'POST',
        headers: { 'Content-Type':'application/json', apikey: CFG.SUPABASE_ANON_KEY },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      const data = await res.json().catch(()=>({}));
      if(!res.ok || !data.access_token) return false;

      setToken(data.access_token);
      if(data.refresh_token) setRefreshToken(data.refresh_token);
      return true;
    } catch(_){
      return false;
    }
  }

  function _clearAuthAndRedirect(){
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    // Show message after navigation so the login page renders first
    const msg = 'Your session has expired. Please log in again.';
    location.hash = '#/login';
    // Defer toast until the login page has mounted
    setTimeout(() => {
      if(window.JadeerUI && window.JadeerUI.toast){
        window.JadeerUI.toast(msg, 'error', 5000);
      }
    }, 300);
  }

  async function _buildAndFetch(url, method, headers, body, blob, noCache){
    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      cache: noCache ? 'no-store' : 'default',
    });
    return res;
  }

  function _buildHeaders(auth, noCache){
    const headers = { 'Content-Type':'application/json' };
    if(noCache){
      headers['Cache-Control'] = 'no-cache';
      headers['Pragma'] = 'no-cache';
    }
    if(auth){
      const t = getToken();
      if(t) headers.Authorization = `Bearer ${t}`;
    }
    return headers;
  }

  async function _parseError(res){
    let msg = `${res.status} ${res.statusText}`;
    try {
      const e = await res.json();
      // Backend may return detail as a string OR as a structured object
      // (e.g. { message: "...", missing_fields: [...] }).
      // Coerce both to a human-readable string so callers never see "[object Object]".
      const raw = e.detail ?? e.message ?? e.error ?? null;
      if(raw !== null && raw !== undefined){
        if(typeof raw === 'object'){
          const base = raw.message || '';
          const missing = Array.isArray(raw.missing_fields) && raw.missing_fields.length
            ? `Missing required fields: ${raw.missing_fields.join(', ')}.`
            : '';
          msg = [base, missing].filter(Boolean).join(' ') || JSON.stringify(raw);
        } else {
          msg = String(raw);
        }
      }
    } catch(_){}
    return msg;
  }

  async function api(path, { method='GET', body, blob=false, auth=true, noCache=false } = {}){
    let url = path.startsWith('http') ? path : `${CFG.API_GATEWAY}${path}`;
    if(noCache){
      // Append a cache-busting query param so the browser never serves a
      // stale GET response after we've just done a mutation.
      url += (url.includes('?') ? '&' : '?') + '_t=' + Date.now();
    }

    const headers = _buildHeaders(auth, noCache);
    let res = await _buildAndFetch(url, method, headers, body, blob, noCache);

    // 401: attempt token refresh once, then retry
    if(res.status === 401 && auth){
      if(!_refreshPromise){
        _refreshPromise = _attemptRefresh().finally(() => { _refreshPromise = null; });
      }
      const refreshed = await _refreshPromise;

      if(refreshed){
        // Retry with new token
        const retryHeaders = _buildHeaders(auth, noCache);
        res = await _buildAndFetch(url, method, retryHeaders, body, blob, noCache);
      }

      if(!refreshed || res.status === 401){
        _clearAuthAndRedirect();
        const err = new Error('Session expired');
        err.status = 401;
        throw err;
      }
    }

    if(!res.ok){
      const msg = await _parseError(res);
      const err = new Error(msg); err.status = res.status; throw err;
    }
    if(blob) return res.blob();
    const ct = res.headers.get('content-type')||'';
    if(ct.includes('application/json')) return res.json();
    if(ct.includes('application/pdf')) return res.blob();
    return res.text();
  }

  // Supabase direct calls
  async function supabase(path, { method='POST', body } = {}){
    const res = await fetch(`${CFG.SUPABASE_URL}${path}`,{
      method,
      headers:{ 'Content-Type':'application/json', apikey: CFG.SUPABASE_ANON_KEY },
      body: body?JSON.stringify(body):undefined,
    });
    const data = await res.json().catch(()=>({}));
    if(!res.ok){
      const err = new Error(data.error_description || data.msg || data.error || `Auth error ${res.status}`);
      err.status = res.status; throw err;
    }
    return data;
  }

  window.JadeerAPI = { api, supabase, getToken, setToken, getRefreshToken, setRefreshToken, getUser, setUser };
})();
