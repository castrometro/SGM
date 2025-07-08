# Implementación de Libro Mayor con Celery Chains

## Estado Actual

### ✅ Completado

1. **Archivo de Tasks Especializado**: `/root/SGM/backend/contabilidad/tasks_libro_mayor.py`
   - Chain de 6 tasks especializadas
   - Validación de nombre de archivo
   - Verificación de existencia
   - Validación de contenido Excel
   - Procesamiento RAW con manejo de excepciones
   - Generación de incidencias consolidadas
   - Finalización y limpieza

2. **Vista Refactorizada**: `/root/SGM/backend/contabilidad/views/libro_mayor.py`
   - Vista `cargar_libro_mayor` minimalista
   - Dispara chain de procesamiento
   - Registro de actividad
   - Manejo de errores robusto

3. **Importación de Tasks**: `/root/SGM/backend/contabilidad/apps.py`
   - Importación automática de `tasks_libro_mayor`
   - Registro correcto en Celery

4. **URL Endpoint**: `/root/SGM/backend/contabilidad/urls.py`
   - Path configurado para `cargar_libro_mayor`

### 🔄 Chain de Procesamiento

```python
def crear_chain_libro_mayor(upload_log_id):
    return chain(
        validar_nombre_archivo_libro_mayor.s(upload_log_id),
        verificar_archivo_libro_mayor.s(),
        validar_contenido_libro_mayor.s(),
        procesar_libro_mayor_raw.s(),
        generar_incidencias_libro_mayor.s(),
        finalizar_procesamiento_libro_mayor.s()
    )
```

### 📋 Tasks del Chain

1. **`validar_nombre_archivo_libro_mayor`**
   - Valida formato: `{RUT}_{LibroMayor|Mayor}_{YYYYMM}.xlsx`
   - Extrae período del nombre
   - Actualiza estado a "procesando"

2. **`verificar_archivo_libro_mayor`** 
   - Verifica existencia del archivo temporal
   - Calcula hash SHA256
   - Valida tamaño del archivo

3. **`validar_contenido_libro_mayor`**
   - Abre archivo Excel con openpyxl
   - Valida headers esperados
   - Verifica estructura del documento

4. **`procesar_libro_mayor_raw`**
   - Procesa movimientos contables
   - Crea/actualiza cuentas contables
   - Aplica datos auxiliares (tipos doc, nombres inglés, clasificaciones)
   - Maneja excepciones de validación por cuenta
   - Genera incidencias por datos faltantes

5. **`generar_incidencias_libro_mayor`**
   - Consolida incidencias por tipo
   - Crea registros de `IncidenciaResumen`
   - Categoriza por severidad (baja, media, alta, crítica)

6. **`finalizar_procesamiento_libro_mayor`**
   - Actualiza estado final
   - Registra actividad
   - Dispara mapeo de clasificaciones RAW
   - Limpia archivos temporales

### 🔧 Características Técnicas

- **Robustez**: Cada task maneja sus propios errores
- **Escalabilidad**: Tasks pueden distribuirse en múltiples workers  
- **Trazabilidad**: Logging detallado en cada paso
- **Recuperación**: Estado persistente en UploadLog
- **Limpieza**: Eliminación automática de archivos temporales

### 🆚 Diferencias con Task Legacy

| Aspecto | Task Legacy | Nuevo Chain |
|---------|-------------|-------------|
| Estructura | Monolítica | 6 tasks especializadas |
| Error Handling | Todo o nada | Por etapa |
| Logging | Básico | Detallado por task |
| Escalabilidad | Limitada | Alta |
| Mantenimiento | Complejo | Modular |
| Testing | Difícil | Unitario por task |

## Próximos Pasos

### 🧪 Validación Requerida

1. **Prueba de Chain Completo**
   - Subir archivo válido de prueba
   - Verificar ejecución de todas las tasks
   - Confirmar datos creados correctamente

2. **Prueba de Manejo de Errores**
   - Archivo con nombre inválido
   - Archivo corrupto
   - Contenido con errores

3. **Prueba de Rendimiento**
   - Archivo grande (>1000 movimientos)
   - Tiempo de procesamiento
   - Uso de memoria

### 🧪 Validación Práctica

#### 1. Verificar Tasks Registradas en Celery
```bash
# Verificar tasks registradas
docker compose exec django celery -A sgm_backend inspect registered | grep libro_mayor

# Ver workers activos  
docker compose exec django celery -A sgm_backend inspect active

# Verificar conectividad con broker
docker compose exec django celery -A sgm_backend inspect ping
```

#### 2. Ejecutar Script de Validación Completo
```bash
# Ejecutar script de validación con Django shell
docker compose exec django python manage.py shell < validar_libro_mayor.py
```

#### 3. Prueba Manual Paso a Paso
```bash
# Acceder al shell Django interactivo
docker compose exec django python manage.py shell

# Dentro del shell, ejecutar:
from contabilidad.tasks_libro_mayor import crear_chain_libro_mayor
from contabilidad.models import UploadLog, Cliente, CierreContabilidad
from django.contrib.auth.models import User

# Crear datos de prueba
user = User.objects.first()
cliente = Cliente.objects.first() 
cierre = CierreContabilidad.objects.filter(cliente=cliente).first()

# Crear UploadLog
upload_log = UploadLog.objects.create(
    cliente=cliente,
    cierre=cierre,
    tipo_archivo='libro_mayor',
    nombre_archivo_original='12345678_LibroMayor_202412.xlsx',
    archivo_hash='test_hash_123',
    usuario=user,
    estado='pendiente'
)

# Crear y ejecutar chain
chain = crear_chain_libro_mayor(upload_log.id)
result = chain.apply_async()
print(f'Chain iniciado con ID: {result.id}')

# Verificar resultado (esperar unos segundos)
print(f'Estado: {result.status}')
print(f'Resultado: {result.result}')
```

#### 4. Monitorear Logs en Tiempo Real
```bash
# Ver logs del django
docker compose logs django -f

# Ver logs específicos de Celery worker
docker compose exec django celery -A sgm_backend worker --loglevel=INFO

# Ver logs con filtro
docker compose logs django -f | grep "libro_mayor"
```

#### 5. Verificar Estado de Base de Datos
```bash
# Verificar UploadLogs creados
docker compose exec django python manage.py shell -c "
from contabilidad.models import UploadLog
print('UploadLogs de libro mayor:')
for ul in UploadLog.objects.filter(tipo_archivo='libro_mayor').order_by('-fecha_creacion')[:5]:
    print(f'  ID: {ul.id}, Estado: {ul.estado}, Archivo: {ul.nombre_archivo_original}')
"

# Verificar MovimientoContable creados
docker compose exec django python manage.py shell -c "
from contabilidad.models import MovimientoContable
print(f'Total movimientos: {MovimientoContable.objects.count()}')
print('Últimos 3 movimientos:')
for mov in MovimientoContable.objects.order_by('-id')[:3]:
    print(f'  {mov.cuenta.codigo} - {mov.debe} - {mov.haber}')
"

# Verificar Incidencias generadas
docker compose exec django python manage.py shell -c "
from contabilidad.models import Incidencia
from contabilidad.models_incidencias import IncidenciaResumen
print(f'Incidencias totales: {Incidencia.objects.count()}')
print(f'Incidencias consolidadas: {IncidenciaResumen.objects.count()}')
"
```

### 🔧 Comandos de Diagnóstico

```bash
# Verificar importación correcta de tasks
docker compose exec django python -c "
import django; django.setup()
from contabilidad.tasks_libro_mayor import crear_chain_libro_mayor
print('✅ Tasks importadas correctamente')
"

# Ver configuración de Celery
docker compose exec django python manage.py shell -c "
from django.conf import settings
print('CELERY_BROKER_URL:', getattr(settings, 'CELERY_BROKER_URL', 'No configurado'))
print('CELERY_RESULT_BACKEND:', getattr(settings, 'CELERY_RESULT_BACKEND', 'No configurado'))
"

# Probar conectividad con Redis/Broker  
docker compose exec django celery -A sgm_backend inspect ping

# Reiniciar worker de Celery si es necesario
docker compose restart celery_worker
```

## Arquitectura Final

```
Frontend Upload
     ↓
cargar_libro_mayor (Vista)
     ↓
crear_chain_libro_mayor()
     ↓
[Task1] validar_nombre_archivo_libro_mayor
     ↓
[Task2] verificar_archivo_libro_mayor  
     ↓
[Task3] validar_contenido_libro_mayor
     ↓
[Task4] procesar_libro_mayor_raw
     ↓
[Task5] generar_incidencias_libro_mayor
     ↓
[Task6] finalizar_procesamiento_libro_mayor
     ↓
mapear_clasificaciones_con_cuentas (Task separada)
```

El patrón de Celery Chains garantiza:
- ✅ Ejecución secuencial confiable
- ✅ Manejo de errores por etapa
- ✅ Trazabilidad completa
- ✅ Escalabilidad horizontal
- ✅ Recuperación ante fallos
- ✅ Mantenimiento simplificado
