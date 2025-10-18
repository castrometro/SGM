# 🔄 ¿Qué es la CONSOLIDACIÓN en SGM?

**Fecha**: 17 de octubre de 2025  
**Sistema**: SGM Nómina - Sistema de Gestión de Nóminas  

---

## 🎯 Definición Simple

**Consolidación** es el proceso de **juntar toda la información dispersa en múltiples archivos Excel** y crear una **vista única y ordenada** de la nómina de cada empleado.

Es como hacer un **resumen ejecutivo** de todos los datos que se subieron por separado.

---

## 📚 El Problema que Resuelve

### **Entrada: Múltiples Archivos Excel Dispersos**

Un cierre de nómina típico tiene:

```
📖 Libro de Remuneraciones           [libro_remuneraciones.xlsx]
   └─ 150 empleados × 80 columnas = 12,000 celdas
   └─ Columnas: RUT, Nombre, Cargo, Sueldo Base, Horas Extras, 
                Gratificación, Bono, AFP, Salud, Líquido, etc.

📅 Movimientos del Mes               [movimientos_mes.xlsx]
   └─ Cambios: Ingresos, Finiquitos, Cambios de cargo, etc.
   └─ 15 registros de movimientos

📋 Archivos Analista                 [incidencias.xlsx, ingresos.xlsx]
   └─ Información adicional: Ausencias, Licencias médicas
   └─ 25 registros de incidencias

🆕 Novedades                          [novedades.xlsx]
   └─ Bonos especiales, Aguinaldos, Descuentos puntuales
   └─ 50 registros de novedades
```

**Problema**: ¿Cómo sé cuánto gana realmente Juan Pérez este mes?
- Está en el Libro con su sueldo base ✅
- Tuvo 3 días de ausencia (Analista) ⚠️
- Le pagaron un bono especial (Novedades) 💰
- Fue promovido (Movimientos) 📈

**Solución**: **CONSOLIDACIÓN** → Junta todo en un solo lugar

---

## 🔄 Flujo de Consolidación

```
┌──────────────────────────────────────────────────────┐
│  FASE 1: CARGA DE ARCHIVOS                          │
├──────────────────────────────────────────────────────┤
│  ✅ Libro de Remuneraciones subido                   │
│  ✅ Movimientos del Mes subido                       │
│  ✅ Archivos Analista subidos                        │
│  ✅ Novedades subidas                                │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│  FASE 2: VALIDACIÓN                                  │
├──────────────────────────────────────────────────────┤
│  ✅ Headers clasificados (analizar + clasificar)     │
│  ✅ Sin discrepancias de datos                       │
│  ✅ Estado: archivos_completos                       │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│  FASE 3: CONSOLIDACIÓN ⚡                            │
├──────────────────────────────────────────────────────┤
│  🔄 Tarea Celery: consolidar_datos_nomina_task()    │
│                                                      │
│  Paso 1: Crear NominaConsolidada                    │
│     └─ Un registro por empleado                     │
│                                                      │
│  Paso 2: Crear HeaderValorEmpleado                  │
│     └─ Todas las columnas del Excel                 │
│                                                      │
│  Paso 3: Crear ConceptoConsolidado                  │
│     └─ Agregar conceptos (sumar montos)             │
│                                                      │
│  Paso 4: Crear MovimientoPersonal                   │
│     └─ Detectar ausencias, ingresos, finiquitos     │
│                                                      │
│  Estado final: datos_consolidados ✅                │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│  FASE 4: RESULTADO                                   │
├──────────────────────────────────────────────────────┤
│  ✅ Vista unificada por empleado                     │
│  ✅ Totales calculados                               │
│  ✅ Listo para reportes                              │
└──────────────────────────────────────────────────────┘
```

---

## 🗄️ Modelos de Consolidación (La Base de Datos)

### **1. NominaConsolidada** (El Maestro)

**Propósito**: Un registro por empleado con su información general y totales

```python
NominaConsolidada:
    cierre = CierreNomina(30)
    rut_empleado = "12345678-9"
    nombre_empleado = "Juan Pérez García"
    cargo = "Ingeniero Senior"
    centro_costo = "TI"
    estado_empleado = "activo"
    
    # 💰 TOTALES CONSOLIDADOS
    haberes_imponibles = 1,500,000      # Sueldo base + comisiones
    haberes_no_imponibles = 200,000      # Colación + movilización
    dctos_legales = 220,000              # AFP + Salud
    otros_dctos = 50,000                 # Préstamo empresa
    impuestos = 45,000                   # Impuesto único
    horas_extras_cantidad = 10.5         # Horas
    aportes_patronales = 180,000         # Aporte empleador
    
    dias_trabajados = 30
    dias_ausencia = 0
```

**Responde**: "Dame todos los empleados de este cierre con sus totales"

---

### **2. HeaderValorEmpleado** (El Detalle Excel)

**Propósito**: Cada celda del Excel guardada 1:1

```python
# Juan Pérez tiene 80 HeaderValorEmpleado (uno por columna)

HeaderValorEmpleado:
    nomina_consolidada = Juan Pérez
    nombre_header = "SUELDO BASE"
    valor_original = "1200000"
    valor_numerico = 1200000.00
    es_numerico = True
    columna_excel = "D"
    fila_excel = 15

HeaderValorEmpleado:
    nomina_consolidada = Juan Pérez
    nombre_header = "HORAS EXTRAS 50%"
    valor_original = "10.5"
    valor_numerico = 10.50
    es_numerico = True
    columna_excel = "M"
    fila_excel = 15

HeaderValorEmpleado:
    nomina_consolidada = Juan Pérez
    nombre_header = "CARGO"
    valor_original = "Ingeniero Senior"
    valor_numerico = None
    es_numerico = False
    columna_excel = "C"
    fila_excel = 15
```

**Responde**: "Muéstrame TODOS los datos del Excel de Juan Pérez"

---

### **3. ConceptoConsolidado** (Los Conceptos Agrupados)

**Propósito**: Agrupar conceptos similares y sumar montos

```python
# Juan Pérez tiene varios conceptos consolidados

ConceptoConsolidado:
    nomina_consolidada = Juan Pérez
    nombre_concepto = "Sueldo Base"
    tipo_concepto = "haber_imponible"
    monto_total = 1,200,000
    cantidad = 1
    fuente_archivo = "libro"

ConceptoConsolidado:
    nomina_consolidada = Juan Pérez
    nombre_concepto = "Horas Extras 50%"
    tipo_concepto = "haber_imponible"
    monto_total = 150,000
    cantidad = 10.5
    fuente_archivo = "libro"

ConceptoConsolidado:
    nomina_consolidada = Juan Pérez
    nombre_concepto = "Bono Especial Navidad"
    tipo_concepto = "haber_no_imponible"
    monto_total = 200,000
    cantidad = 1
    fuente_archivo = "novedades"
```

**Responde**: "Dame el resumen de conceptos de Juan Pérez"

---

### **4. MovimientoPersonal** (Los Eventos)

**Propósito**: Detectar ausencias, ingresos, finiquitos automáticamente

```python
# Juan Pérez tiene movimientos detectados

MovimientoPersonal:
    nomina_consolidada = Juan Pérez
    categoria = "ausencia"
    subtipo = "vacaciones"
    fecha_inicio = 2025-06-10
    fecha_fin = 2025-06-17
    dias_evento = 8
    dias_en_periodo = 8
    descripcion = "Vacaciones programadas"
    detectado_por_sistema = "consolidacion_paralela_v2"

MovimientoPersonal:
    nomina_consolidada = Juan Pérez
    categoria = "cambio_datos"
    subtipo = "promocion"
    fecha_inicio = 2025-06-01
    descripcion = "Promoción a Ingeniero Senior"
    detectado_por_sistema = "movimientos_mes"
```

**Responde**: "¿Qué eventos tuvo Juan Pérez este mes?"

---

## 📊 Ejemplo Visual: Antes y Después

### **ANTES de Consolidar**:

```
Archivo: libro_remuneraciones.xlsx
┌──────────┬────────────────┬───────────┬──────────┬──────────┬─────┐
│ RUT      │ Nombre         │ Sueldo    │ AFP      │ Salud    │ ... │
├──────────┼────────────────┼───────────┼──────────┼──────────┼─────┤
│ 12345678 │ Juan Pérez     │ 1,200,000 │ 120,000  │ 100,000  │ ... │
└──────────┴────────────────┴───────────┴──────────┴──────────┴─────┘

Archivo: novedades.xlsx
┌──────────┬────────────────┬──────────────────┬─────────┐
│ RUT      │ Nombre         │ Concepto         │ Monto   │
├──────────┼────────────────┼──────────────────┼─────────┤
│ 12345678 │ Juan Pérez     │ Bono Navidad     │ 200,000 │
└──────────┴────────────────┴──────────────────┴─────────┘

Archivo: incidencias_analista.xlsx
┌──────────┬────────────────┬──────────┬──────────┬──────┐
│ RUT      │ Nombre         │ Inicio   │ Fin      │ Días │
├──────────┼────────────────┼──────────┼──────────┼──────┤
│ 12345678 │ Juan Pérez     │ 10/06    │ 17/06    │ 8    │
└──────────┴────────────────┴──────────┴──────────┴──────┘

❌ Problema: ¿Cuánto gana Juan? ¿Tuvo ausencias? ¿Hay bonos?
   → Hay que buscar en 3+ archivos
```

### **DESPUÉS de Consolidar**:

```sql
-- Query: Dame TODO de Juan Pérez
SELECT * FROM nomina_consolidada 
WHERE rut_empleado = '12345678-9' AND cierre_id = 30;

┌─────────────────────────────────────────────────────────┐
│ 👤 JUAN PÉREZ GARCÍA (12345678-9)                      │
├─────────────────────────────────────────────────────────┤
│ Cargo: Ingeniero Senior                                 │
│ Estado: Activo                                          │
│                                                         │
│ 💰 TOTALES:                                            │
│   Haberes Imponibles:     $1,500,000                   │
│   Haberes No Imponibles:    $200,000                   │
│   Descuentos Legales:       $220,000                   │
│   Líquido:                $1,480,000                   │
│                                                         │
│ 📋 CONCEPTOS (3):                                      │
│   - Sueldo Base:          $1,200,000                   │
│   - Horas Extras 50%:       $150,000 (10.5 hrs)       │
│   - Bono Navidad:           $200,000                   │
│                                                         │
│ 🔄 MOVIMIENTOS (2):                                    │
│   - Vacaciones: 10/06-17/06 (8 días)                  │
│   - Promoción a Ingeniero Senior                       │
│                                                         │
│ 📊 HEADERS EXCEL (80 columnas guardadas)              │
└─────────────────────────────────────────────────────────┘

✅ Todo en un solo lugar, sin buscar en múltiples archivos
```

---

## ⚡ Proceso Técnico de Consolidación

### **Task Celery: `consolidar_datos_nomina_task(cierre_id)`**

```python
# backend/nomina/tasks.py (línea ~2252)

@shared_task
def consolidar_datos_nomina_task_optimizado(cierre_id):
    """
    🔄 CONSOLIDACIÓN OPTIMIZADA
    
    Junta toda la información de:
    - Libro de Remuneraciones (base)
    - Movimientos del Mes
    - Archivos Analista
    - Novedades
    
    Y crea:
    - NominaConsolidada (maestro por empleado)
    - HeaderValorEmpleado (todas las celdas)
    - ConceptoConsolidado (conceptos agrupados)
    - MovimientoPersonal (eventos detectados)
    """
    
    # 1. Obtener libro de remuneraciones
    libro = LibroRemuneracionesUpload.objects.get(cierre_id=cierre_id)
    df = pd.read_excel(libro.archivo.path)
    
    # 2. Por cada empleado en el Excel:
    for index, row in df.iterrows():
        rut = row['RUT']
        nombre = row['NOMBRE']
        
        # 2.1 Crear NominaConsolidada (maestro)
        nomina = NominaConsolidada.objects.create(
            cierre_id=cierre_id,
            rut_empleado=rut,
            nombre_empleado=nombre,
            haberes_imponibles=0,  # Se calculará después
            # ... otros campos
        )
        
        # 2.2 Guardar TODAS las columnas del Excel
        for columna, valor in row.items():
            HeaderValorEmpleado.objects.create(
                nomina_consolidada=nomina,
                nombre_header=columna,
                valor_original=str(valor),
                valor_numerico=valor if es_numero(valor) else None,
                es_numerico=es_numero(valor)
            )
        
        # 2.3 Agrupar conceptos (sumar montos por tipo)
        conceptos = extraer_conceptos(row)
        for concepto in conceptos:
            ConceptoConsolidado.objects.create(
                nomina_consolidada=nomina,
                nombre_concepto=concepto['nombre'],
                tipo_concepto=concepto['tipo'],
                monto_total=concepto['monto']
            )
        
        # 2.4 Detectar movimientos (ausencias, etc.)
        movimientos = detectar_movimientos(rut, cierre_id)
        for mov in movimientos:
            MovimientoPersonal.objects.create(
                nomina_consolidada=nomina,
                categoria=mov['categoria'],
                subtipo=mov['subtipo'],
                fecha_inicio=mov['fecha_inicio'],
                # ...
            )
    
    # 3. Actualizar estado del cierre
    cierre.estado_consolidacion = 'consolidado'
    cierre.puede_consolidar = True
    cierre.fecha_consolidacion = timezone.now()
    cierre.save()
```

---

## 🎯 ¿Por Qué es Importante?

### **Sin Consolidación**:
- ❌ Datos dispersos en múltiples archivos
- ❌ Imposible generar reportes unificados
- ❌ No se pueden detectar incidencias
- ❌ No se pueden comparar períodos
- ❌ Difícil de auditar

### **Con Consolidación**:
- ✅ Vista única por empleado
- ✅ Reportes rápidos (un solo query)
- ✅ Detección automática de incidencias
- ✅ Comparación entre períodos fácil
- ✅ Auditoría completa

---

## 📈 Métricas de Consolidación

Para un cierre típico de **150 empleados**:

```
Entrada:
├─ Libro Remuneraciones: 150 filas × 80 columnas = 12,000 celdas
├─ Movimientos: 15 registros
├─ Incidencias: 25 registros
└─ Novedades: 50 registros

Salida Consolidada:
├─ NominaConsolidada: 150 registros (1 por empleado)
├─ HeaderValorEmpleado: 12,000 registros (todas las celdas)
├─ ConceptoConsolidado: ~600 registros (conceptos únicos)
└─ MovimientoPersonal: ~80 registros (eventos detectados)

Tiempo de procesamiento: 30-60 segundos
```

---

## 🔍 Queries Útiles Post-Consolidación

### **1. Total de Haberes Imponibles del Cierre**:
```python
total = NominaConsolidada.objects.filter(
    cierre_id=30
).aggregate(
    total=Sum('haberes_imponibles')
)['total']

# Resultado: $225,000,000
```

### **2. Empleados con Ausencias**:
```python
ausentes = NominaConsolidada.objects.filter(
    cierre_id=30,
    dias_ausencia__gt=0
).count()

# Resultado: 25 empleados
```

### **3. Conceptos Más Pagados**:
```python
top_conceptos = ConceptoConsolidado.objects.filter(
    nomina_consolidada__cierre_id=30
).values('nombre_concepto').annotate(
    total=Sum('monto_total')
).order_by('-total')[:10]

# Resultado:
# [{'nombre_concepto': 'Sueldo Base', 'total': 180000000},
#  {'nombre_concepto': 'Horas Extras', 'total': 25000000},
#  ...]
```

---

## 🚀 Estados del Cierre Relacionados

```
pendiente
    ↓
cargando_archivos  (subiendo Excels)
    ↓
archivos_completos (todos los archivos listos)
    ↓
🔄 CONSOLIDACIÓN  (ejecutando consolidar_datos_nomina_task)
    ↓
datos_consolidados ✅ (listo para análisis)
    ↓
verificacion_datos (revisando incidencias)
    ↓
finalizado
```

---

## 📝 Resumen Ejecutivo

| Concepto | Descripción |
|----------|-------------|
| **¿Qué es?** | Juntar datos de múltiples Excels en una vista unificada |
| **¿Cuándo?** | Después de subir todos los archivos (estado: archivos_completos) |
| **¿Cómo?** | Tarea Celery: `consolidar_datos_nomina_task()` |
| **¿Resultado?** | 4 tablas pobladas: NominaConsolidada, HeaderValorEmpleado, ConceptoConsolidado, MovimientoPersonal |
| **¿Beneficio?** | Reportes rápidos, análisis fácil, detección de incidencias |
| **¿Tiempo?** | 30-60 segundos para 150 empleados |

---

## 🎯 Analogía Simple

**Consolidación es como hacer un resumen de tus gastos mensuales**:

```
Entradas dispersas:
- Boleta supermercado: $50,000
- Boleta restaurant: $15,000
- Boleta farmacia: $8,000
- Tarjeta crédito: $200,000
- Transferencia arriendo: $400,000

↓ CONSOLIDACIÓN ↓

Resumen del mes:
┌────────────────────┬───────────┐
│ Categoría          │ Total     │
├────────────────────┼───────────┤
│ Alimentación       │ $65,000   │
│ Salud              │ $8,000    │
│ Vivienda           │ $400,000  │
│ Varios             │ $200,000  │
├────────────────────┼───────────┤
│ TOTAL GASTOS       │ $673,000  │
└────────────────────┴───────────┘

✅ Ahora sé cuánto gasté en cada categoría sin buscar boletas
```

---

**¿Quedó claro?** La consolidación es el **corazón** del sistema SGM. Sin ella, no hay reportes, no hay análisis, no hay incidencias. 🎯
