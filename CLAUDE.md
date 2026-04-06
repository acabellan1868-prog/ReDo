# CLAUDE.md — ReDo

## Qué es
Monitor de red doméstica. Escanea la LAN con nmap/ARP, detecta dispositivos nuevos, envía alertas por ntfy.

- **Repo:** acabellan1868-prog/ReDo
- **Local:** `Desarrollo/ReDo/`
- **Servidor:** `/mnt/datos/redo-build/` (build context), `/mnt/datos/redo/redo.db` (datos)
- **Proxy:** `/red/` → `host.docker.internal:8083`
- **network_mode:** `host` (necesario para escaneos ARP en LAN)

## Estructura

```
ReDo/
├── app/
│   ├── principal.py        ← FastAPI + APScheduler
│   ├── bd.py               ← SQLite + migraciones v1→v2
│   ├── config.py
│   ├── escaner.py
│   ├── esquema.sql
│   ├── modelos.py
│   ├── notificador.py      ← alertas ntfy
│   └── rutas/
│       ├── dispositivos.py
│       ├── escaneos.py
│       ├── presencia.py
│       ├── alertas.py
│       └── resumen.py
├── static/
│   └── index.html          ← SPA completa
└── Dockerfile
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/resumen` | Total, confiables, desconocidos, último escaneo, por_tipo |
| GET | `/api/dispositivos` | Lista (filtros: confiable, tipo, zona) |
| PUT | `/api/dispositivos/{mac}` | Editar nombre, tipo, zona, notas, confiable |
| GET | `/api/dispositivos/zonas` | Zonas en uso |
| GET | `/api/dispositivos/exportar/csv` | Exportar CSV |
| GET | `/api/dispositivos/exportar/json` | Exportar JSON |
| GET/POST | `/api/tipos` | Catálogo de tipos de dispositivo |
| PUT/DELETE | `/api/tipos/{clave}` | Editar/eliminar tipo |
| POST | `/api/escanear` | Lanzar escaneo manual |
| GET | `/api/eventos` | SSE: `fin_escaneo`, `error_escaneo` |
| GET | `/api/logs` | Historial de escaneos |
| GET | `/api/escaneos/estadisticas/por-fecha` | Estadísticas diarias |
| GET | `/api/config` | Parámetros de configuración |
| PUT | `/api/config/{clave}` | Actualizar parámetro |
| GET | `/api/presencia/dispositivos/{id}` | Presencia de un dispositivo |
| GET | `/api/presencia/timeline` | Timeline de todos los dispositivos |
| GET | `/api/alertas` | Alertas (módulo redo) |
| POST | `/api/alertas/{id}/resolver` | Resolver alerta |
| DELETE | `/api/alertas/{id}` | Eliminar alerta |

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `REDO_DB_PATH` | Ruta BD SQLite (defecto `data/redo.db`) |
| `REDO_NETWORK` | Red a escanear (ej: `192.168.31.0/24`) |
| `REDO_SCAN_INTERVAL` | Intervalo escaneo automático (segundos) |
| `REDO_PRESENCIA_DIAS` | Días detalle presencia antes de agregar (defecto 180) |
| `NTFY_TOPIC` | Topic NTFY (intermediario de transporte) para alertas. Valor en `.env`, nunca hardcoded. |
| `PORT` | Puerto servidor (defecto 8083) |

## hogar.css
Nginx reescribe `/static/` → `/red/static/` y lo sirve desde `portal/static/` de hogarOS. ReDo no sirve `hogar.css` por sí mismo. Si da 404, el problema está en nginx.
