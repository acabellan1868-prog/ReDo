"""
ReDo — Configuracion centralizada.
Lee variables de entorno con valores por defecto para desarrollo local.
"""

import os

# Base de datos
RUTA_BD = os.environ.get("REDO_DB_PATH", "data/redo.db")

# Escaneo de red
RED_OBJETIVO = os.environ.get("REDO_NETWORK", "192.168.31.0/24")
INTERVALO_ESCANEO = int(os.environ.get("REDO_SCAN_INTERVAL", "300"))  # segundos

# Notificaciones NTFY
NTFY_URL = os.environ.get("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "hogaros-3ca6f61b")

# Presencia — dias de detalle antes de agregar a resumen diario
PRESENCIA_DIAS_DETALLE = int(os.environ.get("REDO_PRESENCIA_DIAS", "180"))

# Zona horaria
TZ = os.environ.get("TZ", "Europe/Madrid")
