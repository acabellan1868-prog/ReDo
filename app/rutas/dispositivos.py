"""ReDo — Rutas CRUD para dispositivos de la red."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app import bd
from app.modelos import DispositivoRespuesta, DispositivoActualizar

ruta = APIRouter()


@ruta.get("", response_model=list[DispositivoRespuesta])
def listar_dispositivos(
    confiable: Optional[int] = Query(
        None, description="Filtrar: 1=confiables, 0=desconocidos"
    ),
    tipo: Optional[str] = Query(
        None, description="Filtrar por tipo (telefono, portatil, iot, etc.)"
    ),
    zona: Optional[str] = Query(
        None, description="Filtrar por zona (Salon, Despacho, etc.)"
    ),
):
    """Lista dispositivos con filtros opcionales combinables."""
    where = []
    parametros = []

    if confiable is not None:
        where.append("confiable = ?")
        parametros.append(confiable)
    if tipo is not None:
        where.append("tipo = ?")
        parametros.append(tipo)
    if zona is not None:
        where.append("zona = ?")
        parametros.append(zona)

    sql = "SELECT * FROM dispositivos"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ultima_vez DESC"

    return bd.consultar_todos(sql, tuple(parametros))


@ruta.get("/zonas", response_model=list[str])
def listar_zonas():
    """Devuelve las zonas distintas usadas (para autocompletado)."""
    filas = bd.consultar_todos(
        "SELECT DISTINCT zona FROM dispositivos WHERE zona IS NOT NULL AND zona != '' ORDER BY zona"
    )
    return [fila["zona"] for fila in filas]


@ruta.get("/{dispositivo_id}", response_model=DispositivoRespuesta)
def obtener_dispositivo(dispositivo_id: int):
    """Obtiene los detalles de un dispositivo por su ID."""
    fila = bd.consultar_uno(
        "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
    )
    if not fila:
        raise HTTPException(404, "Dispositivo no encontrado")
    return fila


@ruta.post("/{dispositivo_id}/confiable", response_model=DispositivoRespuesta)
def marcar_confiable(dispositivo_id: int):
    """Marca un dispositivo como confiable."""
    existente = bd.consultar_uno(
        "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
    )
    if not existente:
        raise HTTPException(404, "Dispositivo no encontrado")

    bd.ejecutar(
        "UPDATE dispositivos SET confiable = 1 WHERE id = ?",
        (dispositivo_id,),
    )
    return bd.consultar_uno(
        "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
    )


@ruta.put("/{dispositivo_id}", response_model=DispositivoRespuesta)
def actualizar_dispositivo(
    dispositivo_id: int, datos: DispositivoActualizar
):
    """Actualiza notas o estado de confiabilidad de un dispositivo."""
    existente = bd.consultar_uno(
        "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
    )
    if not existente:
        raise HTTPException(404, "Dispositivo no encontrado")

    campos = []
    valores = []
    if datos.confiable is not None:
        campos.append("confiable = ?")
        valores.append(datos.confiable)
    if datos.notas is not None:
        campos.append("notas = ?")
        valores.append(datos.notas)
    if datos.tipo is not None:
        campos.append("tipo = ?")
        valores.append(datos.tipo)
        # Si el usuario cambia el tipo manualmente, ya no es auto-detectado
        campos.append("tipo_auto = 0")

    if datos.zona is not None:
        campos.append("zona = ?")
        valores.append(datos.zona)

    if campos:
        valores.append(dispositivo_id)
        bd.ejecutar(
            f"UPDATE dispositivos SET {', '.join(campos)} WHERE id = ?",
            tuple(valores),
        )

    return bd.consultar_uno(
        "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
    )
