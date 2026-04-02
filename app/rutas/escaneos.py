"""ReDo — Rutas para escaneos: historial y disparo manual."""

from fastapi import APIRouter, Query

from app import bd
from app.modelos import EscaneoRespuesta
from app.escaner import escanear_red

ruta = APIRouter()


@ruta.get("", response_model=list[EscaneoRespuesta])
def listar_escaneos(
    limite: int = Query(
        20, description="Numero maximo de escaneos a devolver"
    ),
):
    """Devuelve el historial de escaneos, mas recientes primero."""
    return bd.consultar_todos(
        "SELECT * FROM escaneos ORDER BY inicio DESC LIMIT ?",
        (limite,),
    )


@ruta.post("/ejecutar")
def ejecutar_escaneo():
    """Dispara un escaneo manual de la red."""
    resultado = escanear_red()
    return resultado


@ruta.get("/estadisticas/por-fecha")
def estadisticas_por_fecha(dias: int = Query(30, description="Últimos N días")):
    """Devuelve estadísticas diarias de escaneos para gráficos."""
    datos = bd.consultar_todos(
        """
        SELECT
            DATE(inicio) as fecha,
            COUNT(*) as num_escaneos,
            ROUND(AVG(dispositivos_encontrados), 1) as promedio_encontrados,
            MAX(dispositivos_nuevos) as max_nuevos,
            ROUND(AVG((JULIANDAY(fin) - JULIANDAY(inicio)) * 24 * 60 * 60), 2) as duracion_promedio_seg
        FROM escaneos
        WHERE inicio >= DATE('now', '-' || ? || ' days')
        GROUP BY DATE(inicio)
        ORDER BY fecha DESC
        """,
        (dias,),
    )
    return datos
