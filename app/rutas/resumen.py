"""ReDo — Ruta de resumen para el portal hogarOS."""

from fastapi import APIRouter

from app import bd
from app.modelos import ResumenRespuesta

ruta = APIRouter()


@ruta.get("", response_model=ResumenRespuesta)
def resumen():
    """
    Devuelve el resumen de estado de la red para el portal hogarOS.

    Formato esperado por el portal:
    {
        "dispositivos_activos": 12,
        "dispositivos_confiables": 11,
        "dispositivos_desconocidos": 1,
        "ultimo_escaneo": "2026-03-13T18:30:00"
    }
    """
    # Dispositivos vistos en las ultimas 24 horas = activos
    contadores = bd.consultar_uno("""
        SELECT
            COUNT(*) as dispositivos_activos,
            SUM(CASE WHEN confiable = 1 THEN 1 ELSE 0 END) as dispositivos_confiables,
            SUM(CASE WHEN confiable = 0 THEN 1 ELSE 0 END) as dispositivos_desconocidos
        FROM dispositivos
        WHERE ultima_vez >= datetime('now', '-24 hours')
    """)

    ultimo = bd.consultar_uno(
        "SELECT inicio FROM escaneos ORDER BY inicio DESC LIMIT 1"
    )

    return {
        "dispositivos_activos": contadores["dispositivos_activos"] if contadores else 0,
        "dispositivos_confiables": contadores["dispositivos_confiables"] or 0 if contadores else 0,
        "dispositivos_desconocidos": contadores["dispositivos_desconocidos"] or 0 if contadores else 0,
        "ultimo_escaneo": ultimo["inicio"] if ultimo else None,
    }
