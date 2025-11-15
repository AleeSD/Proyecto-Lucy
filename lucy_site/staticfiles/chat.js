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

function ensureSession(id){ if(!sessionId){ sessionId = id || `web_${Date.now()}`; localStorage.setItem(SESSION_KEY, sessionId); } if($sessionFooter) $sessionFooter.textContent = `Sesión: ${sessionId}`; }
function addMessage(role,text){ const item=document.createElement('div'); item.className=`msg ${role}`; item.innerHTML=`<div class="avatar">${role==='bot'?'🤖':'🧑'}</div><div class="bubble">${text}</div>`; $messages.appendChild(item); $messages.scrollTop = $messages.scrollHeight; }
async function fetchCsrf(){ try { const r=await fetch('/api/csrf'); const d=await r.json(); csrfToken=d.csrf_token; } catch{} }
async function refreshStats(){ try { const [statsRes, ctxRes] = await Promise.all([ fetch('/api/stats'), sessionId ? fetch(`/api/context?session_id=${encodeURIComponent(sessionId)}`) : Promise.resolve(null) ]); const stats=await statsRes.json(); const context = ctxRes ? await ctxRes.json() : {}; $statsContent.textContent = JSON.stringify({ stats, context }, null, 2); } catch{} }

$form.addEventListener('submit', async (e)=>{ e.preventDefault(); const btn=document.getElementById('btn-send'); btn.disabled=true; const text=$input.value.trim(); if(!text){ btn.disabled=false; return; } $input.value=''; addMessage('user', text); const res = await fetch('/api/chat',{ method:'POST', headers:{ 'Content-Type':'application/json', ...(sessionId?{'X-Session-ID':sessionId}:{}), ...(csrfToken?{'X-CSRF-Token':csrfToken}:{}) }, body: JSON.stringify({ message:text, session_id:sessionId }) }); const data = await res.json(); btn.disabled=false; if(!res.ok){ addMessage('bot', data.error || 'No autorizado'); if(res.status===401){ window.location.href='/login'; } return; } ensureSession(data.session_id); addMessage('bot', data.response); refreshStats(); });

document.getElementById('toggle-stats')?.addEventListener('click',()=>{ $stats.classList.toggle('hidden'); if(!$stats.classList.contains('hidden')) refreshStats(); });
$logout.addEventListener('click', async ()=>{ await fetch('/api/logout',{ method:'POST' }); window.location.href = '/'; });

ensureSession(); fetchCsrf();