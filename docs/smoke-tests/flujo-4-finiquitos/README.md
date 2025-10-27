# 🧪 Smoke Test - Flujo 4: Finiquitos

**Estado**: 🟡 En preparación  
**Última actualización**: 27 de octubre de 2025  
**Tipo de archivo**: Excel con datos de terminaciones de contrato

---

## 📋 Resumen

Este flujo valida el procesamiento de archivos de **Finiquitos** (terminaciones de contrato) subidos por el analista.

### 🎯 Qué se valida

- ✅ Upload de archivo Excel con columnas específicas
- ✅ Procesamiento asíncrono vía Celery
- ✅ Validación de headers (Rut, Nombre, Fecha Retiro, Motivo)
- ✅ Creación de registros en modelo `AnalistaFiniquito`
- ✅ Fechas guardadas correctamente (sin desfase)
- ✅ Usuario propagado correctamente (analista)
- ✅ Logging dual (TarjetaActivityLogNomina + ActivityEvent)
- ✅ Asociación con archivo origen

---

## � Archivos

1. **`generar_excel_finiquitos.py`** (2.5 KB): Script para generar archivo Excel de prueba
2. **`finiquitos_smoke_test.xlsx`** (5.2 KB): Archivo Excel con 5 finiquitos
3. **`README.md`** (este archivo): Documentación completa del Flujo 4
4. **`INSTRUCCIONES_PRUEBA_FLUJO4.md`**: Guía paso a paso para ejecutar la prueba
5. **`RESULTADOS_FLUJO4.md`**: ✅ **Resultados de la prueba: 6/6 VERIFICACIONES PASADAS**

---

## 📊 Estructura del Archivo Excel

### Columnas Requeridas

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| **Rut** | String | RUT del empleado con formato XX.XXX.XXX-X | 19.111.111-1 |
| **Nombre** | String | Nombre completo del empleado | Juan Carlos Pérez López |
| **Fecha Retiro** | Date | Fecha de término del contrato | 31/10/2025 |
| **Motivo** | String | Motivo de la terminación | Renuncia Voluntaria |

### Datos de Prueba Incluidos

El archivo `finiquitos_smoke_test.xlsx` contiene **5 finiquitos**:

1. **19111111-1** - Juan Carlos Pérez López
   - Fecha Retiro: 31/10/2025
   - Motivo: Renuncia Voluntaria

2. **19222222-2** - María Francisca González Muñoz
   - Fecha Retiro: 15/10/2025
   - Motivo: Término de Contrato

3. **19333333-3** - Pedro Antonio Silva Rojas
   - Fecha Retiro: 20/10/2025
   - Motivo: Mutuo Acuerdo

4. **19444444-4** - Ana María Torres Castro
   - Fecha Retiro: 10/10/2025
   - Motivo: Necesidades de la Empresa

5. **19555555-5** - Carlos Alberto Ramírez Flores
   - Fecha Retiro: 25/10/2025
   - Motivo: Renuncia Voluntaria

---

## 🏗️ Arquitectura del Flujo

### Backend (Django + Celery)

```
📁 backend/nomina/
├── views_archivos_analista.py
│   └── ArchivoAnalistaUploadViewSet
│       └── subir(cierre_id, tipo_archivo='finiquitos')
│
├── tasks_refactored/
│   └── archivos_analista.py
│       └── procesar_archivo_analista_con_logging()
│
├── utils/
│   └── ArchivosAnalista.py
│       └── procesar_archivo_finiquitos_util()
│
└── models.py
    ├── ArchivoAnalistaUpload (línea 611)
    └── AnalistaFiniquito (línea 801)
        ├── cierre (FK)
        ├── empleado (FK, opcional)
        ├── archivo_origen (FK)
        ├── rut (CharField)
        ├── nombre (CharField)
        ├── fecha_retiro (DateField)
        └── motivo (CharField)
```

### Frontend (React)

```
📁 src/pages/nomina/components/
└── FiniquitosCard.jsx
    └── Componente de carga de finiquitos
    └── Upload de archivos Excel
    └── Visualización de logs
```

### API Endpoint

```
POST /api/nomina/archivos-analista/subir/{cierre_id}/finiquitos/
```

**Request**:
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `archivo` (file)

**Response**:
```json
{
  "id": 138,
  "tipo_archivo": "finiquitos",
  "estado": "pendiente",
  "archivo_nombre": "finiquitos_smoke_test.xlsx",
  "fecha_subida": "2025-10-27T19:03:00Z",
  "mensaje": "Archivo subido correctamente y enviado a procesamiento"
}
```

---

## 🔄 Flujo de Procesamiento

```
1. Usuario sube Excel desde FiniquitosCard.jsx
   ↓
2. POST /api/nomina/archivos-analista/subir/{cierre_id}/finiquitos/
   ↓
3. ArchivoAnalistaUploadViewSet.subir()
   • Valida archivo (.xlsx)
   • Valida nombre de archivo
   • Crea ArchivoAnalistaUpload (estado='pendiente')
   ↓
4. Lanza task Celery asíncrona
   procesar_archivo_analista_con_logging.delay(archivo_id, usuario_id)
   ↓
5. Celery Worker (nomina_queue)
   • Log: process_start (TarjetaActivityLogNomina)
   • Log: procesamiento_celery_iniciado (ActivityEvent)
   • Estado: 'en_proceso'
   ↓
6. procesar_archivo_finiquitos_util()
   • Valida headers: ['Rut', 'Nombre', 'Fecha Retiro', 'Motivo']
   • Lee datos con pandas
   • Por cada fila:
     - Limpia RUT
     - Busca empleado asociado
     - Parsea fecha_retiro
     - Crea AnalistaFiniquito
     - Asocia archivo_origen
   ↓
7. Actualiza estado final
   • estado='procesado' (si éxito)
   • estado='con_error' (si falla)
   ↓
8. Registra logs finales
   • Log: process_complete (TarjetaActivityLogNomina)
   • Log: procesamiento_completado (ActivityEvent)
   ↓
9. Usuario ve logs en tiempo real en el frontend
```

---

## 🎯 Verificaciones a Realizar

### 1. Upload Registrado ✓
- [ ] ArchivoAnalistaUpload creado
- [ ] Estado inicial: 'pendiente'
- [ ] Estado final: 'procesado'
- [ ] tipo_archivo: 'finiquitos'

### 2. Registros Creados ✓
- [ ] 5 registros AnalistaFiniquito creados
- [ ] Asociados al cierre correcto
- [ ] RUTs correctos y limpios
- [ ] Nombres completos correctos

### 3. Fechas Correctas ✓
- [ ] Fecha Retiro guardada sin desfase
- [ ] Formato correcto en base de datos
- [ ] Comparar con Excel original

### 4. Usuario Propagado ✓
- [ ] Analista asignado al upload
- [ ] Mismo usuario en todos los registros
- [ ] Trazabilidad completa

### 5. Logging Completo ✓
- [ ] 2 logs en TarjetaActivityLogNomina
  - process_start (info)
  - process_complete (success/warning/error)
- [ ] 2 eventos en ActivityEvent
  - procesamiento_celery_iniciado
  - procesamiento_completado

### 6. Asociaciones ✓
- [ ] Todos los finiquitos tienen archivo_origen
- [ ] Relación correcta con ArchivoAnalistaUpload

---

## 🚀 Comparación con Flujo 3 (Ingresos)

| Aspecto | Flujo 3: Ingresos | Flujo 4: Finiquitos |
|---------|-------------------|---------------------|
| **Columnas** | 3 (Rut, Nombre, Fecha Ingreso) | 4 (Rut, Nombre, Fecha Retiro, Motivo) |
| **Complejidad** | Baja | Baja |
| **Arquitectura** | views_archivos_analista.py + tasks_refactored/ | **MISMA** ✅ |
| **ViewSet** | ArchivoAnalistaUploadViewSet | **MISMO** ✅ |
| **Task** | procesar_archivo_analista_con_logging | **MISMA** ✅ |
| **Función** | procesar_archivo_ingresos_util() | procesar_archivo_finiquitos_util() |
| **Logging** | Dual (TarjetaActivityLogNomina + ActivityEvent) | **MISMO** ✅ |

**Ventaja**: Como usan la **misma arquitectura**, el tiempo de implementación y testing es mucho menor.

---

## 📈 Estado del Progreso

```
✅ Flujo 1: Libro de Remuneraciones     (100%)
✅ Flujo 2: Movimientos del Mes         (100%)
✅ Flujo 3: Ingresos                    (100%)
🟡 Flujo 4: Finiquitos                  (20% - En preparación)
⏭️  Flujo 5: Ausentismos/Incidencias    (0%)
```

---

## 🔗 Referencias

- **Modelo**: `backend/nomina/models.py` línea 801
- **Procesamiento**: `backend/nomina/utils/ArchivosAnalista.py` línea 185
- **ViewSet**: `backend/nomina/views_archivos_analista.py`
- **Task**: `backend/nomina/tasks_refactored/archivos_analista.py`
- **Flujo 3 (referencia)**: `/root/SGM/docs/smoke-tests/flujo-3-ingresos/`

---

**Última actualización**: 27 de octubre de 2025  
**Próximos pasos**: Crear instrucciones de prueba y ejecutar smoke test
