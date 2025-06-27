# 📊 Sistema de Logging para Nómina - Documentación

## 🎯 Objetivo
Implementar un sistema unificado de logging para las tarjetas del cierre de nómina, basado en el modelo exitoso de contabilidad, que permita:
- Rastrear todas las subidas de archivos
- Registrar actividades en las tarjetas
- Mantener trazabilidad completa de acciones de usuarios
- Facilitar debugging y auditorías

## 🏗️ Arquitectura

### **Modelo 1: `UploadLogNomina`**
Log unificado para todas las subidas de archivos en nómina.

### **Modelo 2: `TarjetaActivityLogNomina`**
Registro de todas las actividades realizadas en las tarjetas del cierre.

### **Modelo 3: `MovimientosAnalistaUpload`**
Modelo específico para archivos del analista (nuevo).

## 📋 Modelos Detallados

### 🔄 **UploadLogNomina**

```python
# Tipos de archivos soportados
TIPO_CHOICES = [
    ("libro_remuneraciones", "Libro de Remuneraciones"),
    ("movimientos_mes", "Movimientos del Mes"),
    ("novedades", "Novedades"),
    ("movimientos_ingresos", "Movimientos - Ingresos"),
    ("movimientos_egresos", "Movimientos - Egresos"),
    ("movimientos_vacaciones", "Movimientos - Vacaciones"),
    ("movimientos_variacion_sueldo", "Movimientos - Variación Sueldo"),
    ("movimientos_variacion_contrato", "Movimientos - Variación Contrato"),
]

# Estados del procesamiento
ESTADO_CHOICES = [
    ("subido", "Archivo subido"),
    ("procesando", "Procesando"),
    ("analizando_hdrs", "Analizando Headers"),
    ("hdrs_analizados", "Headers Analizados"),
    ("clasif_en_proceso", "Clasificación en Proceso"),
    ("clasif_pendiente", "Clasificación Pendiente"),
    ("clasificado", "Clasificado"),
    ("completado", "Procesado correctamente"),
    ("procesado", "Procesado"),
    ("error", "Con errores"),
    ("con_errores_parciales", "Con Errores Parciales"),
    ("datos_eliminados", "Datos procesados eliminados"),
]
```

#### **Campos Principales:**
- `tipo_upload`: Tipo de archivo subido
- `cliente`: Cliente asociado
- `cierre`: Cierre de nómina asociado
- `usuario`: Usuario que subió el archivo
- `nombre_archivo_original`: Nombre original del archivo
- `ruta_archivo`: Ubicación en storage
- `estado`: Estado actual del procesamiento
- `resumen`: JSON con resultados del procesamiento
- `registros_procesados/exitosos/fallidos`: Contadores específicos de nómina
- `headers_detectados`: Headers encontrados en el archivo

### 📝 **TarjetaActivityLogNomina**

```python
# Tarjetas del cierre de nómina
TARJETA_CHOICES = [
    ("libro_remuneraciones", "Tarjeta 1: Libro de Remuneraciones"),
    ("movimientos_mes", "Tarjeta 2: Movimientos del Mes"),
    ("analista_ingresos", "Tarjeta 3a: Movimientos - Ingresos"),
    ("analista_egresos", "Tarjeta 3b: Movimientos - Egresos"),
    ("analista_vacaciones", "Tarjeta 3c: Movimientos - Vacaciones"),
    ("analista_variacion_sueldo", "Tarjeta 3d: Movimientos - Variación Sueldo"),
    ("analista_variacion_contrato", "Tarjeta 3e: Movimientos - Variación Contrato"),
    ("novedades", "Tarjeta 4: Novedades"),
    ("incidencias", "Tarjeta 5: Incidencias"),
    ("revision", "Tarjeta 6: Revisión"),
]

# Acciones registrables
ACCION_CHOICES = [
    ("upload_excel", "Subida de Excel"),
    ("reprocesar_archivo", "Reprocesar Archivo"),
    ("analizar_headers", "Análisis de Headers"),
    ("mapear_headers", "Mapeo de Headers"),
    ("clasificar_conceptos", "Clasificación de Conceptos"),
    ("procesar_final", "Procesamiento Final"),
    ("manual_create", "Creación Manual"),
    ("manual_edit", "Edición Manual"),
    ("manual_delete", "Eliminación Manual"),
    ("bulk_delete", "Eliminación Masiva"),
    ("view_data", "Visualización de Datos"),
    ("view_modal", "Apertura de Modal"),
    ("modal_action", "Acción en Modal"),
    ("export_data", "Exportación de Datos"),
    ("validation_error", "Error de Validación"),
    ("process_start", "Inicio de Procesamiento"),
    ("process_complete", "Procesamiento Completado"),
    ("incidencia_create", "Creación de Incidencia"),
    ("incidencia_resolve", "Resolución de Incidencia"),
    ("revision_submit", "Envío a Revisión"),
    ("revision_approve", "Aprobación de Revisión"),
    ("revision_reject", "Rechazo de Revisión"),
]
```

#### **Campos Específicos de Nómina:**
- `archivo_relacionado`: Referencia a UploadLogNomina
- `empleado_rut`: RUT del empleado afectado
- `concepto_afectado`: Concepto de remuneración afectado

### 📁 **MovimientosAnalistaUpload** (Nuevo)

Modelo unificado para todos los archivos del analista:

```python
TIPO_ARCHIVO_CHOICES = [
    ('ingresos', 'Ingresos'),
    ('egresos', 'Egresos'),
    ('vacaciones', 'Vacaciones'),
    ('variacion_sueldo', 'Variación Sueldo'),
    ('variacion_contrato', 'Variación Contrato'),
]
```

## 🔗 **Integración con Modelos Existentes**

Todos los modelos de upload existentes ahora tienen referencia al log unificado:

```python
# Agregado a todos los modelos de upload
upload_log = models.ForeignKey(
    "UploadLogNomina",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    help_text="Referencia al log del upload que generó este archivo",
)
```

### **Modelos Actualizados:**
- ✅ `LibroRemuneracionesUpload`
- ✅ `MovimientosMesUpload`
- ✅ `ArchivoNovedadesUpload`
- ✅ `MovimientosAnalistaUpload` (nuevo)

## 🛠️ **Función Helper**

```python
def registrar_actividad_tarjeta_nomina(
    cierre_id,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado="exito",
    ip_address=None,
    archivo_relacionado=None,
    empleado_rut="",
    concepto_afectado=""
)
```

### **Ejemplo de Uso:**

```python
# En una view de subida de archivo
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="novedades",
    accion="upload_excel",
    descripcion=f"Archivo subido: {archivo.name}",
    usuario=request.user,
    detalles={
        "nombre_archivo": archivo.name,
        "tamaño": archivo.size,
        "headers_detectados": headers_list
    },
    resultado="exito",
    ip_address=request.META.get('REMOTE_ADDR'),
    archivo_relacionado=upload_log
)

# En una acción del modal
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="novedades",
    accion="mapear_headers",
    descripcion="Usuario mapeó headers de novedades",
    usuario=request.user,
    detalles={
        "mapeos_creados": len(mapeos),
        "headers_mapeados": list(mapeos.keys())
    },
    concepto_afectado="Sueldo Base"
)
```

## 📊 **Validación de Nombres de Archivo**

El sistema incluye validación automática de nombres de archivo:

### **Formatos Esperados:**
```
{rut_limpio}_LibroRemuneraciones.xlsx
{rut_limpio}_MovimientosMes.xlsx
{rut_limpio}_Novedades.xlsx
{rut_limpio}_MovimientosIngresos.xlsx
{rut_limpio}_MovimientosEgresos.xlsx
{rut_limpio}_MovimientosVacaciones.xlsx
{rut_limpio}_MovimientosVariacionSueldo.xlsx
{rut_limpio}_MovimientosVariacionContrato.xlsx
```

### **Ejemplo:**
```python
# Para RUT 12.345.678-9
12345678_LibroRemuneraciones.xlsx
12345678_Novedades.xlsx
12345678_MovimientosIngresos.xlsx
```

## 🚀 **Beneficios del Sistema**

### **1. Trazabilidad Completa**
- Cada archivo subido queda registrado
- Todas las acciones de usuario se logean
- Historial completo de cambios

### **2. Debugging Facilitado**
- Logs estructurados con detalles JSON
- Estados claros de procesamiento
- Errores capturados con contexto

### **3. Auditoría**
- Quién hizo qué y cuándo
- IP addresses registradas
- Metadatos completos de archivos

### **4. Métricas**
- Contadores de registros procesados
- Tiempo de procesamiento
- Tasas de éxito/error

### **5. Integración con Modales**
- Logs de apertura de modales
- Acciones específicas en modales
- Mapeos y clasificaciones registradas

## 🔄 **Migraciones Requeridas**

Para implementar este sistema se necesitan crear las migraciones:

```bash
cd /root/SGM/backend
python manage.py makemigrations nomina
python manage.py migrate
```

## 📈 **Próximos Pasos**

1. **Implementar en Views**: Integrar los logs en todas las views existentes
2. **Actualizar APIs**: Modificar endpoints para usar el nuevo sistema
3. **Dashboard de Logs**: Crear interface para visualizar logs
4. **Alertas**: Sistema de notificaciones basado en logs
5. **Reportes**: Análisis de actividad por usuario/tarjeta

## 🔧 **Mantenimiento**

### **Índices Optimizados:**
- Por cierre y tarjeta
- Por usuario y timestamp
- Por resultado y fecha
- Por empleado y cierre

### **Limpieza Automática:**
- Configurar retención de logs (ej: 1 año)
- Archivado de logs antiguos
- Compresión de detalles JSON

Este sistema proporciona una base sólida para el tracking completo de actividades en el módulo de nómina, siguiendo las mejores prácticas implementadas en contabilidad.
