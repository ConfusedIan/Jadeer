(function(){
  const routes = {};
  function register(path, handler){ routes[path] = handler; }

  // Path matcher supports `/foo/:id`
  function match(hash){
    const clean = hash.replace(/^#/,'').split('?')[0] || '/';
    for(const pattern of Object.keys(routes)){
      const pParts = pattern.split('/'); const hParts = clean.split('/');
      if(pParts.length!==hParts.length) continue;
      const params = {}; let ok = true;
      for(let i=0;i<pParts.length;i++){
        if(pParts[i].startsWith(':')) params[pParts[i].slice(1)] = decodeURIComponent(hParts[i]);
        else if(pParts[i]!==hParts[i]){ ok=false; break; }
      }
      if(ok) return { handler:routes[pattern], params };
    }
    return null;
  }

  async function render(){
    const hash = location.hash || '#/login';
    const route = match(hash);
    const root = document.getElementById('app-root');
    if(!route){ root.innerHTML = '<div class="empty"><div class="empty-icon">🔍</div><h3>Page not found</h3></div>'; return; }
    root.innerHTML = '<div class="page-loader"><div class="spinner"></div></div>';
    try {
      await route.handler(route.params, root);
      window.JadeerI18n.applyTranslations(root);
    } catch(e){
      console.error(e);
      root.innerHTML = `<div class="empty"><h3>Error loading page</h3><p>${e.message}</p></div>`;
    }
  }

  function go(path){ location.hash = path; }

  window.addEventListener('hashchange', render);
  window.addEventListener('langchange', render);

  window.JadeerRouter = { register, render, go };
})();
