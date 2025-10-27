# FLUJO 5: AUSENTISMOS/INCIDENCIAS - SMOKE TEST

**Propósito:** Verificar el procesamiento de ausentismos/incidencias subidos por analistas de nómina  
**Modelo:** `AnalistaIncidencia` (models.py línea 820)  
**Arquitectura:** 100% refactorizada (views_archivos_analista.py + tasks_refactored/)  
**Estado:** ⏭️ Preparado para ejecutar

---

## 🎯 Objetivo del Test

Validar que el sistema procesa correctamente archivos Excel de incidencias:
- ✅ Crea registros `AnalistaIncidencia` en base de datos
- ✅ Guarda fechas sin desfase de timezone
- ✅ Asocia registros al archivo origen
- ✅ Genera logs de actividad (dual: TarjetaActivityLogNomina + ActivityEvent)
- ✅ Mantiene trazabilidad del usuario analista

---

## 📁 Archivos

1. **`generar_excel_incidencias.py`** (2.7 KB): Script para generar archivo Excel de prueba
2. **`incidencias_smoke_test.xlsx`** (5.4 KB): Archivo Excel con 6 incidencias
3. **`README.md`** (este archivo): Documentación completa del Flujo 5
4. **`INSTRUCCIONES_PRUEBA_FLUJO5.md`**: Guía paso a paso para ejecutar la prueba
5. **`RESULTADOS_FLUJO5.md`**: ✅ **Resultados de la prueba: 7/7 VERIFICACIONES PASADAS - SUITE COMPLETA 5/5**

---

## 📊 Datos de Prueba

### Estructura del Excel

**Columnas esperadas:**
```
Rut | Nombre | Fecha Inicio Ausencia | Fecha Fin Ausencia | Dias | Tipo Ausentismo
```

### 6 Registros de Incidencias

```
1. 19111111-1 - Juan Carlos Pérez López
   Ausencia: 01/10/2025 - 03/10/2025 (3 días)
   Tipo: Licencia Médica

2. 19222222-2 - María Francisca González Muñoz
   Ausencia: 05/10/2025 - 07/10/2025 (3 días)
   Tipo: Vacaciones

3. 19333333-3 - Pedro Antonio Silva Rojas
   Ausencia: 10/10/2025 - 14/10/2025 (5 días)
   Tipo: Permiso Sin Goce de Sueldo

4. 19444444-4 - Ana María Torres Castro
   Ausencia: 15/10/2025 - 16/10/2025 (2 días)
   Tipo: Permiso Administrativo

5. 19555555-5 - Carlos Alberto Ramírez Flores
   Ausencia: 20/10/2025 - 24/10/2025 (5 días)
   Tipo: Licencia Médica

6. 19666666-6 - Sofía Isabel Morales Vega
   Ausencia: 25/10/2025 - 27/10/2025 (3 días)
   Tipo: Capacitación
```

---

## 🏗️ Arquitectura Técnica

### Stack Completo

```
Frontend (React + Vite)
    ↓
API: POST /api/nomina/archivos-analista/subir/
    ↓
ViewSet: ArchivoAnalistaUploadViewSet.subir()
    - Crea ArchivoAnalistaUpload (tipo_archivo='incidencias')
    - Lanza tarea Celery
    ↓
Task: procesar_archivo_analista_con_logging
    - Queue: nomina_queue
    - Logging dual: TarjetaActivityLogNomina + ActivityEvent
    ↓
Util: procesar_archivo_incidencias_util()
    - Lee Excel con pandas
    - Valida columnas: Rut, Nombre, Fecha Inicio, Fecha Fin, Dias, Tipo
    - Crea registros AnalistaIncidencia
    ↓
Modelo: AnalistaIncidencia
    - cierre (FK)
    - empleado (FK nullable)
    - archivo_origen (FK)
    - rut, nombre
    - fecha_inicio_ausencia, fecha_fin_ausencia
    - dias, tipo_ausentismo
```

### Modelo AnalistaIncidencia

```python
class AnalistaIncidencia(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_inicio_ausencia = models.DateField()
    fecha_fin_ausencia = models.DateField()
    dias = models.IntegerField()
    tipo_ausentismo = models.CharField(max_length=80)
```

---

## 🔄 Comparación con Flujos Anteriores

| Aspecto | Flujo 3 | Flujo 4 | Flujo 5 | Diferencia |
|---------|---------|---------|---------|------------|
| **Modelo** | AnalistaIngreso | AnalistaFiniquito | AnalistaIncidencia | ✅ Mismo patrón |
| **Columnas Excel** | 3 | 4 | 6 | +2 columnas |
| **Campos Date** | 1 (fecha_ingreso) | 1 (fecha_retiro) | 2 (inicio + fin) | +1 fecha |
| **Campos Int** | 0 | 0 | 1 (dias) | +1 entero |
| **Arquitectura** | Refactorizada | Refactorizada | Refactorizada | ✅ Idéntica |
| **tipo_archivo** | 'ingresos' | 'finiquitos' | 'incidencias' | Solo param |
| **Tarjeta logging** | analista_ingresos | analista_finiquitos | analista_incidencias | Solo nombre |

**Conclusión:** Misma arquitectura probada en 3 flujos, solo cambian los datos específicos del modelo.

---

## ✅ Verificaciones a Realizar

Después de subir el archivo, verificar:

1. **Upload registrado:**
   - ✅ `ArchivoAnalistaUpload` creado
   - ✅ `tipo_archivo='incidencias'`
   - ✅ `estado='procesado'`
   - ✅ `analista=analista.nomina@bdo.cl`

2. **Registros creados:**
   - ✅ 6 registros `AnalistaIncidencia`
   - ✅ Todos con `archivo_origen` correcto

3. **Fechas correctas:**
   - ✅ `fecha_inicio_ausencia`: 2025-10-01, 2025-10-05, 2025-10-10, 2025-10-15, 2025-10-20, 2025-10-25
   - ✅ `fecha_fin_ausencia`: 2025-10-03, 2025-10-07, 2025-10-14, 2025-10-16, 2025-10-24, 2025-10-27
   - ✅ Sin desfase de timezone

4. **Días calculados:**
   - ✅ RUT 19111111-1: 3 días
   - ✅ RUT 19222222-2: 3 días
   - ✅ RUT 19333333-3: 5 días
   - ✅ RUT 19444444-4: 2 días
   - ✅ RUT 19555555-5: 5 días
   - ✅ RUT 19666666-6: 3 días

5. **Tipos de ausentismo:**
   - ✅ Licencia Médica (2 registros)
   - ✅ Vacaciones (1 registro)
   - ✅ Permiso Sin Goce de Sueldo (1 registro)
   - ✅ Permiso Administrativo (1 registro)
   - ✅ Capacitación (1 registro)

6. **Logs generados:**
   - ✅ 2 eventos: `process_start` + `process_complete`
   - ✅ Tarjeta: `analista_incidencias`
   - ✅ Usuario: analista.nomina@bdo.cl

---

## 🐛 Bugs Esperados

**Predicción:** 0 bugs

**Razones:**
1. Arquitectura ya probada en 3 flujos consecutivos (100% éxito)
2. Mismo patrón de procesamiento
3. Solo cambian columnas específicas del modelo
4. Fechas usan tipo `Date` (sin timezone)
5. Campo `dias` es simplemente `IntegerField`

---

## 📈 Métricas Esperadas

```
Tiempo de preparación:  ~15 minutos (reutilización)
Tiempo de procesamiento: <1 segundo (6 registros)
Tiempo de verificación:  <5 segundos
Total estimado:          ~20 minutos

Confianza de éxito:      100% (arquitectura validada 3 veces)
```

---

## 🎯 Siguiente Paso

Una vez completado el Flujo 5, habremos validado:
- ✅ Flujo 1: Libro de Remuneraciones (datos masivos)
- ✅ Flujo 2: Movimientos del Mes (datos masivos)
- ✅ Flujo 3: Ingresos (datos analista, 3 columnas)
- ✅ Flujo 4: Finiquitos (datos analista, 4 columnas)
- ✅ Flujo 5: Incidencias (datos analista, 6 columnas, 2 fechas)

**Total:** 5 flujos críticos de nómina validados al 100%

---

## 📝 Notas Técnicas

### Procesamiento de Fechas Múltiples

El Flujo 5 es el primero en procesar **2 campos de fecha** en el mismo registro:
- `fecha_inicio_ausencia`
- `fecha_fin_ausencia`

Esto valida que el sistema maneja correctamente múltiples fechas sin confundirlas.

### Campo Integer (Dias)

Primera vez que procesamos un campo numérico entero desde Excel:
- Validación de tipo
- Conversión correcta
- Sin errores de casting

### Tipos de Ausentismo

El campo `tipo_ausentismo` es libre (CharField), no tiene choices definidos.
Esto prueba la flexibilidad del sistema para datos textuales variados.

---

**Preparado por:** GitHub Copilot  
**Fecha:** 27/10/2025  
**Versión:** 1.0  
**Estado:** ✅ Listo para ejecutar
