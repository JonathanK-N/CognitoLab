/* ── Cognito AI Chat ── */
let cognitoOpen = false;

function toggleCognito() {
  const panel = document.getElementById('cognitoPanel');
  cognitoOpen = !cognitoOpen;
  panel.style.display = cognitoOpen ? 'flex' : 'none';
  if (cognitoOpen) {
    setTimeout(() => document.getElementById('cognitoInput')?.focus(), 100);
  }
}

async function sendCognito() {
  const input = document.getElementById('cognitoInput');
  const msgs  = document.getElementById('cognitoMessages');
  const btn   = document.getElementById('cognitoSendBtn');
  const text  = input.value.trim();
  if (!text) return;

  input.value = '';
  input.disabled = true;
  btn.disabled = true;

  // User message
  appendMsg(msgs, 'user', escHtml(text));

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  msgs.innerHTML += `
    <div class="msg msg-ai" id="${typingId}">
      <div class="msg-bubble">
        <span class="typing-dots"><span></span><span></span><span></span></span>
      </div>
    </div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res  = await fetch('/api/ai/assist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: text, board: 'general' })
    });
    const data = await res.json();
    const answer = data.answer || data.error || 'Une erreur est survenue.';
    document.getElementById(typingId)?.remove();
    appendMsg(msgs, 'ai', formatMsg(answer));
  } catch (e) {
    document.getElementById(typingId)?.remove();
    appendMsg(msgs, 'ai', '<span style="color:#f87171">Erreur de connexion. Réessayez.</span>');
  }

  input.disabled = false;
  btn.disabled = false;
  input.focus();
  msgs.scrollTop = msgs.scrollHeight;
}

function appendMsg(container, type, html) {
  const div = document.createElement('div');
  div.className = `msg msg-${type}`;
  div.innerHTML = `<div class="msg-bubble">${html}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

/* ── Message formatter ── */
function formatMsg(text) {
  if (!text) return '';
  // Escape HTML first
  let out = escHtml(text);
  // Code blocks ```...```
  out = out.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
    `<pre style="margin:8px 0;padding:10px;background:rgba(5,8,16,0.8);border-radius:8px;border:1px solid rgba(33,150,243,0.15);overflow:auto"><code>${code.trim()}</code></pre>`
  );
  // Inline code `...`
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bold **...**
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Newlines
  out = out.replace(/\n/g, '<br>');
  return out;
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Tab switching (simulator) ── */
function switchTab(id, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById('tab-' + id);
  if (panel) panel.style.display = 'block';
  if (btn) btn.classList.add('active');
}

/* ── Keyboard shortcut (Ctrl+Enter in Cognito) ── */
document.addEventListener('DOMContentLoaded', () => {
  const cognitoInput = document.getElementById('cognitoInput');
  if (cognitoInput) {
    cognitoInput.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') sendCognito();
    });
  }
});
