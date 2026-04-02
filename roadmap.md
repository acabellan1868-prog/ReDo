# Roadmap — ReDo

## Estado actual

**Fecha:** 2026-03-26

Implementadas las mejoras de tipo/zona y presencia de dispositivos.
Desplegado en VM 101 y funcionando.

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

### Fase 3 — Mejoras de usabilidad ✅

- [x] Tabla responsive — tarjetas en móvil (2026-03-22)
- [x] Notificaciones ntfy al detectar dispositivo nuevo
- [x] Agrupación de dispositivos por tipo y zona (2026-03-26)
- [x] Modal de edición (nombre, tipo, zona) en lugar de prompt (2026-03-26)
- [x] Filtros combinados: confiabilidad + tipo + zona (2026-03-26)
- [x] Iconos Material Symbols por tipo de dispositivo (2026-03-26)
- [x] ~~Confirmación antes de cambiar estado~~ — Descartado: el modal de edición ya actúa como confirmación, y es más ágil sin paso extra (2026-03-26)

### Fase 4 — Presencia ✅

- [x] Tabla `presencia` — registro de cada avistamiento (2026-03-26)
- [x] Tabla `presencia_diaria` — agregación para datos > 180 días (2026-03-26)
- [x] Job nocturno de agregación (APScheduler, 03:00) (2026-03-26)
- [x] Endpoint presencia por dispositivo con cálculo de franjas (2026-03-26)
- [x] Endpoint timeline general por día (2026-03-26)
- [x] Pestaña "Presencia" con timeline Gantt visual (2026-03-26)
- [x] Panel de detalle por dispositivo — clic en fila para ver presencia individual con barras por día y franjas horarias (2026-03-26)
- [x] Marcas de hora completas (0-24) en desktop, cada 3h en móvil (2026-03-26)
- [x] Responsive completo del panel de detalle (columnas, fuentes, padding adaptados a móvil) (2026-03-26)

### Fase 5 — Configuración y mejoras pendientes

- [x] Gestión de tipos de dispositivos (SQLite CRUD) — tabla tipos_dispositivo, API /api/tipos, frontend dinámico (2026-04-01 a 2026-04-02)
- [ ] Pantalla de configuración en ReDo (red, intervalo, presencia días, NTFY)
- [ ] Vista agrupada por zona (dispositivos agrupados en vez de lista plana)
- [x] Auto-detección de tipo por fabricante — 60+ reglas, campo tipo_auto, indicador en modal (2026-03-26)
- [ ] Historial de escaneos con gráfico temporal
- [ ] Exportar listado de dispositivos
