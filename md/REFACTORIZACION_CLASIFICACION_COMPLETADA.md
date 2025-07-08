# FLUJO REFACTORIZADO DE CLASIFICACIÓN - DOCUMENTACIÓN

## ✅ PROBLEMA SOLUCIONADO

**Antes**: El flujo de clasificación intentaba mapear inmediatamente con `CuentaContable` que aún no existían, causando errores y inconsistencias.

**Ahora**: Se almacenan datos RAW primero, y el mapeo ocurre después cuando las cuentas ya fueron creadas por el libro mayor.

## 🔄 NUEVO FLUJO COMPLETO

### 1. **Subida de Archivo de Clasificación**
```
Usuario sube: clasificacion_cliente_12345678_202406.xlsx
┌─────────────────────────────────────────────────────────┐
│ Código Cuenta │ Set Activos │ Set Pasivos │ Set Sector │
├─────────────────────────────────────────────────────────┤
│ 1101          │ Corriente   │            │ Comercial  │
│ 1102          │ No Corriente│            │ Industrial │
│ 2101          │             │ Corriente  │ Servicios  │
└─────────────────────────────────────────────────────────┘
```

**Chain de Tasks Ejecutadas:**
1. `validar_nombre_archivo_clasificacion_task` → Valida convenciones de nombre
2. `verificar_archivo_temporal_clasificacion_task` → Verifica archivo y calcula hash
3. `validar_contenido_clasificacion_excel_task` → Validaciones exhaustivas
4. `procesar_datos_clasificacion_task` → **ALMACENA DATOS RAW**
5. `guardar_archivo_clasificacion_task` → Guarda archivo final
6. `finalizar_procesamiento_clasificacion_task` → Limpia temporales

**Resultado**: Datos almacenados en `ClasificacionCuentaArchivo`:
```python
ClasificacionCuentaArchivo.objects.create(
    cliente=cliente,
    upload_log=upload_log,
    numero_cuenta="1101",  # STRING - No FK
    clasificaciones={      # JSON - Datos RAW
        "Set Activos": "Corriente",
        "Set Sector": "Comercial"
    },
    procesado=False,  # 🔑 Pendiente de mapeo
    fila_excel=2
)
```

### 2. **Subida de Libro Mayor** 
```
Usuario sube: libro_mayor_cliente_12345678_202406.xlsx
- Se crean las CuentaContable reales
- Al FINAL del procesamiento se ejecuta automáticamente:
```

**Mapeo Automático Ejecutado:**
```python
mapear_clasificaciones_con_cuentas.delay(cliente_id, cierre_id)
```

### 3. **Proceso de Mapeo Automático**

**A. Creación de Sets y Opciones:**
```python
# Desde datos RAW se extraen automáticamente:
ClasificacionSet.objects.create(
    cliente=cliente,
    nombre="Set Activos",
    descripcion="Set generado automáticamente desde datos RAW"
)

ClasificacionOption.objects.create(
    set_clas=set_activos,
    valor="Corriente",
    descripcion="Opción generada automáticamente: Corriente"
)
```

**B. Mapeo con Cuentas Reales:**
```python
# Para cada registro RAW:
cuenta = CuentaContable.objects.get(codigo="1101", cliente=cliente)  # ✅ Ahora existe
set_activos = ClasificacionSet.objects.get(nombre="Set Activos", cliente=cliente)
opcion_corriente = ClasificacionOption.objects.get(set_clas=set_activos, valor="Corriente")

AccountClassification.objects.create(
    cuenta=cuenta,           # ✅ FK válida
    set_clas=set_activos,    # ✅ FK válida  
    opcion=opcion_corriente, # ✅ FK válida
    asignado_por=None        # Sistema automático
)

# Marcar como procesado
registro_raw.procesado = True
registro_raw.save()
```

## 📊 ESTADOS Y TRAZABILIDAD

### Estados de UploadLog (Clasificación):
```
subido → validando_nombre → verificando_archivo → validando_contenido → 
procesando_datos → guardando_archivo → completado
```

### Estados de ClasificacionCuentaArchivo:
- `procesado=False` → Datos RAW almacenados, pendiente mapeo
- `procesado=True` → Mapeado exitosamente con cuentas reales

### Actividades Registradas:
1. **"upload_excel"** → Archivo subido
2. **"process_excel"** → Datos RAW almacenados
3. **"mapeo_clasificaciones"** → Mapeo realizado automáticamente

## 🛠 FUNCIONES PRINCIPALES

### Nuevas Tasks Especializadas:
- **`mapear_clasificaciones_con_cuentas(cliente_id, cierre_id=None)`**
  - Se ejecuta automáticamente después del libro mayor
  - Crea sets/opciones desde datos RAW
  - Mapea con cuentas existentes
  - Marca registros como procesados

- **`crear_sets_y_opciones_clasificacion_desde_raw(cliente_id)`**
  - Crea ClasificacionSet y ClasificacionOption desde datos RAW
  - Se ejecuta como parte del mapeo

### Función Legacy (Deprecated):
- **`crear_sets_y_opciones_clasificacion(upload_log_id)`**
  - Mantenida por compatibilidad
  - Redirige a la nueva función

## ⚡ BENEFICIOS

1. **✅ Eliminación de Errores FK**: No más intentos de mapear con cuentas inexistentes
2. **✅ Consistencia**: Mapeo solo cuando ambos elementos existen
3. **✅ Trazabilidad**: Estado claro de qué está pendiente de mapear
4. **✅ Robustez**: Fallos en mapeo no afectan subida de libro mayor
5. **✅ Escalabilidad**: Mapeo puede ejecutarse en worker separado
6. **✅ Flexibilidad**: Posibilidad de remapear si es necesario

## 🔧 ARCHIVOS MODIFICADOS

### Creados:
- **`/backend/contabilidad/tasks_cuentas_bulk.py`** → Tasks especializadas de clasificación

### Modificados:
- **`/backend/contabilidad/views/clasificacion.py`** → Vista simplificada usando chains
- **`/backend/contabilidad/tasks.py`** → Agregado mapeo automático en libro mayor

### Eliminados:
- Funciones monolíticas de clasificación en `tasks.py`

## 📝 TESTING

Para probar el nuevo flujo:

1. **Subir archivo de clasificación** → Verificar datos RAW almacenados
2. **Subir libro mayor** → Verificar cuentas creadas + mapeo automático
3. **Revisar AccountClassification** → Verificar FK correctas
4. **Verificar logs de actividad** → Trazabilidad completa

El flujo ahora es **robusto, escalable y consistente** con el patrón de chains implementado en tipo de documento.
