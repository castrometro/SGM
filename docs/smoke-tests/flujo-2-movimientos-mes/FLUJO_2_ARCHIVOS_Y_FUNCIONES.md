# 📊 FLUJO COMPLETO: MOVIMIENTOS DEL MES - Archivos y Funciones

**Fecha**: 27 de octubre de 2025  
**Propósito**: Documentación técnica completa del flujo de subida y procesamiento de Movimientos del Mes

---

## 🎯 FLUJO GENERAL

```
FRONTEND                      API                      CELERY WORKER
   │                          │                             │
   ├──> Subir archivo ────────┼──> /nomina/movimientos/subir/{cierre_id}/
   │                          │                             │
   │                          ├──> Crear MovimientosMesUpload
   │                          │    Guardar archivo          │
   │                          │    Registrar logs           │
   │                          │                             │
   │                          ├──> Lanzar tarea Celery ─────┼──> procesar_movimientos_mes_con_logging
   │                          │                             │
   │                          │                             ├──> Leer Excel (5 hojas)
   │                          │                             ├──> Validar headers
   │                          │                             ├──> Crear movimientos
   │                          │                             │    - Altas/Bajas ❌ BUG
   │                          │                             │    - Ausentismos ✅
   │                          │                             │    - Vacaciones ✅
   │                          │                             │    - Var. Sueldo ✅
   │                          │                             │    - Var. Contrato ✅
   │                          │                             │
   │                          │                             ├──> Actualizar estado
   │                          │                             └──> Registrar logs
   │                          │                             
   ├──> Polling estado ───────┼──> /nomina/movimientos/estado/{cierre_id}/
   │    (cada 5s)             │                             
   │                          │                             
   └──> Mostrar resultado ────┘                             
```

---

## 📂 ESTRUCTURA DE ARCHIVOS

### FRONTEND

```
src/
├── pages/
│   └── DashboardsNomina/
│       └── MovimientosMes.jsx                    # Página principal (no usada en smoke test)
│
├── components/
│   └── TarjetasCierreNomina/
│       ├── CierreProgresoNomina.jsx              # Componente principal que orquesta
│       ├── MovimientosMesCard.jsx                # Tarjeta de subida de archivo
│       ├── ArchivosTalanaSection.jsx             # Sección que contiene la tarjeta
│       └── ResumenCierreSection.jsx              # Resumen con estado de archivos
│
└── api/
    └── nomina.js                                 # Cliente API
```

### BACKEND - API

```
backend/nomina/
├── views_movimientos_mes.py                      # ViewSet principal
├── urls.py                                       # Rutas de API
├── serializers.py                                # Serializadores
├── models.py                                     # Modelos de datos
├── models_logging.py                             # Logging de actividades
└── signals.py                                    # Señales para limpieza de archivos
```

### BACKEND - PROCESAMIENTO

```
backend/nomina/
├── tasks_refactored/
│   └── movimientos_mes.py                        # Tarea Celery refactorizada
│
└── utils/
    ├── MovimientoMes.py                          # ⚠️ Lógica de procesamiento (BUG en línea 427)
    ├── validaciones.py                           # Validación de archivos
    ├── uploads.py                                # Utilidades de subida
    └── clientes.py                               # Utilidades de clientes
```

---

## 🔍 DETALLE POR CAPA

---

## 📱 FRONTEND

### 1. Componente Principal: `MovimientosMesCard.jsx`

**Ubicación**: `src/components/TarjetasCierreNomina/MovimientosMesCard.jsx`

#### Funciones Principales

```javascript
// Props recibidas
{
  estado,              // Estado del upload ('pendiente', 'en_proceso', 'procesado')
  archivoNombre,       // Nombre del archivo subido
  onSubirArchivo,      // Callback para subir archivo
  onActualizarEstado,  // Callback para actualizar estado
  onEliminarArchivo,   // Callback para eliminar archivo
  subiendo,            // Indicador de subida en progreso
  disabled,            // Deshabilitar interacción
  cierreId,            // ID del cierre
  clienteId,           // ID del cliente
  deberiaDetenerPolling // Flag para detener polling
}

// Funciones internas
const handleFileSelect = async (event) => {
  // Maneja la selección y subida del archivo
  // Llama a onSubirArchivo(formData)
}

const handleEliminar = async () => {
  // Elimina el archivo subido
  // Llama a onEliminarArchivo()
}

const handleDescargarPlantilla = () => {
  // Descarga la plantilla de Excel
  // Usa descargarPlantillaMovimientosMes()
}

// Polling automático
useEffect(() => {
  // Inicia polling cada 5s cuando estado === "en_proceso"
  // Llama a onActualizarEstado() periódicamente
  // Se detiene cuando estado cambia o deberiaDetenerPolling === true
}, [estado, deberiaDetenerPolling])
```

**Activity Logging V2:**
- `logSessionStart()` - Al montar componente
- `logPollingStart(5)` - Al iniciar polling
- `logPollingStop()` - Al detener polling

---

### 2. API Client: `nomina.js`

**Ubicación**: `src/api/nomina.js`

#### Funciones Exportadas

```javascript
// 1. Obtener estado del archivo de movimientos
export const obtenerEstadoMovimientosMes = async (cierreId) => {
  const response = await api.get(`/nomina/movimientos/estado/${cierreId}/`);
  return response.data;
}
// Retorna: { id, cierre, archivo, archivo_nombre, fecha_subida, estado, error_message }

// 2. Subir archivo de movimientos
export const subirMovimientosMes = async (cierreId, formData) => {
  const response = await api.post(
    `/nomina/movimientos/subir/${cierreId}/`, 
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}
// Retorna: { id, estado, mensaje, task_id }

// 3. Descargar plantilla de Excel
export const descargarPlantillaMovimientosMes = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-movimientos-mes/`;
}

// 4. Eliminar archivo de movimientos
export const eliminarMovimientosMes = async (movimientoId) => {
  const response = await api.delete(`/nomina/movimientos-mes/${movimientoId}/`);
  return response.data;
}
```

---

## 🔧 BACKEND - API LAYER

### 1. ViewSet: `MovimientosMesUploadViewSet`

**Ubicación**: `backend/nomina/views_movimientos_mes.py` (líneas 39-451)

#### Endpoints

##### GET `/nomina/movimientos/estado/{cierre_id}/`

```python
@action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
def estado(self, request, cierre_id=None):
    """Obtener el estado del archivo de movimientos para un cierre específico"""
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        movimiento = MovimientosMesUpload.objects.filter(cierre=cierre).first()
        
        if not movimiento:
            return Response({
                "estado": "no_subido",
                "mensaje": "No se ha subido ningún archivo de movimientos"
            })
        
        serializer = self.get_serializer(movimiento)
        return Response(serializer.data)
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
```

**Respuesta:**
```json
{
  "id": 43,
  "cierre": 35,
  "archivo": "remuneraciones/20/2025-10/mov_mes/...",
  "archivo_nombre": "movimientos_mes_smoke_test.xlsx",
  "fecha_subida": "2025-10-27T15:31:12.411448Z",
  "estado": "procesado",
  "error_message": null
}
```

##### POST `/nomina/movimientos/subir/{cierre_id}/`

```python
@action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)')
def subir(self, request, cierre_id=None):
    """Subir archivo de MovimientosMes con logging integrado"""
    
    # 1. OBTENER ARCHIVO
    archivo = request.FILES.get('archivo')
    
    # 2. OBTENER CIERRE Y CLIENTE
    cierre = CierreNomina.objects.get(id=cierre_id)
    cliente = cierre.cliente
    
    # 3. VALIDAR NOMBRE DE ARCHIVO (opcional pero recomendado)
    validacion = validar_nombre_archivo_movimientos_mes(
        archivo.name, 
        rut_cliente=cliente.rut, 
        periodo_cierre=cierre.periodo
    )
    
    # 4. VERIFICAR SI YA EXISTE UPLOAD PREVIO
    movimiento_existente = MovimientosMesUpload.objects.filter(cierre=cierre).first()
    if movimiento_existente:
        # Eliminar registros previos
        limpiar_movimientos_cierre(cierre)
        movimiento_existente.delete()
    
    # 5. CREAR NUEVO UPLOAD
    movimiento = MovimientosMesUpload.objects.create(
        cierre=cierre,
        archivo=archivo,
        archivo_nombre=archivo.name,
        estado='pendiente'
    )
    
    # 6. REGISTRAR EN TARJETA ACTIVITY LOG (User-facing)
    upload_log = registrar_actividad_tarjeta_nomina(
        tarjeta='movimientos_mes',
        cierre=cierre,
        usuario=request.user,
        accion='archivo_subido',
        descripcion=f'Archivo {archivo.name} subido correctamente',
        resultado='success',
        detalles={'archivo_nombre': archivo.name, 'tamaño': archivo.size}
    )
    
    # 7. REGISTRAR EN ACTIVITY EVENT (Audit trail)
    ActivityEvent.log(
        user=request.user,
        cliente=cliente,
        cierre=cierre,
        event_type='upload',
        action='archivo_subido_movimientos_mes',
        resource_type='movimientos_mes',
        resource_id=str(movimiento.id),
        details={'archivo_nombre': archivo.name}
    )
    
    # 8. LANZAR TAREA CELERY (Asíncrono)
    result = procesar_movimientos_mes_con_logging.delay(
        movimiento.id, 
        request.user.id
    )
    
    # 9. RETORNAR RESPUESTA
    return Response({
        'id': movimiento.id,
        'estado': 'pendiente',
        'mensaje': 'Archivo subido exitosamente. Procesando...',
        'task_id': result.id
    })
```

**Flujo de logs:**
1. `TarjetaActivityLogNomina` → `archivo_subido` (usuario visible)
2. `ActivityEvent` → `archivo_subido_movimientos_mes` (audit trail)

---

### 2. Modelos: `models.py`

**Ubicación**: `backend/nomina/models.py`

```python
class MovimientosMesUpload(models.Model):
    """
    Registro de archivos de movimientos del mes subidos.
    Contiene altas, bajas, ausentismos, vacaciones, variaciones.
    """
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    archivo = models.FileField(
        upload_to=movimientos_mes_upload_to,
        validators=[validar_extension_excel]
    )
    archivo_nombre = models.CharField(max_length=255)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=50,
        default='pendiente',
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('procesado', 'Procesado'),
            ('error', 'Error')
        ]
    )
    error_message = models.TextField(null=True, blank=True)

class MovimientoAltaBaja(models.Model):
    """Movimientos de ingresos (altas) y finiquitos (bajas)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.SET_NULL, null=True)
    nombres_apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    empresa_nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255, blank=True)
    centro_de_costo = models.CharField(max_length=255, blank=True)
    sucursal = models.CharField(max_length=255, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_retiro = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=100, blank=True)
    dias_trabajados = models.IntegerField(null=True, blank=True)
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    alta_o_baja = models.CharField(max_length=50)  # 'ALTA' o 'BAJA'
    motivo = models.TextField(blank=True)

class MovimientoAusentismo(models.Model):
    """Ausentismos: licencias médicas, permisos, etc."""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.SET_NULL, null=True)
    nombres_apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    empresa_nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255, blank=True)
    centro_de_costo = models.CharField(max_length=255, blank=True)
    sucursal = models.CharField(max_length=255, blank=True)
    fecha_inicio_ausencia = models.DateField(null=True, blank=True)
    fecha_fin_ausencia = models.DateField(null=True, blank=True)
    dias = models.IntegerField(null=True, blank=True)
    tipo = models.CharField(max_length=100)  # "Licencia Médica", "Permiso Personal", etc.
    motivo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

class MovimientoVacaciones(models.Model):
    """Periodos de vacaciones"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.SET_NULL, null=True)
    nombres_apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    empresa_nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255, blank=True)
    centro_de_costo = models.CharField(max_length=255, blank=True)
    sucursal = models.CharField(max_length=255, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_retorno = models.DateField(null=True, blank=True)
    cantidad_dias = models.IntegerField(null=True, blank=True)

class MovimientoVariacionSueldo(models.Model):
    """Cambios en el sueldo base de empleados"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.SET_NULL, null=True)
    nombres_apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    empresa_nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255, blank=True)
    centro_de_costo = models.CharField(max_length=255, blank=True)
    sucursal = models.CharField(max_length=255, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=100, blank=True)
    sueldo_base_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_base_actual = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_reajuste = models.DecimalField(max_digits=5, decimal_places=2)
    variacion_monto = models.DecimalField(max_digits=12, decimal_places=2)

class MovimientoVariacionContrato(models.Model):
    """Cambios en el tipo de contrato"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.SET_NULL, null=True)
    nombres_apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=20)
    empresa_nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255, blank=True)
    centro_de_costo = models.CharField(max_length=255, blank=True)
    sucursal = models.CharField(max_length=255, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    tipo_contrato_anterior = models.CharField(max_length=100)
    tipo_contrato_actual = models.CharField(max_length=100)
```

---

## ⚙️ BACKEND - PROCESSING LAYER

### 1. Tarea Celery: `procesar_movimientos_mes_con_logging`

**Ubicación**: `backend/nomina/tasks_refactored/movimientos_mes.py` (línea 32)

```python
@shared_task(bind=True, queue='nomina_queue')
def procesar_movimientos_mes_con_logging(self, movimiento_id, usuario_id=None):
    """
    Procesa un archivo de movimientos del mes con logging completo dual.
    
    Esta tarea procesa el archivo Excel de movimientos y genera:
    - Movimientos de Altas/Bajas
    - Movimientos de Ausentismo  
    - Movimientos de Vacaciones
    - Movimientos de Variación de Sueldo
    - Movimientos de Variación de Contrato
    
    Args:
        movimiento_id (int): ID del MovimientosMesUpload a procesar
        usuario_id (int, optional): ID del usuario que inició el procesamiento
        
    Returns:
        dict: Resultados del procesamiento con contadores por tipo de movimiento
    """
    from ..models_logging import registrar_actividad_tarjeta_nomina
    from ..models import ActivityEvent
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # 1. OBTENER USUARIO
    if usuario_id:
        usuario = User.objects.get(id=usuario_id)
    else:
        usuario = _get_sistema_user()
    
    logger.info(f"[MOVIMIENTOS MES] Iniciando procesamiento de archivo id={movimiento_id}, usuario={usuario.correo_bdo}")
    
    try:
        # 2. OBTENER REFERENCIAS
        movimiento = MovimientosMesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=movimiento_id)
        cierre = movimiento.cierre
        cliente = cierre.cliente
        
        # 3. LOGGING: Procesamiento iniciado
        
        # ActivityEvent - Audit trail técnico
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_celery_iniciado',
            resource_type='movimientos_mes',
            resource_id=str(movimiento_id),
            details={
                'movimiento_id': movimiento_id,
                'archivo_nombre': movimiento.archivo.name if movimiento.archivo else "N/A",
                'celery_task_id': self.request.id,
                'usuario_id': usuario_id,
                'usuario_correo': usuario.correo_bdo
            }
        )
        
        # TarjetaActivityLogNomina - User-facing
        registrar_actividad_tarjeta_nomina(
            tarjeta='movimientos_mes',
            cierre=cierre,
            usuario=usuario,
            accion='process_start',
            descripcion=f'Procesamiento de archivo de movimientos iniciado',
            resultado='info',
            detalles={'archivo_nombre': movimiento.archivo_nombre}
        )
        
        # 4. ACTUALIZAR ESTADO A 'en_proceso'
        movimiento.estado = 'en_proceso'
        movimiento.save()
        
        # 5. PROCESAR ARCHIVO (función utilitaria)
        logger.info(f"[MOVIMIENTOS MES] Ejecutando procesamiento de archivo: {movimiento.archivo.path}")
        resultados = procesar_archivo_movimientos_mes_util(movimiento)
        
        logger.info(f"[MOVIMIENTOS MES] Procesamiento completado. Resultados: {resultados}")
        
        # 6. VERIFICAR ERRORES
        if resultados.get('errores'):
            logger.warning(f"[MOVIMIENTOS MES] Procesamiento completado con errores: {resultados['errores']}")
            movimiento.estado = 'con_errores_parciales'
            movimiento.error_message = '; '.join(resultados['errores'])
        else:
            logger.info(f"[MOVIMIENTOS MES] Procesamiento exitoso sin errores")
            movimiento.estado = 'procesado'
            movimiento.error_message = None
        
        movimiento.save()
        
        # 7. LOGGING: Procesamiento completado
        
        # ActivityEvent
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_completado',
            resource_type='movimientos_mes',
            resource_id=str(movimiento_id),
            details={
                'movimiento_id': movimiento_id,
                'resultados': resultados,
                'celery_task_id': self.request.id
            }
        )
        
        # TarjetaActivityLogNomina
        registrar_actividad_tarjeta_nomina(
            tarjeta='movimientos_mes',
            cierre=cierre,
            usuario=usuario,
            accion='process_complete',
            descripcion=f'Procesamiento completado: {sum([v for k,v in resultados.items() if k!="errores"])} movimientos',
            resultado='success',
            detalles={'resultados': resultados}
        )
        
        logger.info(f"[MOVIMIENTOS MES] ✅ Procesamiento finalizado exitosamente. Estado: {movimiento.estado}")
        
        return resultados
        
    except Exception as e:
        # MANEJO DE ERRORES
        logger.error(f"[MOVIMIENTOS MES] ❌ Error en procesamiento: {e}", exc_info=True)
        
        # Actualizar estado
        movimiento.estado = 'error'
        movimiento.error_message = str(e)
        movimiento.save()
        
        # ActivityEvent - Error
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='error',
            action='procesamiento_error',
            resource_type='movimientos_mes',
            resource_id=str(movimiento_id),
            details={
                'error': str(e),
                'celery_task_id': self.request.id
            }
        )
        
        # TarjetaActivityLogNomina - Error
        registrar_actividad_tarjeta_nomina(
            tarjeta='movimientos_mes',
            cierre=cierre,
            usuario=usuario,
            accion='process_error',
            descripcion=f'Error en procesamiento: {str(e)}',
            resultado='error',
            detalles={'error': str(e)}
        )
        
        raise
```

**Flujo de logs en tarea:**
1. `ActivityEvent` → `procesamiento_celery_iniciado`
2. `TarjetaActivityLogNomina` → `process_start`
3. **Procesamiento...**
4. `ActivityEvent` → `procesamiento_completado` (o `procesamiento_error`)
5. `TarjetaActivityLogNomina` → `process_complete` (o `process_error`)

---

### 2. Función Utilitaria: `procesar_archivo_movimientos_mes_util`

**Ubicación**: `backend/nomina/utils/MovimientoMes.py` (línea 377)

```python
def procesar_archivo_movimientos_mes_util(movimiento_upload: MovimientosMesUpload) -> Dict[str, int]:
    """
    Función utilitaria principal para procesar archivo de movimientos.
    Retorna un diccionario con el conteo de registros procesados por tipo.
    """
    archivo_path = movimiento_upload.archivo.path
    cierre = movimiento_upload.cierre
    
    logger.info(f"Iniciando procesamiento de archivo de movimientos: {archivo_path}")
    
    # 1. LEER ARCHIVO EXCEL (5 hojas)
    hojas = leer_archivo_movimientos_mes(archivo_path)
    
    resultados = {
        'altas_bajas': 0,
        'ausentismos': 0,
        'vacaciones': 0,
        'variaciones_sueldo': 0,
        'variaciones_contrato': 0,
        'errores': []
    }
    
    # 2. MAPEO DE HOJAS A FUNCIONES DE PROCESAMIENTO
    mapeo_hojas = {
        'altas_bajas': ('altas_bajas', procesar_altas_bajas),
        'altasbajas': ('altas_bajas', procesar_altas_bajas),
        'altas y bajas': ('altas_bajas', procesar_altas_bajas),
        'ausentismos': ('ausentismos', procesar_ausentismos),
        'ausentismo': ('ausentismos', procesar_ausentismos),
        'vacaciones': ('vacaciones', procesar_vacaciones),
        'variaciones_sueldo': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones sueldo': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones de sueldo base': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones_contrato': ('variaciones_contrato', procesar_variaciones_contrato),
        'variaciones contrato': ('variaciones_contrato', procesar_variaciones_contrato),
        'variaciones de tipo contrato': ('variaciones_contrato', procesar_variaciones_contrato),
    }
    
    # 3. PROCESAR CADA HOJA ENCONTRADA
    for nombre_hoja, df in hojas.items():
        if df.empty:
            logger.warning(f"Hoja '{nombre_hoja}' está vacía, omitiendo...")
            continue
        
        # ⚠️ BUG AQUÍ - LÍNEA 427
        # Buscar el mapeo correspondiente
        clave_encontrada = None
        for posible_nombre, (tipo, funcion) in mapeo_hojas.items():
            # 🐛 BUG: nombre_hoja ya está en minúsculas ('altas_bajas')
            #         pero se hace .replace('_', ' ') → 'altas bajas'
            #         entonces 'altas_bajas' in 'altas bajas' → False
            if posible_nombre in nombre_hoja.lower().replace('_', ' ').replace('-', ' '):
                clave_encontrada = (tipo, funcion)
                break
        
        if not clave_encontrada:
            logger.warning(f"Hoja '{nombre_hoja}' no reconocida, omitiendo...")
            continue
        
        tipo, funcion_procesamiento = clave_encontrada
        
        # 4. VALIDAR HEADERS
        headers_esperados = HEADERS_ESPERADOS[tipo]
        es_valida, headers_faltantes = validar_headers_hoja(df, headers_esperados, nombre_hoja)
        
        if not es_valida:
            error_msg = f"Hoja '{nombre_hoja}' - Headers faltantes: {headers_faltantes}"
            resultados['errores'].append(error_msg)
            logger.error(error_msg)
            continue
        
        # 5. PROCESAR LA HOJA
        try:
            count = funcion_procesamiento(df, cierre)
            resultados[tipo] = count
            logger.info(f"Hoja '{nombre_hoja}' procesada exitosamente: {count} registros")
        except Exception as e:
            error_msg = f"Error procesando hoja '{nombre_hoja}': {str(e)}"
            resultados['errores'].append(error_msg)
            logger.error(error_msg)
    
    total_procesados = sum([v for k, v in resultados.items() if k != 'errores'])
    logger.info(f"Procesamiento completado. Total de registros: {total_procesados}")
    
    return resultados
```

**⚠️ BUG IDENTIFICADO:**

Línea 427:
```python
if posible_nombre in nombre_hoja.lower().replace('_', ' ').replace('-', ' '):
```

**Problema:**
- `nombre_hoja` = `'altas_bajas'` (ya en minúsculas desde lectura)
- `.replace('_', ' ')` → `'altas bajas'`
- `posible_nombre` = `'altas_bajas'`
- `'altas_bajas' in 'altas bajas'` → **False** ❌

**Solución:**
```python
# Normalizar ambos lados
nombre_normalizado = nombre_hoja.lower().replace('_', ' ').replace('-', ' ')
posible_normalizado = posible_nombre.replace('_', ' ').replace('-', ' ')
if posible_normalizado in nombre_normalizado:
    clave_encontrada = (tipo, funcion)
    break
```

---

### 3. Función de Lectura: `leer_archivo_movimientos_mes`

**Ubicación**: `backend/nomina/utils/MovimientoMes.py` (línea 46)

```python
def leer_archivo_movimientos_mes(archivo_path: str) -> Dict[str, pd.DataFrame]:
    """
    Lee el archivo Excel de movimientos del mes y retorna un diccionario con DataFrames
    para cada hoja. Los headers están siempre en la fila 3 (índice 2).
    """
    try:
        # Leer todas las hojas con headers en fila 3
        hojas = pd.read_excel(archivo_path, sheet_name=None, engine='openpyxl', header=2)
        
        logger.info(f"Hojas encontradas en el archivo: {list(hojas.keys())}")
        
        hojas_procesadas = {}
        
        for nombre_hoja, df in hojas.items():
            # Limpiar filas vacías
            df = df.dropna(how='all')
            
            if not df.empty:
                # Normalizar headers a MAYÚSCULAS
                headers_limpios = []
                for col in df.columns:
                    if pd.notna(col):
                        header_limpio = str(col).strip().upper()
                        header_limpio = header_limpio.replace("|", "").replace("Unnamed:", "COLUMNA")
                        headers_limpios.append(header_limpio)
                    else:
                        headers_limpios.append(f"COLUMNA_{len(headers_limpios)}")
                
                df.columns = headers_limpios
                
                # Eliminar columnas vacías sin header válido
                columnas_a_mantener = []
                for col in df.columns:
                    if col.startswith('COLUMNA_') and df[col].isna().all():
                        continue
                    else:
                        columnas_a_mantener.append(col)
                
                df = df[columnas_a_mantener]
                df = df.reset_index(drop=True)
                
                # ⚠️ AQUÍ SE CONVIERTE A MINÚSCULAS
                hojas_procesadas[nombre_hoja.strip().lower()] = df
                logger.info(f"Hoja '{nombre_hoja}' procesada con {len(df.columns)} columnas: {df.columns.tolist()}")
        
        return hojas_procesadas
        
    except Exception as e:
        logger.error(f"Error leyendo archivo de movimientos: {e}")
        raise
```

**Nota importante:**
- Los headers de columnas se normalizan a MAYÚSCULAS
- Los nombres de hojas se convierten a minúsculas
- Esto causa el bug posterior en el mapeo

---

### 4. Funciones de Procesamiento por Tipo

**Ubicación**: `backend/nomina/utils/MovimientoMes.py`

#### `procesar_altas_bajas(df, cierre)` - Línea 169

```python
def procesar_altas_bajas(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Altas y Bajas (ingresos y finiquitos)"""
    contador = 0
    
    # Limpiar registros anteriores
    MovimientoAltaBaja.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoAltaBaja.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_ingreso=convertir_fecha(row.get('FECHA INGRESO')),
                fecha_retiro=convertir_fecha(row.get('FECHA RETIRO')),
                tipo_contrato=str(row.get('TIPO CONTRATO', '')).strip(),
                dias_trabajados=convertir_entero(row.get('DIAS TRABAJADOS')),
                sueldo_base=convertir_decimal(row.get('SUELDO BASE')),
                alta_o_baja=str(row.get('ALTA / BAJA', '')).strip().upper(),
                motivo=str(row.get('MOTIVO', '')).strip()
            )
            contador += 1
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Altas/Bajas: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Altas/Bajas")
    return contador
```

#### `procesar_ausentismos(df, cierre)` - Línea 214

```python
def procesar_ausentismos(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Ausentismos"""
    contador = 0
    
    MovimientoAusentismo.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoAusentismo.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_inicio_ausencia=convertir_fecha(row.get('FECHA INICIO AUSENCIA')),
                fecha_fin_ausencia=convertir_fecha(row.get('FECHA FIN AUSENCIA')),
                dias=convertir_entero(row.get('DIAS')),
                tipo=str(row.get('TIPO DE AUSENTISMO', '')).strip(),
                motivo=str(row.get('MOTIVO', '')).strip(),
                observaciones=str(row.get('OBSERVACIONES', '')).strip()
            )
            contador += 1
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Ausentismos: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Ausentismos")
    return contador
```

#### `procesar_vacaciones(df, cierre)` - Línea 253

Similar estructura, crea registros de `MovimientoVacaciones`.

#### `procesar_variaciones_sueldo(df, cierre)` - Línea 291

Similar estructura, crea registros de `MovimientoVariacionSueldo`.

#### `procesar_variaciones_contrato(df, cierre)` - Línea 336

Similar estructura, crea registros de `MovimientoVariacionContrato`.

---

## 📊 RESUMEN DE FLUJO DE DATOS

### Estado del Upload

| Estado | Descripción | Cuándo ocurre |
|--------|-------------|---------------|
| `no_subido` | No hay archivo subido | Estado inicial |
| `pendiente` | Archivo subido, esperando procesamiento | Después del POST subir/ |
| `en_proceso` | Celery procesando el archivo | Al inicio de la tarea |
| `procesado` | Procesamiento exitoso | Al finalizar sin errores |
| `con_errores_parciales` | Procesamiento con algunos errores | Al finalizar con errores no críticos |
| `error` | Error crítico en procesamiento | Excepción en tarea Celery |

### Logging Dual

#### TarjetaActivityLogNomina (User-facing)

| Acción | Cuándo | Usuario |
|--------|--------|---------|
| `archivo_subido` | POST /subir/ | Usuario del request |
| `process_start` | Inicio tarea Celery | Usuario propagado |
| `process_complete` | Fin exitoso tarea | Usuario propagado |
| `process_error` | Error en tarea | Usuario propagado |

#### ActivityEvent (Audit trail)

| Action | Event Type | Cuándo |
|--------|------------|--------|
| `archivo_subido_movimientos_mes` | `upload` | POST /subir/ |
| `procesamiento_celery_iniciado` | `process` | Inicio tarea |
| `procesamiento_completado` | `process` | Fin exitoso |
| `procesamiento_error` | `error` | Error en tarea |

---

## 🔧 ARCHIVOS DE UTILIDADES

### Validaciones: `validaciones.py`

```python
def validar_nombre_archivo_movimientos_mes(
    nombre_archivo: str, 
    rut_cliente: str = None, 
    periodo_cierre: str = None
) -> Dict[str, Any]:
    """
    Valida el nombre del archivo de movimientos del mes.
    Formato esperado: {periodo}_movimientos_mes_{rut}.xlsx
    """
    # Implementación de validación
```

### Helpers: `MovimientoMes.py`

```python
def limpiar_rut(rut: str) -> str:
    """Limpia y normaliza un RUT"""

def convertir_fecha(fecha_valor: Any) -> Any:
    """Convierte un valor a fecha"""

def convertir_decimal(valor: Any) -> float:
    """Convierte un valor a decimal"""

def convertir_entero(valor: Any) -> int:
    """Convierte un valor a entero"""

def buscar_empleado_por_rut(rut: str, cierre) -> EmpleadoCierre:
    """Busca un empleado por RUT en el cierre"""
```

---

## 📝 HEADERS ESPERADOS POR HOJA

```python
HEADERS_ESPERADOS = {
    'altas_bajas': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO', 'SUCURSAL', 
        'FECHA INGRESO', 'FECHA RETIRO', 'TIPO CONTRATO', 'DIAS TRABAJADOS', 
        'SUELDO BASE', 'ALTA / BAJA', 'MOTIVO'
    ],
    'ausentismos': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INICIO AUSENCIA', 'FECHA FIN AUSENCIA',
        'DIAS', 'TIPO DE AUSENTISMO', 'MOTIVO', 'OBSERVACIONES'
    ],
    'vacaciones': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'FECHA INICIAL', 'FECHA FIN VACACIONES',
        'FECHA RETORNO', 'CANTIDAD DE DIAS'
    ],
    'variaciones_sueldo': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'TIPO CONTRATO', 'SUELDO BASE ANTERIOR',
        'SUELDO BASE ACTUAL', '% DE REAJUSTE', 'VARIACIÓN ($)'
    ],
    'variaciones_contrato': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'TIPO CONTRATO ANTERIOR', 'TIPO CONTRATO ACTUAL'
    ]
}
```

---

## 🎯 CONCLUSIÓN

Este documento detalla todo el flujo desde que el usuario hace click en "Subir archivo" hasta que se crean los registros en la base de datos. El bug identificado en la línea 427 de `MovimientoMes.py` impide que la hoja "ALTAS_BAJAS" sea procesada correctamente, resultando en la pérdida de 5 movimientos en el smoke test.

---

**Documentado por**: Sistema automatizado  
**Fecha**: 27 de octubre de 2025  
**Basado en**: Smoke Test Flujo 2 - Movimientos del Mes
