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


class DispositivoActualizar(BaseModel):
    confiable: Optional[int] = None
    notas: Optional[str] = None


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


# ============================================================
# Resumen (para hogarOS portal)
# ============================================================

class ResumenRespuesta(BaseModel):
    dispositivos_activos: int
    dispositivos_confiables: int
    dispositivos_desconocidos: int
    ultimo_escaneo: Optional[str] = None
