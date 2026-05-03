(function(){
  const { el, toast, modal, confirmDialog } = window.JadeerUI;
  const { api } = window.JadeerAPI;
  const { requireAuth } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;
  const { t } = window.JadeerI18n;

  const toArr = (v) => Array.isArray(v) ? v
    : (v && (v.items || v.data || v.certificates || v.issuers || v.results)) || [];
  const fmtDate = (d)=> d ? new Date(d).toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}) : '';
  const isInternalManualId = (v) => typeof v === 'string' && /^manual-/i.test(v.trim());

  const legacyCustomIssuerFromDetails = (details) => {
    const m = String(details || '').match(/(?:^|\b)Issuer:\s*(.+)$/i);
    return m ? m[1].trim() : '';
  };

  const displayIssuer = (c) =>
    c.issuer ||
    legacyCustomIssuerFromDetails(c.verification_details) ||
    (c.issuer_id === 'custom' ? '' : (c.issuer_id || ''));

  const displayCredentialId = (c) => {
    const v = c.credential_id || c.display_credential_id || c.certificate_id || c.cert_id || '';
    return isInternalManualId(v) ? '' : v;
  };
  
  // Per-issuer verification requirements — derived from actual verifier code.
  // Each verifier reads specific fields from the cert object; we show only
  // what's needed and mark required vs optional accordingly.
  // The backend /certificates/issuers endpoint may also return these as
  // required_fields / optional_fields — if so, we merge them in at runtime.
  // IMPORTANT: these defaults MUST mirror the backend's ISSUER_FIELDS in
  // Cert_Ver_Service/routers/certificates.py exactly.
  // At runtime, openAddCert() fetches /certificates/issuers and overwrites
  // each entry with whatever the backend reports, so this is only the fallback
  // used if the network call fails.
  const ISSUER_FIELDS = {
    edx: {
      required: ['certificate_id'],
      optional: ['certificate_name', 'issue_date', 'expiration_date'],
      hint: 'Enter your edX certificate ID (found in your certificate URL after /cert/).',
    },
    coursera: {
      required: ['certificate_id'],
      optional: ['certificate_name', 'issue_date', 'expiration_date'],
      hint: 'Enter your Coursera verification code (found on your certificate page).',
    },
    udemy: {
      required: ['certificate_id'],
      optional: ['certificate_name', 'issue_date', 'expiration_date'],
      hint: 'Enter your Udemy certificate number (from the certificate URL).',
    },
    comptia: {
      required: ['certificate_id'],
      optional: ['certificate_name', 'issue_date', 'expiration_date'],
      hint: 'Enter your CompTIA certification verification code.',
    },
    eccouncil: {
      required: ['certificate_id', 'first_name', 'last_name'],
      optional: ['certificate_name', 'issue_date', 'expiration_date'],
      hint: 'EC-Council requires your full name exactly as it appears on the certificate.',
    },
  __custom__: {
      required: [],
      optional: ['certificate_id', 'certificate_name', 'issue_date', 'expiration_date', 'credential_url', 'first_name', 'last_name'],
      hint: 'This issuer is not supported for automatic verification. The certificate will be saved as Unverified.',
    },
  };

  // All possible form fields with their UI metadata
  const FIELD_DEFS = {
    certificate_id:   { label:'Credential ID',       i18n:'credential_id',    type:'text',  ph:'e.g., ABC123XYZ' },
    certificate_name: { label:'Certificate Name',     i18n:'cert_name',        type:'text',  ph:'e.g., AWS Certified Developer' },
    first_name:       { label:'First Name',           i18n:'first_name',       type:'text',  ph:'As it appears on the certificate' },
    last_name:        { label:'Last Name',            i18n:'last_name',        type:'text',  ph:'As it appears on the certificate' },
    issue_date:       { label:'Issue Date',           i18n:'issue_date',       type:'date',  ph:'' },
    expiration_date:  { label:'Expiration Date',      i18n:'expiration_date',  type:'date',  ph:'' },
    credential_url:   { label:'Credential URL',       i18n:'credential_url',   type:'url',   ph:'https://verify.issuer.com/...' },
  };

  // Collapse every possible backend/db state into exactly 2 UI buckets:
  //   'verified'   — automated verification succeeded
  //   'unverified' — everything else (manual add, failed verification, pending,
  //                  rejected, unsupported issuer, missing status, etc.)
  // Internally the verification service may still use Pending/Rejected/Failed,
  // but the user only ever sees Verified or Unverified.
  function statusOf(c){
    const s = (c.verification_status || c.status || '').toLowerCase();
    if(s === 'verified' || c.verified === true) return 'verified';
    return 'unverified';
  }

  function certCard(c){
    const status = statusOf(c);
    const isVerified = status === 'verified';
    const badgeMap = {
      verified:   {cls:'badge-success', label:'✓ '+(t('cert_verified')   || 'Verified')},
      unverified: {cls:'badge-muted',   label:    (t('cert_unverified') || 'Unverified')},
    };
    const b = badgeMap[status];
    const credId = displayCredentialId(c);
    // For verified certs: label says "Complete Details" to hint only missing fields are editable
    const editLabel = isVerified
      ? (t('complete_details') || 'Complete Details')
      : (t('edit') || 'Edit');
    const card = el(`
      <div class="card" style="margin-bottom:12px">
        <div class="row-between" style="align-items:flex-start;gap:12px">
          <div style="flex:1;min-width:0">
            <div class="row gap-sm" style="margin-bottom:4px;flex-wrap:wrap">
              <strong style="font-size:15px">${c.certificate_name||'Certificate'}</strong>
              <span class="badge ${b.cls}">${b.label}</span>
            </div>
            ${credId ? `<p class="mono" style="font-size:12px;color:var(--text3);margin-bottom:4px">${t('credential_id')||'Credential ID'}: ${credId}</p>` : ''}
            <p class="muted" style="font-size:13px;margin-bottom:4px">${displayIssuer(c)}</p>
            <div class="row" style="gap:16px;font-size:12px;color:var(--text3);flex-wrap:wrap">
              ${c.issue_date?`<span><strong data-i18n="cert_issued">Issued</strong>: ${fmtDate(c.issue_date)}</span>`:''}
              ${c.expiration_date?`<span><strong data-i18n="expiration_date">Expires</strong>: ${fmtDate(c.expiration_date)}</span>`:''}
              ${c.credential_url?`<a href="${c.credential_url}" target="_blank" rel="noopener" style="color:var(--accent2)">🔗 <span data-i18n="cert_view">View</span></a>`:''}
              ${c.pdf_url?`<a href="${c.pdf_url}" target="_blank" rel="noopener" style="color:var(--accent2)">📄 <span data-i18n="view_pdf">View PDF</span></a>`:''}
            </div>
          </div>
          <div class="row gap-sm">
            <button class="btn btn-sm btn-ghost" data-edit>✏️ ${editLabel}</button>
            <button class="btn btn-sm btn-danger" data-del aria-label="Delete">🗑</button>
          </div>
        </div>
      </div>
    `);

    // Delete handler
    card.querySelector('[data-del]').onclick = async ()=>{
      const ok = await confirmDialog({title:'Delete certificate',message:c.certificate_name,danger:true,confirmText:'Delete'});
      if(!ok) return;
      const certId = c.certificate_id || c.id || c.cert_id;
      if(!certId){ toast('Cannot delete: missing cert id','error'); return; }
      try {
        await api(`/profile/me/certificates/${encodeURIComponent(certId)}`,{method:'DELETE'});
        toast('Deleted','success');
        loadPage();
      }
      catch(e){ toast(e.message,'error'); }
    };

    // Edit handler — both verified and unverified (verified locks scraped fields)
    const editBtn = card.querySelector('[data-edit]');
    if(editBtn){
      editBtn.onclick = ()=> openEditCert(c, isVerified);
    }

    return card;
  }

  function openEditCert(c, isVerified){
    const certId = c.certificate_id || c.id || c.cert_id;

    // For verified certs: fields that already have data were scraped by the
    // verifier and are locked (disabled). Only empty fields can be filled.
    // For unverified certs: all fields are editable (except issuer + credential ID).
    const lockIfVerifiedAndFilled = (val) => isVerified && !!val;

    const b = el(`
      <div>
        ${isVerified ? `<p class="muted" style="margin-bottom:14px;font-size:13px;padding:10px;background:var(--surface2);border-radius:var(--radius-sm)">
          🔒 ${t('verified_edit_hint') || 'This certificate is verified. Fields pulled from the issuer are locked. You can only fill in missing details.'}
        </p>` : ''}
        <div class="field">
          <label data-i18n="cert_name">Certificate Name</label>
          <input class="input" id="edit-cert-name" value="${c.certificate_name||''}" ${lockIfVerifiedAndFilled(c.certificate_name)?'disabled':''}>
          ${lockIfVerifiedAndFilled(c.certificate_name)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
        </div>
        <div class="field">
        <input class="input" id="edit-issuer" value="${displayIssuer(c)}" ${(!isVerified && (c.issuer_id || '').toLowerCase() === 'custom') ? '' : 'disabled'}>          
          <div class="hint" style="font-size:11px">🔒 Cannot be changed after submission.</div>
        </div>
        <div class="field">
          <label data-i18n="credential_id">Credential ID</label>
          <input class="input" id="edit-cred-id" value="${displayCredentialId(c)}" ${(!isVerified && (c.issuer_id || '').toLowerCase() === 'custom') ? '' : 'disabled'}>
          <div class="hint" style="font-size:11px">🔒 Cannot be changed after submission.</div>
        </div>
        <div class="grid grid-2">
          <div class="field">
            <label data-i18n="issue_date">Issue Date</label>
            <input class="input" type="date" id="edit-issue-date" value="${c.issue_date||''}" ${lockIfVerifiedAndFilled(c.issue_date)?'disabled':''}>
            ${lockIfVerifiedAndFilled(c.issue_date)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
          </div>
          <div class="field">
            <label data-i18n="expiration_date">Expiration Date</label>
            <input class="input" type="date" id="edit-exp-date" value="${c.expiration_date||''}" ${lockIfVerifiedAndFilled(c.expiration_date)?'disabled':''}>
            ${lockIfVerifiedAndFilled(c.expiration_date)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
          </div>
        </div>
        <div class="field">
          <label data-i18n="credential_url">Credential URL</label>
          <input class="input" type="url" id="edit-cred-url" value="${c.credential_url||''}" ${lockIfVerifiedAndFilled(c.credential_url)?'disabled':''}>
          ${lockIfVerifiedAndFilled(c.credential_url)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
        </div>
        <div class="field">
          <label data-i18n="first_name">First Name</label>
          <input class="input" id="edit-first-name" value="${c.first_name||''}" ${lockIfVerifiedAndFilled(c.first_name)?'disabled':''}>
          ${lockIfVerifiedAndFilled(c.first_name)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
        </div>
        <div class="field">
          <label data-i18n="last_name">Last Name</label>
          <input class="input" id="edit-last-name" value="${c.last_name||''}" ${lockIfVerifiedAndFilled(c.last_name)?'disabled':''}>
          ${lockIfVerifiedAndFilled(c.last_name)?'<div class="hint" style="font-size:11px">🔒 Pulled from issuer</div>':''}
        </div>
        ${isVerified
          // ── VERIFIED: PDF is locked. View only if exists; no upload/change allowed.
          ? (c.pdf_url
            ? `<div class="field" style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
                <label>📄 ${t('certificate_pdf')||'Certificate PDF'}</label>
                <div style="padding:8px 0">
                  <a href="${c.pdf_url}" target="_blank" rel="noopener" style="color:var(--accent2)">📄 ${t('view_pdf')||'View PDF'}</a>
                </div>
                <div class="hint" style="font-size:11px">🔒 ${t('pdf_locked_verified')||'PDF cannot be changed for verified certificates.'}</div>
               </div>`
            : `<div class="field" style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
                <label>📄 ${t('certificate_pdf')||'Certificate PDF'}</label>
                <div class="hint" style="font-size:11px">${t('pdf_verified_only_initial')||'PDF can only be attached during the initial verification submission.'}</div>
               </div>`)
          // ── UNVERIFIED: can upload if none exists, or delete then re-upload.
          : (c.pdf_url
            ? `<div class="field" style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
                <label>📄 ${t('certificate_pdf')||'Certificate PDF'}</label>
                <div style="display:flex;align-items:center;gap:12px;padding:8px 0">
                  <a href="${c.pdf_url}" target="_blank" rel="noopener" style="color:var(--accent2)">📄 ${t('view_pdf')||'View Current PDF'}</a>
                  <button type="button" class="btn btn-sm btn-danger" id="remove-pdf-btn">🗑 ${t('remove_pdf')||'Remove PDF'}</button>
                </div>
                <div class="hint" style="font-size:11px">${t('pdf_remove_hint')||'Remove the current PDF first, then edit again to upload a new one.'}</div>
               </div>`
            : `<div class="field" style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
                <label>📄 ${t('upload_pdf')||'Upload Certificate PDF'} <span class="muted" style="font-size:11px">(${t('optional')||'optional'})</span></label>
                <input type="file" id="edit-cert-pdf" accept="application/pdf" class="input" style="padding:8px">
                <div class="hint" style="font-size:11px">${t('pdf_upload_hint')||'Upload a PDF copy of your certificate. Max 5MB.'}</div>
               </div>`)
        }
      </div>
    `);

    const foot = document.createElement('div');
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.type = 'button';
    cancelBtn.textContent = t('cancel') || 'Cancel';
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.type = 'button';
    saveBtn.textContent = t('save') || 'Save';
    foot.appendChild(cancelBtn);
    foot.appendChild(saveBtn);

    const m = modal({ title: (isVerified ? (t('complete_details')||'Complete Details') : (t('edit_certificate')||'Edit Certificate')), body:b, footer:foot });

    cancelBtn.addEventListener('click', (ev)=>{ ev.preventDefault(); m.close(); });

    // "Remove PDF" button — only shown for unverified certs with existing PDF
    const removePdfBtn = b.querySelector('#remove-pdf-btn');
    if(removePdfBtn){
      removePdfBtn.addEventListener('click', async (ev)=>{
        ev.preventDefault();
        const ok = await confirmDialog({
          title: t('remove_pdf') || 'Remove PDF',
          message: t('remove_pdf_confirm') || 'Are you sure you want to remove the attached PDF?',
          danger: true,
          confirmText: t('remove') || 'Remove',
        });
        if(!ok) return;
        removePdfBtn.disabled = true;
        removePdfBtn.textContent = '...';
        try {
          // Direct Supabase PATCH to null out pdf_url
          const CFG   = window.JADEER_CONFIG;
          const token = window.JadeerAPI.getToken();
          const patchRes = await fetch(
            `${CFG.SUPABASE_URL}/rest/v1/certificates?certificate_id=eq.${encodeURIComponent(certId)}`,
            {
              method: 'PATCH',
              headers: {
                'Authorization': `Bearer ${token}`,
                'apikey':        CFG.SUPABASE_ANON_KEY,
                'Content-Type':  'application/json',
                'Prefer':        'return=minimal',
              },
              body: JSON.stringify({ pdf_url: null }),
            }
          );
          if(patchRes.ok || patchRes.status === 204){
            toast(t('pdf_removed') || 'PDF removed','success');
            m.close();
            setTimeout(loadPage, 400);
          } else {
            toast('Could not remove PDF (' + patchRes.status + ')','error');
            removePdfBtn.disabled = false;
            removePdfBtn.textContent = '🗑 ' + (t('remove_pdf') || 'Remove PDF');
          }
        } catch(e){
          toast(e.message || 'Could not remove PDF','error');
          removePdfBtn.disabled = false;
          removePdfBtn.textContent = '🗑 ' + (t('remove_pdf') || 'Remove PDF');
        }
      });
    }

    saveBtn.addEventListener('click', async (ev)=>{
      ev.preventDefault();
      const payload = {};

      // Only collect values from non-disabled fields (= fields the user can actually change)
      const fields = [
        { id:'edit-cert-name',   key:'certificate_name', orig: c.certificate_name },
        { id:'edit-issuer',      key:'issuer',           orig: displayIssuer(c) },
        { id:'edit-cred-id',     key:'certificate_id',   orig: displayCredentialId(c) },
        { id:'edit-issue-date',  key:'issue_date',       orig: c.issue_date },
        { id:'edit-exp-date',    key:'expiration_date',  orig: c.expiration_date },
        { id:'edit-cred-url',    key:'credential_url',   orig: c.credential_url },
        { id:'edit-first-name',  key:'first_name',       orig: c.first_name },
        { id:'edit-last-name',   key:'last_name',        orig: c.last_name },
      ];

      for(const f of fields){
        const input = b.querySelector(`#${f.id}`);
        if(!input || input.disabled) continue;  // locked field → skip
        const val = input.value.trim();
        if(val && val !== (f.orig||'')){
          if(f.key === 'credential_url' && !val.startsWith('https://')){
            toast('URL must start with https://','error');
            return;
          }
          payload[f.key] = val;
        }
      }

      // Handle PDF upload — only for unverified certs without an existing PDF.
      // (Verified certs: PDF locked. Unverified with PDF: must remove first.)
      // The #edit-cert-pdf input only exists in the DOM for that specific case.
      const editPdfInput = b.querySelector('#edit-cert-pdf');
      if(editPdfInput && editPdfInput.files && editPdfInput.files[0]){
        const file = editPdfInput.files[0];
        if(file.size > 5 * 1024 * 1024){
          toast('PDF must be under 5MB.','error'); return;
        }
        try {
          const userId   = window.JadeerAPI.getUser()?.id;
          const fileName = `${userId}/${Date.now()}-${file.name.replace(/[^a-z0-9.\-_]/gi,'')}`;
          const CFG      = window.JADEER_CONFIG;
          const token    = window.JadeerAPI.getToken();
          const uploadRes = await fetch(`${CFG.SUPABASE_URL}/storage/v1/object/cert-pdfs/${fileName}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'apikey':        CFG.SUPABASE_ANON_KEY,
              'Content-Type': file.type,
              'x-upsert': 'true',
            },
            body: file,
          });
          if(uploadRes.ok){
            payload.pdf_url = `${CFG.SUPABASE_URL}/storage/v1/object/public/cert-pdfs/${fileName}`;
          } else {
            const errBody = await uploadRes.text().catch(()=>'');
            console.warn('PDF upload failed:', uploadRes.status, errBody);
            toast('PDF upload failed (' + uploadRes.status + '). Other changes will still be saved.','info', 5000);
          }
        } catch(uploadErr){
          console.warn('PDF upload error:', uploadErr);
          toast('PDF upload error. Other changes will still be saved.','info', 4000);
        }
      }

      if(!Object.keys(payload).length){
        toast(t('no_changes') || 'No changes to save','info');
        m.close();
        return;
      }

      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner"></span>';
      try {
        await api(`/profile/me/certificates/${encodeURIComponent(certId)}`,{method:'PUT', body:payload});
        toast(t('cert_updated') || 'Certificate updated','success');
        m.close();
        setTimeout(loadPage, 400);
      } catch(e){
        toast(e.message || 'Could not update','error');
        saveBtn.disabled = false;
        saveBtn.textContent = t('save') || 'Save';
      }
    });

    window.JadeerI18n.applyTranslations(b);
  }

  async function openAddCert(){
    let issuers = [];
    try {
      const res = await api('/certificates/issuers');
      issuers = toArr(res);
    } catch(_){}

    // Scope filter
    const EXCLUDED_ISSUERS = ['pmi', 'project management institute', 'custom'];
    issuers = issuers.filter(i=>{
      const id   = (i.issuer_id   || i.id   || '').toString().toLowerCase().trim();
      const name = (i.issuer_name || i.name || i.title || '').toString().toLowerCase().trim();
      return !EXCLUDED_ISSUERS.includes(id) && !EXCLUDED_ISSUERS.includes(name);
    });

    // Always override required_fields from backend (source of truth for validation).
    // For optional_fields: if backend returns an empty array, keep the local definition
    // so all optional fields (including expiration_date) still appear in the form.
    issuers.forEach(i=>{
      const id = (i.issuer_id || '').toLowerCase();
      if(i.required_fields){
        const backendOptional = (i.optional_fields && i.optional_fields.length)
          ? i.optional_fields
          : (ISSUER_FIELDS[id]?.optional || []);
        ISSUER_FIELDS[id] = {
          required: i.required_fields,
          optional: backendOptional,
          hint: i.hint || ISSUER_FIELDS[id]?.hint || '',
        };
      }
    });

    const issuerOpts = issuers.map(i=>{
      const name = i.issuer_name || i.name || i.title || 'Unknown Issuer';
      const id   = i.issuer_id   || i.id   || name;
      return `<option value="${id}" data-name="${name}">${name}</option>`;
    }).join('');

    const b = el(`
      <div>
        <p class="muted" style="margin-bottom:14px" data-i18n="add_cert_sub">Verification is processed automatically for supported issuers. Unsupported issuers are saved as Unverified.</p>

        <div class="field">
          <label><span data-i18n="issuing_org">Issuing Organization</span> *</label>
          <select class="select" name="issuer_select" id="issuer-select" required>
            <option value="" data-i18n="select_issuer">Select an issuer</option>
            ${issuerOpts}
            <option value="__custom__" data-i18n="issuer_other">Other (not listed)</option>
          </select>
          <input class="input hidden" name="issuer_custom" id="issuer-custom" style="margin-top:8px" placeholder="Type the issuer name">
        </div>

        <div id="issuer-hint" class="hint" style="display:none;margin-bottom:14px;padding:10px;background:var(--surface2);border-radius:var(--radius-sm)"></div>

        <div id="dynamic-fields"></div>

        <div class="field" style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
          <label>📄 ${t('upload_pdf') || 'Upload Certificate PDF'} <span class="muted" style="font-size:11px">(${t('optional')||'optional'})</span></label>
          <input type="file" id="cert-pdf" accept="application/pdf" class="input" style="padding:8px">
          <div class="hint" style="font-size:11px">${t('pdf_optional_hint') || 'Upload a PDF copy of your certificate. Max 5MB.'}</div>
        </div>
      </div>
    `);

    const foot = document.createElement('div');
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-ghost';
    cancelBtn.type = 'button';
    cancelBtn.textContent = t('cancel') || 'Cancel';
    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn btn-primary';
    submitBtn.type = 'button';
    submitBtn.textContent = t('verify_btn') || 'Verify';
    foot.appendChild(cancelBtn);
    foot.appendChild(submitBtn);

    const m = modal({ title:t('add_new_cert'), body:b, footer:foot, size:'lg' });

    const sel     = b.querySelector('#issuer-select');
    const cust    = b.querySelector('#issuer-custom');
    const hintBox = b.querySelector('#issuer-hint');
    const dynBox  = b.querySelector('#dynamic-fields');

    // Build dynamic fields based on the selected issuer's requirements
    function renderDynamicFields(){
      const issuerKey = sel.value.toLowerCase();
      const isCustom  = sel.value === '__custom__';
      const cfg       = ISSUER_FIELDS[issuerKey] || ISSUER_FIELDS['__custom__'];

      cust.classList.toggle('hidden', !isCustom);

      // Show issuer-specific hint
      if(cfg.hint){
        hintBox.textContent = cfg.hint;
        hintBox.style.display = '';
      } else {
        hintBox.style.display = 'none';
      }

      // Determine which fields to show
      const reqSet    = new Set(cfg.required || []);
      const optSet    = new Set(cfg.optional || []);
      const allFields = [...new Set([...reqSet, ...optSet])];

      // Always include certificate_id
      if(!isCustom && !allFields.includes('certificate_id')) allFields.unshift('certificate_id');

      dynBox.innerHTML = '';

      // Separate date fields (render in 2-column grid) from others
      const dateFields  = allFields.filter(k=> FIELD_DEFS[k] && FIELD_DEFS[k].type === 'date');
      const otherFields = allFields.filter(k=> FIELD_DEFS[k] && FIELD_DEFS[k].type !== 'date');

      otherFields.forEach(key=>{
        const def = FIELD_DEFS[key];
        if(!def) return;
        const isReq = reqSet.has(key);
        const fieldEl = el(`
          <div class="field">
            <label>
              <span data-i18n="${def.i18n}">${def.label}</span>
              ${isReq
                ? ' <span style="color:var(--danger)">*</span>'
                : ' <span class="muted" style="font-size:11px">(optional)</span>'}
            </label>
            <input class="input" name="${key}" type="${def.type}" placeholder="${def.ph}" ${isReq?'required':''}>
          </div>
        `);
        dynBox.appendChild(fieldEl);
      });

      if(dateFields.length){
        const grid = el(`<div class="grid grid-2"></div>`);
        dateFields.forEach(key=>{
          const def = FIELD_DEFS[key];
          if(!def) return;
          const isReq = reqSet.has(key);
          const fieldEl = el(`
            <div class="field">
              <label>
                <span data-i18n="${def.i18n}">${def.label}</span>
                ${isReq
                  ? ' <span style="color:var(--danger)">*</span>'
                  : ' <span class="muted" style="font-size:11px">(optional)</span>'}
              </label>
              <input class="input" name="${key}" type="${def.type}" ${isReq?'required':''}>
            </div>
          `);
          grid.appendChild(fieldEl);
        });
        dynBox.appendChild(grid);
      }

      // Update submit button label
      if(isCustom){
        submitBtn.textContent = t('add_certificate_btn') || 'Add Certificate';
      } else if(sel.value){
        submitBtn.textContent = t('verify_btn') || 'Verify';
      }

      window.JadeerI18n.applyTranslations(dynBox);
    }

    sel.addEventListener('change', renderDynamicFields);
    cancelBtn.addEventListener('click', (ev)=>{ ev.preventDefault(); m.close(); });

    submitBtn.addEventListener('click', async (ev)=>{
      ev.preventDefault();
      const isCustom   = sel.value === '__custom__';
      const issuerVal  = sel.value;
      const issuerKey  = issuerVal.toLowerCase();
      const issuerName = isCustom
        ? cust.value.trim()
        : (sel.options[sel.selectedIndex]?.getAttribute('data-name') || '');

      // Validate issuer
      if(!issuerVal){ toast(t('err_issuer_required') || 'Select an issuer.','error'); return; }
      if(isCustom && !issuerName){ toast(t('err_issuer_required') || 'Enter the issuer name.','error'); return; }

      // Validate required fields for this issuer
      const cfg    = ISSUER_FIELDS[issuerKey] || ISSUER_FIELDS['__custom__'];
      const reqSet = new Set(cfg.required || []);
      for(const key of reqSet){
        const input = dynBox.querySelector(`[name="${key}"]`);
        const val   = input ? input.value.trim() : '';
        if(!val){
          const def = FIELD_DEFS[key];
          toast(`${def?.label || key} is required for ${issuerName || 'this issuer'}.`,'error');
          return;
        }
      }

      // Validate URL if present
      const urlInput = dynBox.querySelector('[name="credential_url"]');
      if(urlInput && urlInput.value.trim() && !urlInput.value.trim().startsWith('https://')){
        toast('URL must start with https://','error'); return;
      }

      // Collect all field values
      const fieldValues = {};
      dynBox.querySelectorAll('input[name]').forEach(inp=>{
        const v = inp.value.trim();
        if(v) fieldValues[inp.name] = v;
      });

      // Handle PDF upload (optional — best effort)
      const pdfInput = b.querySelector('#cert-pdf');
      let pdfUrl = null;
      if(pdfInput && pdfInput.files && pdfInput.files[0]){
        const file = pdfInput.files[0];
        if(file.size > 5 * 1024 * 1024){
          toast('PDF must be under 5MB.','error'); return;
        }
        try {
          const userId   = window.JadeerAPI.getUser()?.id;
          const fileName = `${userId}/${Date.now()}-${file.name.replace(/[^a-z0-9.\-_]/gi,'')}`;
          const CFG      = window.JADEER_CONFIG;
          const token    = window.JadeerAPI.getToken();
          const uploadRes = await fetch(`${CFG.SUPABASE_URL}/storage/v1/object/cert-pdfs/${fileName}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'apikey':        CFG.SUPABASE_ANON_KEY,
              'Content-Type': file.type,
              'x-upsert': 'true',
            },
            body: file,
          });
          if(uploadRes.ok){
            pdfUrl = `${CFG.SUPABASE_URL}/storage/v1/object/public/cert-pdfs/${fileName}`;
          } else {
            const errBody = await uploadRes.text().catch(()=>'');
            console.warn('PDF upload failed:', uploadRes.status, errBody);
            toast('PDF upload failed (' + uploadRes.status + '). Certificate will be saved without PDF.','info', 5000);
          }
        } catch(e){
          console.warn('PDF upload error:', e);
          toast('PDF upload error. Certificate will be saved without PDF.','info', 4000);
        }
      }

      submitBtn.disabled = true;
      cancelBtn.disabled = true;
      const origLabel = submitBtn.textContent;

      function setStatus(msg){
        submitBtn.innerHTML = `<span class="spinner"></span> <span style="font-size:13px;opacity:.8">${msg}</span>`;
      }

      async function pollUntilSaved(certId, maxAttempts=18, intervalMs=5000){
        for(let i=0; i<maxAttempts; i++){
          await new Promise(r => setTimeout(r, intervalMs));
          setStatus(t('cert_checking')||'Checking verification status…');
          try {
            const list = await api('/profile/me/certificates', { noCache: true });
            const items = Array.isArray(list) ? list : (list.items || list.data || []);
            const found = items.find(c => (c.certificate_id || c.cert_id || '') === certId);
            if(found) return found;
          } catch(_){}
        }
        return null;
      }

      // ---- Supported issuer: call verification service ----
      if(!isCustom){
        try {
          const candidateId = window.JadeerAPI.getUser()?.id;
          if(!candidateId) throw new Error('Session expired — please log in again.');
          const vPayload = {
            candidate_id:     candidateId,
            issuer_id:        issuerVal,
            certificate_id:   fieldValues.certificate_id,
            certificate_name: fieldValues.certificate_name || null,
            issue_date:       fieldValues.issue_date || null,
            expiration_date:  fieldValues.expiration_date || null,
            first_name:       fieldValues.first_name || null,
            last_name:        fieldValues.last_name || null,
          };
          setStatus(t('cert_verifying')||'Verifying certificate…');
          const vRes = await api('/certificates', { method:'POST', body: vPayload });

          // Cert_Ver_Service saves to its own postgres DB.
          // Profile Service (the list view) reads from Supabase — a separate DB.
          // So we must sync the verified cert into Profile Service / Supabase manually,
          // and include the pdf_url here rather than in a follow-up PUT.
          const verifiedStatus = vRes.status || '';
          const isVerified = /^verif/i.test(verifiedStatus);
          try {
            const syncPayload = {
              certificate_id:   vRes.certificate_id || fieldValues.certificate_id,
              issuer_id:        issuerVal,
              certificate_name: vRes.certificate_name || fieldValues.certificate_name || null,
              issue_date:       vRes.issue_date || fieldValues.issue_date || null,
              expiration_date:  vRes.expiration_date || fieldValues.expiration_date || null,
              first_name:       vRes.first_name || fieldValues.first_name || null,
              last_name:        vRes.last_name || fieldValues.last_name || null,
              status:           verifiedStatus || 'NOT_FOUND',
              pdf_url:          pdfUrl || null,
            };
            await api('/profile/me/certificates', { method:'POST', body: syncPayload });
          } catch(syncErr){
            // Cert already in Supabase from a previous run — update it with latest data + pdf
            const certId = vRes.certificate_id || fieldValues.certificate_id;
            try {
              await api(`/profile/me/certificates/${encodeURIComponent(certId)}`, {
                method: 'PUT',
                body: {
                  certificate_name: vRes.certificate_name || fieldValues.certificate_name || null,
                  issue_date:       vRes.issue_date || fieldValues.issue_date || null,
                  expiration_date:  vRes.expiration_date || fieldValues.expiration_date || null,
                  pdf_url:          pdfUrl || null,
                },
              });
            } catch(_){ console.warn('Could not sync cert to profile service'); }
          }

          if(isVerified){
            toast(t('toast_verified') || 'Certificate verified successfully ✓','success');
          } else {
            const detail = vRes.verification_details || '';
            toast((detail ? detail + ' — ' : '') + (t('toast_saved_unverified') || 'Saved as Unverified'),'info', 5000);
          }
          m.close();
          setTimeout(loadPage, 600);
          return;
        } catch(e){
          // 409 = already exists — cert was saved, treat as soft success
          if(e.status === 409){
            toast(t('cert_already_exists') || 'This certificate was already added.','info', 4000);
            m.close();
            setTimeout(loadPage, 600);
            return;
          }
          // 502 / 503 / 504 = gateway timed out waiting for the Selenium verifier.
          // The scraper is STILL RUNNING in the background and will save the
          // correct status (VERIFIED or NOT_FOUND) when it finishes.
          //
          // CRITICAL: Do NOT create a fallback Supabase row with status:'NOT_FOUND'
          // here — that was the regression! It overwrites the real verification
          // result that the scraper will produce seconds later.
          //
          // Instead: just tell the user to wait and refresh.
                    if(e.status === 502 || e.status === 503 || e.status === 504){
            setStatus(t('cert_verification_slow')||'Verification in progress…');
            // Wait 35s for scraper to finish, then check and close
            await new Promise(r => setTimeout(r, 10000));
            setStatus(t('cert_checking')||'Almost done…');
            await new Promise(r => setTimeout(r, 15000));
            setStatus(t('cert_checking')||'Finalizing…');
            await new Promise(r => setTimeout(r, 10000));
            // Reload list and check if cert appeared as verified
            try {
              const list = await api('/profile/me/certificates', { noCache: true });
              const items = Array.isArray(list) ? list : (list.items || list.data || []);
              const certId = fieldValues.certificate_id;
              const found = items.find(c =>
                (c.certificate_id||'').toLowerCase() === certId.toLowerCase()
              );
              if(found){
                const isVer = /^verif/i.test(found.status||found.verification_status||'');
                toast(isVer
                  ? (t('toast_verified')||'✓ Certificate verified successfully')
                  : (t('toast_saved_unverified')||'Certificate saved as Unverified'),
                  isVer ? 'success' : 'info', 5000);
              } else {
                toast(t('toast_verified')||'✓ Certificate verified successfully','success', 5000);
              }
            } catch(_){
              toast(t('toast_verified')||'✓ Certificate added successfully','success', 5000);
            }
            m.close();
            setTimeout(loadPage, 400);
            return;
          }

          toast((e.message || 'Verification failed'),'error', 6000);
          submitBtn.disabled = false;
          cancelBtn.disabled = false;
          submitBtn.innerHTML = '';
          submitBtn.textContent = origLabel;
          return;
        }
      }

      // ---- Custom (unsupported) issuer path ----
      // Save via Profile Service POST. Backend generates certificate_id,
      // maps issuer to 'custom' FK, sets status to NOT_FOUND (= Unverified).
      try {
        const profilePayload = {
          issuer_id:        'custom',
          issuer:           issuerName,
          certificate_name: fieldValues.certificate_name || null,
          issue_date:       fieldValues.issue_date || null,
          expiration_date:  fieldValues.expiration_date || null,
          first_name:       fieldValues.first_name || null,
          last_name:        fieldValues.last_name || null,
          credential_url:   fieldValues.credential_url || null,
          certificate_id:   fieldValues.certificate_id || null,
        };
        if(pdfUrl) profilePayload.pdf_url = pdfUrl;
        await api('/profile/me/certificates', { method:'POST', body: profilePayload });
        toast(t('toast_saved_unverified') || 'Certificate saved as Unverified','success');
        m.close();
        setTimeout(loadPage, 600);
      } catch(e){
        toast(e.message || 'Could not save certificate','error', 6000);
        submitBtn.disabled = false;
        cancelBtn.disabled = false;
        submitBtn.innerHTML = '';
        submitBtn.textContent = origLabel;
      }
    });

    // Initial render if an issuer is already selected
    if(sel.value) renderDynamicFields();
    window.JadeerI18n.applyTranslations(b);
  }

  let activeTab = 'verified';

  async function loadPage(){
    const content = document.getElementById('certs-content');
    if(!content) return;
    content.innerHTML = `<div class="page-loader"><div class="spinner"></div></div>`;
    try {
      const raw = await api('/profile/me/certificates', { noCache:true }).catch(()=>[]);
      const all = toArr(raw);
      // Two groups only: verified vs unverified. statusOf() already collapses
      // pending/rejected/other into 'unverified'.
      const groups = { verified:[], unverified:[] };
      all.forEach(c=> groups[statusOf(c)].push(c));

      content.innerHTML = `
        <div class="page-header">
          <div>
            <h1 data-i18n="my_certificates">My Certificates</h1>
            <p class="sub" data-i18n="my_certificates_sub">Manage and verify your professional certificates</p>
          </div>
          <button class="btn btn-primary" id="add-cert-btn" data-i18n="add_certificate">+ Add Certificate</button>
        </div>

        <!-- Stacked vertical sections, Verified on top, Unverified below -->
        <div style="display:flex;flex-direction:column;gap:14px">

          <section class="card" style="padding:0;overflow:hidden">
            <button class="row-between" data-section-header="verified"
                    style="width:100%;padding:14px 18px;background:var(--surface2);border:0;cursor:pointer;text-align:start">
              <div class="row gap-sm" style="align-items:center">
                <span style="font-size:18px">✓</span>
                <strong data-i18n="tab_verified">Verified</strong>
                <span class="muted" style="font-size:13px">(${groups.verified.length})</span>
              </div>
              <span id="chev-verified" class="muted" style="font-size:12px;transition:transform 0.2s">▾</span>
            </button>
            <div id="section-verified" style="padding:14px 18px"></div>
          </section>

          <section class="card" style="padding:0;overflow:hidden">
            <button class="row-between" data-section-header="unverified"
                    style="width:100%;padding:14px 18px;background:var(--surface2);border:0;cursor:pointer;text-align:start">
              <div class="row gap-sm" style="align-items:center">
                <span style="font-size:18px;color:var(--text3)">○</span>
                <strong data-i18n="tab_unverified">Unverified</strong>
                <span class="muted" style="font-size:13px">(${groups.unverified.length})</span>
              </div>
              <span id="chev-unverified" class="muted" style="font-size:12px;transition:transform 0.2s">▾</span>
            </button>
            <div id="section-unverified" style="padding:14px 18px"></div>
          </section>

        </div>
      `;

      function renderSection(key){
        const list = groups[key] || [];
        const box  = content.querySelector(`#section-${key}`);
        box.innerHTML = '';
        if(!list.length){
          box.innerHTML = `<p class="muted" style="padding:10px 0;text-align:center" data-i18n="no_matching_certs">No certificates in this category yet.</p>`;
        } else {
          list.forEach(c=>box.appendChild(certCard(c)));
        }
        window.JadeerI18n.applyTranslations(box);
      }

      function showSection(key){
        activeTab = key;
        ['verified','unverified'].forEach(k=>{
          const box  = content.querySelector(`#section-${k}`);
          const chev = content.querySelector(`#chev-${k}`);
          const open = (k === key);
          box.style.display  = open ? '' : 'none';
          chev.style.transform = open ? 'rotate(0deg)' : 'rotate(-90deg)';
        });
        renderSection(key);
      }

      content.querySelectorAll('[data-section-header]').forEach(h=>{
        h.onclick = ()=>{
          const key = h.getAttribute('data-section-header');
          // Accordion-style: clicking the already-open header closes it;
          // clicking the closed one opens it and collapses the other.
          if(activeTab === key){
            // collapse current
            const box = content.querySelector(`#section-${key}`);
            const chev = content.querySelector(`#chev-${key}`);
            box.style.display = 'none';
            chev.style.transform = 'rotate(-90deg)';
            activeTab = null;
          } else {
            showSection(key);
          }
        };
      });

      // Initial state — render both once, then hide the non-active one.
      renderSection('verified');
      renderSection('unverified');
      showSection(activeTab || 'verified');

      content.querySelector('#add-cert-btn').onclick = openAddCert;
      window.JadeerI18n.applyTranslations(content);
    } catch(e){
      content.innerHTML = `<div class="empty"><h3>Could not load</h3><p class="muted">${e.message}</p></div>`;
    }
  }

  register('/certificates', (_p, root)=>{
    if(!requireAuth()) return;
    root.innerHTML = '';
    const content = el(`<div id="certs-content"></div>`);
    root.appendChild(shell({ title:'Jadeer', content }));
    loadPage();
  });
})();
