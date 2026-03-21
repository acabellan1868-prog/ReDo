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
│   ├── principal.py        → Punto de entrada FastAPI
│   ├── bd.py               → Acceso a SQLite (redo.db)
│   ├── config.py           → Variables de entorno
│   ├── escaner.py          → Lógica de escaneo ARP/nmap
│   ├── esquema.sql         → DDL de la base de datos
│   ├── modelos.py          → Modelos Pydantic
│   ├── notificador.py      → Alertas ntfy
│   └── rutas/
│       ├── dispositivos.py → CRUD dispositivos (GET, PUT)
│       ├── escaneos.py     → POST /api/escanear + SSE /api/eventos
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
| GET | `/api/estado` | Resumen: total, confiables, desconocidos, último escaneo |
| GET | `/api/dispositivos` | Lista todos los dispositivos |
| PUT | `/api/dispositivos/{mac}` | Editar nombre, tipo, notas, trusted |
| POST | `/api/escanear` | Lanza escaneo manual |
| GET | `/api/eventos` | SSE — eventos `fin_escaneo` y `error_escaneo` |
| GET | `/api/logs` | Historial de escaneos |

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `REDO_DB_PATH` | Ruta a la BD SQLite (por defecto `data/redo.db`) |
| `REDO_NETWORK` | Red a escanear (ej: `192.168.31.0/24`) |
| `REDO_SCAN_INTERVAL` | Intervalo de escaneo automático en segundos |
| `NTFY_TOPIC` | Topic de ntfy para alertas |
| `PORT` | Puerto del servidor (por defecto 8083) |

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
