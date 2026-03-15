# ReDo — Red Doméstica

Monitor de red doméstica para el ecosistema [hogarOS](https://github.com/acabellan1868-prog/hogarOS). Detecta dispositivos conectados, avisa de intrusos y mantiene un inventario de la red.

## Objetivo

Saber en todo momento **qué dispositivos hay conectados** a la red de casa:

1. **Detección automática** — escaneos periódicos con nmap cada 5 minutos.
2. **Alertas inmediatas** — notificación push (NTFY) cuando aparece un dispositivo desconocido.
3. **Inventario** — marcar dispositivos como confiables, añadir notas, consultar historial.

## Stack técnico

| Componente | Tecnología |
|------------|------------|
| Backend | Python + FastAPI |
| Frontend | HTML/JS servido por FastAPI (StaticFiles) — fase posterior |
| Base de datos | SQLite (WAL mode) |
| Escaneo de red | python-nmap (`nmap -sn`) |
| Tareas periódicas | APScheduler (BackgroundScheduler) |
| Notificaciones | NTFY (push al móvil) |
| Despliegue | Docker (1 contenedor) en servidor Debian con Proxmox |

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/resumen` | Resumen para el portal hogarOS |
| `GET` | `/api/dispositivos` | Lista dispositivos (filtro: `?confiable=1`) |
| `GET` | `/api/dispositivos/{id}` | Detalle de un dispositivo |
| `POST` | `/api/dispositivos/{id}/confiable` | Marcar como confiable |
| `PUT` | `/api/dispositivos/{id}` | Editar notas / confiable |
| `GET` | `/api/escaneos` | Historial de escaneos |
| `POST` | `/api/escaneos/ejecutar` | Lanzar escaneo manual |
| `POST` | `/api/escanear` | Atajo para escaneo manual |

Documentación interactiva (Swagger) disponible en `/docs`.

## Configuración

Variables de entorno (definidas en `docker-compose.yml`):

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `REDO_DB_PATH` | `data/redo.db` | Ruta de la base de datos SQLite |
| `REDO_NETWORK` | `192.168.31.0/24` | Red a escanear |
| `REDO_SCAN_INTERVAL` | `300` | Intervalo entre escaneos (segundos) |
| `NTFY_URL` | `https://ntfy.sh` | Servidor NTFY |
| `NTFY_TOPIC` | `hogaros-3ca6f61b` | Topic para notificaciones push |
| `TZ` | `Europe/Madrid` | Zona horaria |

## Despliegue

```bash
# En la VM de Proxmox (192.168.31.131)
cd /mnt/datos/redo
docker compose build
docker compose up -d
```

> **Nota:** ReDo necesita `network_mode: host` y capabilities `NET_RAW` + `NET_ADMIN` para que nmap pueda detectar direcciones MAC en la red local.

## Estructura del proyecto

```
ReDo/
├── app/
│   ├── principal.py      ← Entry point (FastAPI + APScheduler)
│   ├── bd.py             ← Capa SQLite
│   ├── config.py         ← Variables de entorno
│   ├── escaner.py        ← Lógica de escaneo nmap
│   ├── esquema.sql       ← DDL de la base de datos
│   ├── modelos.py        ← Modelos Pydantic
│   ├── notificador.py    ← Cliente NTFY
│   └── rutas/
│       ├── resumen.py    ← GET /api/resumen
│       ├── dispositivos.py ← CRUD dispositivos
│       └── escaneos.py   ← Historial + escaneo manual
├── static/               ← Frontend (fase posterior)
├── data/                 ← Base de datos (no versionada)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Licencia

Proyecto privado de uso familiar.
