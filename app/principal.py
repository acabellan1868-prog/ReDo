"""
ReDo — Punto de entrada de la aplicacion FastAPI.
Inicializa la BD, configura el escaner periodico y registra todas las rutas.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.bd import inicializar_bd
from app.config import RUTA_BD, INTERVALO_ESCANEO, PRESENCIA_DIAS_DETALLE
from app.escaner import escanear_red
from app.rutas import resumen, dispositivos, escaneos, presencia

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("redo")

# Planificador de escaneos periodicos y tareas de mantenimiento
planificador = BackgroundScheduler()


def agregar_presencia():
    """
    Agrega datos de presencia antiguos a resumen diario.

    Para cada dia anterior al umbral (PRESENCIA_DIAS_DETALLE, por defecto 180):
    1. Calcula primera_vez, ultima_vez, minutos_conectado y num_avistamientos
    2. Inserta (o reemplaza) en presencia_diaria
    3. Borra los registros detallados de presencia de ese dia

    Se ejecuta una vez al dia a las 03:00 via APScheduler.
    """
    from app import bd

    umbral = f"-{PRESENCIA_DIAS_DETALLE} days"
    logger.info(
        f"Agregacion de presencia: procesando datos anteriores a {PRESENCIA_DIAS_DETALLE} dias"
    )

    # Buscar dias con datos detallados que ya superan el umbral
    dias_antiguos = bd.consultar_todos(
        """SELECT DISTINCT DATE(visto_en) as fecha
           FROM presencia
           WHERE DATE(visto_en) < DATE('now', ?)
           ORDER BY fecha""",
        (umbral,),
    )

    if not dias_antiguos:
        logger.info("Agregacion de presencia: sin datos antiguos que procesar")
        return

    total_agregados = 0
    total_borrados = 0

    for dia in dias_antiguos:
        fecha = dia["fecha"]

        # Calcular resumen por dispositivo para este dia
        resumenes = bd.consultar_todos(
            """SELECT dispositivo_id,
                      MIN(TIME(visto_en)) as primera_vez,
                      MAX(TIME(visto_en)) as ultima_vez,
                      COUNT(*) as num_avistamientos
               FROM presencia
               WHERE DATE(visto_en) = ?
               GROUP BY dispositivo_id""",
            (fecha,),
        )

        for resumen_dia in resumenes:
            # Calcular minutos conectados (franjas)
            timestamps = bd.consultar_todos(
                """SELECT visto_en FROM presencia
                   WHERE dispositivo_id = ? AND DATE(visto_en) = ?
                   ORDER BY visto_en""",
                (resumen_dia["dispositivo_id"], fecha),
            )
            minutos = _calcular_minutos([t["visto_en"] for t in timestamps])

            # Insertar o reemplazar en presencia_diaria
            bd.ejecutar(
                """INSERT OR REPLACE INTO presencia_diaria
                   (dispositivo_id, fecha, primera_vez, ultima_vez,
                    minutos_conectado, num_avistamientos)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    resumen_dia["dispositivo_id"],
                    fecha,
                    resumen_dia["primera_vez"],
                    resumen_dia["ultima_vez"],
                    minutos,
                    resumen_dia["num_avistamientos"],
                ),
            )
            total_agregados += 1

        # Borrar registros detallados de este dia
        borrados = bd.ejecutar(
            "DELETE FROM presencia WHERE DATE(visto_en) = ?",
            (fecha,),
        )
        total_borrados += 1

    logger.info(
        f"Agregacion completada: {total_agregados} resumenes creados, "
        f"{total_borrados} dias limpiados"
    )


def _calcular_minutos(timestamps: list[str], umbral_min: int = 15) -> int:
    """Calcula minutos totales de conexion a partir de timestamps."""
    if not timestamps:
        return 0

    from datetime import datetime

    minutos = 0
    inicio = datetime.fromisoformat(timestamps[0])
    anterior = inicio

    for ts in timestamps[1:]:
        actual = datetime.fromisoformat(ts)
        if (actual - anterior).total_seconds() > umbral_min * 60:
            minutos += int((anterior - inicio).total_seconds() / 60)
            inicio = actual
        anterior = actual

    minutos += int((anterior - inicio).total_seconds() / 60)
    return max(minutos, 0)


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    """Se ejecuta al arrancar la app: crea BD y lanza escaneos periodicos."""
    # Asegurar que el directorio de datos existe
    directorio_bd = os.path.dirname(RUTA_BD)
    if directorio_bd:
        os.makedirs(directorio_bd, exist_ok=True)

    inicializar_bd()

    # Configurar escaneo periodico
    planificador.add_job(
        escanear_red,
        "interval",
        seconds=INTERVALO_ESCANEO,
        id="escaneo_periodico",
        name="Escaneo periodico de red",
        replace_existing=True,
    )
    # Agregacion nocturna de presencia (cada dia a las 03:00)
    planificador.add_job(
        agregar_presencia,
        CronTrigger(hour=3, minute=0),
        id="agregacion_presencia",
        name="Agregacion nocturna de presencia",
        replace_existing=True,
    )

    planificador.start()
    logger.info(
        f"Escaneo periodico configurado cada {INTERVALO_ESCANEO} segundos"
    )
    logger.info(
        f"Agregacion de presencia: cada noche a las 03:00 "
        f"(detalle {PRESENCIA_DIAS_DETALLE} dias)"
    )

    # Ejecutar un primer escaneo al arrancar
    logger.info("Ejecutando escaneo inicial...")
    escanear_red()

    yield

    # Apagar planificador al cerrar
    planificador.shutdown(wait=False)
    logger.info("Planificador detenido")


app = FastAPI(
    title="ReDo — Red Domestica",
    description="Monitor de dispositivos en la red local",
    version="1.0.0",
    lifespan=ciclo_vida,
)

# ---- Registrar rutas API ----
app.include_router(resumen.ruta, prefix="/api/resumen", tags=["Resumen"])
app.include_router(dispositivos.ruta, prefix="/api/dispositivos", tags=["Dispositivos"])
app.include_router(escaneos.ruta, prefix="/api/escaneos", tags=["Escaneos"])
app.include_router(presencia.ruta, prefix="/api/presencia", tags=["Presencia"])


# ---- Ruta de conveniencia: POST /api/escanear ----
@app.post("/api/escanear", tags=["Escaneos"])
def escanear_manual():
    """Alias de /api/escaneos/ejecutar para mayor comodidad."""
    return escanear_red()


# ---- Servir frontend estatico (DEBE ir al final, es catch-all) ----
app.mount("/", StaticFiles(directory="static", html=True), name="static")
