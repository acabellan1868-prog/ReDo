"""
ReDo — Modulo de escaneo de red.
Usa python-nmap para descubrir dispositivos en la red local.
"""

import nmap
import logging
from datetime import datetime

from app import bd
from app.config import RED_OBJETIVO
from app.notificador import notificar_dispositivo_nuevo

logger = logging.getLogger("redo.escaner")


def escanear_red() -> dict:
    """
    Ejecuta un escaneo ARP de la red local.

    Flujo:
    1. Registra el escaneo en la tabla 'escaneos' (inicio)
    2. Ejecuta nmap -sn (ping scan) contra RED_OBJETIVO
    3. Por cada host encontrado:
       a. Extrae MAC, IP, hostname, vendor
       b. Si MAC ya existe: actualiza ip, hostname, ultima_vez
       c. Si MAC es nueva: INSERT + alerta + notificacion NTFY
    4. Actualiza el registro de escaneo con fin y contadores
    5. Retorna resumen del escaneo

    Returns:
        dict con claves: escaneo_id, encontrados, nuevos
    """
    inicio = datetime.now().isoformat()
    escaneo_id = bd.ejecutar(
        "INSERT INTO escaneos (inicio) VALUES (?)",
        (inicio,),
    )

    encontrados = 0
    nuevos = 0

    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=RED_OBJETIVO, arguments="-sn")

        for host in nm.all_hosts():
            ip = host
            # Extraer MAC address (solo disponible con privilegios root)
            direcciones = nm[host].get("addresses", {})
            mac = direcciones.get("mac", "").upper()

            if not mac:
                # Sin MAC = es el propio host o no se pudo resolver
                continue

            hostname = nm[host].hostname() or None
            # Extraer fabricante del vendor dict de nmap
            fabricante = None
            vendor = nm[host].get("vendor", {})
            if mac in vendor:
                fabricante = vendor[mac]

            encontrados += 1

            # Buscar si el dispositivo ya existe por MAC
            existente = bd.consultar_uno(
                "SELECT id, confiable FROM dispositivos WHERE mac = ?",
                (mac,),
            )

            if existente:
                # Actualizar IP, hostname y ultima_vez
                bd.ejecutar(
                    """UPDATE dispositivos
                       SET ip = ?, hostname = ?, fabricante = COALESCE(?, fabricante),
                           ultima_vez = datetime('now')
                       WHERE mac = ?""",
                    (ip, hostname, fabricante, mac),
                )
                # Registrar presencia
                bd.ejecutar(
                    "INSERT INTO presencia (dispositivo_id, escaneo_id, ip) VALUES (?, ?, ?)",
                    (existente["id"], escaneo_id, ip),
                )
            else:
                # Nuevo dispositivo
                dispositivo_id = bd.ejecutar(
                    """INSERT INTO dispositivos (mac, ip, hostname, fabricante)
                       VALUES (?, ?, ?, ?)""",
                    (mac, ip, hostname, fabricante),
                )
                nuevos += 1

                # Registrar presencia del nuevo dispositivo
                bd.ejecutar(
                    "INSERT INTO presencia (dispositivo_id, escaneo_id, ip) VALUES (?, ?, ?)",
                    (dispositivo_id, escaneo_id, ip),
                )

                # Crear alerta
                mensaje = (
                    f"Nuevo dispositivo: {ip} "
                    f"({hostname or 'sin nombre'}) - "
                    f"{fabricante or mac}"
                )
                alerta_id = bd.ejecutar(
                    """INSERT INTO alertas (tipo, mensaje, dispositivo_id)
                       VALUES ('dispositivo_nuevo', ?, ?)""",
                    (mensaje, dispositivo_id),
                )

                # Enviar notificacion NTFY
                enviada = notificar_dispositivo_nuevo(
                    ip, hostname, mac, fabricante
                )
                if enviada:
                    bd.ejecutar(
                        "UPDATE alertas SET enviada = 1 WHERE id = ?",
                        (alerta_id,),
                    )

        # Actualizar registro de escaneo
        fin = datetime.now().isoformat()
        bd.ejecutar(
            """UPDATE escaneos
               SET fin = ?, dispositivos_encontrados = ?, dispositivos_nuevos = ?
               WHERE id = ?""",
            (fin, encontrados, nuevos, escaneo_id),
        )

        logger.info(
            f"Escaneo #{escaneo_id} completado: "
            f"{encontrados} encontrados, {nuevos} nuevos"
        )

    except Exception as e:
        logger.error(f"Error en escaneo #{escaneo_id}: {e}")
        fin = datetime.now().isoformat()
        bd.ejecutar(
            "UPDATE escaneos SET fin = ? WHERE id = ?",
            (fin, escaneo_id),
        )
        # Crear alerta de error
        bd.ejecutar(
            """INSERT INTO alertas (tipo, mensaje)
               VALUES ('error_escaneo', ?)""",
            (str(e),),
        )

    return {
        "escaneo_id": escaneo_id,
        "encontrados": encontrados,
        "nuevos": nuevos,
    }
