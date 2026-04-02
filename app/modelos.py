"""
ReDo — Modelos Pydantic (esquemas de request/response).
"""

from pydantic import BaseModel
from typing import Optional


# ============================================================
# Dispositivos
# ============================================================

class DispositivoRespuesta(BaseModel):
    id: int
    mac: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    fabricante: Optional[str] = None
    primera_vez: Optional[str] = None
    ultima_vez: Optional[str] = None
    confiable: int = 0
    notas: Optional[str] = None
    tipo: str = "otro"
    tipo_auto: int = 0
    zona: Optional[str] = None


class DispositivoActualizar(BaseModel):
    confiable: Optional[int] = None
    notas: Optional[str] = None
    tipo: Optional[str] = None
    zona: Optional[str] = None


# ============================================================
# Tipos de dispositivo
# ============================================================

class TipoDispositivoRespuesta(BaseModel):
    clave: str
    nombre: str
    icono: str


class TipoDispositivoCrear(BaseModel):
    clave: str
    nombre: str
    icono: str


class TipoDispositivoActualizar(BaseModel):
    nombre: Optional[str] = None
    icono: Optional[str] = None


# ============================================================
# Escaneos
# ============================================================

class EscaneoRespuesta(BaseModel):
    id: int
    inicio: str
    fin: Optional[str] = None
    dispositivos_encontrados: int = 0
    dispositivos_nuevos: int = 0


# ============================================================
# Alertas
# ============================================================

class AlertaRespuesta(BaseModel):
    id: int
    tipo: str
    mensaje: str
    dispositivo_id: Optional[int] = None
    fecha: Optional[str] = None
    enviada: int = 0
    resuelta: int = 0


# ============================================================
# Presencia
# ============================================================

class FranjaPresencia(BaseModel):
    """Una franja de conexion continua (ej: 07:30 - 08:15)."""
    desde: str
    hasta: str


class DiaPresencia(BaseModel):
    """Resumen de presencia de un dispositivo en un dia concreto."""
    fecha: str
    primera_vez: Optional[str] = None
    ultima_vez: Optional[str] = None
    minutos_conectado: int = 0
    num_avistamientos: int = 0
    franjas: list[FranjaPresencia] = []


class PresenciaDispositivo(BaseModel):
    """Historial de presencia de un dispositivo."""
    dispositivo_id: int
    nombre: Optional[str] = None
    dias: list[DiaPresencia] = []


class DispositivoTimeline(BaseModel):
    """Presencia de un dispositivo en un dia (para el timeline general)."""
    dispositivo_id: int
    nombre: Optional[str] = None
    mac: str
    tipo: str = "otro"
    franjas: list[FranjaPresencia] = []


# ============================================================
# Configuracion
# ============================================================

class ConfiguracionRespuesta(BaseModel):
    clave: str
    valor: str
    tipo: str  # string, int, float
    editable: int
    descripcion: Optional[str] = None
    ultima_actualizacion: Optional[str] = None


class ConfiguracionActualizar(BaseModel):
    valor: str  # El usuario manda el valor como string, backend lo convierte


# ============================================================
# Resumen (para hogarOS portal)
# ============================================================

class ResumenRespuesta(BaseModel):
    dispositivos_activos: int
    dispositivos_confiables: int
    dispositivos_desconocidos: int
    ultimo_escaneo: Optional[str] = None
    por_tipo: dict[str, int] = {}
