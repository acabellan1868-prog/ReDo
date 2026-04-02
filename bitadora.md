# Bitadora — ReDo

Registro detallado del trabajo día a día.

---

## 2026-04-01 — Gestión de tipos de dispositivos (Opción A: SQLite)

### ✅ Completado

**Backend:**
- [x] Migración esquema.sql v2 → v3: nueva tabla `tipos_dispositivo`
- [x] bd.py: migración que puebla 11 tipos iniciales (teléfono, portátil, tablet, TV, impresora, router, IoT, servidor, consola, otro)
- [x] modelos.py: agregados modelos Pydantic para tipos (`TipoDispositivoRespuesta`, `TipoDispositivoCrear`, `TipoDispositivoActualizar`)
- [x] app/rutas/tipos.py: nuevo módulo con CRUD completo
  - `GET /api/tipos` — listar tipos ordenados por nombre
  - `POST /api/tipos` — crear tipo (validar clave única)
  - `PUT /api/tipos/{clave}` — editar nombre/icono
  - `DELETE /api/tipos/{clave}` — eliminar (reasigna dispositivos a 'otro')
- [x] principal.py: registrado router `/api/tipos`
- [x] rutas/dispositivos.py: validación de tipo existente al actualizar dispositivo

**Frontend:**
- [x] static/index.html: removidos `<option>` hardcodeados de selects de tipo (modal + filtro)
- [x] Comentarios indicando que se pueblan dinámicamente desde `/api/tipos`

### ✅ Completado (continuación 2026-04-02)

**Frontend:**
- [x] Función `cargarTipos()` que carga tipos desde `/api/tipos`
- [x] Puebla dinámicamente `#modalTipo` (modal de edición)
- [x] Puebla dinámicamente `#filtroTipo` (filtro de tipo en panel)
- [x] Actualiza `TIPOS_ICONO` dinámicamente para que iconos en tabla usen datos de API
- [x] Integrada en inicialización (`cargarTipos()` se ejecuta al cargar página)

### 📋 Tareas pendientes

1. **Testing**: Verificar flujo completo (crear, editar, eliminar tipos) en VM
2. **Documentación**: Actualizar CLAUDE.md con API `/api/tipos`
3. **Despliegue**: Hacer push a VM y testear

---

## Notas

- **Razón de la Opción A (SQLite):** Ya existe FastAPI + SQLite, los tipos son datos (no configuración), es el lugar natural. Alternativas (env vars, JSON) son menos mantenibles.
- **Impacto:** No rompe nada existente; los 11 tipos iniciales cubren el 99% de dispositivos hogareños.
- **Próximo paso:** Si se termina hoy, se podría agregar una pestaña "Tipos" en ReDo para gestionar el catálogo desde la UI.
