# Plan de Integración Híbrida: Django + FastAPI para Lucy AI

## Objetivo y Alcance
- Integrar un proyecto Django dentro de la aplicación FastAPI actual para añadir administración (Django Admin), ORM y vistas adicionales, manteniendo la API y el chat en FastAPI.
- Mantener el motor `LucyAI` y la base de datos actual sin cambios.

## Referencias del Código Actual
- App FastAPI y rutas: `src/lucy/web/app.py:30` crea la app; `src/lucy/web/app.py:239` sirve páginas HTML; `src/lucy/web/app.py:87` chat API; `src/lucy/web/app.py:223` WebSocket.
- Arranque del servidor: `lucy.py:547` inicia Uvicorn con `create_app()`.
- Motor IA: `src/lucy/lucy_ai.py:32` inicializa; `src/lucy/lucy_ai.py:239` procesa mensajes.
- DB SQLite: `config/config.json:24–31` y conexiones en `src/lucy/database.py:140`.
- Autenticación y CSRF: `src/lucy/web/app.py:84` cookies `session_token`; `src/lucy/web/app.py:137` CSRF.

## Arquitectura Propuesta
- FastAPI sigue sirviendo:
  - `/` (registro e información), `/login`, `/chat` (protegido).
  - Endpoints: `POST /api/register`, `POST /api/login`, `POST /api/logout`, `POST /api/chat`.
  - WebSocket: `/ws/chat`.
- Django se monta bajo `/django` usando WSGIMiddleware:
  - `/django/admin` para panel de administración.
  - Rutas adicionales informativas/CMS si se requieren.

## Requerimientos Técnicos
- Python 3.8+ y entorno virtual activo.
- Paquetes:
  - `fastapi`, `uvicorn`, `pydantic` (ya presentes).
  - `django`, `djangorestframework`, `channels` (para admin/ORM y websockets si se migra completamente).
- Base de datos: `data/conversations.db` (SQLite).
- Estáticos: carpeta `src/lucy/web/static/assets`, mantener imágenes desde `src/lucy/web/static/assets/img`.

## Decisiones Clave
- Autenticación:
  - Mantener cookie `session_token` HttpOnly para acceso a `/chat` en FastAPI.
  - Usar sesiones Django para `/django/admin` y vistas Django.
- CSRF:
  - FastAPI conserva `GET /api/csrf` y verificación en endpoints.
  - Formularios Django usan CSRF nativo.
- ORM:
  - Integrar Django ORM apuntando a la SQLite existente. Generar modelos con `inspectdb` y revisar `managed=False`.
- WebSocket:
  - Continuar con FastAPI para `@app.websocket("/ws/chat")`.
  - Si se migra a Django Channels, planificar transición posterior.

## Pasos de Implementación (Híbrido)
1) Instalar dependencias Django
```bash
pip install django djangorestframework channels
```

2) Crear proyecto Django dentro del repositorio
```bash
django-admin startproject lucy_site
```
Estructura resultante:
```
lucy_site/
  manage.py
  lucy_site/
    settings.py
    urls.py
    asgi.py
    wsgi.py
```

3) Configurar la base de datos en `lucy_site/lucy_site/settings.py`
```python
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / '..' / 'data' / 'conversations.db',
  }
}
```
- Ajustar `BASE_DIR` según sea necesario; probar la ruta absoluta si la relativa no funciona.

4) Configurar estáticos en Django
```python
STATIC_URL = '/djstatic/'
STATICFILES_DIRS = [BASE_DIR / '..' / 'src' / 'lucy' / 'web' / 'static' / 'assets']
```
- Para Admin, ejecutar `python manage.py collectstatic` y montar esa carpeta si se requiere.

5) Generar modelos desde la DB existente
```bash
cd lucy_site
python manage.py inspectdb > app_models.py
```
- Revisar `managed = False` en `Meta`. Mantenerlo para no permitir a Django gestionar tablas ya usadas por FastAPI.
- Dividir modelos en una app Django: `python manage.py startapp core_models` y mover `app_models.py` a `core_models/models.py`. Registrar en `INSTALLED_APPS`.

6) Habilitar Django Admin
```bash
python manage.py migrate
python manage.py createsuperuser
```
- Registrar los modelos en `core_models/admin.py` para visualización.

7) Montar Django dentro de FastAPI
- Editar `src/lucy/web/app.py` para montar WSGI:
```python
from django.core.wsgi import get_wsgi_application
from fastapi.middleware.wsgi import WSGIMiddleware

# dentro de create_app()
django_app = get_wsgi_application()
app.mount('/django', WSGIMiddleware(django_app))

# si usas collectstatic para admin
from fastapi.staticfiles import StaticFiles
app.mount('/djstatic', StaticFiles(directory='lucy_site/staticfiles'), name='djstatic')
```
- Mantener assets propios en `/assets` ya montados.

8) Rutas y protección
- FastAPI:
  - Mantener `/chat` con verificación de cookie `session_token`.
  - Mantener `CSRF` en `/api/register` y `/api/login`.
- Django:
  - Acceso a `/django/admin` con sesión de Django.

9) Arranque y verificación
```bash
python lucy.py --api
```
- Probar:
  - `http://localhost:8000/` (registro + info IA)
  - `http://localhost:8000/login`
  - `http://localhost:8000/chat` (autenticado)
  - `http://localhost:8000/django/admin` (Django Admin)

## Ajustes de Estáticos y Fondo
- Fondo unificado en CSS: `src/lucy/web/static/assets/styles.css:1` usa `background.jpg`.
- Avatar consistente: aplicado en headers (`register.html:11`, `login.html:11`, `chat.html:11`).
- Mantener opacidad 85% y `backdrop-filter` moderado para rendimiento.

## Diseño de Inicio de Sesión (UI)
### Tipografía
- Aumentar tamaño base en vistas de login en 15% y ajustar interlineado proporcional.
- Aplicación sugerida usando scope por vista:
```css
.login-layout { font-size: 1.15em; line-height: 1.6; }
.login-layout h1, .login-layout h2 { line-height: 1.25; }
.login-layout .subtitle { font-size: 0.9em; }
```

### Formulario
- Incrementar ancho del contenedor de login en 20% y mantener padding ≥ 15px.
```css
.login-card { width: min(92vw, 864px); }
.login-card, .login-card .field input { padding: 15px; }
```
- Mantener el diseño flotante centrado usando `center-wrap` + `float-card`.

## Sidebar de Atajos (vertical)
- Reorganizar atajos en un sidebar vertical con espaciado modular y reserva del 30% para expansión.
```html
<main class="center-wrap login-layout">
  <div class="login-grid">
    <aside class="sidebar">
      <nav class="sidebar-menu" aria-label="Atajos">
        <a class="item" href="/register">Registro</a>
        <a class="item" href="/login">Inicio de sesión</a>
        <a class="item" href="/">Inicio</a>
      </nav>
      <div class="sidebar-reserved" aria-hidden="true"></div>
    </aside>
    <section class="float-card login-card">...</section>
  </div>
</main>
```
```css
.login-grid { display: grid; grid-template-columns: 280px 1fr; gap: var(--space-4); }
.sidebar { background: rgba(17,24,39,0.5); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: var(--space-4); }
.sidebar-menu { display: flex; flex-direction: column; gap: var(--space-3); }
.sidebar-menu .item { padding: var(--space-3) var(--space-4); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; text-decoration: none; color: var(--text); background: rgba(255,255,255,0.06); }
.sidebar-reserved { min-height: 30%; }
@media (max-width: 900px) {
  .login-grid { grid-template-columns: 1fr; }
  .sidebar { order: -1; }
}
```

## Sistema de Diseño: componentes y tokens
- Mantener coherencia con el sistema actual; añadir tokens de espaciado reutilizables.
```css
:root {
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-5: 20px;
}
```
- Componentes reutilizables:
  - `login-layout`: scope tipográfico para la vista.
  - `login-grid`: layout con sidebar + contenido.
  - `login-card`: variante de `float-card` con ancho ampliado y padding mínimo.
- Documentación de estilos: usar estos nombres en HTML para vistas de login; respetar colores, sombras y bordes existentes.

## Consideraciones de Seguridad
- FastAPI: cookies HttpOnly (`src/lucy/web/app.py:199`), CSRF (`src/lucy/web/app.py:137`).
- Django: CSRF y sesiones nativas; revisar `ALLOWED_HOSTS`, `SECURE_*` si se despliega en producción.
- Documentar rutas protegidas y origen de tokens.

## Pruebas y Validación
- Flujo:
  - Registro → redirección a `/login` → login → `/chat`.
  - Logout en chat → `/`.
- Admin:
  - Ingreso a `/django/admin`, verificar modelos generados por `inspectdb`.
- Accesibilidad y rendimiento:
  - Validar WCAG AA; revisar `docs/Checklist_Pruebas_Web.md`.
- Endpoints:
  - `POST /api/register`, `POST /api/login`, `POST /api/chat`, `POST /api/logout`.

## Riesgos y Mitigaciones
- Plugins dinámicos: rutas relativas en `src/lucy/plugins/manager.py:96–115`. Mantener estructura y paths.
- Estáticos Admin: montar `/djstatic` y usar `collectstatic` si fuera necesario.
- Doble sesión: no cruzar sesiones Django con las de FastAPI; dejar `session_token` solo para chat.
- `inspectdb`: modelos con `managed=False` para no alterar tablas existentes.

## Roadmap de Migración Completa (opcional)
- Reescribir vistas registro/login en Django.
- DRF para endpoints; mover lógica de validación de Pydantic a serializers.
- Django Channels para `/ws/chat`.
- Unificar auth en Django (`auth_user`) y migrar usuarios.

## Comandos Útiles
```bash
# Instalar dependencias
pip install django djangorestframework channels

# Crear proyecto Django
django-admin startproject lucy_site

# Generar modelos y habilitar admin
cd lucy_site
python manage.py inspectdb > app_models.py
python manage.py migrate
python manage.py createsuperuser

# Ejecutar servidor híbrido
cd ..
python lucy.py --api
```

## Checklist de Entrega
- Proyecto Django creado y configurado con SQLite.
- Modelos generados por `inspectdb` y registrados en Admin.
- Django montado en FastAPI bajo `/django` y estáticos servidos.
- Rutas FastAPI intactas y protegidas.
- Pruebas de flujo y accesibilidad completadas.

## Progreso de Implementación
- Paso 1: Coexistencia básica
  - Instalados paquetes: `django`, `djangorestframework`, `channels`.
  - Proyecto creado: carpeta `lucy_site/` con `manage.py` y `settings.py`.
  - Configuración DB y estáticos en `lucy_site/lucy_site/settings.py:75-81` y `lucy_site/lucy_site/settings.py:117-122`.
- Paso 2: Enrutamiento híbrido
  - Montado Django en FastAPI: `src/lucy/web/app.py:9` (imports) y `src/lucy/web/app.py:258-263` (`/django`).
  - Assets de FastAPI siguen montados en `/assets`.
- Pruebas
  - Ejecutado `pytest -q`: suite verde, cobertura total 46.54%.
  - Arranque de servidor con `python lucy.py --api` válido; puerto 8000 ocupado en el sistema, verificar con `config.json` si se necesita cambiar a `8001`.
- Paso 3: Comunicación interna
  - Añadido endpoint de salud para verificar configuración de Django desde FastAPI: `src/lucy/web/app.py:218-224` (`GET /api/health/django`).
- Paso 4: Ajustes de UI y navegación
  - Avatar aplicado desde `/assets/img/Avatar_Lucy.jpg` en todas las vistas.
  - Botones "Registro" y "Inicio de sesión" ubicados en la esquina superior izquierda.
  - Opacidad de paneles ajustada al rango 75–80% para legibilidad y fondo visible.
  - Transiciones suaves añadidas a botones, paneles, entradas y menú rápido.
  - Vista inicial (`/`) rediseñada para mostrar solo información y accesos.