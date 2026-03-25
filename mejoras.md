# Mejoras propuestas — ReDo

> Mejoras internas de ReDo: esquema de datos, escáner, API y frontend.
> Creado: 2026-03-25
> Estado: borrador para discusión

---

## Índice

1. [Historial de presencia de dispositivos](#1-historial-de-presencia-de-dispositivos)
2. [Agrupación de dispositivos por tipo y zona](#2-agrupación-de-dispositivos-por-tipo-y-zona)
3. [Orden de implementación](#3-orden-de-implementación)

---

## 1. Historial de presencia de dispositivos

### Problema actual

ReDo escanea la red cada 5 minutos y guarda `primera_vez` y `ultima_vez` por dispositivo. Pero **no guarda el historial intermedio** — si un móvil estuvo conectado de 18:00 a 23:00, al día siguiente solo se sabe que "fue visto por última vez a las 23:00". No hay forma de saber:

- A qué horas está cada dispositivo en casa
- Cuánto tiempo lleva conectado un dispositivo
- Qué dispositivos aparecen solo de madrugada (posible intruso)
- Patrones de presencia de la familia ("Lucía llega sobre las 18h")

### Qué se gana

| Caso de uso | Valor |
|---|---|
| **Detección de intrusos** | Un dispositivo que solo aparece entre 2:00-5:00 es sospechoso |
| **Patrones familiares** | Ver cuándo llega cada miembro (por el móvil) |
| **Diagnóstico de red** | Dispositivos IoT que se desconectan intermitentemente |
| **Estadísticas** | "Hoy hay 8 dispositivos activos, hace un mes eran 12" |

### Diseño propuesto

#### Nueva tabla: `presencia`

```sql
CREATE TABLE IF NOT EXISTS presencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivos(id),
    escaneo_id INTEGER NOT NULL REFERENCES escaneos(id),
    ip TEXT,
    visto_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_presencia_dispositivo ON presencia(dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_presencia_visto ON presencia(visto_en);
CREATE INDEX IF NOT EXISTS idx_presencia_escaneo ON presencia(escaneo_id);
```

Cada fila = "el dispositivo X fue visto en el escaneo Y a la hora Z con la IP W".

#### Impacto en el escáner (`escaner.py`)

En el bucle actual, después de insertar o actualizar un dispositivo, se añade una línea:

```python
# Tras confirmar que el dispositivo existe (INSERT o UPDATE)
bd.ejecutar(
    "INSERT INTO presencia (dispositivo_id, escaneo_id, ip) VALUES (?, ?, ?)",
    (dispositivo_id, escaneo_id, ip),
)
```

Es un cambio mínimo en `escanear_red()` — una sola línea INSERT por cada dispositivo encontrado.

#### Volumen de datos estimado

| Parámetro | Valor |
|---|---|
| Escaneos por día | 288 (cada 5 min) |
| Dispositivos promedio por escaneo | ~15 |
| Filas de presencia por día | ~4.320 |
| Filas por mes | ~130.000 |
| Filas por año | ~1.500.000 |
| Tamaño estimado por fila | ~80 bytes |
| Tamaño por año | ~120 MB |

**Gestión del volumen:** Política de retención con limpieza automática. Mantener detalle completo 90 días y luego agregar a resumen diario (tabla `presencia_diaria` con minutos conectado por dispositivo/día). Se implementa como tarea programada en APScheduler.

#### Tabla de agregación: `presencia_diaria`

```sql
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

CREATE INDEX IF NOT EXISTS idx_presencia_diaria_fecha ON presencia_diaria(fecha);
CREATE INDEX IF NOT EXISTS idx_presencia_diaria_disp ON presencia_diaria(dispositivo_id);
```

El job nocturno de APScheduler:
1. Para cada día > 90 días, calcula los agregados y los inserta en `presencia_diaria`
2. Borra las filas detalladas de `presencia` de ese día
3. Resultado: historial ilimitado con granularidad diaria, detalle solo para los últimos 3 meses

#### Nuevos endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/dispositivos/{id}/presencia` | Historial de presencia de un dispositivo |
| GET | `/api/presencia/timeline` | Timeline general (todos los dispositivos, un día) |

**`GET /api/dispositivos/{id}/presencia?dias=7`**

```json
{
  "dispositivo_id": 5,
  "nombre": "iPhone de Lucía",
  "dias": [
    {
      "fecha": "2026-03-25",
      "primera_vez": "07:30",
      "ultima_vez": "23:45",
      "minutos_conectado": 245,
      "franjas": [
        { "desde": "07:30", "hasta": "08:15" },
        { "desde": "17:50", "hasta": "23:45" }
      ]
    }
  ]
}
```

Las `franjas` se calculan agrupando registros consecutivos (si hay más de 10 min sin verlo, se cierra la franja y se abre otra).

**`GET /api/presencia/timeline?fecha=2026-03-25`**

Devuelve todos los dispositivos con sus franjas para un día concreto. Sirve para pintar un gráfico de barras horizontales tipo Gantt.

#### Frontend — Vista de presencia

**Opción A: Timeline integrado en la ficha de dispositivo**

Al hacer clic en un dispositivo, se abre un detalle con barras horizontales tipo "heatmap" por día mostrando cuándo estuvo conectado (verde) y cuándo no (gris). Últimos 7 días.

**Opción B: Página de presencia general**

Nueva pestaña/filtro "Presencia" en ReDo con un gráfico Gantt de todos los dispositivos en el día actual. Cada fila = un dispositivo, cada bloque verde = franja de conexión.

Se implementa con `<canvas>` o SVG inline (sin librerías externas, coherente con la filosofía vanilla).

> **Nota:** Ambas opciones no son excluyentes. Se puede empezar con la opción A (más sencilla) y luego añadir la B.

#### Complejidad estimada

| Componente | Esfuerzo |
|---|---|
| Tabla SQL + migración | Bajo |
| Modificar `escaner.py` | Bajo (1 INSERT por dispositivo) |
| Tabla `presencia_diaria` + job limpieza | Bajo-medio |
| Endpoints API (lógica de franjas) | Medio |
| Frontend timeline | Medio-alto |

#### Dependencias

- Ninguna nueva. Usa el stack actual (FastAPI + SQLite + APScheduler).

---

## 2. Agrupación de dispositivos por tipo y zona

### Problema actual

Todos los dispositivos aparecen en una lista plana. Con 15-20 dispositivos la lista es manejable, pero no responde preguntas como:

- "¿Cuántos dispositivos IoT tengo?" → Hay que contarlos mentalmente
- "¿Qué hay conectado en el despacho?" → No hay forma de saberlo
- "¿Todos los enchufes Shelly están online?" → Buscar uno por uno

Además, el campo `notas` se usa tanto para nombre descriptivo como para información extra, mezclando conceptos.

### Qué se gana

| Caso de uso | Valor |
|---|---|
| **Vista por tipo** | "5 teléfonos, 3 portátiles, 7 IoT, 2 TV" de un vistazo |
| **Vista por zona** | "En el salón hay 6 dispositivos conectados" |
| **Filtros combinados** | Tipo=IoT + Zona=Jardín → solo dispositivos de riego |
| **Iconos por tipo** | Material Symbols según el tipo (phone, laptop, router, etc.) |
| **Dashboard más rico** | Tarjeta de ReDo en el portal mostraría desglose por tipo |

### Diseño propuesto

#### Nuevos campos en `dispositivos`

```sql
ALTER TABLE dispositivos ADD COLUMN tipo TEXT DEFAULT 'otro';
ALTER TABLE dispositivos ADD COLUMN zona TEXT;
```

**Tipos predefinidos** (con icono Material Symbols):

| `tipo` | Icono | Descripción |
|---|---|---|
| `telefono` | `smartphone` | Teléfonos móviles |
| `portatil` | `laptop` | Portátiles |
| `sobremesa` | `desktop_windows` | PCs de escritorio |
| `tablet` | `tablet` | Tablets |
| `tv` | `tv` | Smart TVs, Chromecast, Fire TV |
| `impresora` | `print` | Impresoras |
| `router` | `router` | Routers, APs, switches |
| `iot` | `sensors` | Dispositivos IoT (sensores, enchufes, bombillas) |
| `servidor` | `dns` | Servidores, NAS |
| `consola` | `videogame_asset` | Consolas de videojuegos |
| `otro` | `device_unknown` | Sin clasificar (valor por defecto) |

**Zonas** (texto libre con autocompletado):

Ejemplos: Salón, Despacho, Dormitorio principal, Cocina, Jardín, Exterior

No se crea tabla de zonas: el frontend ofrece autocompletado basado en `SELECT DISTINCT zona FROM dispositivos WHERE zona IS NOT NULL`.

#### Cambios en la API

**Ampliar `DispositivoActualizar`:**

```python
class DispositivoActualizar(BaseModel):
    confiable: int | None = None
    notas: str | None = None
    tipo: str | None = None      # NUEVO
    zona: str | None = None      # NUEVO
```

**Nuevo endpoint de zonas:**

```
GET /api/zonas → ["Salón", "Despacho", "Dormitorio", ...]
```

**Filtros ampliados en `GET /api/dispositivos`:**

```
GET /api/dispositivos?confiable=1&tipo=iot&zona=Salón
```

**Ampliar `GET /api/resumen`** con desglose por tipo:

```json
{
  "dispositivos_activos": 15,
  "dispositivos_confiables": 13,
  "dispositivos_desconocidos": 2,
  "ultimo_escaneo": "2026-03-25T14:30:00",
  "por_tipo": {
    "telefono": 4,
    "iot": 5,
    "portatil": 3,
    "tv": 2,
    "otro": 1
  }
}
```

> **Nota:** Este cambio en `/api/resumen` afecta a la tarjeta de ReDo en el portal de hogarOS. Ver `hogarOS/mejoras.md` para los cambios en el lado del portal.

#### Frontend — Cambios en la UI de ReDo

**1. Tabla mejorada:**
Añadir columna de icono (según tipo) y columna de zona. Los iconos Material Symbols dan información visual inmediata.

**2. Filtros por tipo y zona:**
Además de los filtros actuales (Todos / Confiables / Desconocidos), añadir:
- Selector de tipo (dropdown o chips)
- Selector de zona (dropdown con las zonas existentes)

**3. Formulario de edición mejorado:**
Al editar un dispositivo (actualmente solo cambia nombre y confiable), añadir:
- Selector de tipo (dropdown con los tipos predefinidos)
- Campo de zona (input con autocompletado basado en zonas existentes)

**4. Vista agrupada (opcional, fase posterior):**
Modo de vista alternativo: dispositivos agrupados por zona o por tipo. Toggle para cambiar entre vista lista y vista agrupada.

#### Auto-detección de tipo (mejora futura)

Inferir el tipo basándose en `fabricante` (dato que nmap ya captura):

| Fabricante contiene | Tipo inferido |
|---|---|
| `Apple`, `Samsung`, `Xiaomi`, `Huawei` | `telefono` (heurística) |
| `Espressif`, `Tuya`, `Shelly`, `IKEA` | `iot` |
| `HP Inc`, `Canon`, `Brother` | `impresora` |
| `Raspberry`, `Intel` | `servidor` |

No es 100% fiable (un Apple puede ser un MacBook, no un iPhone), por eso solo se **sugiere** al usuario, no se asigna automáticamente. El usuario confirma o corrige.

#### Complejidad estimada

| Componente | Esfuerzo |
|---|---|
| ALTER TABLE (migración) | Bajo |
| Ampliar modelo Pydantic + PUT | Bajo |
| GET con filtros tipo/zona | Bajo |
| Endpoint `/api/zonas` | Bajo |
| Frontend: iconos por tipo | Bajo |
| Frontend: filtros tipo/zona | Medio |
| Frontend: formulario edición | Medio |
| Frontend: vista agrupada | Medio (fase posterior) |
| Auto-detección por fabricante | Medio (fase posterior) |

#### Dependencias

- Ninguna nueva. Solo cambios internos de ReDo.

---

## 3. Orden de implementación

Las dos mejoras son independientes pero complementarias. Propuesta basada en valor/esfuerzo:

| Prioridad | Mejora | Esfuerzo | Valor |
|---|---|---|---|
| 1 | Tipo y zona | Bajo-medio | Alto (mejora inmediata en usabilidad) |
| 2 | Presencia | Medio | Alto (nueva funcionalidad) |

**Si se hacen las dos**, el formulario de edición de dispositivo se amplía una sola vez (tipo + zona en la misma iteración, presencia como visualización adicional).

### Sinergia entre ambas mejoras

Con tipo + zona + presencia se pueden responder preguntas potentes:
- "¿Los dispositivos IoT del jardín se desconectan por la noche?" (tipo=iot, zona=Jardín, presencia nocturna)
- "¿A qué hora se conecta el primer teléfono cada mañana?" (tipo=telefono, primera franja del día)
- "¿Cuánto tiempo estuvo encendida la TV del salón ayer?" (tipo=tv, zona=Salón, minutos_conectado)

### Relación con hogarOS

Estas mejoras son internas de ReDo. Los cambios que afectan al portal de hogarOS (tarjeta con desglose por tipo, integración visual) se documentan en `hogarOS/mejoras.md`.
