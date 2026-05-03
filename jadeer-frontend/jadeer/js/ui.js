(function(){
  // Toast
  function toast(msg, type='info', ttl=3500){
    let host = document.querySelector('.toast-host');
    if(!host){ host=document.createElement('div'); host.className='toast-host'; document.body.appendChild(host); }
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    host.appendChild(el);
    setTimeout(()=>{ el.style.opacity='0'; el.style.transition='opacity .2s'; setTimeout(()=>el.remove(),200); }, ttl);
  }

  // Modal
  function modal({ title, body, footer, size }){
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const m = document.createElement('div');
    m.className = 'modal' + (size==='lg'?' modal-lg':'');
    m.innerHTML = `
      <div class="modal-header">
        <h3>${title||''}</h3>
        <button class="modal-close" aria-label="Close">✕</button>
      </div>
      <div class="modal-body"></div>
      ${footer?'<div class="modal-footer"></div>':''}
    `;
    overlay.appendChild(m);
    document.body.appendChild(overlay);
    const bodyEl = m.querySelector('.modal-body');
    if(typeof body==='string') bodyEl.innerHTML = body; else if(body) bodyEl.appendChild(body);
    if(footer){
      const f = m.querySelector('.modal-footer');
      if(typeof footer==='string') f.innerHTML = footer; else f.appendChild(footer);
    }
    function close(){ overlay.classList.remove('open'); setTimeout(()=>overlay.remove(),200); }
    m.querySelector('.modal-close').onclick = close;
    overlay.addEventListener('click',e=>{ if(e.target===overlay) close(); });
    requestAnimationFrame(()=>overlay.classList.add('open'));
    return { close, root:m, body:bodyEl };
  }

  // Simple confirm
  function confirmDialog({ title='Confirm', message, confirmText='Confirm', danger=false } = {}){
    return new Promise(resolve=>{
      const foot = document.createElement('div');
      foot.innerHTML = `<button class="btn btn-ghost" data-cancel>Cancel</button>
        <button class="btn ${danger?'btn-danger':'btn-primary'}" data-ok>${confirmText}</button>`;
      const m = modal({ title, body:`<p style="color:var(--text2)">${message||''}</p>`, footer: foot });
      foot.querySelector('[data-cancel]').onclick = ()=>{ m.close(); resolve(false); };
      foot.querySelector('[data-ok]').onclick = ()=>{ m.close(); resolve(true); };
    });
  }

  // Element factory
  function el(html){
    const t = document.createElement('template');
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  // Initials from name
  function initials(name){
    if(!name) return '?';
    return name.trim().split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();
  }

  window.JadeerUI = { toast, modal, confirmDialog, el, initials };
})();
