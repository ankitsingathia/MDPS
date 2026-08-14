/* ============================================================
   VERA — the assistant widget.

   Drops a launcher into any page. All it does is relay messages to
   /api/chat and render the reply; the scoping (health questions only,
   never a risk score) lives in the system prompt on the server, so it
   cannot be edited away from the browser.
   ============================================================ */
(function () {
  'use strict';

  const API = window.VITALS_API || (location.port === '8000' || location.port === '' ? '/api' : 'http://127.0.0.1:8000/api');
  const NAME = 'VERA';

  const css = `
  #vera-fab{position:fixed;right:24px;bottom:24px;z-index:1200;display:flex;align-items:center;gap:10px;
    padding:13px 20px;border-radius:999px;border:1px solid rgba(221,216,202,.28);
    background:#232c28;color:#ddd8ca;font:inherit;font-size:13px;cursor:pointer;
    box-shadow:0 8px 30px rgba(0,0,0,.34);transition:transform .3s cubic-bezier(.16,1,.3,1),border-color .3s}
  #vera-fab:hover{transform:translateY(-2px);border-color:rgba(221,216,202,.6)}
  #vera-fab .dot{width:7px;height:7px;border-radius:50%;background:#e0b878}
  #vera-fab.hide{display:none}

  #vera{position:fixed;right:24px;bottom:24px;z-index:1201;width:min(400px,calc(100vw - 32px));
    height:min(590px,calc(100vh - 48px));display:none;flex-direction:column;
    background:#232c28;border:1px solid rgba(221,216,202,.2);border-radius:6px;
    box-shadow:0 20px 60px rgba(0,0,0,.5);overflow:hidden}
  #vera.open{display:flex}
  #vera header{display:flex;align-items:center;gap:11px;padding:15px 17px;
    border-bottom:1px solid rgba(221,216,202,.16);background:#1e2622}
  #vera header .nm{font-size:14px;letter-spacing:.22em}
  #vera header .st{font-size:10.5px;color:rgba(221,216,202,.45);margin-left:auto}
  #vera header button{background:none;border:0;color:rgba(221,216,202,.6);font-size:19px;
    cursor:pointer;line-height:1;padding:0 2px}
  #vera header button:hover{color:#ddd8ca}

  #vera-log{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:14px}
  #vera-log::-webkit-scrollbar{width:6px}
  #vera-log::-webkit-scrollbar-thumb{background:rgba(221,216,202,.18);border-radius:3px}
  .vm{max-width:88%;font-size:13.5px;line-height:1.62;white-space:pre-wrap}
  .vm.u{align-self:flex-end;background:#2f3a35;padding:10px 13px;border-radius:10px 10px 2px 10px}
  .vm.a{align-self:flex-start;color:rgba(221,216,202,.9)}
  .vm.sys{align-self:stretch;font-size:12px;color:rgba(221,216,202,.5);
    border-left:2px solid rgba(224,184,120,.6);padding:9px 12px;background:#1e2622}
  .vm .who{display:block;font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;
    color:rgba(221,216,202,.34);margin-bottom:5px}

  #vera-sug{display:flex;flex-wrap:wrap;gap:7px;padding:0 18px 12px}
  #vera-sug button{font:inherit;font-size:11.5px;padding:6px 11px;border-radius:999px;cursor:pointer;
    border:1px solid rgba(221,216,202,.22);background:none;color:rgba(221,216,202,.72)}
  #vera-sug button:hover{border-color:rgba(221,216,202,.55);color:#ddd8ca}

  #vera-form{display:flex;gap:9px;padding:13px 15px;border-top:1px solid rgba(221,216,202,.16);background:#1e2622}
  #vera-in{flex:1;background:#2b3530;border:1px solid rgba(221,216,202,.18);border-radius:3px;
    padding:10px 12px;font:inherit;font-size:13px;color:#ddd8ca;resize:none;max-height:96px}
  #vera-in:focus{outline:none;border-color:#e0b878}
  #vera-send{background:#ddd8ca;color:#2b3530;border:0;border-radius:3px;padding:0 16px;
    font:inherit;font-size:13px;cursor:pointer}
  #vera-send:disabled{opacity:.45;cursor:default}
  .vera-typing span{display:inline-block;width:5px;height:5px;margin-right:3px;border-radius:50%;
    background:rgba(221,216,202,.5);animation:vb 1.1s infinite}
  .vera-typing span:nth-child(2){animation-delay:.15s}
  .vera-typing span:nth-child(3){animation-delay:.3s}
  @keyframes vb{0%,60%,100%{opacity:.25}30%{opacity:1}}
  @media (prefers-reduced-motion:reduce){#vera-fab,.vera-typing span{transition:none;animation:none}}
  `;

  const SUGGESTIONS = [
    'What does a high ALT mean?',
    'Why does creatinine matter?',
    'What is HbA1c?',
    'How do I lower my cholesterol?',
  ];

  document.head.appendChild(Object.assign(document.createElement('style'), { textContent: css }));

  const fab = document.createElement('button');
  fab.id = 'vera-fab';
  fab.innerHTML = `<span class="dot"></span> Ask ${NAME}`;

  const panel = document.createElement('div');
  panel.id = 'vera';
  panel.innerHTML = `
    <header>
      <span class="dot" style="width:7px;height:7px;border-radius:50%;background:#e0b878"></span>
      <span class="nm">${NAME}</span>
      <span class="st" id="vera-st">checking…</span>
      <button id="vera-x" aria-label="Close">&times;</button>
    </header>
    <div id="vera-log"></div>
    <div id="vera-sug">${SUGGESTIONS.map(s => `<button>${s}</button>`).join('')}</div>
    <form id="vera-form">
      <textarea id="vera-in" rows="1" placeholder="Ask a health question…"></textarea>
      <button id="vera-send" type="submit">Send</button>
    </form>`;

  document.body.append(fab, panel);

  const log = panel.querySelector('#vera-log');
  const input = panel.querySelector('#vera-in');
  const send = panel.querySelector('#vera-send');
  const status = panel.querySelector('#vera-st');
  const history = [];
  let ready = false;

  function bubble(role, text) {
    const el = document.createElement('div');
    el.className = 'vm ' + (role === 'user' ? 'u' : role === 'system' ? 'sys' : 'a');
    el.innerHTML = role === 'assistant' ? `<span class="who">${NAME}</span>` : '';
    el.appendChild(document.createTextNode(text));
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  function open() {
    panel.classList.add('open'); fab.classList.add('hide');
    if (!log.children.length) {
      bubble('assistant',
        `I'm ${NAME}. I can explain what a lab value means, what a condition involves, ` +
        `or how to read a screening result.\n\nI don't diagnose, and I don't produce risk ` +
        `scores — those come from the screening tool itself.`);
    }
    input.focus();
  }
  function close() { panel.classList.remove('open'); fab.classList.remove('hide'); }

  fab.addEventListener('click', open);
  panel.querySelector('#vera-x').addEventListener('click', close);
  addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

  // Click anywhere outside the panel closes it.
  //
  // `downInside` covers the drag case: selecting a reply and releasing past
  // the panel edge fires a click whose target is outside, which would
  // otherwise shut the panel mid-selection. Tracking where the press started
  // is enough - no stopPropagation, which at document level would block the
  // Send button and the suggestion chips from ever receiving their clicks.
  let downInside = false;
  document.addEventListener('mousedown', e => {
    downInside = panel.contains(e.target) || fab.contains(e.target);
  });
  document.addEventListener('click', e => {
    if (!panel.classList.contains('open')) return;
    if (downInside) return;
    if (panel.contains(e.target) || fab.contains(e.target)) return;
    close();
  });

  panel.querySelector('#vera-sug').addEventListener('click', e => {
    if (e.target.tagName !== 'BUTTON') return;
    input.value = e.target.textContent;
    panel.querySelector('#vera-form').requestSubmit();
  });

  // grow with the text, but never below the resting height and never past 120
  // Cap matches the CSS max-height, otherwise the textarea grows past the
  // limit the stylesheet enforces and the two disagree about its size.
  function autosize() {
    input.style.height = 'auto';
    input.style.height = Math.min(96, input.scrollHeight) + 'px';
  }
  input.addEventListener('input', autosize);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); panel.querySelector('#vera-form').requestSubmit(); }
  });

  panel.querySelector('#vera-form').addEventListener('submit', async e => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;

    if (!ready) {
      bubble('system', `${NAME} is not configured on this instance. Set GROQ_API_KEY in apps/api/.env and restart the API.`);
      return;
    }

    bubble('user', msg);
    history.push({ role: 'user', content: msg });
    input.value = ''; autosize();
    send.disabled = true;

    const typing = bubble('assistant', '');
    typing.innerHTML = `<span class="who">${NAME}</span><span class="vera-typing"><span></span><span></span><span></span></span>`;

    try {
      const r = await fetch(API + '/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: history.slice(0, -1).slice(-8) }),
      });
      const data = await r.json();
      typing.remove();
      if (!r.ok) { bubble('system', data.detail || ('Request failed — HTTP ' + r.status)); return; }
      bubble('assistant', data.reply);
      history.push({ role: 'assistant', content: data.reply });
    } catch (err) {
      typing.remove();
      bubble('system', 'Could not reach the assistant. Is the API running?');
    } finally {
      send.disabled = false; input.focus();
    }
  });

  // availability is a server fact, so ask rather than assume
  fetch(API + '/chat/status')
    .then(r => r.json())
    .then(d => { ready = !!d.available; status.textContent = ready ? 'online' : 'not configured'; })
    .catch(() => { ready = false; status.textContent = 'offline'; });
})();
