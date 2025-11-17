const SESSION_KEY = "lucy_session_id";
let sessionId = localStorage.getItem(SESSION_KEY) || null;
let csrfToken = null;
const $messages = document.getElementById("messages");
const $form = document.getElementById("chat-form");
const $input = document.getElementById("message-input");
const $stats = document.getElementById("stats");
const $statsContent = document.getElementById("stats-content");
const $sessionFooter = document.getElementById("session-id");
const $logout = document.getElementById("logout");
const $wsStatus = document.getElementById("ws-status");
let ws = null;
let reconnectTimer = null;
let typingEl=null;
let isStreaming=false;
function setWSStatus(ok){ if(!$wsStatus) return; $wsStatus.textContent = `WS: ${ok?'conectado':'desconectado'}`; $wsStatus.className = `badge ${ok?'ok':'err'}`; }
function ensureWS(){
  if(ws && ws.readyState===1) return;
  if(ws && ws.readyState===0) return;
  ws = new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/chat`);
  ws.onopen = ()=>{ setWSStatus(true); };
  ws.onclose = ()=>{ setWSStatus(false); if(reconnectTimer) clearTimeout(reconnectTimer); reconnectTimer = setTimeout(()=>ensureWS(), 1500); };
  ws.onerror = ()=>{ setWSStatus(false); };
  ws.onmessage = (ev)=>{
    const data = JSON.parse(ev.data);
    if(data.cancelled){ finishTyping(''); isStreaming=false; return; }
    if(data.partial){ updateTyping(data.delta); isStreaming=true; ensureCancelButton(); return; }
    if(data.final){ finishTyping(data.response); isStreaming=false; refreshStats(); ensureCancelButton(); return; }
    if(data.response){ addMessage('bot', data.response); refreshStats(); }
  };
}
function createTyping(){ typingEl=document.createElement('div'); typingEl.className='msg bot typing'; typingEl.innerHTML=`<div class="avatar">🤖</div><div class="bubble"></div>`; $messages.appendChild(typingEl); $messages.scrollTop=$messages.scrollHeight; }
function updateTyping(delta){ if(!typingEl) createTyping(); const b=typingEl.querySelector('.bubble'); b.textContent = `${b.textContent}${b.textContent? ' ' : ''}${delta}`; $messages.scrollTop=$messages.scrollHeight; }
function finishTyping(text){ if(!typingEl){ if(text) addMessage('bot', text); return; } const b=typingEl.querySelector('.bubble'); b.textContent = text; typingEl.classList.remove('typing'); typingEl=null; }
function ensureCancelButton(){ let c=document.getElementById('btn-cancel'); if(!c){ c=document.createElement('button'); c.id='btn-cancel'; c.type='button'; c.className='btn secondary'; c.textContent='Cancelar'; c.addEventListener('click', ()=>{ if(ws && ws.readyState===1){ ws.send(JSON.stringify({ cancel:true, session_id: sessionId })); } }); document.getElementById('chat-form').appendChild(c); } c.style.display = isStreaming ? 'inline-block' : 'none'; }


function ensureSession(id){ if(!sessionId){ sessionId = id || `web_${Date.now()}`; localStorage.setItem(SESSION_KEY, sessionId); } if($sessionFooter) $sessionFooter.textContent = `Sesión: ${sessionId}`; }
function addMessage(role,text){ const item=document.createElement('div'); item.className=`msg ${role}`; item.innerHTML=`<div class="avatar">${role==='bot'?'🤖':'🧑'}</div><div class="bubble">${text}</div>`; $messages.appendChild(item); $messages.scrollTop = $messages.scrollHeight; }
async function fetchCsrf(){ try { const r=await fetch('/api/csrf'); const d=await r.json(); csrfToken=d.csrf_token; } catch{} }
async function refreshStats(){ try { const [statsRes, ctxRes] = await Promise.all([ fetch('/api/stats'), sessionId ? fetch(`/api/context?session_id=${encodeURIComponent(sessionId)}`) : Promise.resolve(null) ]); const stats=await statsRes.json(); const context = ctxRes ? await ctxRes.json() : {}; $statsContent.textContent = JSON.stringify({ stats, context }, null, 2); } catch{} }

$form.addEventListener('submit', async (e)=>{ e.preventDefault(); const btn=document.getElementById('btn-send'); btn.disabled=true; const text=$input.value.trim(); if(!text){ btn.disabled=false; return; } $input.value='';
  if(text.startsWith('/help')){ addMessage('user', text); addMessage('bot', 'Comandos: /help (ayuda), /clear (limpiar contexto), /lang es|en (cambiar idioma)'); btn.disabled=false; return; }
  if(text.startsWith('/clear')){ addMessage('user', text); await fetch('/api/clear',{ method:'POST', headers:{ 'X-Session-ID': sessionId || '' } }); $messages.innerHTML=''; addMessage('bot','Contexto limpiado'); btn.disabled=false; return; }
  if(text.startsWith('/lang ')){ const code = text.split(' ')[1]?.trim(); addMessage('user', text); const r = await fetch(`/api/lang?code=${encodeURIComponent(code)}`, { method:'POST', headers:{ ...(sessionId?{'X-Session-ID':sessionId}:{}) } }); const d = await r.json(); addMessage('bot', d.error? (d.error) : (`Idioma: ${d.language}`)); btn.disabled=false; return; }
  addMessage('user', text);
  try{ ensureWS(); createTyping(); ws.send(JSON.stringify({ message:text, session_id: sessionId })); ensureCancelButton(); btn.disabled=false; }
  catch{ const res = await fetch('/api/chat',{ method:'POST', headers:{ 'Content-Type':'application/json', ...(sessionId?{'X-Session-ID':sessionId}:{}), ...(csrfToken?{'X-CSRF-Token':csrfToken}:{}) }, body: JSON.stringify({ message:text, session_id:sessionId }) }); const data = await res.json(); btn.disabled=false; if(!res.ok){ addMessage('bot', data.error || 'No autorizado'); if(res.status===401){ window.location.href='/login'; } return; } ensureSession(data.session_id); addMessage('bot', data.response); refreshStats(); }
});

document.getElementById('toggle-stats')?.addEventListener('click',()=>{ $stats.classList.toggle('hidden'); if(!$stats.classList.contains('hidden')) refreshStats(); });
$logout.addEventListener('click', async ()=>{ await fetch('/api/logout',{ method:'POST' }); window.location.href = '/'; });

ensureSession(); fetchCsrf(); ensureWS(); addMessage('bot', 'Hola, soy Lucy. Tu asistente de I.A de escritorio. Puedo conversar, mantener contexto y ayudarte con funciones del sistema. ¿En qué puedo ayudarte hoy?');