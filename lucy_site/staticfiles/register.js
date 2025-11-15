let csrfToken = null;
async function fetchCsrf(){ try { const r = await fetch('/api/csrf'); const d = await r.json(); csrfToken = d.csrf_token; } catch {} }
function setError(id, msg){ const el = document.getElementById(id); if(el) el.textContent = msg || ''; }
function validateUsername(v){ return /^[A-Za-z0-9]{6,}$/.test(v); }
function validateEmail(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
function validateNotEmpty(v){ return v.trim().length>0; }
function validateDob(v){ if(!v) return false; const dob = new Date(v); const now = new Date(); const min = new Date(now.getFullYear()-18, now.getMonth(), now.getDate()); return dob<=min; }
function validatePassword(v){ return /[A-Z]/.test(v)&&/[a-z]/.test(v)&&/[0-9]/.test(v)&&v.length>=8; }
function attachRealtime(){ const u=document.getElementById('reg-username'); const e=document.getElementById('reg-email'); const f=document.getElementById('reg-first'); const l=document.getElementById('reg-last'); const d=document.getElementById('reg-dob'); const p=document.getElementById('reg-password');
  u.addEventListener('input',()=>setError('err-username', validateUsername(u.value)?'':'Mínimo 6, solo letras y números'));
  e.addEventListener('input',()=>setError('err-email', validateEmail(e.value)?'':'Formato de correo inválido'));
  f.addEventListener('input',()=>setError('err-first', validateNotEmpty(f.value)?'':'Ingresa tus nombres'));
  l.addEventListener('input',()=>setError('err-last', validateNotEmpty(l.value)?'':'Ingresa tus apellidos'));
  d.addEventListener('change',()=>setError('err-dob', validateDob(d.value)?'':'Debes ser mayor de 18 años'));
  p.addEventListener('input',()=>setError('err-password', validatePassword(p.value)?'':'Mínimo 8, incluye mayúscula, minúscula y dígito'));
}
document.getElementById('register-form').addEventListener('submit', async (e)=>{
  e.preventDefault(); const btn = document.getElementById('btn-register'); btn.disabled = true; 
  const payload = { username: document.getElementById('reg-username').value.trim(), email: document.getElementById('reg-email').value.trim(), first_name: document.getElementById('reg-first').value.trim(), last_name: document.getElementById('reg-last').value.trim(), dob: document.getElementById('reg-dob').value, password: document.getElementById('reg-password').value };
  let ok=true; if(!validateUsername(payload.username)){ setError('err-username','Mínimo 6, solo letras y números'); ok=false; }
  if(!validateEmail(payload.email)){ setError('err-email','Formato de correo inválido'); ok=false; }
  if(!validateNotEmpty(payload.first_name)){ setError('err-first','Ingresa tus nombres'); ok=false; }
  if(!validateNotEmpty(payload.last_name)){ setError('err-last','Ingresa tus apellidos'); ok=false; }
  if(!validateDob(payload.dob)){ setError('err-dob','Debes ser mayor de 18 años'); ok=false; }
  if(!validatePassword(payload.password)){ setError('err-password','Mínimo 8, incluye mayúscula, minúscula y dígito'); ok=false; }
  if(!ok){ btn.disabled=false; return; }
  const res = await fetch('/api/register',{ method:'POST', headers:{ 'Content-Type':'application/json', ...(csrfToken?{'X-CSRF-Token':csrfToken}:{}) }, body: JSON.stringify(payload) }); const data = await res.json();
  btn.disabled=false; if(!res.ok){ alert(data.error||'Error en registro'); } else { window.location.href = '/login'; }
});
function initQuickMenu(){
  const links = Array.from(document.querySelectorAll('.quick-menu a'));
  links.forEach(a=>a.addEventListener('click',()=>{
    links.forEach(l=>l.removeAttribute('aria-current'));
    a.setAttribute('aria-current','true');
  }));
  const sections = links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
  const io = new IntersectionObserver((entries)=>{
    const visible = entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if(!visible) return; const id = `#${visible.target.id}`; links.forEach(l=>{
      if(l.getAttribute('href')===id) l.setAttribute('aria-current','true'); else l.removeAttribute('aria-current');
    });
  },{threshold:[0.3,0.6]});
  sections.forEach(s=>io.observe(s));
}
attachRealtime(); initQuickMenu(); fetchCsrf();