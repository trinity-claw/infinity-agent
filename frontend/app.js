/* =============================================================================
   InfinitePay AI — Chat Application
   ============================================================================= */

const API_BASE = window.location.origin;

// Configure marked.js
marked.setOptions({
  breaks: true,
  gfm: true,
});

/* ─── DOM refs ─── */
const messagesArea    = document.getElementById('messagesArea');
const messageInput    = document.getElementById('messageInput');
const sendBtn         = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const typingText      = document.getElementById('typingText');
const charCount       = document.getElementById('charCount');
const userIdInput     = document.getElementById('userIdInput');
const clearChat       = document.getElementById('clearChat');
const activeAgentLabel = document.getElementById('activeAgentLabel');
const welcomeScreen   = document.getElementById('welcomeScreen');
const toastEl         = document.getElementById('toast');
const toastMsg        = document.getElementById('toastMsg');
const sidebarToggle   = document.getElementById('sidebarToggle');
const sidebarClose    = document.getElementById('sidebarClose');
const sidebarPeek     = document.getElementById('sidebarPeek');
const sidebarOverlay  = document.getElementById('sidebarOverlay');
const appWrapper      = document.getElementById('appWrapper');
const sidebar         = document.getElementById('sidebar');
const healthInfo      = document.getElementById('health-info');

/* ─── State ─── */
let isLoading   = false;
let sessionId   = null;   // active escalation session
let pollTimer   = null;   // escalation polling interval
let pollOffset  = 0;      // next message index to fetch

/* ─── Agent badge config ─── */
const AGENT_CONFIG = {
  knowledge: { label: 'Knowledge', badgeClass: 'badge-knowledge' },
  support:   { label: 'Support',   badgeClass: 'badge-support'   },
  sentiment: { label: 'Sentiment', badgeClass: 'badge-sentiment' },
  router:    { label: 'Router',    badgeClass: 'badge-router'    },
  guardrail: { label: 'Guardrail', badgeClass: 'badge-guardrail' },
  human:     { label: 'Humano',    badgeClass: 'badge-human'     },
};

/* =============================================================================
   Initialization
   ============================================================================= */

async function init() {
  restoreSidebarState();
  bindEvents();
  autoResizeTextarea();
  checkHealth();
  initShader();
}

function restoreSidebarState() {
  // On desktop start expanded; on mobile start collapsed
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    appWrapper.classList.add('sidebar-collapsed');
  }
}

function bindEvents() {
  sendBtn.addEventListener('click', handleSend);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading) handleSend();
    }
  });

  messageInput.addEventListener('input', () => {
    autoResizeTextarea();
    updateCharCount();
    sendBtn.disabled = messageInput.value.trim().length === 0 || isLoading;
  });

  clearChat.addEventListener('click', () => {
    stopPolling();
    sessionId  = null;
    pollOffset = 0;
    messagesArea.innerHTML = '';
    messagesArea.appendChild(welcomeScreen);
    welcomeScreen.style.display = 'flex';
    activeAgentLabel.textContent = 'Pronto para ajudar';
  });

  // Sidebar toggle — inside sidebar (sidebarClose) and peek tab (sidebarPeek)
  sidebarToggle.addEventListener('click', toggleSidebar);
  sidebarClose.addEventListener('click', toggleSidebar);
  sidebarPeek.addEventListener('click', toggleSidebar);
  sidebarOverlay.addEventListener('click', closeSidebarMobile);

  // Quick action buttons in sidebar
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.dataset.msg;
      if (msg) insertAndSend(msg);
    });
  });

  // Welcome chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const msg = chip.dataset.msg;
      if (msg) insertAndSend(msg);
    });
  });
}

/* =============================================================================
   Sidebar
   ============================================================================= */

function toggleSidebar() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    // On mobile: overlay mode
    const isOpen = sidebar.classList.contains('open');
    if (isOpen) {
      closeSidebarMobile();
    } else {
      openSidebarMobile();
    }
  } else {
    // On desktop: push-collapse mode
    appWrapper.classList.toggle('sidebar-collapsed');
  }
}

function openSidebarMobile() {
  sidebar.classList.add('open');
  sidebarOverlay.classList.remove('hidden');
  sidebarOverlay.classList.add('visible');
  appWrapper.classList.remove('sidebar-collapsed');  // hide peek tab while sidebar is open
}

function closeSidebarMobile() {
  sidebar.classList.remove('open');
  sidebarOverlay.classList.remove('visible');
  sidebarOverlay.classList.add('hidden');
  appWrapper.classList.add('sidebar-collapsed');  // show peek tab when sidebar is closed
}

function autoResizeTextarea() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
}

function updateCharCount() {
  const len = messageInput.value.length;
  charCount.textContent = `${len}/5000`;
  charCount.style.color = len > 4500 ? 'var(--sentiment)' : 'var(--text-muted)';
}

function insertAndSend(msg) {
  messageInput.value = msg;
  autoResizeTextarea();
  updateCharCount();
  sendBtn.disabled = false;
  // Close sidebar on mobile after selecting quick action
  if (window.innerWidth <= 768) closeSidebarMobile();
  handleSend();
}

/* =============================================================================
   Health Check
   ============================================================================= */

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/v1/health`);
    if (!res.ok) return;
    const data = await res.json();
    const services = data.services || {};
    const lines = [];
    if (services.llm) lines.push(`LLM: ${services.llm}`);
    if (services.knowledge_base) lines.push(`KB: ${services.knowledge_base}`);
    healthInfo.innerHTML = lines.map(l => `<div>${l}</div>`).join('');
  } catch {
    healthInfo.innerHTML = '<div style="color:var(--text-muted)">Health check indisponível</div>';
  }
}

/* =============================================================================
   Send Message
   ============================================================================= */

async function handleSend() {
  const message = messageInput.value.trim();
  if (!message || isLoading) return;

  const userId = userIdInput.value.trim() || 'client789';

  // Hide welcome screen
  welcomeScreen.style.display = 'none';

  // Append user message
  appendMessage('user', message);

  // Clear input
  messageInput.value = '';
  autoResizeTextarea();
  updateCharCount();
  sendBtn.disabled = true;

  // If there's an active escalation session, route to operator
  if (sessionId) {
    await sendToOperator(userId, message);
    return;
  }

  // Normal AI flow
  setLoading(true, 'Classificando intenção...');

  try {
    const response = await fetch(`${API_BASE}/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_id: userId }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();

    setLoading(false);
    appendAgentMessage(data);

    // If escalated, start polling for operator replies
    if (data.metadata?.escalated && data.metadata?.session_id) {
      sessionId  = data.metadata.session_id;
      pollOffset = 0;
      showHumanConnectedBanner(sessionId);
      startPolling(sessionId);
    }

  } catch (err) {
    setLoading(false);
    showToast(`Erro: ${err.message}`);
    activeAgentLabel.textContent = 'Erro na requisição';
  }
}

async function sendToOperator(userId, message) {
  try {
    const res = await fetch(`${API_BASE}/v1/messages/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: message, user_id: userId }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    // No typewriter for user-sent messages; just confirmation
  } catch (err) {
    showToast(`Erro ao enviar mensagem: ${err.message}`);
  }
}

/* =============================================================================
   Human escalation — polling
   ============================================================================= */

function startPolling(sid) {
  activeAgentLabel.textContent = '🟢 Atendente humano conectado';
  pollTimer = setInterval(() => pollOperatorMessages(sid), 3000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollOperatorMessages(sid) {
  try {
    const res = await fetch(`${API_BASE}/v1/messages/${sid}?since=${pollOffset}`);
    if (!res.ok) return;
    const data = await res.json();

    for (const msg of data.messages) {
      if (msg.sender === 'agent') {
        appendHumanMessage(msg.content);
        pollOffset = msg.index + 1;
      } else if (msg.sender === 'user') {
        // User messages are already shown locally — skip
        if (pollOffset <= msg.index) pollOffset = msg.index + 1;
      }
    }

    if (!data.active) {
      stopPolling();
      activeAgentLabel.textContent = 'Atendimento encerrado';
    }
  } catch {
    // Silently ignore poll errors
  }
}

function showHumanConnectedBanner(sid) {
  const div = document.createElement('div');
  div.className = 'human-connected-banner';
  div.innerHTML = `
    <div class="hcb-dot"></div>
    <span>Atendente humano conectado — Sessão <strong>${sid}</strong></span>
  `;
  messagesArea.appendChild(div);
  scrollToBottom();
}

function appendHumanMessage(content) {
  const div = document.createElement('div');
  div.className = 'message agent human';
  div.innerHTML = `
    <div class="msg-avatar">AG</div>
    <div class="msg-body">
      <div class="msg-meta">
        <span class="msg-time">${formatTime(new Date())}</span>
      </div>
      <div class="msg-bubble">
        <span class="agent-badge badge-human">Humano</span>
        ${marked.parse(content)}
      </div>
    </div>
  `;
  messagesArea.appendChild(div);
  scrollToBottom();
}

/* =============================================================================
   Message Rendering
   ============================================================================= */

function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;

  if (role === 'user') {
    div.innerHTML = `
      <div class="msg-avatar">EU</div>
      <div class="msg-body">
        <div class="msg-meta">
          <span class="msg-time">${formatTime(new Date())}</span>
        </div>
        <div class="msg-bubble">${escapeHtml(content)}</div>
      </div>
    `;
  }

  messagesArea.appendChild(div);
  scrollToBottom();
  return div;
}

function appendAgentMessage(data) {
  const agentKey = (data.agent_used || 'unknown').toLowerCase();
  const config = AGENT_CONFIG[agentKey] || { label: agentKey || 'Agent', badgeClass: 'badge-unknown' };

  // Update header subtitle
  activeAgentLabel.textContent = `Respondido por ${config.label} Agent`;

  const div = document.createElement('div');
  div.className = 'message agent';

  const escalated = data.metadata?.escalated;
  const escalationHtml = escalated
    ? `<div class="escalation-notice">
         🚨 Esta conversa foi escalada para um agente humano
       </div>`
    : '';

  div.innerHTML = `
    <div class="msg-avatar">
      <svg viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="9" stroke="#00E676" stroke-width="1.5"/>
        <path d="M6 10L9 13L14 7" stroke="#00E676" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="msg-body">
      <div class="msg-meta">
        <span class="msg-time">${formatTime(new Date())}</span>
      </div>
      <div class="msg-bubble" id="bubble-${Date.now()}">
        <span class="agent-badge ${config.badgeClass}">${config.label}</span>
      </div>
      ${escalationHtml}
    </div>
  `;

  messagesArea.appendChild(div);
  scrollToBottom();

  // Typewriter animation (appended after the badge span)
  const bubble = div.querySelector('.msg-bubble');
  typewrite(bubble, data.response || '', config.badgeClass, config.label);
}

/* =============================================================================
   Typewriter Effect
   ============================================================================= */

function typewrite(element, fullText, badgeClass, badgeLabel, speed = 8) {
  element.classList.add('typewriter-cursor');
  const words = fullText.split(' ');
  let current = '';
  let wordIdx = 0;

  function step() {
    if (wordIdx < words.length) {
      current += (wordIdx > 0 ? ' ' : '') + words[wordIdx];
      wordIdx++;
      // Badge stays at the top-right via float; update text content
      element.innerHTML = `<span class="agent-badge ${badgeClass}">${badgeLabel}</span>${marked.parse(current)}`;
      scrollToBottom();
      setTimeout(step, speed);
    } else {
      element.classList.remove('typewriter-cursor');
      element.innerHTML = `<span class="agent-badge ${badgeClass}">${badgeLabel}</span>${marked.parse(fullText)}`;
      scrollToBottom();
    }
  }

  step();
}

/* =============================================================================
   Loading State
   ============================================================================= */

function setLoading(loading, message = 'Processando...') {
  isLoading = loading;
  sendBtn.disabled = loading || messageInput.value.trim().length === 0;

  if (loading) {
    typingIndicator.classList.remove('hidden');
    typingText.textContent = message;
    sendBtn.classList.add('loading');
    const stages = [
      { delay: 800, msg: 'Roteando para o agente...' },
      { delay: 2000, msg: 'Gerando resposta...' },
    ];
    stages.forEach(({ delay, msg }) => {
      setTimeout(() => {
        if (isLoading) typingText.textContent = msg;
      }, delay);
    });
  } else {
    typingIndicator.classList.add('hidden');
    sendBtn.classList.remove('loading');
  }
}

/* =============================================================================
   WebGL Shader — concentric rings background
   ============================================================================= */

function initShader() {
  if (typeof THREE === 'undefined') return;

  const canvas = document.getElementById('shaderCanvas');
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene  = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const vertexShader = `
    void main() {
      gl_Position = vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    precision mediump float;

    uniform float time;
    uniform vec2  resolution;

    void main() {
      vec2 uv = gl_FragCoord.xy / resolution;
      uv -= 0.5;
      uv.x *= resolution.x / resolution.y;

      float dist = length(uv);

      // Concentric pulsating rings
      float rings = 0.0;
      for (int i = 0; i < 6; i++) {
        float fi    = float(i);
        float phase = time * 0.5 + fi * 1.05;
        float radius = 0.08 + fi * 0.11 + sin(phase) * 0.015;
        float width  = 0.003 + fi * 0.0008;
        float ring   = smoothstep(width, 0.0, abs(dist - radius));
        rings += ring * (1.0 - fi * 0.12);
      }

      // InfinitePay green: #00E676
      vec3 color = vec3(0.0, 0.902, 0.463);
      float alpha = rings * 0.18;

      gl_FragColor = vec4(color * rings, alpha);
    }
  `;

  const uniforms = {
    time:       { value: 0.0 },
    resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
  };

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms,
    transparent: true,
    depthWrite: false,
  });

  const geometry = new THREE.PlaneGeometry(2, 2);
  scene.add(new THREE.Mesh(geometry, material));

  function animate() {
    requestAnimationFrame(animate);
    uniforms.time.value += 0.02;   // slightly slower than original (0.05)
    renderer.render(scene, camera);
  }

  animate();

  window.addEventListener('resize', () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    uniforms.resolution.value.set(window.innerWidth, window.innerHeight);
  });
}

/* =============================================================================
   Utilities
   ============================================================================= */

function scrollToBottom() {
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

function formatTime(date) {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

let toastTimer = null;
function showToast(message, duration = 4000) {
  toastMsg.textContent = message;
  toastEl.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.add('hidden'), duration);
}

/* ─── Boot ─── */
init();
