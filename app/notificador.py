"""
ReDo — Modulo de notificaciones via NTFY.
Envia alertas push cuando se detectan dispositivos desconocidos.
"""

import httpx
import logging

from app.config import NTFY_URL, NTFY_TOPIC

logger = logging.getLogger("redo.notificador")


def notificar_dispositivo_nuevo(
    ip: str,
    hostname: str | None,
    mac: str,
    fabricante: str | None,
) -> bool:
    """
    Envia una notificacion NTFY sobre un dispositivo nuevo en la red.

    Returns:
        True si se envio correctamente, False en caso de error.
    """
    titulo = "Dispositivo desconocido detectado"
    nombre = hostname or fabricante or mac
    cuerpo = f"IP: {ip}\nMAC: {mac}\nNombre: {nombre}"
    if fabricante:
        cuerpo += f"\nFabricante: {fabricante}"

    url = f"{NTFY_URL}/{NTFY_TOPIC}"

    try:
        respuesta = httpx.post(
            url,
            content=cuerpo.encode("utf-8"),
            headers={
                "Title": titulo,
                "Priority": "high",
                "Tags": "warning,computer",
            },
            timeout=10.0,
        )
        respuesta.raise_for_status()
        logger.info(f"Notificacion enviada: {nombre} ({ip})")
        return True
    except Exception as e:
        logger.error(f"Error enviando notificacion NTFY: {e}")
        return False
