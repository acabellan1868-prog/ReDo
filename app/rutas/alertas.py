"""ReDo — Rutas de alertas para el centro de alertas unificado."""

from fastapi import APIRouter, HTTPException

from app import bd
from app.modelos import AlertaRespuesta

ruta = APIRouter()


@ruta.get("")
def listar_alertas():
    """Lista alertas: activas primero, luego por fecha descendente."""
    activas = bd.consultar_uno(
        "SELECT COUNT(*) as total FROM alertas WHERE resuelta = 0"
    )
    alertas = bd.consultar_todos(
        """SELECT id, tipo, mensaje, dispositivo_id, fecha, enviada, resuelta
           FROM alertas
           ORDER BY resuelta ASC, fecha DESC
           LIMIT 50"""
    )
    return {
        "modulo": "redo",
        "activas": activas["total"] if activas else 0,
        "alertas": alertas,
    }


@ruta.post("/{alerta_id}/resolver")
def resolver_alerta(alerta_id: int):
    """Marca una alerta como resuelta."""
    existente = bd.consultar_uno(
        "SELECT id FROM alertas WHERE id = ?", (alerta_id,)
    )
    if not existente:
        raise HTTPException(404, "Alerta no encontrada")

    bd.ejecutar(
        "UPDATE alertas SET resuelta = 1 WHERE id = ?", (alerta_id,)
    )
    return {"ok": True, "id": alerta_id}


@ruta.delete("/{alerta_id}")
def eliminar_alerta(alerta_id: int):
    """Elimina una alerta."""
    existente = bd.consultar_uno(
        "SELECT id FROM alertas WHERE id = ?", (alerta_id,)
    )
    if not existente:
        raise HTTPException(404, "Alerta no encontrada")

    bd.ejecutar("DELETE FROM alertas WHERE id = ?", (alerta_id,))
    return {"ok": True, "id": alerta_id}
