# CLAUDE.md — ReDo

## Qué es

**ReDo** (Red Doméstica) es el monitor de red del ecosistema hogarOS.
Escanea la LAN con nmap/ARP, detecta dispositivos nuevos y envía alertas por ntfy.

- **GitHub:** acabellan1868-prog/ReDo
- **Ruta local:** `E:\Documentos\Desarrollo\claude\ReDo\`
- **En el servidor:** `/mnt/datos/redo-build/` (git clone, build context Docker)
- **Datos persistentes:** `/mnt/datos/redo/redo.db`

---

## Estructura del repo

```
ReDo/
├── app/
│   ├── principal.py        → Punto de entrada FastAPI + APScheduler
│   ├── bd.py               → Acceso a SQLite (redo.db) + migraciones v1→v2
│   ├── config.py           → Variables de entorno
│   ├── escaner.py          → Lógica de escaneo ARP/nmap + registro de presencia
│   ├── esquema.sql         → DDL de la base de datos (v2: tipo, zona, presencia)
│   ├── modelos.py          → Modelos Pydantic
│   ├── notificador.py      → Alertas ntfy
│   └── rutas/
│       ├── dispositivos.py → CRUD dispositivos (GET, PUT) + filtros tipo/zona
│       ├── escaneos.py     → POST /api/escanear + SSE /api/eventos
│       ├── presencia.py    → GET presencia por dispositivo + timeline + agregación
│       ├── alertas.py      → GET/POST/DELETE /api/alertas (centro de alertas)
│       └── resumen.py      → GET /api/estado + GET /api/logs
├── static/
│   └── index.html          → Frontend completo (SPA vanilla)
├── data/
│   └── .gitkeep            → La BD redo.db se crea aquí en runtime
├── Dockerfile
├── docker-compose.yml      → Solo para desarrollo local
└── requirements.txt
```

---

## Integración con hogarOS

ReDo se sirve en `/red/` a través del Nginx de hogarOS.

**Puerto:** 8083 (configurable por env `PORT`)
**network_mode:** `host` — necesario para los escaneos ARP en la LAN

### ⚠️ hogar.css — cómo llega al frontend

`static/index.html` referencia el design system con:
```html
<link rel="stylesheet" href="/static/hogar.css">
```

Nginx reescribe esa ruta a `/red/static/hogar.css` mediante `sub_filter`.
El `location /red/static/` de nginx sirve ese fichero desde `portal/static/`
del repo hogarOS — **ReDo no sirve hogar.css por sí mismo**.

Si hogar.css no carga, el problema está en nginx, no en ReDo.

---

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/resumen` | Resumen: total, confiables, desconocidos, último escaneo, `por_tipo` |
| GET | `/api/dispositivos` | Lista dispositivos (filtros: `confiable`, `tipo`, `zona`) |
| GET | `/api/dispositivos/zonas` | Lista de zonas en uso (para autocompletado) |
| GET | `/api/dispositivos/exportar/csv` | Descarga CSV de dispositivos (respeta filtros) |
| GET | `/api/dispositivos/exportar/json` | Descarga JSON de dispositivos (respeta filtros) |
| GET | `/api/tipos` | Catalogo de tipos de dispositivo (clave, nombre, icono) |
| POST | `/api/tipos` | Crear tipo nuevo (clave, nombre, icono) |
| PUT | `/api/tipos/{clave}` | Editar tipo (nombre, icono) |
| DELETE | `/api/tipos/{clave}` | Eliminar tipo (reasigna dispositivos a 'otro') |
| PUT | `/api/dispositivos/{mac}` | Editar nombre, tipo, zona, notas, confiable |
| POST | `/api/escanear` | Lanza escaneo manual |
| GET | `/api/escaneos/estadisticas/por-fecha` | Estadísticas diarias de escaneos (gráficos) |
| GET | `/api/eventos` | SSE — eventos `fin_escaneo` y `error_escaneo` |
| GET | `/api/logs` | Historial de escaneos |
| GET | `/api/presencia/dispositivos/{id}` | Presencia de un dispositivo (`?dias=7`) |
| GET | `/api/presencia/timeline` | Timeline de todos los dispositivos (`?fecha=YYYY-MM-DD`) |
| GET | `/api/alertas` | Alertas: `modulo: "redo"`, activas primero, límite 50 |
| POST | `/api/alertas/{id}/resolver` | Marcar alerta como resuelta |
| DELETE | `/api/alertas/{id}` | Eliminar alerta |

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `REDO_DB_PATH` | Ruta a la BD SQLite (por defecto `data/redo.db`) |
| `REDO_NETWORK` | Red a escanear (ej: `192.168.31.0/24`) |
| `REDO_SCAN_INTERVAL` | Intervalo de escaneo automático en segundos |
| `REDO_PRESENCIA_DIAS` | Días de detalle de presencia antes de agregar (defecto 180) |
| `NTFY_TOPIC` | Topic de ntfy para alertas |
| `PORT` | Puerto del servidor (por defecto 8083) |

---

## Catálogo de tipos de dispositivos

Tabla `tipos_dispositivo` (gestión por API):

| Clave | Nombre | Icono | Descripción |
|---|---|---|---|
| `telefono` | Teléfono | `smartphone` | Teléfonos móviles |
| `portatil` | Portátil | `laptop` | Portátiles y laptops |
| `sobremesa` | PC Sobremesa | `desktop_windows` | Ordenadores de escritorio |
| `tablet` | Tablet | `tablet` | Tablets y iPad |
| `tv` | TV / Streaming | `tv` | Smart TVs, Chromecast, Fire TV |
| `impresora` | Impresora | `print` | Impresoras y multifuncionales |
| `router` | Router / AP / Switch | `router` | Routers, puntos de acceso, switches |
| `iot` | IoT | `sensors` | Sensores, enchufes, bombillas, etc. |
| `servidor` | Servidor / NAS | `dns` | Servidores, NAS, Proxmox |
| `consola` | Consola | `videogame_asset` | Consolas de videojuegos |
| `otro` | Sin clasificar | `device_unknown` | Valor por defecto (no se puede eliminar) |

**Notas:**
- Los tipos se poblan automáticamente en la primera inicialización (migración en `bd.py`)
- El frontend carga tipos dinámicamente desde `/api/tipos` al iniciar
- Los iconos son Material Symbols (ej: `smartphone`, `laptop`, etc.)
- Al eliminar un tipo, los dispositivos que lo usaban se reasignan a `otro`

---

## Design system

El frontend usa el design system **Living Sanctuary** de hogarOS.
Ver `portal/static/hogar.css` en el repo hogarOS para referencia de componentes,
variables CSS y convenciones visuales.

---

## Convenciones de código

- Todo en español: variables, funciones, clases, comentarios
- Backend: Python + FastAPI + SQLite
- Frontend: HTML/CSS/JS vanilla, sin frameworks ni bundlers
