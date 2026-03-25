# Roadmap — ReDo

## Estado actual

**Fecha:** 2026-03-22

Tabla de dispositivos responsive completada y desplegada. En pantallas ≤ 768 px
las filas se convierten en tarjetas apiladas con etiquetas (`data-label`) y
botones de acción accesibles. Corregido también el desbordamiento lateral
(overflow del wrapper). Commits `c9d7ec4` y `4a7a3e9` subidos a GitHub.

**Próximo paso:** Verificar en móvil que las tarjetas se ven correctamente
tras desplegar con `actualizar.sh`.

---

## Fases

### Fase 1 — MVP funcional ✅

- [x] Backend FastAPI con escaneo ARP/nmap
- [x] Base de datos SQLite para persistir dispositivos
- [x] API REST: listar, editar, escanear
- [x] Frontend SPA vanilla con tabla de dispositivos
- [x] Filtros por estado (todos / confiables / desconocidos)
- [x] Botón de escaneo manual
- [x] Nombre personalizado para dispositivos (notas)

### Fase 2 — Integración hogarOS ✅

- [x] Docker con `network_mode: host`
- [x] Proxy Nginx en `/red/`
- [x] Design system Living Sanctuary (`hogar.css`)
- [x] Drawer lateral con navegación entre apps
- [x] Toggle tema claro/oscuro

### Fase 3 — Mejoras de usabilidad (en curso)

- [x] Tabla responsive — tarjetas en móvil (2026-03-22)
- [ ] Confirmación antes de cambiar estado de un dispositivo
- [ ] Notificaciones ntfy al detectar dispositivo nuevo

### Fase 4 — Futuro

- [ ] Historial de escaneos con gráfico temporal
- [ ] Agrupación de dispositivos por tipo
- [ ] Exportar listado de dispositivos
