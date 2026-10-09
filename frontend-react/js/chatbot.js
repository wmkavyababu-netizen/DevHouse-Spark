/* ============================================================
   TARANG - Chatbot + Live Simulation Widget  (chatbot.js)
   Injected via <script defer> on every page.
   ============================================================ */

const _tarangStyles = `
#tarang-chat-widget{position:fixed;bottom:20px;right:20px;z-index:9999;font-family:'Inter',sans-serif}
#tarang-chat-button{width:60px;height:60px;border-radius:30px;background:#0ea5e9;color:#fff;border:none;
  box-shadow:0 4px 14px rgba(14,165,233,.45);cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:transform .2s}
#tarang-chat-button:hover{transform:scale(1.07)}
#tarang-chat-button svg{width:28px;height:28px;fill:currentColor}
#tarang-chat-window{display:none;width:350px;height:500px;background:#fff;border-radius:14px;
  box-shadow:0 10px 40px rgba(0,0,0,.18);position:absolute;bottom:80px;right:0;
  flex-direction:column;overflow:hidden;border:1px solid #e2e8f0}
#tarang-chat-header{background:linear-gradient(135deg,#0ea5e9,#06b6d4);color:#fff;padding:14px 16px;
  font-weight:700;font-size:14px;display:flex;justify-content:space-between;align-items:center}
#tarang-chat-header button{background:none;border:none;color:#fff;cursor:pointer;font-size:22px}
#tarang-chat-messages{flex:1;padding:14px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;background:#f8fafc}
.chat-message{max-width:86%;padding:10px 14px;border-radius:12px;font-size:13.5px;line-height:1.45}
.chat-message.user{background:#0ea5e9;color:#fff;align-self:flex-end;border-bottom-right-radius:3px}
.chat-message.bot{background:#fff;color:#1e293b;align-self:flex-start;border:1px solid #e2e8f0;border-bottom-left-radius:3px}
.chat-message.err-msg{background:#fff1f2;color:#9f1239;border-color:#fecdd3}
#tarang-chat-input-area{padding:10px 12px;background:#fff;border-top:1px solid #e2e8f0;display:flex;gap:8px}
#tarang-chat-input{flex:1;padding:9px 14px;border:1px solid #cbd5e1;border-radius:20px;outline:none;font-size:13.5px}
#tarang-chat-input:focus{border-color:#0ea5e9}
#tarang-chat-send{background:#0ea5e9;color:#fff;border:none;width:40px;height:40px;border-radius:20px;
  cursor:pointer;display:flex;align-items:center;justify-content:center}
#tarang-chat-send:disabled{background:#cbd5e1;cursor:not-allowed}
.t-typing{display:flex;gap:4px;padding:10px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;align-self:flex-start}
.t-dot{width:6px;height:6px;background:#94a3b8;border-radius:50%;animation:tDot 1.4s infinite ease-in-out}
.t-dot:nth-child(1){animation-delay:-.32s}.t-dot:nth-child(2){animation-delay:-.16s}
@keyframes tDot{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}

/* Simulation floating button */
#tarang-sim-widget{position:fixed;bottom:96px;right:20px;z-index:9998}
#tarang-sim-button{width:56px;height:56px;border-radius:28px;background:#14B8A6;color:#fff;border:none;
  box-shadow:0 4px 14px rgba(20,184,166,.4);cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:transform .2s}
#tarang-sim-button:hover{transform:scale(1.08)}

/* Backdrop - translucent, NOT a solid black screen */
#tarang-sim-back{display:none;position:fixed;inset:0;background:rgba(0,8,20,.52);
  z-index:10000;backdrop-filter:blur(3px)}
#tarang-sim-back.open{display:block}

/* Floating panel - centered, NOT full-screen */
#tarang-sim-panel{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
  width:min(96vw,1100px);height:min(90vh,700px);background:#000d1a;border-radius:14px;
  overflow:hidden;border:1px solid rgba(20,184,166,.45);
  box-shadow:0 0 60px rgba(20,184,166,.12),0 32px 90px rgba(0,0,0,.6);
  z-index:10001;flex-direction:column}
#tarang-sim-panel.open{display:flex}
#tarang-sim-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;
  background:rgba(2,12,28,.98);border-bottom:1px solid rgba(20,184,166,.22);flex-shrink:0}
#tarang-sim-bar-l{display:flex;align-items:center;gap:10px}
#tarang-sim-dot{width:8px;height:8px;border-radius:50%;background:#14B8A6;animation:simPulse 1.5s infinite}
@keyframes simPulse{0%,100%{opacity:1}50%{opacity:.4}}
#tarang-sim-title{color:#14B8A6;font-family:monospace;font-size:13px;font-weight:bold;letter-spacing:.07em}
#tarang-sim-sub{color:#475569;font-family:monospace;font-size:11px}
#tarang-sim-x{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);color:#94a3b8;
  width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:20px;
  display:flex;align-items:center;justify-content:center;transition:background .2s,color .2s}
#tarang-sim-x:hover{background:#14B8A6;color:#fff}
#tarang-sim-iframe{flex:1;width:100%;border:none;background:#000}
`;

document.addEventListener('DOMContentLoaded', () => {
  /* Inject styles */
  const s = document.createElement('style');
  s.textContent = _tarangStyles;
  document.head.appendChild(s);

  /* ── Chat Widget ── */
  const chatHtml = document.createElement('div');
  chatHtml.id = 'tarang-chat-widget';
  chatHtml.innerHTML = `
    <button id="tarang-chat-button" aria-label="Open TARANG Chat">
      <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.2L4 17.2V4h16v12z"/></svg>
    </button>
    <div id="tarang-chat-window">
      <div id="tarang-chat-header">
        <span>&#9875; TARANG AI</span>
        <button id="tarang-chat-close" aria-label="Close">&times;</button>
      </div>
      <div id="tarang-chat-messages">
        <div class="chat-message bot" id="tarang-lang-prompt">
          Please select your preferred language:<br>
          <div style="display:flex;gap:8px;flex-direction:column;margin-top:10px">
            <button class="lang-btn" data-lang="english" style="padding:8px;border:1px solid #0ea5e9;border-radius:6px;background:#fff;color:#0ea5e9;cursor:pointer;font-weight:600">English</button>
            <button class="lang-btn" data-lang="hindi" style="padding:8px;border:1px solid #0ea5e9;border-radius:6px;background:#fff;color:#0ea5e9;cursor:pointer;font-weight:600">&#2361;&#2367;&#2306;&#2342;&#2368; (Hindi)</button>
            <button class="lang-btn" data-lang="tamil" style="padding:8px;border:1px solid #0ea5e9;border-radius:6px;background:#fff;color:#0ea5e9;cursor:pointer;font-weight:600">&#2980;&#2990;&#3007;&#2996;&#3021; (Tamil)</button>
          </div>
        </div>
      </div>
      <form id="tarang-chat-input-area" style="display:none">
        <input type="text" id="tarang-chat-input" placeholder="Ask about TARANG..." autocomplete="off">
        <button type="submit" id="tarang-chat-send" aria-label="Send">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </form>
    </div>
  `;
  document.body.appendChild(chatHtml);

  /* ── Simulation Widget ── */
  const simBack  = document.createElement('div');
  simBack.id = 'tarang-sim-back';
  document.body.appendChild(simBack);

  const simWrap = document.createElement('div');
  simWrap.id = 'tarang-sim-widget';
  simWrap.innerHTML = `
    <button id="tarang-sim-button" title="Open Live TARANG Simulation" aria-label="Live Simulation">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="2"/>
        <path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49"/>
        <path d="M20.49 3.51a16 16 0 0 1 0 16.97M3.51 3.51a16 16 0 0 0 0 16.97"/>
      </svg>
    </button>
  `;
  document.body.appendChild(simWrap);

  const simPanel = document.createElement('div');
  simPanel.id = 'tarang-sim-panel';
  simPanel.innerHTML = `
    <div id="tarang-sim-bar">
      <div id="tarang-sim-bar-l">
        <div id="tarang-sim-dot"></div>
        <span id="tarang-sim-title">TARANG &mdash; LIVE SONAR SIMULATION</span>
        <span id="tarang-sim-sub">&nbsp;&middot;&nbsp;Indian Ocean AUV Side-Scan Feed</span>
      </div>
      <button id="tarang-sim-x" aria-label="Close">&times;</button>
    </div>
    <iframe id="tarang-sim-iframe" src="" title="TARANG Live Sonar Simulation" allowfullscreen></iframe>
  `;
  document.body.appendChild(simPanel);

  /* ── Chat logic ── */
  const chatBtn    = document.getElementById('tarang-chat-button');
  const chatWin    = document.getElementById('tarang-chat-window');
  const chatClose  = document.getElementById('tarang-chat-close');
  const msgs       = document.getElementById('tarang-chat-messages');
  const inputForm  = document.getElementById('tarang-chat-input-area');
  const input      = document.getElementById('tarang-chat-input');
  const sendBtn    = document.getElementById('tarang-chat-send');
  let chatOpen = false;
  let lang = 'english';

  const intros = {
    english: "Hello! I am the TARANG AI Assistant. I can help with marine debris detection, underwater sonar, XTF files, AUV surveys, hotspot mapping, and the TARANG workflow. How can I assist?",
    hindi:   "\u0928\u092e\u0938\u094d\u0924\u0947! \u092e\u0948\u0902 TARANG AI \u0938\u0939\u093e\u092f\u0915 \u0939\u0942\u0902\u0964 \u0938\u092e\u0941\u0926\u094d\u0930\u0940 \u092e\u0932\u092c\u0947 \u092a\u0939\u091a\u093e\u0928, XTF \u092b\u093c\u093e\u0907\u0932\u0947\u0902, AUV \u0938\u0930\u094d\u0935\u0947\u0915\u094d\u0937\u0923 \u0914\u0930 \u0938\u092b\u093e\u0908 \u092e\u093f\u0936\u0928 \u092e\u0947\u0902 \u0938\u0939\u093e\u092f\u0924\u093e \u0915\u0930 \u0938\u0915\u0924\u093e \u0939\u0942\u0902\u0964",
    tamil:   "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd! \u0ba8\u0bbe\u0ba9\u0bcd TARANG AI \u0b89\u0ba4\u0bb5\u0bbf\u0baf\u0bbe\u0bb3\u0bb0\u0bcd. XTF \u0b95\u0bcb\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd, AUV \u0b95\u0ba3\u0b95\u0bcd\u0b95\u0bc6\u0b9f\u0bc1\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0b95\u0b9f\u0bb2\u0bcd \u0b9a\u0bc1\u0ba4\u0bcd\u0ba4\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bb2\u0bcd \u0baa\u0ba3\u0bbf\u0b95\u0bb3\u0bcd \u0baa\u0bb1\u0bcd\u0bb1\u0bbf \u0b89\u0ba4\u0bb5 \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bc1\u0bae\u0bcd."
  };

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      lang = e.target.getAttribute('data-lang');
      document.getElementById('tarang-lang-prompt').style.display = 'none';
      addMsg(intros[lang], 'bot');
      inputForm.style.display = 'flex';
      input.focus();
    });
  });

  chatBtn.addEventListener('click', () => {
    chatOpen = !chatOpen;
    chatWin.style.display = chatOpen ? 'flex' : 'none';
    if (chatOpen) input.focus();
  });
  chatClose.addEventListener('click', () => { chatOpen = false; chatWin.style.display = 'none'; });

  function addMsg(text, who, isErr) {
    const d = document.createElement('div');
    d.className = 'chat-message ' + who + (isErr ? ' err-msg' : '');
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  }
  function showTyping() {
    const d = document.createElement('div');
    d.className = 't-typing'; d.id = 'tarang-typing';
    d.innerHTML = '<div class="t-dot"></div><div class="t-dot"></div><div class="t-dot"></div>';
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight;
  }
  function hideTyping() { const e = document.getElementById('tarang-typing'); if (e) e.remove(); }

  let _lastSent = 0;

  inputForm.addEventListener('submit', async e => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    // Client-side 1-second debounce to prevent accidental double-sends
    const now = Date.now();
    if (now - _lastSent < 1000) return;
    _lastSent = now;

    input.value = ''; input.disabled = true; sendBtn.disabled = true;
    addMsg(text, 'user');
    showTyping();
    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: text, language: lang })
      });
      const data = await res.json();
      hideTyping();
      if (res.status === 503 && data.error === 'missing_api_key') {
        addMsg('TARANG AI is not configured yet. Please set GEMINI_API_KEY in the server .env file.', 'bot', true);
      } else if (res.status === 429) {
        addMsg(data.reply || "You're sending messages too quickly. Please wait a moment.", 'bot', true);
      } else if (data.reply) {
        addMsg(data.reply, 'bot');
      } else {
        addMsg("Could not get a response. Please try again.", 'bot', true);
      }
    } catch (err) {
      hideTyping();
      addMsg('Network error - please check your connection.', 'bot', true);
    } finally {
      input.disabled = false; sendBtn.disabled = false; input.focus();
    }
  });


  /* ── Simulation logic ── */
  const simBtn   = document.getElementById('tarang-sim-button');
  const simClose = document.getElementById('tarang-sim-x');
  const iframe   = document.getElementById('tarang-sim-iframe');

  function openSim() {
    if (!iframe.getAttribute('data-loaded')) {
      iframe.src = '/simulation/';
      iframe.setAttribute('data-loaded', '1');
    }
    simPanel.classList.add('open');
    simBack.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSim() {
    simPanel.classList.remove('open');
    simBack.classList.remove('open');
    document.body.style.overflow = '';
  }

  simBtn.addEventListener('click', openSim);
  simClose.addEventListener('click', closeSim);
  simBack.addEventListener('click', closeSim);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSim(); });

  /* Global hooks so index.html / public.html Live Session buttons work */
  window.tarangOpenSimulation  = openSim;
  window.tarangCloseSimulation = closeSim;
});
