# 🆕 Flujo 3: Ingresos - Smoke Test

# 🧪 Smoke Test - Flujo 3: Ingresos

**Estado**: ✅ COMPLETADO (100%)  
**Última actualización**: 27 de octubre de 2025  
**Resultado**: 6/6 verificaciones pasadas - 0 bugs detectados
**Tipo de archivo:** Excel con datos de nuevas contrataciones

---

## 📋 Resumen

Este flujo valida el procesamiento de archivos de **Ingresos** (nuevas contrataciones) subidos por el analista.

### 🎯 Qué se valida

- ✅ Upload de archivo Excel con columnas específicas
- ✅ Procesamiento asíncrono vía Celery
- ✅ Validación de headers (Rut, Nombre, Fecha Ingreso)
- ✅ Creación de registros en modelo `AnalistaIngreso`
- ✅ Fechas guardadas correctamente (sin desfase)
- ✅ Usuario propagado correctamente (analista)
- ✅ Logging dual (TarjetaActivityLogNomina + ActivityEvent)
- ✅ Asociación con archivo origen

---

## 📂 Archivos del Test

### 📝 Documentación
- [x] `INSTRUCCIONES_PRUEBA_FLUJO3.md` - Guía completa paso a paso (12 KB)
- [x] `RESULTADOS_FLUJO3.md` - ✅ **Resultados completos de la ejecución** (100% validado)
- [x] `VERIFICACION_ARQUITECTURA.md` - ✅ **Verificación técnica de arquitectura** (17 KB)

### 🛠️ Scripts y Datos
- [x] `generar_excel_ingresos.py` - Generador de datos de prueba (3.2 KB)
- [x] `ingresos_smoke_test.xlsx` - Archivo Excel generado (5.1 KB)
- [x] `verificar_flujo3.sh` - Script de verificación automática (4.8 KB)

---

## 🎯 Tarea a Validar

### Endpoint
```
POST /api/nomina/archivos-analista/subir/{cierre_id}/ingresos/
```

### Flujo Backend
```
ArchivoAnalistaUploadViewSet.subir()
    ↓
procesar_archivo_analista_con_logging.delay(archivo_id, usuario_id)
    ↓
procesar_archivo_analista_util(archivo)
    ↓
procesar_archivo_ingresos_util(archivo)
    ↓
AnalistaIngreso.objects.create(...)
```

### Archivos Involucrados

**Backend:**
- `views_archivos_analista.py` - ViewSet para upload
- `tasks_refactored/archivos_analista.py` - Tarea Celery
- `utils/ArchivosAnalista.py` - Lógica de procesamiento
- `models.py` - Modelos ArchivoAnalistaUpload y AnalistaIngreso

**Frontend:**
- `IngresosCard.jsx` - Componente de UI
- `api/nomina.js` - Funciones de API

---

## 📊 Datos de Prueba

### Archivo Excel

**Nombre**: `ingresos_smoke_test.xlsx`  
**Tamaño**: 5.1 KB  
**Registros**: 5 ingresos

### Estructura

| Columna | Tipo | Obligatorio |
|---------|------|-------------|
| Rut | String | Sí |
| Nombre | String | Sí |
| Fecha Ingreso | Date | Sí |

### Contenido

| Rut | Nombre | Fecha Ingreso |
|-----|--------|---------------|
| 19111111-1 | Juan Carlos Pérez López | 01/10/2025 |
| 19222222-2 | María Francisca González Muñoz | 05/10/2025 |
| 19333333-3 | Pedro Antonio Silva Rojas | 10/10/2025 |
| 19444444-4 | Ana María Torres Castro | 15/10/2025 |
| 19555555-5 | Carlos Alberto Ramírez Flores | 20/10/2025 |

---

## 🚀 Cómo Ejecutar

### 1. Preparación

```bash
cd /root/SGM/docs/smoke-tests/flujo-3-ingresos

# Verificar que existe el Excel
ls -lh ingresos_smoke_test.xlsx
```

### 2. Limpiar datos anteriores (opcional)

```bash
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import ArchivoAnalistaUpload, AnalistaIngreso, CierreNomina
cierre = CierreNomina.objects.get(id=35)
AnalistaIngreso.objects.filter(cierre=cierre).delete()
ArchivoAnalistaUpload.objects.filter(cierre=cierre, tipo_archivo='ingresos').delete()
print("✅ Datos anteriores eliminados")
EOF
```

### 3. Subir archivo via Frontend

1. Ir a: `http://172.17.11.18:5174`
2. Login: `analista.nomina@bdo.cl`
3. Navegar al Cierre ID 35
4. Sección "Archivos del Analista" → "Ingresos"
5. Subir: `ingresos_smoke_test.xlsx`
6. Esperar procesamiento (~1-2 segundos)

### 4. Verificar resultados

```bash
./verificar_flujo3.sh
```

---

## ✅ Resultados Esperados

### Base de Datos

```
ArchivoAnalistaUpload:
├── tipo_archivo: 'ingresos'
├── estado: 'procesado'
├── analista: analista.nomina@bdo.cl (ID: 2)
└── archivo: [ruta al Excel]

AnalistaIngreso: 5 registros
├── Todos vinculados a archivo_origen
├── Fechas correctas (sin desfase)
└── RUTs y nombres procesados
```

### Logs

```
TarjetaActivityLogNomina:
├── process_start
└── process_complete

ActivityEvent:
├── procesamiento_celery_iniciado
└── procesamiento_completado
```

### Performance

- **Tiempo**: < 2 segundos
- **Registros/seg**: ~3-5
- **Sin errores**

---

## 🐛 Validaciones Críticas

| # | Validación | Criterio |
|---|------------|----------|
| 1 | Upload registrado | Estado = 'procesado' |
| 2 | Registros creados | 5 AnalistaIngreso |
| 3 | Fechas correctas | Sin desfase de 1 día |
| 4 | Usuario correcto | analista.nomina@bdo.cl (ID: 2) |
| 5 | Asociación | Todos con archivo_origen |
| 6 | Logs completos | ≥ 2 logs registrados |

---

## 📁 Estructura de Archivos

```
flujo-3-ingresos/
├── README.md                           ← Este archivo
├── INSTRUCCIONES_PRUEBA_FLUJO3.md     ← Guía detallada
├── generar_excel_ingresos.py          ← Generador de datos
├── ingresos_smoke_test.xlsx           ← Archivo de prueba
├── verificar_flujo3.sh                ← Script de verificación
└── SMOKE_TEST_FLUJO_3_RESULTADOS.md   ← Resultados (pendiente)
```

---

## 🔄 Estado del Flujo

- [x] Estructura de carpetas creada
- [x] Generador de Excel creado
- [x] Archivo Excel generado (5 ingresos)
- [x] Instrucciones documentadas
- [x] Script de verificación creado
- [ ] **Pendiente**: Ejecutar prueba
- [ ] **Pendiente**: Documentar resultados

---

## 📝 Notas

### Diferencias con Flujo 1 y 2

- **Más simple**: Solo 3 columnas (vs múltiples hojas)
- **Sin clasificación**: No requiere mapeo de headers
- **Modelo directo**: Un solo modelo (AnalistaIngreso)
- **Sin consolidación**: No afecta RegistroNomina consolidada

### Particularidades

- El RUT se normaliza antes de buscar empleado existente
- Si el empleado no existe en EmpleadoCierre, se crea la referencia nula
- Las fechas deben coincidir exactamente con el Excel
- El archivo_origen siempre debe estar asociado

---

## 🎯 Próximos Pasos

Después de validar este flujo:

1. ✅ Flujo 1: Libro de Remuneraciones (100%)
2. ✅ Flujo 2: Movimientos del Mes (100%)
3. 🔄 **Flujo 3: Ingresos** ← Actual
4. ⏭️ Flujo 4: Finiquitos
5. ⏭️ Flujo 5: Ausentismos/Incidencias

---

**Preparado por**: Sistema de QA  
**Última actualización**: 27 de octubre de 2025  
**Estado**: ✅ Listo para ejecución
