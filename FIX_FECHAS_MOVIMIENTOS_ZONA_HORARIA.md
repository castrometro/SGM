# Fix: Fechas con un día de diferencia en Movimientos de Personal

## Problema Identificado

Las fechas de ausentismos se mostraban con **1 día anterior** al registrado en la base de datos.

### Causa Raíz

Problema clásico de **conversión de zona horaria** en JavaScript:

```javascript
// ❌ CÓDIGO ANTERIOR (PROBLEMA)
new Date("2024-01-15").toLocaleDateString('es-CL')
// JavaScript interpreta "2024-01-15" como:
// → 2024-01-15T00:00:00Z (medianoche UTC)
// → En Chile (UTC-3/UTC-4): 2024-01-14T21:00:00 o 2024-01-14T20:00:00
// → Resultado: "14-01-2024" ❌ (un día menos)
```

### Solución Implementada

Nueva función utilitaria `formatearFechaLocal()` que parsea fechas como **fecha local** sin conversión de zona horaria:

```javascript
// ✅ CÓDIGO NUEVO (SOLUCIÓN)
formatearFechaLocal("2024-01-15")
// Crea Date en zona horaria local directamente:
// → new Date(2024, 0, 15) // mes es 0-indexed
// → 2024-01-15T00:00:00 (hora local, sin conversión UTC)
// → Resultado: "15-01-2024" ✅ (fecha correcta)
```

## Archivos Modificados

### 1. Nueva utilidad: `/src/utils/dashboard/dates.js`
- `formatearFechaLocal(fecha)`: Formatea fecha string a formato chileno sin ajuste de zona horaria
- `parseFechaLocal(fechaStr)`: Convierte string a objeto Date local

### 2. Componente principal: `/src/pages/DashboardsNomina/MovimientosMes.jsx`
- ✅ Importa `formatearFechaLocal` desde utils
- ✅ Elimina función local `formatearFecha` (implementación incorrecta)

### 3. Tabla de resumen: `/src/components/DashboardNomina/Movimientos/TablaResumenMovimientos.jsx`
- ✅ Importa `formatearFechaLocal`
- ✅ Reemplaza todas las instancias de `new Date(fecha).toLocaleDateString('es-CL')`
- ✅ Aplica corrección en:
  - Columna "Fecha" (ingresos/finiquitos)
  - Columna "Fecha Inicio" (ausencias)
  - Columna "Fecha Fin" (ausencias)

## Cómo Verificar el Fix

1. **Backend**: Verificar fecha guardada en BD
   ```sql
   SELECT fecha_inicio, fecha_fin FROM nomina_movimientopersonal WHERE categoria = 'ausencia';
   ```

2. **Frontend**: La fecha mostrada debe coincidir exactamente con la de BD
   - Antes: Si BD tiene `2024-01-15`, frontend mostraba `14-01-2024` ❌
   - Ahora: Si BD tiene `2024-01-15`, frontend muestra `15-01-2024` ✅

## Patrón Recomendado para el Proyecto

**Para todas las fechas que vienen de la BD en formato YYYY-MM-DD:**

```javascript
// ✅ CORRECTO
import { formatearFechaLocal } from '@/utils/dashboard/dates';
<td>{formatearFechaLocal(movimiento.fecha_inicio)}</td>

// ❌ EVITAR
<td>{new Date(movimiento.fecha_inicio).toLocaleDateString('es-CL')}</td>
```

## Impacto

- ✅ Las fechas ahora se muestran correctamente en la vista de Movimientos
- ✅ Sin dependencia de zona horaria del navegador/servidor
- ✅ Función reutilizable para otros componentes del dashboard
- ✅ Sin cambios necesarios en el backend

---
**Fecha del fix**: 12 de noviembre de 2025
**Componentes afectados**: Dashboard de Movimientos de Personal (Nómina)
