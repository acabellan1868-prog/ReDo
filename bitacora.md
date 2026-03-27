# Bitácora — ReDo

## 2026-03-26

### Implementación de historial de presencia y clasificación de dispositivos

Implementadas las mejoras analizadas en `analisis-mejoras.md`:

- **Historial de presencia**: nuevo esquema de BD `presencia` que registra cada
  conexión/desconexión con timestamps de entrada y salida por dispositivo.
- **Tipo y zona de dispositivos**: campos `tipo` y `zona` añadidos al esquema.
  API ampliada con filtros. Frontend actualizado con selectores en el drawer de edición.
- **Agregación nocturna**: tarea programada a las 03:00 que consolida el historial
  manteniendo detalle de 180 días.

Commits: `b001e05`, `b0381f5`

## 2026-03-27

### Reorganización de documentación

- `mejoras.md` renombrado a `analisis-mejoras.md`
- Creada `bitacora.md` (este fichero)
