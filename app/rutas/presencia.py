"""ReDo — Rutas de historial de presencia de dispositivos."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from app import bd
from app.modelos import (
    PresenciaDispositivo,
    DiaPresencia,
    FranjaPresencia,
    DispositivoTimeline,
)

ruta = APIRouter()

# Minutos sin ver un dispositivo para cerrar una franja
UMBRAL_DESCONEXION_MIN = 15


def _calcular_franjas(avistamientos: list[str], intervalo_min: int = UMBRAL_DESCONEXION_MIN) -> list[dict]:
    """
    Agrupa timestamps consecutivos en franjas de conexion.

    Si entre dos avistamientos pasan mas de `intervalo_min` minutos,
    se cierra la franja actual y se abre una nueva.

    Args:
        avistamientos: Lista de timestamps ISO ordenados cronologicamente
        intervalo_min: Minutos maximos entre avistamientos consecutivos

    Returns:
        Lista de dicts con 'desde' y 'hasta' (formato HH:MM)
    """
    if not avistamientos:
        return []

    franjas = []
    inicio = datetime.fromisoformat(avistamientos[0])
    anterior = inicio

    for ts in avistamientos[1:]:
        actual = datetime.fromisoformat(ts)
        if (actual - anterior).total_seconds() > intervalo_min * 60:
            # Hueco grande: cerrar franja anterior, abrir nueva
            franjas.append({
                "desde": inicio.strftime("%H:%M"),
                "hasta": anterior.strftime("%H:%M"),
            })
            inicio = actual
        anterior = actual

    # Cerrar la ultima franja
    franjas.append({
        "desde": inicio.strftime("%H:%M"),
        "hasta": anterior.strftime("%H:%M"),
    })

    return franjas


@ruta.get(
    "/dispositivos/{dispositivo_id}",
    response_model=PresenciaDispositivo,
)
def presencia_dispositivo(
    dispositivo_id: int,
    dias: int = Query(7, description="Numero de dias de historial", ge=1, le=365),
):
    """
    Historial de presencia de un dispositivo.

    Devuelve las franjas de conexion por dia para los ultimos N dias.
    Si el dia cae dentro del periodo de detalle (< 180 dias), se calculan
    franjas exactas. Si es mas antiguo, se devuelve el resumen diario.
    """
    # Verificar que el dispositivo existe
    dispositivo = bd.consultar_uno(
        "SELECT id, notas FROM dispositivos WHERE id = ?",
        (dispositivo_id,),
    )
    if not dispositivo:
        raise HTTPException(404, "Dispositivo no encontrado")

    fecha_desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
    resultado_dias = []

    # Obtener datos detallados de la tabla presencia
    registros = bd.consultar_todos(
        """SELECT visto_en, DATE(visto_en) as fecha
           FROM presencia
           WHERE dispositivo_id = ? AND DATE(visto_en) >= ?
           ORDER BY visto_en""",
        (dispositivo_id, fecha_desde),
    )

    # Agrupar por dia
    dias_detalle = {}
    for reg in registros:
        fecha = reg["fecha"]
        if fecha not in dias_detalle:
            dias_detalle[fecha] = []
        dias_detalle[fecha].append(reg["visto_en"])

    # Construir respuesta para dias con detalle
    for fecha, timestamps in sorted(dias_detalle.items()):
        franjas = _calcular_franjas(timestamps)
        primera = datetime.fromisoformat(timestamps[0]).strftime("%H:%M")
        ultima = datetime.fromisoformat(timestamps[-1]).strftime("%H:%M")

        # Calcular minutos conectados (suma de duracion de franjas)
        minutos = 0
        for f in franjas:
            h1, m1 = map(int, f["desde"].split(":"))
            h2, m2 = map(int, f["hasta"].split(":"))
            minutos += (h2 * 60 + m2) - (h1 * 60 + m1)

        resultado_dias.append(DiaPresencia(
            fecha=fecha,
            primera_vez=primera,
            ultima_vez=ultima,
            minutos_conectado=max(minutos, 0),
            num_avistamientos=len(timestamps),
            franjas=[FranjaPresencia(**f) for f in franjas],
        ))

    # Completar con datos agregados (presencia_diaria) para dias mas antiguos
    registros_diarios = bd.consultar_todos(
        """SELECT * FROM presencia_diaria
           WHERE dispositivo_id = ? AND fecha >= ? AND fecha NOT IN ({})
           ORDER BY fecha""".format(
            ",".join(f"'{d.fecha}'" for d in resultado_dias) or "''"
        ),
        (dispositivo_id, fecha_desde),
    )

    for reg in registros_diarios:
        resultado_dias.append(DiaPresencia(
            fecha=reg["fecha"],
            primera_vez=reg["primera_vez"],
            ultima_vez=reg["ultima_vez"],
            minutos_conectado=reg["minutos_conectado"] or 0,
            num_avistamientos=reg["num_avistamientos"] or 0,
            franjas=[],  # Sin franjas para datos agregados
        ))

    # Ordenar por fecha descendente
    resultado_dias.sort(key=lambda d: d.fecha, reverse=True)

    return PresenciaDispositivo(
        dispositivo_id=dispositivo_id,
        nombre=dispositivo["notas"],
        dias=resultado_dias,
    )


@ruta.get("/timeline", response_model=list[DispositivoTimeline])
def timeline(
    fecha: Optional[str] = Query(
        None,
        description="Fecha YYYY-MM-DD (por defecto hoy)",
    ),
):
    """
    Timeline de presencia de todos los dispositivos en un dia concreto.

    Devuelve una lista de dispositivos con sus franjas de conexion,
    ideal para pintar un grafico Gantt horizontal.
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    # Obtener todos los avistamientos del dia agrupados por dispositivo
    registros = bd.consultar_todos(
        """SELECT p.dispositivo_id, p.visto_en,
                  d.notas, d.mac, d.tipo
           FROM presencia p
           JOIN dispositivos d ON d.id = p.dispositivo_id
           WHERE DATE(p.visto_en) = ?
           ORDER BY p.dispositivo_id, p.visto_en""",
        (fecha,),
    )

    if not registros:
        return []

    # Agrupar por dispositivo
    dispositivos = {}
    for reg in registros:
        did = reg["dispositivo_id"]
        if did not in dispositivos:
            dispositivos[did] = {
                "nombre": reg["notas"],
                "mac": reg["mac"],
                "tipo": reg["tipo"] or "otro",
                "timestamps": [],
            }
        dispositivos[did]["timestamps"].append(reg["visto_en"])

    # Construir respuesta
    resultado = []
    for did, info in dispositivos.items():
        franjas = _calcular_franjas(info["timestamps"])
        resultado.append(DispositivoTimeline(
            dispositivo_id=did,
            nombre=info["nombre"],
            mac=info["mac"],
            tipo=info["tipo"],
            franjas=[FranjaPresencia(**f) for f in franjas],
        ))

    return resultado
