"""ReDo — Rutas CRUD para configuración dinámica del sistema."""

from fastapi import APIRouter, HTTPException
from ipaddress import IPv4Network, AddressValueError
from datetime import datetime

from app import bd
from app.modelos import ConfiguracionRespuesta, ConfiguracionActualizar

ruta = APIRouter()


def _validar_cidr(cidr: str) -> bool:
    """Valida que una cadena sea un CIDR IPv4 válido."""
    try:
        IPv4Network(cidr, strict=False)
        return True
    except (AddressValueError, ValueError):
        return False


def _convertir_valor(valor_str: str, tipo: str):
    """Convierte una cadena al tipo especificado."""
    if tipo == "int":
        try:
            return int(valor_str)
        except ValueError:
            raise ValueError(f"No se puede convertir '{valor_str}' a entero")
    elif tipo == "float":
        try:
            return float(valor_str)
        except ValueError:
            raise ValueError(f"No se puede convertir '{valor_str}' a decimal")
    else:  # string
        return str(valor_str)


def _validar_config(clave: str, valor: str) -> tuple[bool, str]:
    """
    Valida un valor de configuración según su clave.
    Retorna (es_valido, mensaje_error).
    """
    if clave == "red_objetivo":
        if not _validar_cidr(valor):
            return False, f"'{valor}' no es un CIDR IPv4 válido (ej: 192.168.31.0/24)"
        return True, ""

    elif clave == "intervalo_escaneo":
        try:
            segundos = int(valor)
            if segundos < 60:
                return False, "El intervalo debe ser al menos 60 segundos"
            if segundos > 3600:
                return False, "El intervalo no puede exceder 3600 segundos"
            return True, ""
        except ValueError:
            return False, f"'{valor}' no es un número entero válido"

    elif clave == "presencia_dias_detalle":
        try:
            dias = int(valor)
            if dias < 1:
                return False, "Debe ser al menos 1 día"
            if dias > 365:
                return False, "No puede exceder 365 días"
            return True, ""
        except ValueError:
            return False, f"'{valor}' no es un número entero válido"

    elif clave == "ntfy_url":
        # Validación básica: debe empezar con http
        if not (valor.startswith("http://") or valor.startswith("https://")):
            return False, "La URL debe empezar con http:// o https://"
        return True, ""

    elif clave == "ntfy_topic":
        # Validación básica: no puede estar vacío
        if not valor or not valor.strip():
            return False, "El topic de NTFY no puede estar vacío"
        return True, ""

    return True, ""


@ruta.get("", response_model=list[ConfiguracionRespuesta])
def listar_configuracion():
    """Lista toda la configuración editable del sistema."""
    filas = bd.consultar_todos(
        "SELECT clave, valor, tipo, editable, descripcion, ultima_actualizacion FROM configuracion WHERE editable = 1 ORDER BY clave"
    )
    return filas


@ruta.get("/{clave}", response_model=ConfiguracionRespuesta)
def obtener_configuracion(clave: str):
    """Obtiene un parámetro de configuración por su clave."""
    fila = bd.consultar_uno(
        "SELECT clave, valor, tipo, editable, descripcion, ultima_actualizacion FROM configuracion WHERE clave = ?",
        (clave,),
    )
    if not fila:
        raise HTTPException(404, f"Configuración '{clave}' no encontrada")
    return fila


@ruta.put("/{clave}", response_model=ConfiguracionRespuesta)
def actualizar_configuracion(clave: str, datos: ConfiguracionActualizar):
    """
    Actualiza un parámetro de configuración.

    Validaciones:
    - red_objetivo: debe ser un CIDR IPv4 válido
    - intervalo_escaneo: entero entre 60 y 3600 segundos
    - presencia_dias_detalle: entero entre 1 y 365
    - ntfy_url: debe ser http:// o https://
    - ntfy_topic: no puede estar vacío

    El cambio se aplica inmediatamente a la BD y se sincroniza con el runtime.
    """
    # Verificar que existe
    existente = bd.consultar_uno(
        "SELECT * FROM configuracion WHERE clave = ?", (clave,)
    )
    if not existente:
        raise HTTPException(404, f"Configuración '{clave}' no encontrada")

    # Verificar que es editable
    if existente["editable"] != 1:
        raise HTTPException(
            400, f"Configuración '{clave}' no es editable desde la API"
        )

    # Validar el valor
    es_valido, mensaje_error = _validar_config(clave, datos.valor)
    if not es_valido:
        raise HTTPException(400, mensaje_error)

    # Actualizar en BD
    bd.ejecutar(
        """UPDATE configuracion
           SET valor = ?, ultima_actualizacion = ?
           WHERE clave = ?""",
        (datos.valor, datetime.now().isoformat(), clave),
    )

    # Aplicar cambio en runtime (si es necesario)
    _aplicar_config_en_runtime(clave, datos.valor)

    # Retornar el valor actualizado
    return bd.consultar_uno(
        "SELECT clave, valor, tipo, editable, descripcion, ultima_actualizacion FROM configuracion WHERE clave = ?",
        (clave,),
    )


def _aplicar_config_en_runtime(clave: str, valor: str) -> None:
    """
    Aplica un cambio de configuración en el runtime.

    - intervalo_escaneo: replanifica el job de APScheduler
    - presencia_dias_detalle: replanifica el job de agregación
    - Otros: se aplican en el próximo ciclo de escaneo
    """
    import logging
    logger = logging.getLogger("redo.config")

    if clave == "intervalo_escaneo":
        try:
            from app.principal import planificador
            segundos = int(valor)
            planificador.reschedule_job(
                "escaneo_periodico",
                trigger="interval",
                seconds=segundos
            )
            logger.info(f"Intervalo de escaneo replanificado a {segundos} segundos")
        except Exception as e:
            logger.error(f"Error al replanificar escaneo: {e}")

    elif clave == "presencia_dias_detalle":
        # Esta variable se usa en lectura dentro de agregar_presencia
        # Se aplicará en el próximo ciclo (no necesita replanificación)
        logger.info(f"Presencia días detalle actualizado a {valor} (aplicará en próx ciclo)")


