from typing import Optional, Dict, Any
import os
import time
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from django.core.wsgi import get_wsgi_application
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
import secrets

from lucy import get_config_manager
from lucy.lucy_ai import LucyAI
from lucy.database import ConversationDB
from lucy.logging_system import log_conversation, log_performance, get_logger


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def _gen_session_id() -> str:
    return f"web_{int(time.time())}_{str(uuid.uuid4())[:8]}"


def create_app() -> FastAPI:
    config_manager = get_config_manager()
    config = config_manager.get_all()
    logger = get_logger(__name__)

    app = FastAPI(title=config.get("app", {}).get("name", "Lucy AI"),
                  version=config.get("app", {}).get("version", "1.0.0"),
                  docs_url="/api/docs",
                  redoc_url="/api/redoc")

    api_cfg = config.get("api", {})

    if api_cfg.get("cors_enabled", True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    static_dir = config_manager.project_root / "src" / "lucy" / "web" / "static"
    assets_dir = static_dir / "assets"

    app.state.config_manager = config_manager
    app.state.db = ConversationDB(config.get("database", {}).get("path", "data/conversations.db"))
    app.state.engine = LucyAI(config_manager)
    app.state.rate_limit = {
        "enabled": api_cfg.get("rate_limit", {}).get("enabled", True),
        "rpm": int(api_cfg.get("rate_limit", {}).get("requests_per_minute", 60)),
        "buckets": {}
    }
    app.state.auth_tokens = {}

    class RegisterRequest(BaseModel):
        username: str
        email: EmailStr
        first_name: str
        last_name: str
        dob: date
        password: str

    class LoginRequest(BaseModel):
        identifier: str
        password: str

    def _require_csrf(request: Request):
        token_header = request.headers.get("x-csrf-token")
        token_cookie = request.cookies.get("csrftoken")
        if not token_header or not token_cookie or token_header != token_cookie:
            return False
        return True

    def _require_auth(request: Request) -> bool:
        token = request.cookies.get("session_token")
        return bool(token and token in app.state.auth_tokens)

    @app.post("/api/chat")
    async def chat(req: ChatRequest, request: Request):
        if not _require_auth(request):
            return JSONResponse(status_code=401, content={"error": "No autorizado"})
        session_id = req.session_id or request.headers.get("X-Session-ID") or _gen_session_id()

        if app.state.rate_limit["enabled"]:
            bucket = app.state.rate_limit["buckets"].setdefault(session_id, [])
            now = time.time()
            window = 60.0
            rpm = max(1, app.state.rate_limit["rpm"])
            bucket[:] = [t for t in bucket if now - t < window]
            if len(bucket) >= rpm:
                return JSONResponse(status_code=429, content={"error": "Rate limit excedido"})
            bucket.append(now)

        start = time.time()
        response = app.state.engine.process_message(req.message, context=req.context or {})
        elapsed = time.time() - start

        try:
            log_performance("response_time", elapsed, unit="seconds", tags={"feature": "web_api"})
            log_conversation(
                session_id=session_id,
                user_input=req.message,
                bot_response=response,
                intent=app.state.engine.get_last_intent(),
                confidence=app.state.engine.get_last_confidence(),
                language=app.state.engine.get_current_language(),
                response_time=elapsed
            )
        except Exception:
            pass

        try:
            app.state.db.save_conversation(
                session_id=session_id,
                user_input=req.message,
                bot_response=response,
                language=app.state.engine.get_current_language(),
                confidence=app.state.engine.get_last_confidence(),
                intent=app.state.engine.get_last_intent(),
                response_time=elapsed,
                context=req.context or {}
            )
        except Exception:
            logger.warning("No se pudo guardar conversación en DB")

        return {"session_id": session_id, "response": response}

    @app.get("/api/csrf")
    async def csrf(request: Request):
        token = secrets.token_urlsafe(32)
        resp = JSONResponse({"csrf_token": token})
        resp.set_cookie("csrftoken", token, secure=False, samesite="lax")
        return resp

    @app.post("/api/register")
    async def register(req: RegisterRequest, request: Request):
        if not _require_csrf(request):
            return JSONResponse(status_code=403, content={"error": "CSRF inválido"})

        u = req.username.strip()
        if not u or len(u) < 6 or not u.isalnum():
            return JSONResponse(status_code=422, content={"error": "Usuario inválido: mínimo 6, solo letras y números"})

        fn = req.first_name.strip()
        ln = req.last_name.strip()
        if not fn or not ln:
            return JSONResponse(status_code=422, content={"error": "Nombres y apellidos son obligatorios"})

        today = date.today()
        age = (today - req.dob).days // 365
        if age < 18:
            return JSONResponse(status_code=422, content={"error": "Debes ser mayor de 18 años"})

        pw = req.password.strip()
        has_upper = any(c.isupper() for c in pw)
        has_lower = any(c.islower() for c in pw)
        has_digit = any(c.isdigit() for c in pw)
        if not (has_upper and has_lower and has_digit) or len(pw) < 8:
            return JSONResponse(status_code=422, content={"error": "Contraseña inválida: mínimo 8, incluye mayúscula, minúscula y dígito"})

        try:
            created = app.state.db.create_user(u, req.email, fn, ln, req.dob.isoformat(), pw)
            if not created:
                return JSONResponse(status_code=409, content={"error": "Usuario o correo ya existe"})
        except Exception:
            return JSONResponse(status_code=500, content={"error": "Error al registrar usuario"})

        return {"ok": True}

    @app.post("/api/login")
    async def login(req: LoginRequest, request: Request):
        if not _require_csrf(request):
            return JSONResponse(status_code=403, content={"error": "CSRF inválido"})

        identifier = req.identifier.strip()
        password = req.password.strip()
        if not identifier or not password:
            return JSONResponse(status_code=422, content={"error": "Credenciales obligatorias"})

        try:
            ok, user = app.state.db.verify_login(identifier, password)
            if not ok:
                return JSONResponse(status_code=401, content={"error": "Usuario/contraseña inválidos"})
        except Exception:
            return JSONResponse(status_code=500, content={"error": "Error al iniciar sesión"})

        token = secrets.token_urlsafe(32)
        app.state.auth_tokens[token] = {"username": user.get("username"), "email": user.get("email")}
        resp = JSONResponse({"ok": True})
        resp.set_cookie("session_token", token, secure=False, httponly=True, samesite="lax")
        return resp

    @app.post("/api/logout")
    async def logout():
        resp = JSONResponse({"ok": True})
        resp.delete_cookie("session_token")
        return resp

    @app.get("/api/context")
    async def context(session_id: str):
        return {
            "session_id": session_id,
            "history": app.state.db.get_conversation_history(session_id, limit=20),
            "engine_context": app.state.engine.get_conversation_context(),
        }

    @app.get("/api/stats")
    async def stats():
        return {
            "engine": app.state.engine.get_statistics(),
            "db": app.state.db.get_database_stats(),
        }

    @app.get("/api/health/django")
    async def health_django():
        try:
            from django.conf import settings as dj_settings
            db_name = str(dj_settings.DATABASES['default']['NAME'])
            return {"django": True, "db": db_name}
        except Exception:
            return {"django": False}

    @app.websocket("/ws/chat")
    async def ws_chat(ws: WebSocket):
        await ws.accept()
        session_id = None
        try:
            while True:
                payload = await ws.receive_json()
                message = payload.get("message", "")
                session_id = payload.get("session_id") or session_id or _gen_session_id()
                start = time.time()
                response = app.state.engine.process_message(message)
                elapsed = time.time() - start
                await ws.send_json({"session_id": session_id, "response": response, "t": elapsed})
        except WebSocketDisconnect:
            return

    # Rutas HTML con protección
    @app.get("/")
    async def home_page():
        with open(static_dir / "index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/register")
    async def register_page():
        with open(static_dir / "register.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/login")
    async def login_page():
        with open(static_dir / "login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    @app.get("/chat")
    async def chat_page(request: Request):
        if not _require_auth(request):
            return RedirectResponse(url="/login")
        with open(static_dir / "chat.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    # Montar assets estáticos
    app.mount("/assets", StaticFiles(directory=str(assets_dir), html=False), name="assets")

    # Montar Django bajo /django (coexistencia híbrida)
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lucy_site.settings")
        django_app = get_wsgi_application()
        app.mount("/django", WSGIMiddleware(django_app))
    except Exception:
        pass

    return app