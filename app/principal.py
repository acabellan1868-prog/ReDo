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

from app.bd import inicializar_bd
from app.config import RUTA_BD, INTERVALO_ESCANEO
from app.escaner import escanear_red
from app.rutas import resumen, dispositivos, escaneos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("redo")

# Planificador de escaneos periodicos
planificador = BackgroundScheduler()


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
    planificador.start()
    logger.info(
        f"Escaneo periodico configurado cada {INTERVALO_ESCANEO} segundos"
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


# ---- Ruta de conveniencia: POST /api/escanear ----
@app.post("/api/escanear", tags=["Escaneos"])
def escanear_manual():
    """Alias de /api/escaneos/ejecutar para mayor comodidad."""
    return escanear_red()


# ---- Servir frontend estatico (DEBE ir al final, es catch-all) ----
app.mount("/", StaticFiles(directory="static", html=True), name="static")
