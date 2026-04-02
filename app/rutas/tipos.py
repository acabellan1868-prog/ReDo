"""ReDo — Rutas CRUD para tipos de dispositivo."""

from fastapi import APIRouter, HTTPException

from app import bd
from app.modelos import (
    TipoDispositivoRespuesta,
    TipoDispositivoCrear,
    TipoDispositivoActualizar,
)

ruta = APIRouter()


@ruta.get("", response_model=list[TipoDispositivoRespuesta])
def listar_tipos():
    """Devuelve todos los tipos de dispositivo ordenados por nombre."""
    return bd.consultar_todos(
        "SELECT clave, nombre, icono FROM tipos_dispositivo ORDER BY nombre"
    )


@ruta.post("", response_model=TipoDispositivoRespuesta, status_code=201)
def crear_tipo(datos: TipoDispositivoCrear):
    """Crea un nuevo tipo de dispositivo."""
    existente = bd.consultar_uno(
        "SELECT clave FROM tipos_dispositivo WHERE clave = ?", (datos.clave,)
    )
    if existente:
        raise HTTPException(409, f"Ya existe un tipo con clave '{datos.clave}'")

    bd.ejecutar(
        "INSERT INTO tipos_dispositivo (clave, nombre, icono) VALUES (?, ?, ?)",
        (datos.clave, datos.nombre, datos.icono),
    )
    return bd.consultar_uno(
        "SELECT clave, nombre, icono FROM tipos_dispositivo WHERE clave = ?",
        (datos.clave,),
    )


@ruta.put("/{clave}", response_model=TipoDispositivoRespuesta)
def actualizar_tipo(clave: str, datos: TipoDispositivoActualizar):
    """Actualiza nombre y/o icono de un tipo existente."""
    existente = bd.consultar_uno(
        "SELECT clave FROM tipos_dispositivo WHERE clave = ?", (clave,)
    )
    if not existente:
        raise HTTPException(404, "Tipo no encontrado")

    campos = []
    valores = []
    if datos.nombre is not None:
        campos.append("nombre = ?")
        valores.append(datos.nombre)
    if datos.icono is not None:
        campos.append("icono = ?")
        valores.append(datos.icono)

    if campos:
        valores.append(clave)
        bd.ejecutar(
            f"UPDATE tipos_dispositivo SET {', '.join(campos)} WHERE clave = ?",
            tuple(valores),
        )

    return bd.consultar_uno(
        "SELECT clave, nombre, icono FROM tipos_dispositivo WHERE clave = ?",
        (clave,),
    )


@ruta.delete("/{clave}", status_code=204)
def eliminar_tipo(clave: str):
    """
    Elimina un tipo de dispositivo.
    Los dispositivos que lo usaban pasan a tipo 'otro'.
    No se puede eliminar el tipo 'otro' (es el fallback).
    """
    if clave == "otro":
        raise HTTPException(400, "No se puede eliminar el tipo 'otro' (es el valor por defecto)")

    existente = bd.consultar_uno(
        "SELECT clave FROM tipos_dispositivo WHERE clave = ?", (clave,)
    )
    if not existente:
        raise HTTPException(404, "Tipo no encontrado")

    # Reasignar dispositivos que usaban este tipo
    bd.ejecutar(
        "UPDATE dispositivos SET tipo = 'otro', tipo_auto = 0 WHERE tipo = ?",
        (clave,),
    )
    bd.ejecutar(
        "DELETE FROM tipos_dispositivo WHERE clave = ?", (clave,)
    )
