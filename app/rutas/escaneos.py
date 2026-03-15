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
