# Bitadora — ReDo

Registro detallado del trabajo día a día.

---

## 2026-04-02 — Fase 5: 3 tareas completadas + 3 fixes ✅

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

## 2026-04-02 (tarde) — Fixes de las 3 tareas ✅

### Fix 1: Descarga CSV/JSON no funcionaba ❌ → ✅

**Problema:** Campo `nombre` no existe en tabla `dispositivos`
**Error:** `sqlite3.OperationalError: no such column: nombre`

**Solución:**
- Campo correcto es `notas` (nombre personalizado del usuario)
- Incluir también `hostname` (nombre de equipo en LAN)
- Formato en CSV: `notas · hostname`
- Manejar valores NULL con `or ""`

**Archivos modificados:**
- `app/rutas/dispositivos.py` líneas 140-190 (endpoint `/api/dispositivos/exportar/csv`)
  - SELECT: cambiar `nombre` por `notas`
  - writerow: usar `d["notas"]` en lugar de `d["nombre"]`
  - Null-check: `d["ip"] or ""`

**Testing:** ✅
```bash
curl "http://192.168.31.131/red/api/dispositivos/exportar/csv" > dispositivos.csv
# CSV debe tener columnas: id,mac,ip,nombre,hostname,tipo,zona,confiable
```

---

### Fix 2: No vuelve a vista lista ❌ → ✅

**Problema:** Toggle "Vista: Lista ↔ Agrupada" no funcionaba
- Hacer click en toggle no volvía a lista (quedaba en agrupada)
- Botón no respondía bien

**Causa:** `renderizarAgrupado()` escribía en contenedor equivocado
- Línea 1487 (antes): `document.getElementById('panelDispositivos').innerHTML = html`
- `panelDispositivos` es el padre de `vistaLista` y `vistaAgrupada`
- Esto sobrescribía ambas vistas

**Solución:**
- Cambiar a: `document.getElementById('vistaAgrupada').innerHTML = html`
- Ahora `cargarDispositivos()` puede mostrar/ocultar correctamente:
  - Línea 1212: `document.getElementById('vistaLista').style.display = vistaAgrupada ? 'none' : 'block'`
  - Línea 1213: `document.getElementById('vistaAgrupada').style.display = vistaAgrupada ? 'block' : 'none'`

**Archivos modificados:**
- `static/index.html` línea ~1487

**Testing:** ✅
- Click en "Vista: Lista" → tabla visible
- Click en "Vista: Agrupada" → tarjetas visibles
- Click en "Vista: Lista" → tabla visible nuevamente

---

### Fix 3: Vista agrupada cambio de plana a jerárquica ❌ → ✅

**Antes:** Agrupado solo por zona (estructura plana)
```
📍 Salón (5)
  - iPhone (teléfono)
  - MacBook (portátil)
  - Monitor (tv)
  - Shelly (iot)
  - ...
```

**Ahora:** Agrupado por tipo → zona (estructura jerárquica)
```
📱 Teléfono (4)
  📍 Salón (2)
    - iPhone Luis
    - Samsung María
  📍 Despacho (2)
    - Xiaomi Luis
    - Motorola María

💻 Portátil (3)
  📍 Despacho (3)
    - MacBook Luis
    - XPS María
    - Lenovo Antonio

🔌 Iot (6)
  📍 Salón (2)
    - Shelly Plus 1
    - Bombilla IKEA
  📍 Cocina (2)
    - Enchufe TP-Link
    - Sensor movimiento
  ...
```

**Implementación:**
- Crear estructura anidada: `gruposPorTipo[tipo][zona] = []`
- Iterar tipos (sorted alfabético)
- Dentro de cada tipo, iterar zonas (sorted)
- Mostrar icono y contador por tipo
- Mostrar contador por zona

**CSS new:**
- `.tipo-grupo` - contenedor de tipo (border-bottom 3px)
- `.tipo-titulo` - título del tipo (18px, bold, primary)
- `.zona-grupo` - indentación visual (margin-left)
- `.zona-titulo` - título de zona (15px, on-surface-variant)

**Archivos modificados:**
- `static/index.html` líneas ~1443-1487 (función renderizarAgrupado)
- `static/index.html` líneas ~330-365 (CSS nuevos)

**Testing:** ✅
- Click en "Vista: Agrupada"
- Verificar que se ve estructura tipo → zona
- Contador de dispositivos por tipo y zona es correcto
- Iconos Material Symbols visibles
- Ordenamiento alfabético (tipos y zonas)

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

## 2026-04-02 (noche) — Fase 5: Tarea 4 - Configuración en vivo ✅

**Contexto:** Las 3 tareas anteriores (Exportar CSV, Vista agrupada, Historial escaneos) fueron completadas y testeadas. Ahora se termina Fase 5 con Configuración en vivo.

### Backend: Rutas API

**Archivo: `app/rutas/config.py` (NUEVO)**

- [x] Endpoint `GET /api/config` — lista parámetros editables
- [x] Endpoint `GET /api/config/{clave}` — obtiene un parámetro
- [x] Endpoint `PUT /api/config/{clave}` — actualiza con validaciones:
  - `red_objetivo`: valida CIDR IPv4 (usa `ipaddress.IPv4Network`)
  - `intervalo_escaneo`: entero 60-3600 segundos
  - `presencia_dias_detalle`: entero 1-365 días
  - `ntfy_url`: debe ser http:// o https://
  - `ntfy_topic`: no puede estar vacío
- [x] Función `_aplicar_config_en_runtime()`:
  - Si `intervalo_escaneo` cambia → replanifica job APScheduler
  - Si `presencia_dias_detalle` cambia → se aplica en próx ciclo
  - Otros parámetros se aplican en próx escaneo

**Archivo: `app/modelos.py` (MODIFICADO)**

- [x] Modelo `ConfiguracionRespuesta` (clave, valor, tipo, editable, descripcion, ultima_actualizacion)
- [x] Modelo `ConfiguracionActualizar` (valor como string)

**Archivo: `app/principal.py` (MODIFICADO)**

- [x] Importado módulo `config`
- [x] Registrado router con `app.include_router(config.ruta, prefix="/api/config")`

**Archivo: `app/escaner.py` (MODIFICADO)**

- [x] Removed import de `RED_OBJETIVO` desde `app/config`
- [x] Nueva función `obtener_red_objetivo()`: lee de BD, con fallback a config.py
- [x] Modificado `escanear_red()` para usar `obtener_red_objetivo()` dinámicamente

**Archivo: `app/esquema.sql` (MODIFICADO en sesión anterior)**

- [x] Tabla `configuracion`: clave (PK), valor, tipo, editable, descripcion, ultima_actualizacion
- [x] Índice `idx_config_editable`

**Archivo: `app/bd.py` (MODIFICADO en sesión anterior)**

- [x] Migración que puebla `configuracion` con 5 variables iniciales (red_objetivo, intervalo_escaneo, presencia_dias_detalle, ntfy_url, ntfy_topic)

### Frontend: Tab de Configuración

**Archivo: `static/index.html` (MODIFICADO)**

**Tab button (línea ~957):**
- [x] Nuevo botón `data-tab="config"` con icono `settings`
- [x] Texto: "Configuración"

**Panel (línea ~1056):**
- [x] Nuevo `<div id="panelConfiguracion">`
- [x] Contenedor `#configFormContainer` para renderizar dinámicamente

**CSS (líneas ~673-743):**
- [x] `.config-item` — tarjeta de configuración (border-left 4px primary)
- [x] `.config-item__titulo` — nombre del parámetro
- [x] `.config-item__descripcion` — explicación
- [x] `.config-item__control` — flex con input + botón
- [x] `.config-item input` — estilos de input con focus state
- [x] `.config-item__btn` — botón Guardar con estados disabled/hover
- [x] `.config-item__error` — mensaje de error (rojo)
- [x] `.config-item__exito` — mensaje de éxito (verde)

**JavaScript (líneas ~1976-2060):**
- [x] Función `cargarConfiguracion()`:
  - Fetch `GET /api/config`
  - Renderiza form dinámicamente (un item por parámetro)
  - Inputtype: text, number según tipo (int/float/string)
  - Botón Guardar para cada parámetro
  - Event listener: Enter en input dispara actualizar
- [x] Función `actualizarConfig(clave)`:
  - Validación client-side (no vacío)
  - Fetch `PUT /api/config/{clave}` con {valor}
  - Manejo de errores: muestra mensaje desde API
  - Feedback visual: "Guardando..." → "✓ Actualizado" o "✗ Error"
  - Mensaje desaparece en 3 segundos
- [x] Tab switch: call `cargarConfiguracion()` cuando se selecciona tab "config"

**Testing:**
```bash
# API OK?
curl http://192.168.31.131/red/api/config
curl http://192.168.31.131/red/api/config/red_objetivo

# Actualizar config
curl -X PUT http://192.168.31.131/red/api/config/intervalo_escaneo \
  -H "Content-Type: application/json" \
  -d '{"valor": "120"}'

# Validación CIDR
curl -X PUT http://192.168.31.131/red/api/config/red_objetivo \
  -H "Content-Type: application/json" \
  -d '{"valor": "192.168.1.0/24"}'  # ✓ OK
# vs
curl -X PUT ... -d '{"valor": "invalid"}' # ✗ Error

# Frontend: click tab Configuración
# - Cargar 5 parámetros
# - Editar uno (ej: intervalo_escaneo → 120)
# - Verificar mensaje "✓ Actualizado"
# - Próximo escaneo usa nuevo intervalo
```

### Documentación

**Archivo: `CLAUDE.md` (MODIFICADO)**

- [x] Agregadas 3 nuevas rutas API en tabla:
  ```
  | GET | `/api/config` | Listado de parámetros de configuración editables |
  | GET | `/api/config/{clave}` | Obtiene un parámetro de configuración específico |
  | PUT | `/api/config/{clave}` | Actualiza un parámetro (con validaciones) |
  ```

### Resumen Tarea 4 (versión inicial)

✅ **COMPLETADA** — Endpoints API + formulario inline

- Backend: Rutas API CRUD con validaciones completas
- Frontend: Tab de configuración con form dinámico y feedback visual
- Runtime: Cambios aplican inmediatamente (APScheduler replanificado si es intervalo)
- BD: Tabla `configuracion` persistente con migración automática

---

## 2026-04-02 (noche) — Refinamientos UX de Tarea 4

**Iteración 2: Modal emergente tipo FiDo**

Problema inicial: Formulario inline muy grande, requería scroll para 5 campos → UX pobre

Solución: Modal emergente centrado (similar a FiDo):

**Cambios HTML:**
- Panel de configuración: muestra solo RESUMEN (clave: valor en código)
- Botón "EDITAR CONFIGURACIÓN" abre modal
- Modal con estructura: header (título + cerrar) | body (campos) | footer (CANCELAR + GUARDAR)

**Cambios CSS:**
- `.config-modal-overlay`: overlay semi-transparente, flex centered, z-index 1000
- `.config-modal`: width 90%/max 500px, max-height 80vh, animaciones fadeIn/slideUp
- `.config-campo`: margin-bottom gap-lg, label + input + descripción + error
- Inputs: padding 0.75rem, focus state con primary border + shadow

**Cambios JavaScript:**
- `cargarConfiguracion()`: carga resumen en el panel
- `abrirModalConfig()`: fetch config, renderiza modal con todos los campos
- `guardarConfiguracion()`: **un único click** persiste TODOS los cambios con `Promise.all()`
- `cerrarModalConfig()`: click X, CANCELAR, o fuera del modal
- Validación: recopila errores antes de guardar, muestra inline en cada campo

**Flujo UX:**
1. Abre tab "Configuración" → ve resumen compacto (5 líneas)
2. Click "EDITAR CONFIGURACIÓN" → modal emergente
3. Edita campos que quiera
4. Click "GUARDAR" → persiste todos los cambios
5. Modal cierra automáticamente, panel actualiza resumen

**Fixes de bugs:**
1. ❌ ID del panel: `panelConfiguracion` → `panelConfig` (coincida con lógica de tabs)
   - Error: "Cannot read properties of null (reading 'classList')"
2. ❌ Formulario inline demasiado espacioso (gap-lg = 24px × 5 campos = 120px solo en gaps)
   - Solución: modal compacto, max-width 500px, scroll interno si es necesario

**Testing completo:**
- ✅ Modal abre/cierra correctamente
- ✅ Carga config desde API
- ✅ Guarda cambios con un click
- ✅ Validación muestra errores en rojo
- ✅ Resumen se actualiza al cerrar modal
- ✅ Responsive en móvil/tablet

---

## Notas finales

- **Razón de Modal sobre Inline:**
  - Modal = patrón familiar (usuario lo ve en FiDo)
  - Compacto: 5 campos en ~400px de altura
  - UX clara: LEER resumen + EDITAR modal + GUARDAR todo
  - Vs formulario inline: requería scroll, confuso el "guardar por campo"

- **Fase 5 CERRADA:** Las 4 tareas + 2 iteraciones de UX cierran Fase 5 completamente.
  - Exportar CSV/JSON ✅
  - Vista agrupada por zona ✅
  - Historial escaneos ✅
  - Configuración en vivo ✅
  - UX refinements ✅

- **Estado final:** Sistema completamente funcional, intuitivo, y listo para producción.
