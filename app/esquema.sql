-- ============================================================
-- ReDo — Esquema de base de datos v1
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Dispositivos detectados en la red
CREATE TABLE IF NOT EXISTS dispositivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT NOT NULL UNIQUE,
    ip TEXT,
    hostname TEXT,
    fabricante TEXT,
    primera_vez TEXT NOT NULL DEFAULT (datetime('now')),
    ultima_vez TEXT NOT NULL DEFAULT (datetime('now')),
    confiable INTEGER NOT NULL DEFAULT 0,
    notas TEXT
);

-- Historial de escaneos
CREATE TABLE IF NOT EXISTS escaneos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio TEXT NOT NULL,
    fin TEXT,
    dispositivos_encontrados INTEGER NOT NULL DEFAULT 0,
    dispositivos_nuevos INTEGER NOT NULL DEFAULT 0
);

-- Alertas generadas
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('dispositivo_nuevo', 'dispositivo_regresa', 'error_escaneo')),
    mensaje TEXT NOT NULL,
    dispositivo_id INTEGER REFERENCES dispositivos(id),
    fecha TEXT NOT NULL DEFAULT (datetime('now')),
    enviada INTEGER NOT NULL DEFAULT 0
);

-- Indices para rendimiento
CREATE INDEX IF NOT EXISTS idx_dispositivos_mac ON dispositivos(mac);
CREATE INDEX IF NOT EXISTS idx_dispositivos_confiable ON dispositivos(confiable);
CREATE INDEX IF NOT EXISTS idx_escaneos_inicio ON escaneos(inicio);
CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha);
CREATE INDEX IF NOT EXISTS idx_alertas_dispositivo ON alertas(dispositivo_id);
