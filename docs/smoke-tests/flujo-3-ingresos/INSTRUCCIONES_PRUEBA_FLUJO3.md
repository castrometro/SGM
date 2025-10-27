# 📋 INSTRUCCIONES - SMOKE TEST FLUJO 3: INGRESOS

**Fecha**: 27 de octubre de 2025  
**Objetivo**: Validar el procesamiento de archivo Excel de Ingresos (nuevas contrataciones)

---

## 🎯 Objetivo del Test

Verificar que el sistema procesa correctamente un archivo de ingresos de empleados, incluyendo:
- Subida del archivo vía frontend
- Procesamiento asíncrono con Celery
- Validación de headers esperados
- Creación de registros en la base de datos
- Logging dual (TarjetaActivityLogNomina + ActivityEvent)
- Propagación correcta del usuario

---

## 📋 Pre-requisitos

### 1. Cierre de Nómina Activo
- **Cierre ID**: 35
- **Cliente ID**: 20 (EMPRESA SMOKE TEST)
- **Período**: 202510 (Octubre 2025)
- **Estado**: Debe estar en estado que permita subir archivos

### 2. Usuario de Prueba
- **Email**: analista.nomina@bdo.cl
- **Rol**: Analista de Nómina
- **ID**: 2

### 3. Archivo de Prueba
- **Ubicación**: `/root/SGM/docs/smoke-tests/flujo-3-ingresos/ingresos_smoke_test.xlsx`
- **Tamaño**: ~5 KB
- **Registros**: 5 ingresos

---

## 📊 Datos de Prueba

### Contenido del Excel

El archivo contiene 5 nuevos ingresos con las siguientes columnas:

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| Rut | String | Sí | RUT del empleado (formato: 19111111-1) |
| Nombre | String | Sí | Nombre completo del empleado |
| Fecha Ingreso | Date | Sí | Fecha de ingreso del empleado |

### Registros Incluidos

| Rut | Nombre | Fecha Ingreso |
|-----|--------|---------------|
| 19111111-1 | Juan Carlos Pérez López | 01/10/2025 |
| 19222222-2 | María Francisca González Muñoz | 05/10/2025 |
| 19333333-3 | Pedro Antonio Silva Rojas | 10/10/2025 |
| 19444444-4 | Ana María Torres Castro | 15/10/2025 |
| 19555555-5 | Carlos Alberto Ramírez Flores | 20/10/2025 |

**Total**: 5 registros de ingresos

---

## 🔄 Pasos de Ejecución

### Paso 1: Preparar el Entorno

```bash
# Navegar a la carpeta del flujo
cd /root/SGM/docs/smoke-tests/flujo-3-ingresos

# Verificar que existe el archivo Excel
ls -lh ingresos_smoke_test.xlsx
```

### Paso 2: Limpiar Datos Anteriores (Opcional)

Si ya existen datos de pruebas anteriores, limpiarlos:

```bash
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import ArchivoAnalistaUpload, AnalistaIngreso, CierreNomina

cierre = CierreNomina.objects.get(id=35)

# Eliminar ingresos anteriores
AnalistaIngreso.objects.filter(cierre=cierre).delete()

# Eliminar upload anterior
ArchivoAnalistaUpload.objects.filter(cierre=cierre, tipo_archivo='ingresos').delete()

print("✅ Datos anteriores eliminados")
EOF
```

### Paso 3: Subir el Archivo via Frontend

1. **Abrir el navegador**: `http://172.17.11.18:5174`

2. **Iniciar sesión** con:
   - Email: `analista.nomina@bdo.cl`
   - Password: [contraseña del analista]

3. **Navegar al cierre**:
   - Ir al Dashboard de Nómina
   - Seleccionar el cierre ID 35 (Octubre 2025)

4. **Ir a la sección "Archivos del Analista"**:
   - Expandir la sección si está colapsada
   - Localizar la tarjeta de "Ingresos"

5. **Subir el archivo**:
   - Click en "Subir Archivo" o zona de drop
   - Seleccionar: `ingresos_smoke_test.xlsx`
   - Esperar confirmación de subida

6. **Observar el procesamiento**:
   - El estado debe cambiar a "Procesando..."
   - Luego a "Procesado" (tarda ~1-2 segundos)
   - Debe mostrar: "5 registros procesados"

### Paso 4: Verificar Resultados

Ejecutar el script de verificación:

```bash
./verificar_flujo3.sh
```

El script verificará:
- ✅ Upload registrado correctamente
- ✅ Estado final: "procesado"
- ✅ 5 registros de AnalistaIngreso creados
- ✅ Usuario correcto (analista.nomina@bdo.cl)
- ✅ Fechas guardadas correctamente
- ✅ Logs de actividad registrados

---

## ✅ Resultados Esperados

### 1. Upload Exitoso
```
ArchivoAnalistaUpload:
├── ID: [nuevo ID]
├── Tipo: ingresos
├── Estado: procesado
├── Cierre: 35
└── Analista: analista.nomina@bdo.cl (ID: 2)
```

### 2. Registros Procesados
```
AnalistaIngreso: 5 registros
├── 19111111-1: Juan Carlos Pérez López (01/10/2025)
├── 19222222-2: María Francisca González Muñoz (05/10/2025)
├── 19333333-3: Pedro Antonio Silva Rojas (10/10/2025)
├── 19444444-4: Ana María Torres Castro (15/10/2025)
└── 19555555-5: Carlos Alberto Ramírez Flores (20/10/2025)
```

### 3. Logging Dual
```
TarjetaActivityLogNomina:
├── process_start: "Iniciando procesamiento de archivo de ingresos"
└── process_complete: "Archivo procesado: 5 registros creados"

ActivityEvent:
├── procesamiento_celery_iniciado
└── procesamiento_completado
```

### 4. Métricas de Performance
- **Tiempo de procesamiento**: < 2 segundos
- **Registros por segundo**: ~3-5 registros/seg
- **Sin errores en logs**

---

## 🐛 Problemas Comunes

### El archivo no se procesa

**Síntomas**:
- Estado queda en "pendiente" o "en_proceso"
- No aparecen registros

**Solución**:
```bash
# Verificar que Celery worker está corriendo
docker compose ps celery_worker

# Ver logs de Celery
docker compose logs celery_worker --tail=50
```

### Fechas incorrectas

**Síntomas**:
- Las fechas se guardan con un día menos

**Verificación**:
```bash
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import AnalistaIngreso
for ing in AnalistaIngreso.objects.filter(cierre_id=35):
    print(f"{ing.rut}: {ing.fecha_ingreso}")
EOF
```

### Usuario incorrecto

**Síntomas**:
- Los logs muestran usuario diferente al esperado

**Verificación**:
```bash
docker compose exec -T django python manage.py shell <<EOF
from nomina.models_logging import TarjetaActivityLogNomina
logs = TarjetaActivityLogNomina.objects.filter(
    tarjeta_tipo='archivo_analista',
    accion__in=['process_start', 'process_complete']
).order_by('-timestamp')[:5]
for log in logs:
    print(f"{log.accion}: {log.usuario.correo_bdo if log.usuario else 'None'}")
EOF
```

---

## 📊 Validaciones del Test

| Aspecto | Criterio de Éxito |
|---------|-------------------|
| Upload | ArchivoAnalistaUpload creado con estado "procesado" |
| Registros | 5 AnalistaIngreso creados |
| Fechas | Fechas coinciden exactamente con el Excel |
| Usuario | analista.nomina@bdo.cl (ID: 2) en todos los logs |
| Asociación | Todos los registros vinculados al archivo_origen |
| Performance | Procesamiento < 2 segundos |
| Logs | TarjetaActivityLogNomina y ActivityEvent registrados |

---

## 📁 Archivos Relacionados

### Frontend
- `src/components/TarjetasCierreNomina/IngresosCard.jsx`
- `src/api/nomina.js` (funciones `subirIngresos`, `obtenerEstadoIngresos`)

### Backend
- `backend/nomina/views_archivos_analista.py` (ViewSet)
- `backend/nomina/tasks_refactored/archivos_analista.py` (Tarea Celery)
- `backend/nomina/utils/ArchivosAnalista.py` (Procesamiento)
- `backend/nomina/models.py` (ArchivoAnalistaUpload, AnalistaIngreso)

---

## 🎯 Próximos Pasos

Después de completar este test exitosamente:

1. ✅ **Flujo 3 validado**: Ingresos funcionando al 100%
2. ⏭️ **Flujo 4**: Finiquitos
3. ⏭️ **Flujo 5**: Ausentismos/Incidencias

---

**Preparado por**: Sistema de QA  
**Última actualización**: 27 de octubre de 2025
