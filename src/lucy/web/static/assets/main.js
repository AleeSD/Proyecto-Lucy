const SESSION_KEY = "lucy_session_id";
let sessionId = localStorage.getItem(SESSION_KEY) || null;

const $messages = document.getElementById("messages");
const $form = document.getElementById("chat-form");
const $input = document.getElementById("message-input");
const $stats = document.getElementById("stats");
const $statsContent = document.getElementById("stats-content");
const $toggleStats = document.getElementById("toggle-stats");
const $sessionFooter = document.getElementById("session-id");
const $regForm = document.getElementById("register-form");
const $loginForm = document.getElementById("login-form");

let csrfToken = null;

function ensureSession(id) {
  if (!sessionId) {
    sessionId = id || `web_${Date.now()}`;
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  if ($sessionFooter) {
    $sessionFooter.textContent = `Sesión: ${sessionId}`;
  }
}

function addMessage(role, text) {
  if (!$messages) return;
  const item = document.createElement("div");
  item.className = `msg ${role}`;
  item.innerHTML = `
    <div class="avatar">${role === "bot" ? "🤖" : "🧑"}</div>
    <div class="bubble">${text}</div>
  `;
  $messages.appendChild(item);
  $messages.scrollTop = $messages.scrollHeight;
}

async function sendMessage(text) {
  addMessage("user", text);
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(sessionId ? { "X-Session-ID": sessionId } : {}),
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    },
    body: JSON.stringify({ message: text, session_id: sessionId }),
  });
  const data = await res.json();
  ensureSession(data.session_id);
  addMessage("bot", data.response);
  refreshStats();
}

async function refreshStats() {
  try {
    const [statsRes, ctxRes] = await Promise.all([
      fetch("/api/stats"),
      sessionId ? fetch(`/api/context?session_id=${encodeURIComponent(sessionId)}`) : Promise.resolve(null),
    ]);
    const stats = await statsRes.json();
    const context = ctxRes ? await ctxRes.json() : {};
    $statsContent.textContent = JSON.stringify({ stats, context }, null, 2);
  } catch {}
}

if ($form && $input) {
  $form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = $input.value.trim();
    if (!text) return;
    $input.value = "";
    sendMessage(text);
  });
}

if ($toggleStats && $stats) {
  $toggleStats.addEventListener("click", () => {
    $stats.classList.toggle("hidden");
    if (!$stats.classList.contains("hidden")) {
      refreshStats();
    }
  });
}

ensureSession();

async function fetchCsrf() {
  try {
    const res = await fetch("/api/csrf");
    const data = await res.json();
    csrfToken = data.csrf_token;
  } catch {}
}

function setError(id, msg) { const el = document.getElementById(id); if (el) el.textContent = msg || ""; }

function validateUsername(v) { return /^[A-Za-z0-9]{6,}$/.test(v); }
function validateEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
function validateNotEmpty(v) { return v.trim().length > 0; }
function validateDob(v) {
  if (!v) return false;
  const dob = new Date(v);
  const now = new Date();
  const min = new Date(now.getFullYear() - 18, now.getMonth(), now.getDate());
  return dob <= min;
}
function validatePassword(v) {
  const hasUpper = /[A-Z]/.test(v);
  const hasLower = /[a-z]/.test(v);
  const hasDigit = /[0-9]/.test(v);
  return hasUpper && hasLower && hasDigit && v.length >= 8;
}

function attachRealtimeValidation() {
  const u = document.getElementById("reg-username");
  const e = document.getElementById("reg-email");
  const f = document.getElementById("reg-first");
  const l = document.getElementById("reg-last");
  const d = document.getElementById("reg-dob");
  const p = document.getElementById("reg-password");
  u.addEventListener("input", () => setError("err-username", validateUsername(u.value) ? "" : "Mínimo 6, solo letras y números"));
  e.addEventListener("input", () => setError("err-email", validateEmail(e.value) ? "" : "Formato de correo inválido"));
  f.addEventListener("input", () => setError("err-first", validateNotEmpty(f.value) ? "" : "Ingresa tus nombres"));
  l.addEventListener("input", () => setError("err-last", validateNotEmpty(l.value) ? "" : "Ingresa tus apellidos"));
  d.addEventListener("change", () => setError("err-dob", validateDob(d.value) ? "" : "Debes ser mayor de 18 años"));
  p.addEventListener("input", () => setError("err-password", validatePassword(p.value) ? "" : "Mínimo 8, incluye mayúscula, minúscula y dígito"));
}

if ($regForm) {
  attachRealtimeValidation();
  $regForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      username: document.getElementById("reg-username").value.trim(),
      email: document.getElementById("reg-email").value.trim(),
      first_name: document.getElementById("reg-first").value.trim(),
      last_name: document.getElementById("reg-last").value.trim(),
      dob: document.getElementById("reg-dob").value,
      password: document.getElementById("reg-password").value,
    };
    let valid = true;
    if (!validateUsername(payload.username)) { setError("err-username", "Mínimo 6, solo letras y números"); valid = false; }
    if (!validateEmail(payload.email)) { setError("err-email", "Formato de correo inválido"); valid = false; }
    if (!validateNotEmpty(payload.first_name)) { setError("err-first", "Ingresa tus nombres"); valid = false; }
    if (!validateNotEmpty(payload.last_name)) { setError("err-last", "Ingresa tus apellidos"); valid = false; }
    if (!validateDob(payload.dob)) { setError("err-dob", "Debes ser mayor de 18 años"); valid = false; }
    if (!validatePassword(payload.password)) { setError("err-password", "Mínimo 8, incluye mayúscula, minúscula y dígito"); valid = false; }
    if (!valid) return;
    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}) },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Error en registro");
    } else {
      alert("Registro completado");
    }
  });
}

if ($loginForm) {
  $loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      identifier: document.getElementById("login-id").value.trim(),
      password: document.getElementById("login-password").value,
    };
    if (!payload.identifier) { setError("err-login-id", "Ingresa tu email o usuario"); return; }
    if (!payload.password) { setError("err-login-password", "Ingresa tu contraseña"); return; }
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}) },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Error en inicio de sesión");
    } else {
      alert("Sesión iniciada");
    }
  });
}

fetchCsrf();

// Sidebar: resaltado activo al hacer scroll
const sidebarMenu = document.querySelector('.home-menu');
if (sidebarMenu) {
  const links = Array.from(sidebarMenu.querySelectorAll('a[href^="#"]'));
  const sectionByEl = new Map();
  links.forEach((link) => {
    const id = link.getAttribute('href').slice(1);
    const section = document.getElementById(id);
    if (section) sectionByEl.set(section, link);
  });
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const link = sectionByEl.get(entry.target);
        if (!link) return;
        if (entry.isIntersecting) {
          links.forEach((a) => a.removeAttribute('aria-current'));
          link.setAttribute('aria-current', 'true');
        }
      });
    },
    { rootMargin: '-60% 0px -35% 0px', threshold: 0.15 }
  );
  sectionByEl.forEach((_, section) => observer.observe(section));
  sidebarMenu.addEventListener('click', (ev) => {
    const t = ev.target;
    if (t && t.tagName === 'A') {
      links.forEach((a) => a.removeAttribute('aria-current'));
      t.setAttribute('aria-current', 'true');
    }
  });
}