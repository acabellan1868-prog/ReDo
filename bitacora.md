# Bitácora — ReDo

## 2026-05-05

### Fase 15 Paso 4 — Rediseño Cockpit completo

Reescritura completa de `static/index.html` del estilo Living Sanctuary al estilo Cockpit.
Sin cambios en la lógica JS ni en los endpoints de API.

**Estructura visual nueva:**
- Header fijo 48px con `ck-header`, nav inline de 4 pestañas en escritorio, drawer lateral en móvil.
- 4 KPIs en fila horizontal (total activos, confiables, desconocidos, último escaneo).
- Tabla de dispositivos con cabeceras `0.48rem` uppercase, borders `1px var(--ck-line)`, badges `--ok/--warn`, botones de acción compactos.
- Pestaña Presencia: timeline de barras con color `--ck-accent`.
- Pestaña Historial: gráfica SVG (líneas) preservada con colores CSS variables.
- Pestaña Configuración: inputs y selects con clases Cockpit.
- Toggle de tema: `data-tema-cockpit` / `localStorage('hogar-cockpit-tema')`.
- Reloj `tickReloj()` con hora y fecha en el header.

**Fix tipografía (commit `0eae3a2`):**
- Añadido `html { font-size: 150% }` — sin este reset `1rem = 16px` en lugar de `24px`, haciendo los textos más pequeños que en hogarOS/FiDo.

**Commits:** `1fb510e` (rediseño), `0eae3a2` (fix font-size)

---

## 2026-04-25

### AGENTS.md local para Codex

Creado `AGENTS.md` en el repo de ReDo a partir de `CLAUDE.md`, con estructura,
API, variables de entorno y gotchas operativos.

Gotchas destacados:
- `network_mode: host` es necesario para escaneos ARP.
- `/red/` proxifica a `host.docker.internal:8083`.
- `hogar.css` lo sirve hogarOS, no ReDo.

---

## 2026-04-07

### Variables sensibles a .env — añadido .env.example

- `docker-compose.yml`: `NTFY_TOPIC=hogaros-3ca6f61b` → `${NTFY_TOPIC}` (leído desde `.env`)
- `docker-compose.yml`: `REDO_NETWORK=192.168.31.0/24` → `${REDO_NETWORK}` (leído desde `.env`)
- Añadido `.env.example` como plantilla pública con los nombres de variables sin valores reales

Ver convención completa en hogarOS/CLAUDE.md.

---

## 2026-03-26

### Implementación de historial de presencia y clasificación de dispositivos

Implementadas las mejoras analizadas en `analisis-mejoras.md`:

- **Historial de presencia**: nuevo esquema de BD `presencia` que registra cada
  conexión/desconexión con timestamps de entrada y salida por dispositivo.
- **Tipo y zona de dispositivos**: campos `tipo` y `zona` añadidos al esquema.
  API ampliada con filtros. Frontend actualizado con selectores en el drawer de edición.
- **Agregación nocturna**: tarea programada a las 03:00 que consolida el historial
  manteniendo detalle de 180 días.

Commits: `b001e05`, `b0381f5`

## 2026-03-27

### Reorganización de documentación

- `mejoras.md` renombrado a `analisis-mejoras.md`
- Creada `bitacora.md` (este fichero)
