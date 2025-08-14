# 🚀 PLAN IMPLEMENTACIÓN PAYROLL - 12 HORAS

## 📋 **RESUMEN EJECUTIVO**
Sistema de comparación y validación automática de nóminas entre archivos Talana (oficial) y Analista, con detección de variaciones temporales e incidencias.

---

## 🏗️ **MODELO DE BASE DE DATOS**

### **Entidades Principales (8 + 1)**
```python
# ENTIDAD PRINCIPAL
class CierrePayroll(models.Model):
    cliente = ForeignKey(Cliente)
    usuario = ForeignKey(Usuario)  # quien creó
    periodo = CharField(max_length=7)  # 'YYYY-MM'
    estado = CharField(choices=[
        ('pendiente', 'Pendiente'),
        ('cargando_archivos', 'Cargando Archivos'),
        ('mapeando_columnas', 'Mapeando Columnas'),
        ('comparando_archivos', 'Comparando Archivos'),
        ('archivos_validados', 'Archivos Validados'),
        ('consolidando', 'Consolidando Datos'),
        ('datos_consolidados', 'Datos Consolidados'),
        ('analizando_variaciones', 'Analizando Variaciones'),
        ('incidencias_detectadas', 'Incidencias Detectadas'),
        ('revision_analista', 'Revisión Analista'),
        ('revision_supervisor', 'Revisión Supervisor'),
        ('aprobado', 'Aprobado'),
        ('finalizado', 'Finalizado'),
        ('error', 'Error')
    ])
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_completado = DateTimeField(null=True)
    total_empleados = IntegerField(default=0)
    monto_total = DecimalField(default=0)
    porcentaje_tolerancia = DecimalField(default=10.0)  # % para detectar variaciones

# DATOS CONSOLIDADOS (7 entidades del usuario)
class Empleados_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    rut_empleado = CharField(max_length=12)
    nombre_completo = CharField(max_length=200)
    estado_empleado = CharField(choices=[
        ('activo', 'Activo'),
        ('nuevo_ingreso', 'Nuevo Ingreso'),
        ('finiquito', 'Finiquito')
    ])
    fecha_ingreso = DateField(null=True)
    fecha_salida = DateField(null=True)

class Item_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    codigo_item = CharField(max_length=50)
    nombre_item = CharField(max_length=200)
    tipo_item = CharField(choices=[
        ('haberes', 'Haberes'),
        ('descuentos', 'Descuentos'),
        ('aportes', 'Aportes')
    ])

class Item_Empleado(models.Model):
    empleado_cierre = ForeignKey(Empleados_Cierre)
    item_cierre = ForeignKey(Item_Cierre)
    monto = DecimalField(max_digits=12, decimal_places=2)
    cantidad = DecimalField(max_digits=8, decimal_places=2, default=1)

class Finiquitos_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    empleado_cierre = ForeignKey(Empleados_Cierre)
    fecha_finiquito = DateField()
    motivo_salida = CharField(max_length=100)
    monto_finiquito = DecimalField(max_digits=12, decimal_places=2)

class Ingresos_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    empleado_cierre = ForeignKey(Empleados_Cierre)
    fecha_ingreso = DateField()
    tipo_contrato = CharField(max_length=50)
    sueldo_base = DecimalField(max_digits=12, decimal_places=2)

class Ausentismos_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    empleado_cierre = ForeignKey(Empleados_Cierre)
    tipo_ausentismo = CharField(max_length=50)
    fecha_inicio = DateField()
    fecha_fin = DateField()
    dias_ausentismo = IntegerField()

# INCIDENCIAS Y LOGS
class Incidencias_Cierre(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    item_empleado_actual = ForeignKey(Item_Empleado, related_name='incidencias_actual')
    item_empleado_anterior = ForeignKey(Item_Empleado, related_name='incidencias_anterior', null=True)
    tipo_incidencia = CharField(choices=[
        ('variacion_significativa', 'Variación Significativa'),
        ('empleado_nuevo', 'Empleado Nuevo'),
        ('empleado_salida', 'Empleado con Salida')
    ])
    valor_anterior = DecimalField(max_digits=12, decimal_places=2, null=True)
    valor_actual = DecimalField(max_digits=12, decimal_places=2)
    porcentaje_variacion = DecimalField(max_digits=5, decimal_places=2, null=True)
    estado_validacion = CharField(choices=[
        ('pendiente', 'Pendiente'),
        ('validada', 'Validada'),
        ('descartada', 'Descartada')
    ], default='pendiente')
    explicacion = TextField(blank=True)
    validado_por = ForeignKey(Usuario, null=True)
    fecha_validacion = DateTimeField(null=True)

class Logs_Comparacion(models.Model):
    cierre_payroll = ForeignKey(CierrePayroll)
    timestamp = DateTimeField(auto_now_add=True)
    usuario = ForeignKey(Usuario)
    accion = CharField(choices=[
        ('upload_archivos', 'Upload Archivos'),
        ('mapeo_columnas', 'Mapeo Columnas'),
        ('comparacion_archivos', 'Comparación Archivos'),
        ('consolidacion_datos', 'Consolidación Datos'),
        ('analisis_variaciones', 'Análisis Variaciones')
    ])
    resultado = CharField(choices=[
        ('exito', 'Éxito'),
        ('discrepancias', 'Discrepancias Encontradas'),
        ('error', 'Error')
    ])
    detalles = TextField()  # JSON con información detallada
```

---

## 🔄 **FLUJO COMPLETO DEL CIERRE**

### **FASE 1: CREACIÓN** ✅
```
Estado: pendiente
```
- Usuario crea cierre para cliente + período
- Validar que no existe cierre para ese período
- Inicializar estructuras base

### **FASE 2: COMPARACIÓN DE ARCHIVOS** ✅
```
Estados: cargando_archivos → mapeando_columnas → comparando_archivos → archivos_validados
```

#### **2.1 Upload de Archivos**
- Upload archivo Talana (oficial)
- Upload archivo Analista (verificación)
- Almacenar temporalmente en Redis

#### **2.2 Mapeo de Columnas**
- Detectar headers de ambos archivos
- Interface para mapear columnas: "¿Qué columna del analista corresponde a 'employee_id' de Talana?"
- Guardar mapeo en Redis

#### **2.3 Comparación**
- Task Celery para comparar ambos archivos
- Usar mapeo de columnas para comparación correcta
- Mostrar discrepancias en tiempo real (sin persistir en BD)
- Solo continuar si NO hay discrepancias

### **FASE 3: CONSOLIDACIÓN DE DATOS** ✅
```
Estados: consolidando → datos_consolidados
```
- Parsear **SOLO archivos Talana** (descartar analista)
- Crear registros en BD:
  - `Empleados_Cierre`, `Item_Empleado`, `Finiquitos_Cierre`, `Ingresos_Cierre`, `Ausentismos_Cierre`
- Limpiar datos temporales de Redis

### **FASE 4: COMPARACIÓN TEMPORAL** ✅
```
Estados: analizando_variaciones → incidencias_detectadas
```
- Buscar cierre anterior del mismo cliente
- Comparar `Item_Empleado` actual vs anterior
- Generar `Incidencias_Cierre` automáticas donde variación > tolerancia%
- Detectar empleados nuevos y salidas

### **FASE 5: REVISIÓN INCIDENCIAS** ⚠️ *COMPLEJA*
```
Estados: revision_analista → revision_supervisor → aprobado
```
- **Analista**: Primera revisión, explicar incidencias
- **Supervisor**: Validación final y aprobación
- Workflow de aprobación multinivel

### **FASE 6: FINALIZACIÓN** ✅
```
Estado: finalizado
```
- Generar reportes ejecutivos
- Bloquear modificaciones
- Limpiar datos temporales

---

## 🛠️ **ARQUITECTURA TÉCNICA**

### **Backend Components**
```
payroll/
├── models.py          # 9 modelos definidos arriba
├── views.py           # API endpoints
├── tasks.py           # Celery tasks para processing
├── parsers.py         # Parsers de archivos Excel/CSV  
├── comparators.py     # Lógica de comparación
└── utils.py           # Utilidades Redis y helpers
```

### **API Endpoints**
```python
# FASE 1
POST /api/payroll/cierres/crear/

# FASE 2  
POST /api/payroll/cierres/{id}/upload-archivos/
GET  /api/payroll/cierres/{id}/headers-archivos/
POST /api/payroll/cierres/{id}/mapear-y-comparar/
GET  /api/payroll/cierres/{id}/estado-comparacion/

# FASE 3
POST /api/payroll/cierres/{id}/consolidar/

# FASE 4
POST /api/payroll/cierres/{id}/analizar-variaciones/
GET  /api/payroll/cierres/{id}/incidencias/

# FASE 5
POST /api/payroll/cierres/{id}/incidencias/{inc_id}/validar/
POST /api/payroll/cierres/{id}/enviar-supervisor/
POST /api/payroll/cierres/{id}/aprobar/

# FASE 6
POST /api/payroll/cierres/{id}/finalizar/
```

### **Redis Structure**
```
cierre_{id}_archivo_talana: {data: [...], headers: [...]}
cierre_{id}_archivo_analista: {data: [...], headers: [...]}
cierre_{id}_mapeo_columnas: {"talana_col": "analista_col"}
cierre_{id}_discrepancias: [{empleado, campo, valor_talana, valor_analista}]
cierre_{id}_estado_proceso: "procesando|completado|error"
```

---

## ⏰ **PLAN DE IMPLEMENTACIÓN 12H**

### **Horas 1-3: Setup + Modelos**
- [ ] Crear app `payroll` en Django
- [ ] Implementar 9 modelos
- [ ] Migraciones
- [ ] Tests básicos de modelos

### **Horas 4-6: FASES 1-3**
- [ ] API endpoints básicos
- [ ] Upload y storage temporal
- [ ] Parsers Excel/CSV
- [ ] Mapeo de columnas
- [ ] Consolidación a BD

### **Horas 7-9: FASE 4**
- [ ] Lógica comparación temporal
- [ ] Algoritmo detección variaciones
- [ ] Generación automática incidencias

### **Horas 10-11: FASE 5 (MVP)**
- [ ] Interface revisión incidencias básica
- [ ] Validación simple (sin workflow complejo)

### **Hora 12: FASE 6 + DEMO**
- [ ] Finalización
- [ ] Frontend integration
- [ ] Demo preparation

---

## 🎯 **CRITERIOS DE ÉXITO**

### **MVP Funcional (12h)**
✅ Crear cierre payroll  
✅ Upload y comparar archivos  
✅ Consolidar datos Talana a BD  
✅ Detectar variaciones automáticas  
✅ Revisar incidencias básicas  
✅ Finalizar cierre  

### **Features Avanzadas (Post-MVP)**
- Workflow complejo analista-supervisor
- Reportes ejecutivos
- Integración directa API Talana
- Dashboard analytics avanzado

---

## 🚨 **RIESGOS Y MITIGACIONES**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Fase 5 muy compleja | Alta | Alto | Implementar versión simple primero |
| Parsers fallan | Media | Alto | Tests con archivos reales |
| Redis no configurado | Baja | Alto | Verificar setup temprano |
| Frontend integration | Media | Medio | Usar APIs existentes |

---

## ✅ **ESTADO ACTUAL**
- [x] Análisis completo del sistema
- [x] Modelo de datos definido  
- [x] Arquitectura técnica clara
- [x] Plan de implementación 12h
- [ ] **READY TO CODE** 🚀

**PRÓXIMO PASO: Implementar modelos y migraciones**
