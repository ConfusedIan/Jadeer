// Jadeer API client — wraps all fetch calls with JWT auth + error handling
(function(){
  const CFG = window.JADEER_CONFIG;
  const TOKEN_KEY = 'jadeer.jwt';
  const USER_KEY  = 'jadeer.user';

  function getToken(){ return localStorage.getItem(TOKEN_KEY); }
  function setToken(t){ t ? localStorage.setItem(TOKEN_KEY,t) : localStorage.removeItem(TOKEN_KEY); }
  function getUser(){ try{ return JSON.parse(localStorage.getItem(USER_KEY)||'null'); }catch(e){ return null; } }
  function setUser(u){ u ? localStorage.setItem(USER_KEY,JSON.stringify(u)) : localStorage.removeItem(USER_KEY); }

  async function api(path, { method='GET', body, blob=false, auth=true, noCache=false } = {}){
    let url = path.startsWith('http') ? path : `${CFG.API_GATEWAY}${path}`;
    if(noCache){
      // Append a cache-busting query param so the browser never serves a
      // stale GET response after we've just done a mutation.
      url += (url.includes('?') ? '&' : '?') + '_t=' + Date.now();
    }
    const headers = { 'Content-Type':'application/json' };
    if(noCache){
      headers['Cache-Control'] = 'no-cache';
      headers['Pragma'] = 'no-cache';
    }
    if(auth){
      const t = getToken();
      if(t) headers.Authorization = `Bearer ${t}`;
    }
    const res = await fetch(url,{
      method,
      headers,
      body: body?JSON.stringify(body):undefined,
      cache: noCache ? 'no-store' : 'default',
    });
    if(!res.ok){
      let msg = `${res.status} ${res.statusText}`;
      try {
        const e = await res.json();
        // Backend may return detail as a string OR as a structured object
        // (e.g. { message: "...", missing_fields: [...] }).
        // Coerce both to a human-readable string so callers never see "[object Object]".
        const raw = e.detail ?? e.message ?? e.error ?? null;
        if(raw !== null && raw !== undefined){
          if(typeof raw === 'object'){
            // Structured error — build a readable sentence
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

  window.JadeerAPI = { api, supabase, getToken, setToken, getUser, setUser };
})();
