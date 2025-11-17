let csrfToken = null;
function showToast(message, type = 'success'){
  let container = document.querySelector('.toast-container');
  if(!container){ container = document.createElement('div'); container.className='toast-container'; document.body.appendChild(container); }
  const toast = document.createElement('div'); toast.className = `toast ${type}`; toast.textContent = message; container.appendChild(toast);
  setTimeout(()=>{ toast.remove(); if(container.children.length===0) container.remove(); }, 7000);
}
async function fetchCsrf(){ try { const r=await fetch('/api/csrf'); const d=await r.json(); csrfToken=d.csrf_token; } catch{} }
function setError(id,msg){ const el=document.getElementById(id); if(el) el.textContent = msg||''; }
document.getElementById('login-form').addEventListener('submit', async (e)=>{
  e.preventDefault(); const btn=document.getElementById('btn-login'); btn.disabled=true;
  const payload={ identifier: document.getElementById('login-id').value.trim(), password: document.getElementById('login-password').value };
  if(!payload.identifier){ setError('err-login-id','Ingresa tu email o usuario'); btn.disabled=false; return; }
  if(!payload.password){ setError('err-login-password','Ingresa tu contraseña'); btn.disabled=false; return; }
  const res = await fetch('/api/login',{ method:'POST', headers:{ 'Content-Type':'application/json', ...(csrfToken?{'X-CSRF-Token':csrfToken}:{}) }, body: JSON.stringify(payload) });
  const data = await res.json(); btn.disabled=false;
  if(!res.ok){ showToast(data.error||'Error en inicio de sesión','error'); } else { showToast('Sesión iniciada correctamente','success'); setTimeout(()=>{ window.location.href = '/chat'; }, 1200); }
});
fetchCsrf();