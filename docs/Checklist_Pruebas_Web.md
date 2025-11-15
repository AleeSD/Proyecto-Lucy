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

## Inicio (Sidebar de información)
- [ ] Sidebar visible solo en `/` y oculto en vistas de auth
- [ ] Enlaces del sidebar apuntan a anclajes de la página y funcionan
- [ ] Reserva del 30% presente y sin romper layout
- [ ] Comportamiento responsive correcto (sidebar arriba en ≤900px)
- [ ] Legibilidad y contraste adecuados en enlaces y encabezados

## Validación
- [ ] HTML/CSS válido según W3C (validator.w3.org)
- [ ] Consola sin errores en navegación estándar
- [ ] Endpoints devuelven códigos HTTP correctos