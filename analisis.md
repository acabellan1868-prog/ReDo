# Análisis — ReDo (Red Doméstica)

## Qué es

ReDo es el monitor de red del ecosistema **hogarOS**. Escanea la LAN
periódicamente mediante ARP/nmap, detecta dispositivos nuevos o desconocidos
y envía alertas por ntfy.

## Por qué se hace

- Tener visibilidad completa de qué dispositivos están conectados a la red
  doméstica en cada momento.
- Detectar intrusos o dispositivos no autorizados de forma automática.
- Poder clasificar dispositivos como «confiables» o «desconocidos» y
  asignarles un nombre descriptivo para identificarlos fácilmente.

## Stack

| Capa       | Tecnología                          |
|------------|-------------------------------------|
| Backend    | Python + FastAPI + SQLite           |
| Frontend   | HTML/CSS/JS vanilla (SPA)           |
| Escaneo    | nmap / ARP                          |
| Alertas    | ntfy                                |
| Despliegue | Docker (`network_mode: host`)       |
| Proxy      | Nginx de hogarOS en `/red/`         |

## Integración

- Se sirve en el puerto **8083** de la VM 101.
- Nginx de hogarOS enruta `/red/` hacia ReDo.
- Usa el design system **Living Sanctuary** (`hogar.css`) servido por Nginx.
