// Wake all Render services in the background as soon as the app loads.
// Render free tier sleeps after 15 minutes — first request after sleep takes
// 30-60s, which causes "Failed to fetch" or upstream timeout errors. By pinging
// the public health endpoints in parallel right at boot, services warm up while
// the user logs in / navigates, so by the time they need real data it's ready.
(function(){
  const ENDPOINTS = [
    // Each Gateway proxy route hits a different downstream service.
    // /health on each forces a wake-up without needing auth.
    '/cv/health',
    '/recommendation/health',
    '/ranking/health',
    '/assessment/skills-list',  // assessment service has no /health, this works
  ];

  function warmup(){
    const base = window.JADEER_CONFIG.API_GATEWAY;
    ENDPOINTS.forEach(path=>{
      // no-cors: we just want to wake the service. The response is opaque,
      // but that's fine — we never read it. This suppresses the CORS spam
      // that appears when the backend's auth middleware returns 401 without
      // CORS headers on the error response.
      fetch(base + path, { method:'GET', mode:'no-cors' })
        .catch(()=>{ /* expected during cold start */ });
    });
  }

  // Run once on initial load
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', warmup);
  } else {
    warmup();
  }
})();
