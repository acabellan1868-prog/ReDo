"""ReDo — Rutas de alertas para el centro de alertas unificado."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import bd
from app.modelos import AlertaRespuesta

ruta = APIRouter()


class SilenciarCuerpo(BaseModel):
    """Cuerpo de la petición para silenciar una alerta."""
    horas: int | None = None
    permanente: bool = False


@ruta.get("")
def listar_alertas():
    """Lista alertas: activas primero, luego por fecha descendente."""
    activas = bd.consultar_uno(
        """SELECT COUNT(*) as total FROM alertas
           WHERE resuelta = 0
           AND (silenciada_hasta IS NULL OR silenciada_hasta < datetime('now'))"""
    )
    alertas = bd.consultar_todos(
        """SELECT id, tipo, mensaje, dispositivo_id, fecha, enviada, resuelta, silenciada_hasta
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


@ruta.post("/{alerta_id}/silenciar")
def silenciar_alerta(alerta_id: int, cuerpo: SilenciarCuerpo):
    """Silencia una alerta temporalmente (horas) o de forma permanente."""
    existente = bd.consultar_uno(
        "SELECT id FROM alertas WHERE id = ?", (alerta_id,)
    )
    if not existente:
        raise HTTPException(404, "Alerta no encontrada")

    if cuerpo.permanente:
        hasta = "9999-12-31"
    elif cuerpo.horas and cuerpo.horas > 0:
        hasta = (datetime.now(timezone.utc) + timedelta(hours=cuerpo.horas)).strftime("%Y-%m-%dT%H:%M:%S")
    else:
        raise HTTPException(400, "Indica horas o permanente=true")

    bd.ejecutar(
        "UPDATE alertas SET silenciada_hasta = ? WHERE id = ?", (hasta, alerta_id)
    )
    return {"ok": True, "id": alerta_id, "silenciada_hasta": hasta}


@ruta.post("/{alerta_id}/activar")
def activar_alerta(alerta_id: int):
    """Quita el silencio de una alerta (vuelve a ser activa)."""
    existente = bd.consultar_uno(
        "SELECT id FROM alertas WHERE id = ?", (alerta_id,)
    )
    if not existente:
        raise HTTPException(404, "Alerta no encontrada")

    bd.ejecutar(
        "UPDATE alertas SET silenciada_hasta = NULL WHERE id = ?", (alerta_id,)
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
