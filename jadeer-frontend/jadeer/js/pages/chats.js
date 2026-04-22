(function(){
  const { el } = window.JadeerUI;
  const { requireAuth, currentRole } = window.JadeerAuth;
  const { register } = window.JadeerRouter;
  const { render: shell } = window.JadeerShell;

  const CSS = `
    .chat-outer {
      display: flex;
      height: calc(100vh - var(--topbar-h));
      overflow: hidden;
    }

    /* Left panel — conversation list */
    .chat-sidebar {
      width: 300px;
      flex-shrink: 0;
      border-inline-end: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      background: var(--surface);
    }
    .chat-sidebar-header {
      padding: 18px 20px 14px;
      border-bottom: 1px solid var(--border);
    }
    .chat-sidebar-header h3 {
      font-size: 15px;
      font-weight: 700;
      color: var(--text);
      margin: 0 0 12px;
    }
    .chat-search {
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 7px 12px;
    }
    .chat-search svg { opacity: .4; flex-shrink: 0; }
    .chat-search span {
      font-size: 13px;
      color: var(--text3);
    }
    .chat-list {
      flex: 1;
      overflow-y: auto;
      padding: 12px 0;
    }
    .chat-list-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      padding: 32px 20px;
      text-align: center;
    }
    .chat-list-empty-icon {
      font-size: 32px;
      margin-bottom: 12px;
      opacity: .35;
    }
    .chat-list-empty p {
      font-size: 13px;
      color: var(--text3);
      line-height: 1.6;
      margin: 0;
    }

    /* Right panel — chat area */
    .chat-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      background: var(--bg);
    }
    .chat-main-header {
      height: 60px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 24px;
      background: var(--surface);
      flex-shrink: 0;
    }
    .chat-main-header-placeholder {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .chat-main-header-avatar {
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--surface3);
      border: 1px solid var(--border);
    }
    .chat-main-header-text {
      width: 120px; height: 12px; border-radius: 6px;
      background: var(--surface3);
    }

    /* Messages area */
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 32px 24px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .chat-empty-state {
      text-align: center;
      max-width: 360px;
    }
    .chat-empty-icon {
      width: 64px; height: 64px;
      background: linear-gradient(135deg, rgba(124,92,252,.15), rgba(192,132,252,.1));
      border: 1px solid rgba(124,92,252,.2);
      border-radius: 18px;
      display: flex; align-items: center; justify-content: center;
      font-size: 28px;
      margin: 0 auto 20px;
    }
    .chat-empty-state h3 {
      font-size: 16px; font-weight: 600; color: var(--text);
      margin: 0 0 8px;
    }
    .chat-empty-state p {
      font-size: 13px; color: var(--text3); line-height: 1.65; margin: 0;
    }
    .chat-coming-badge {
      display: inline-block;
      margin-top: 16px;
      background: rgba(124,92,252,.1);
      border: 1px solid rgba(124,92,252,.25);
      color: var(--accent2);
      font-size: 11px; font-weight: 600;
      letter-spacing: .05em; text-transform: uppercase;
      padding: 4px 12px; border-radius: 20px;
    }

    /* Composer */
    .chat-composer {
      border-top: 1px solid var(--border);
      padding: 14px 20px;
      background: var(--surface);
      flex-shrink: 0;
    }
    .chat-composer-inner {
      display: flex; align-items: center; gap: 10px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      opacity: .45;
      cursor: not-allowed;
    }
    .chat-composer-inner span {
      flex: 1; font-size: 13px; color: var(--text3);
    }
    .chat-send-icon {
      color: var(--text3);
    }

    @media(max-width:720px){
      .chat-sidebar { width: 100%; }
      .chat-main { display: none; }
    }
  `;

  function injectStyles(){
    if(document.getElementById('chat-shell-styles')) return;
    const s = document.createElement('style');
    s.id = 'chat-shell-styles'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  register('/chats', (_p, root) => {
    if(!requireAuth()) return;
    injectStyles();

    const role = currentRole();
    const isEmployer = role === 'employer';

    // Role-aware copy
    const copy = isEmployer ? {
      title:       'Conversations',
      listEmpty:   'No conversations yet.',
      listSub:     'Candidate conversations will appear here once messaging is enabled.',
      emptyTitle:  'Select a conversation',
      emptySub:    'Once messaging is enabled, you\'ll be able to chat with candidates directly from search results.',
      composerPh:  'Type a message…',
    } : {
      title:       'Messages',
      listEmpty:   'No messages yet.',
      listSub:     'Employers will reach out here once your profile is complete and messaging is enabled.',
      emptyTitle:  'No conversation selected',
      emptySub:    'Once messaging is enabled, your conversations with employers will appear here.',
      composerPh:  'Type a message…',
    };

    root.innerHTML = '';

    const content = document.createElement('div');

    // Shell renders topbar+sidebar — we inject the chat layout into the content slot
    // We override the content padding to flush for chat
    root.appendChild(shell({ title: copy.title, content }));

    // Override content area padding to flush
    const contentEl = root.querySelector('.content');
    if(contentEl){
      contentEl.style.padding = '0';
      contentEl.style.maxWidth = 'none';
    }

    const outer = document.createElement('div');
    outer.className = 'chat-outer';
    outer.innerHTML = `
      <!-- Left: conversation list -->
      <div class="chat-sidebar">
        <div class="chat-sidebar-header">
          <h3>${copy.title}</h3>
          <div class="chat-search">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <span>Search conversations</span>
          </div>
        </div>
        <div class="chat-list">
          <div class="chat-list-empty">
            <div class="chat-list-empty-icon">💬</div>
            <p>${copy.listEmpty}<br>${copy.listSub}</p>
          </div>
        </div>
      </div>

      <!-- Right: chat area -->
      <div class="chat-main">
        <!-- Header placeholder -->
        <div class="chat-main-header">
          <div class="chat-main-header-placeholder">
            <div class="chat-main-header-avatar"></div>
            <div class="chat-main-header-text"></div>
          </div>
        </div>

        <!-- Messages area -->
        <div class="chat-messages">
          <div class="chat-empty-state">
            <div class="chat-empty-icon">💬</div>
            <h3>${copy.emptyTitle}</h3>
            <p>${copy.emptySub}</p>
            <span class="chat-coming-badge">Coming Soon</span>
          </div>
        </div>

        <!-- Composer (disabled) -->
        <div class="chat-composer">
          <div class="chat-composer-inner">
            <span>${copy.composerPh}</span>
            <svg class="chat-send-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </div>
        </div>
      </div>
    `;

    content.appendChild(outer);
  });
})();
