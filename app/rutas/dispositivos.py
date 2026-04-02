"""ReDo — Rutas CRUD para dispositivos de la red."""

import io
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
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
        # Validar que el tipo exista en el catalogo
        tipo_valido = bd.consultar_uno(
            "SELECT clave FROM tipos_dispositivo WHERE clave = ?",
            (datos.tipo,),
        )
        if not tipo_valido:
            raise HTTPException(400, f"Tipo '{datos.tipo}' no existe en el catalogo")
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


# ============================================================
# Exportación de datos
# ============================================================

@ruta.get("/exportar/csv")
def exportar_csv(
    confiable: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    zona: Optional[str] = Query(None),
):
    """Exporta dispositivos como CSV con filtros aplicados."""
    # Construir WHERE dinámicamente (reutilizar lógica de listar_dispositivos)
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

    sql = "SELECT id, mac, ip, hostname, tipo, zona, confiable, notas FROM dispositivos"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ultima_vez DESC"

    dispositivos = bd.consultar_todos(sql, tuple(parametros))

    # Generar CSV
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "mac", "ip", "nombre", "hostname", "tipo", "zona", "confiable"],
    )
    writer.writeheader()
    for d in dispositivos:
        # Nombre es notas (personalizado) o vacío
        nombre = d["notas"] or ""
        writer.writerow({
            "id": d["id"],
            "mac": d["mac"],
            "ip": d["ip"] or "",
            "nombre": nombre,
            "hostname": d["hostname"] or "",
            "tipo": d["tipo"],
            "zona": d["zona"] or "",
            "confiable": d["confiable"],
        })

    # Retornar como descarga
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dispositivos_{fecha}.csv"},
    )


@ruta.get("/exportar/json")
def exportar_json(
    confiable: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    zona: Optional[str] = Query(None),
):
    """Exporta dispositivos como JSON con filtros aplicados."""
    # Construir WHERE dinámicamente (reutilizar lógica de listar_dispositivos)
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

    dispositivos = bd.consultar_todos(sql, tuple(parametros))

    # Retornar JSON con headers de descarga
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    return JSONResponse(
        content=dispositivos,
        headers={"Content-Disposition": f"attachment; filename=dispositivos_{fecha}.json"},
    )
