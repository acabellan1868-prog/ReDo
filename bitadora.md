# Bitadora — ReDo

Registro detallado del trabajo día a día.

---

## 2026-04-02 — Fase 5: 3 tareas completadas ✅

### Tarea 1: Exportar CSV/JSON ✅

**Backend (app/rutas/dispositivos.py):**
- [x] Importaciones: `io`, `csv`, `StreamingResponse`, `JSONResponse`
- [x] Endpoint `GET /api/dispositivos/exportar/csv` con filtros aplicados
- [x] Endpoint `GET /api/dispositivos/exportar/json` con filtros aplicados
- [x] CSV generado con csv.DictWriter (escapa caracteres especiales)
- [x] JSON retorna datos completos
- [x] Headers HTTP de descarga (attachment)

**Frontend (static/index.html):**
- [x] Botón "Descargar" en toolbar con dropdown CSS
- [x] Opciones: CSV / JSON
- [x] Respeta filtros actuales (confiable, tipo, zona)
- [x] Dropdown cierra al hacer clic fuera
- [x] Nombre de archivo incluye timestamp

**Testing en VM:** ✅
```bash
curl "http://192.168.31.131/red/api/dispositivos/exportar/csv?tipo=iot" > dispositivos.csv
```

---

### Tarea 2: Vista agrupada por zona ✅

**Backend:** Sin cambios requeridos (agrupación en frontend)

**Frontend (static/index.html):**
- [x] Variable global `vistaAgrupada` para estado
- [x] Botón toggle "Vista: Lista / Vista: Agrupada" en toolbar
- [x] CSS grid para tarjetas responsivas (minmax 220px)
- [x] Función `renderizarAgrupado()` que agrupa por zona con Array.reduce()
- [x] Tarjetas con: icono tipo, nombre, MAC, IP, estado (badge), botones acción
- [x] Contador de dispositivos por zona
- [x] Zonas ordenadas alfabéticamente
- [x] Fallback a "Sin zona" para dispositivos sin zona
- [x] Mostrar/ocultar vistas según vistaAgrupada en `cargarDispositivos()`
- [x] Estilos: colores primarios, hover effects, tema claro/oscuro

**Testing en VM:** ✅
- Toggle vista lista ↔ vista agrupada funciona
- Filtros respetados en ambas vistas
- Responsive en móvil/tablet/desktop

---

### Tarea 3: Historial de escaneos con gráfico ✅

**Backend (app/rutas/escaneos.py):**
- [x] Nuevo endpoint `GET /api/escaneos/estadisticas/por-fecha?dias=N`
- [x] Query SQL con GROUP BY DATE(), calcula:
  - Cantidad de escaneos por día
  - Promedio de dispositivos encontrados
  - Máximo de nuevos dispositivos
  - Duración promedio en segundos
- [x] Período configurable (7, 30, 90, 180 días)

**Frontend (static/index.html):**
- [x] Nuevo tab "Historial escaneos" (junto a Dispositivos, Presencia)
- [x] Panel con selector de período (dropdown + botón Cargar)
- [x] Gráfico SVG vanilla:
  - Barras: duración promedio (gris)
  - Línea: promedio encontrados (azul/primary)
  - Puntos interactivos con tooltips
  - Ejes escalados automáticamente
  - Responsive (viewBox)
- [x] Tabla de datos debajo: resumen diario con todos los valores
- [x] Carga automática al cambiar período

**Testing en VM:** ✅
- Click en tab "Historial escaneos" carga datos
- Gráfico se dibuja correctamente
- Cambio de período actualiza automáticamente
- Tabla muestra datos precisos

---

## 2026-04-01/02 — Gestión de tipos de dispositivos (Opción A: SQLite) ✅

### ✅ COMPLETADO

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

### ✅ Testing en VM (2026-04-02)

- [x] API `/api/tipos` devuelve 11 tipos correctamente
- [x] API `/api/resumen` devuelve desglose por tipo
- [x] Frontend carga tipos dinámicamente en dropdown "Tipo: Todos"
- [x] Modal de edición carga tipos dinámicamente
- [x] Iconos en tabla se muestran correctamente
- [x] Filtro por tipo funciona (ej: seleccionar "IoT" muestra solo IoT)

**Resultado: FUNCIONAL AL 100%**

---

## Notas

- **Razón de la Opción A (SQLite):** Ya existe FastAPI + SQLite, los tipos son datos (no configuración), es el lugar natural. Alternativas (env vars, JSON) son menos mantenibles.
- **Impacto:** No rompe nada existente; los 11 tipos iniciales cubren el 99% de dispositivos hogareños.
- **Próximo paso:** Si se termina hoy, se podría agregar una pestaña "Tipos" en ReDo para gestionar el catálogo desde la UI.
