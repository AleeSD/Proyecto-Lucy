# Checklist de pruebas web

## Accesibilidad (WCAG AA)
- [ ] Alternativas textuales en imágenes (alt)
- [ ] Navegación por teclado y foco visible
- [ ] Semántica HTML5 correcta (header, nav, main, section, footer)
- [ ] Contraste suficiente en textos y botones
- [ ] Respeto a `prefers-reduced-motion`

## Rendimiento
- [ ] Imágenes con `loading="lazy"` y dimensiones definidas
- [ ] Fondo servido por CSS y cacheado
- [ ] Minimización de repintados y uso de `backdrop-filter` moderado

## Seguridad
- [ ] CSRF emitido y validado en formularios
- [ ] Cookie `session_token` HttpOnly establecida en login
- [ ] Acceso a `/chat` bloqueado sin sesión

## Flujo
- [ ] Registro exitoso redirige a `/login`
- [ ] Login exitoso redirige a `/chat`
- [ ] Logout redirige a `/`

## Validación
- [ ] HTML/CSS válido según W3C (validator.w3.org)
- [ ] Consola sin errores en navegación estándar
- [ ] Endpoints devuelven códigos HTTP correctos