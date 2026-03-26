"""
ReDo — Modulo de base de datos SQLite.
Gestion de conexion, helpers e inicializacion del esquema.
"""

import sqlite3
from pathlib import Path

from app.config import RUTA_BD


def obtener_conexion() -> sqlite3.Connection:
    """Abre una conexion a la BD con WAL y foreign keys activados."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA journal_mode=WAL")
    conexion.execute("PRAGMA foreign_keys=ON")
    return conexion


def inicializar_bd():
    """Crea las tablas si no existen ejecutando migraciones + esquema.sql."""
    ruta_esquema = Path(__file__).parent / "esquema.sql"
    conexion = obtener_conexion()

    # ── Migraciones para BDs existentes (v1 → v2) ──
    # Deben ejecutarse ANTES del esquema, porque esquema.sql v2
    # referencia las columnas nuevas en índices y CREATE TABLE.
    # SQLite no soporta ALTER TABLE ... IF NOT EXISTS,
    # así que comprobamos las columnas antes de añadirlas.
    tablas = {
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "dispositivos" in tablas:
        columnas = {
            fila[1]
            for fila in conexion.execute("PRAGMA table_info(dispositivos)").fetchall()
        }
        if "tipo" not in columnas:
            conexion.execute(
                "ALTER TABLE dispositivos ADD COLUMN tipo TEXT NOT NULL DEFAULT 'otro'"
            )
        if "tipo_auto" not in columnas:
            conexion.execute(
                "ALTER TABLE dispositivos ADD COLUMN tipo_auto INTEGER NOT NULL DEFAULT 0"
            )
        if "zona" not in columnas:
            conexion.execute("ALTER TABLE dispositivos ADD COLUMN zona TEXT")
        conexion.commit()

    # ── Esquema: crea tablas que no existan (presencia, presencia_diaria, etc.) ──
    conexion.executescript(ruta_esquema.read_text(encoding="utf-8"))

    # ── Migración puntual: auto-detectar tipo en dispositivos existentes ──
    # Solo toca dispositivos con tipo='otro' (sin clasificar) y fabricante conocido.
    # Se importa aquí (lazy) para evitar dependencia circular.
    from app.escaner import inferir_tipo

    sin_clasificar = conexion.execute(
        "SELECT id, fabricante FROM dispositivos WHERE tipo = 'otro' AND fabricante IS NOT NULL"
    ).fetchall()
    reclasificados = 0
    for fila in sin_clasificar:
        tipo_sugerido = inferir_tipo(fila["fabricante"])
        if tipo_sugerido:
            conexion.execute(
                "UPDATE dispositivos SET tipo = ?, tipo_auto = 1 WHERE id = ?",
                (tipo_sugerido, fila["id"]),
            )
            reclasificados += 1
    if reclasificados:
        conexion.commit()
        import logging
        logging.getLogger("redo.bd").info(
            f"Migración auto-tipo: {reclasificados} dispositivos reclasificados"
        )

    conexion.close()


def consultar_todos(sql: str, parametros: tuple = ()) -> list[dict]:
    """Ejecuta una consulta SELECT y devuelve todas las filas como lista de dicts."""
    conexion = obtener_conexion()
    filas = conexion.execute(sql, parametros).fetchall()
    conexion.close()
    return [dict(fila) for fila in filas]


def consultar_uno(sql: str, parametros: tuple = ()) -> dict | None:
    """Ejecuta una consulta SELECT y devuelve una fila como dict, o None."""
    conexion = obtener_conexion()
    fila = conexion.execute(sql, parametros).fetchone()
    conexion.close()
    return dict(fila) if fila else None


def ejecutar(sql: str, parametros: tuple = ()) -> int:
    """Ejecuta INSERT/UPDATE/DELETE y devuelve el lastrowid."""
    conexion = obtener_conexion()
    cursor = conexion.execute(sql, parametros)
    conexion.commit()
    ultimo_id = cursor.lastrowid
    conexion.close()
    return ultimo_id


def ejecutar_varios(sql: str, lista_parametros: list[tuple]) -> None:
    """Ejecuta la misma sentencia con multiples conjuntos de parametros."""
    conexion = obtener_conexion()
    conexion.executemany(sql, lista_parametros)
    conexion.commit()
    conexion.close()
