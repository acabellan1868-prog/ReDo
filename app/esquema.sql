-- ============================================================
-- ReDo — Esquema de base de datos v4
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Configuracion del sistema (editable desde interfaz)
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'string',
    editable INTEGER NOT NULL DEFAULT 1,
    descripcion TEXT,
    ultima_actualizacion TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Catalogo de tipos de dispositivo (gestionable desde la app)
CREATE TABLE IF NOT EXISTS tipos_dispositivo (
    clave TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    icono TEXT NOT NULL
);

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
    notas TEXT,
    tipo TEXT NOT NULL DEFAULT 'otro',
    tipo_auto INTEGER NOT NULL DEFAULT 0,
    zona TEXT
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
    enviada INTEGER NOT NULL DEFAULT 0,
    resuelta INTEGER NOT NULL DEFAULT 0
);

-- Historial de presencia (cada avistamiento individual)
CREATE TABLE IF NOT EXISTS presencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivos(id),
    escaneo_id INTEGER NOT NULL REFERENCES escaneos(id),
    ip TEXT,
    visto_en TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Resumen diario de presencia (agregacion de datos > 180 dias)
CREATE TABLE IF NOT EXISTS presencia_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivos(id),
    fecha TEXT NOT NULL,
    primera_vez TEXT,
    ultima_vez TEXT,
    minutos_conectado INTEGER,
    num_avistamientos INTEGER,
    UNIQUE(dispositivo_id, fecha)
);

-- Indices para rendimiento
CREATE INDEX IF NOT EXISTS idx_config_editable ON configuracion(editable);
CREATE INDEX IF NOT EXISTS idx_dispositivos_mac ON dispositivos(mac);
CREATE INDEX IF NOT EXISTS idx_dispositivos_confiable ON dispositivos(confiable);
CREATE INDEX IF NOT EXISTS idx_dispositivos_tipo ON dispositivos(tipo);
CREATE INDEX IF NOT EXISTS idx_escaneos_inicio ON escaneos(inicio);
CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas(fecha);
CREATE INDEX IF NOT EXISTS idx_alertas_dispositivo ON alertas(dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_presencia_dispositivo ON presencia(dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_presencia_visto ON presencia(visto_en);
CREATE INDEX IF NOT EXISTS idx_presencia_escaneo ON presencia(escaneo_id);
CREATE INDEX IF NOT EXISTS idx_presencia_diaria_fecha ON presencia_diaria(fecha);
CREATE INDEX IF NOT EXISTS idx_presencia_diaria_disp ON presencia_diaria(dispositivo_id);
