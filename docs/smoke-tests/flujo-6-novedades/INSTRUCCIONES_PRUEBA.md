# 🧪 INSTRUCCIONES DE PRUEBA - FLUJO 6: NOVEDADES

**Objetivo:** Validar el procesamiento de archivo Excel con novedades de remuneraciones

**Duración estimada:** 30 minutos

---

## 📋 PRE-REQUISITOS

### 1. Sistema activo
```bash
# Backend Django + Celery workers
cd /root/SGM/backend
docker compose up -d

# Frontend (debe estar corriendo)
# Verificar en http://172.17.11.18:5174
```

### 2. Usuario autenticado
- **Rol:** Analista (mínimo)
- **Cliente asignado:** Cliente de prueba
- **Permisos:** Subir archivos de novedades

### 3. Cierre activo
- Estado: `abierto` o `en_proceso`
- Periodo: Octubre 2025 (o actual)
- Cliente: Asociado al usuario

---

## 🎯 PASO A PASO

### PASO 1: Generar Excel de Prueba

**Script Python:**

```python
# crear_excel_novedades.py
import pandas as pd
from datetime import datetime

# Datos de empleados (primeras 4 columnas fijas)
data = {
    'RUT': [
        '12345678-9',
        '98765432-1',
        '11111111-1',
        '22222222-2',
        '33333333-3',
        '44444444-4',
    ],
    'Nombre': [
        'Juan',
        'María',
        'Pedro',
        'Ana',
        'Carlos',
        'Sofía',
    ],
    'Apellido Paterno': [
        'Pérez',
        'González',
        'Rodríguez',
        'Martínez',
        'López',
        'Fernández',
    ],
    'Apellido Materno': [
        'Silva',
        'Muñoz',
        'Soto',
        'Rojas',
        'Torres',
        'Vega',
    ],
    # Conceptos de novedades (columnas dinámicas)
    'Sueldo Base': [
        500000,
        600000,
        550000,
        580000,
        520000,
        590000,
    ],
    'Bono Producción': [
        50000,
        75000,
        60000,
        0,
        45000,
        80000,
    ],
    'Gratificación': [
        100000,
        120000,
        110000,
        115000,
        105000,
        125000,
    ],
    'Colación': [
        30000,
        30000,
        30000,
        30000,
        30000,
        30000,
    ],
    'Movilización': [
        20000,
        20000,
        20000,
        20000,
        20000,
        20000,
    ],
}

df = pd.DataFrame(data)

# Guardar Excel
filename = f'/tmp/novedades_prueba_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
df.to_excel(filename, index=False, engine='openpyxl')

print(f"✅ Archivo creado: {filename}")
print(f"📊 Empleados: {len(df)}")
print(f"💰 Conceptos: {len(df.columns) - 4}")
print(f"\nPrimeras filas:")
print(df.head(2))
```

**Ejecutar:**
```bash
cd /root/SGM/backend
python manage.py shell < crear_excel_novedades.py
```

**Resultado esperado:**
```
✅ Archivo creado: /tmp/novedades_prueba_20251027_XXXXXX.xlsx
📊 Empleados: 6
💰 Conceptos: 5
```

---

### PASO 2: Subir Archivo desde Frontend

1. **Navegar a Cierre**
   - URL: `http://172.17.11.18:5174/cierres/{cierre_id}`
   - Verificar que el cierre esté `abierto`

2. **Ir a sección Novedades**
   - Buscar tarjeta o tab "Novedades"
   - Verificar estado: "No subido" o "Pendiente"

3. **Subir archivo**
   - Click en "Subir Archivo de Novedades"
   - Seleccionar `/tmp/novedades_prueba_XXXXXX.xlsx`
   - Esperar respuesta (task_id)

**Verificación:**
```bash
# En logs de Celery
docker compose logs celery_worker -f | grep -i "novedad"

# Esperado:
# "analizar_headers_archivo_novedades iniciado"
# "clasificar_headers_archivo_novedades iniciado"
# "Headers encontrados: ['Sueldo Base', 'Bono Producción', ...]"
```

---

### PASO 3: Verificar Análisis y Clasificación (Automático)

**En Frontend:**
- Debería ver estado actualizado:
  - `hdrs_analizados` → `clasificado` (si todos los headers tienen mapeo)
  - `hdrs_analizados` → `clasif_pendiente` (si hay headers sin mapeo)

**En logs:**
```bash
docker compose logs celery_worker -f | tail -50

# Buscar:
# "Clasificación automática novedades: X mapeados, Y sin mapear"
```

**Si hay headers sin clasificar:**
- Usar endpoint `/mapear_headers/` para mapeo manual
- O configurar mapeos en `ConceptoRemuneracionNovedades` antes de resubir

---

### PASO 4: Procesar Archivo

**En Frontend:**
1. Click en "Procesar Novedades"
2. Esperar confirmación de task iniciada
3. Monitorear progreso (si hay barra de progreso)

**Verificación en logs:**
```bash
docker compose logs celery_worker -f

# Esperado:
# "Procesando archivo novedades con usuario: X"
# "actualizar_empleados_desde_novedades iniciado"
# "Empleados creados: 6, actualizados: 0"
# "guardar_registros_novedades iniciado"
# "Registros guardados: 30" (6 empleados × 5 conceptos)
# "Procesamiento de novedades completado"
```

---

### PASO 5: Verificar Resultados en Base de Datos

**Script de verificación:**

```python
# verificar_novedades.py
from nomina.models import (
    ArchivoNovedadesUpload,
    EmpleadoCierreNovedades,
    RegistroConceptoEmpleadoNovedades,
    ActivityEvent
)
from nomina.models_logging import TarjetaActivityLogNomina

# Obtener último archivo de novedades
archivo = ArchivoNovedadesUpload.objects.latest('fecha_subida')

print("="*70)
print("📄 ARCHIVO DE NOVEDADES")
print("="*70)
print(f"ID: {archivo.id}")
print(f"Estado: {archivo.estado}")
print(f"Cierre: {archivo.cierre.id} - {archivo.cierre.periodo}")
print(f"Analista: {archivo.analista.correo_bdo if archivo.analista else 'N/A'}")
print(f"Fecha subida: {archivo.fecha_subida}")
print()

# Headers
print("="*70)
print("🔖 HEADERS")
print("="*70)
if isinstance(archivo.header_json, dict):
    clasificados = archivo.header_json.get('headers_clasificados', [])
    sin_clasificar = archivo.header_json.get('headers_sin_clasificar', [])
    print(f"✅ Clasificados: {len(clasificados)}")
    for h in clasificados:
        print(f"   - {h}")
    print(f"⚠️  Sin clasificar: {len(sin_clasificar)}")
    for h in sin_clasificar:
        print(f"   - {h}")
else:
    print(f"Headers (list): {archivo.header_json}")
print()

# Empleados
print("="*70)
print("👤 EMPLEADOS")
print("="*70)
empleados = EmpleadoCierreNovedades.objects.filter(cierre=archivo.cierre)
print(f"Total: {empleados.count()}")
for emp in empleados[:3]:  # Primeros 3
    print(f"  - {emp.rut}: {emp.nombre} {emp.apellido_paterno} {emp.apellido_materno}")
if empleados.count() > 3:
    print(f"  ... y {empleados.count() - 3} más")
print()

# Registros de conceptos
print("="*70)
print("💰 REGISTROS DE CONCEPTOS")
print("="*70)
registros = RegistroConceptoEmpleadoNovedades.objects.filter(
    empleado__cierre=archivo.cierre
)
print(f"Total: {registros.count()}")
# Mostrar algunos ejemplos
for reg in registros[:5]:
    concepto_nombre = reg.concepto.nombre_concepto_novedades if reg.concepto else 'N/A'
    print(f"  - {reg.empleado.rut}: {concepto_nombre} = {reg.valor_novedades}")
if registros.count() > 5:
    print(f"  ... y {registros.count() - 5} más")
print()

# Logging: TarjetaActivityLogNomina
print("="*70)
print("📋 TARJETA ACTIVITY LOG")
print("="*70)
logs_tarjeta = TarjetaActivityLogNomina.objects.filter(
    cierre=archivo.cierre,
    tarjeta='novedades'
).order_by('-fecha')
print(f"Total eventos: {logs_tarjeta.count()}")
for log in logs_tarjeta[:5]:
    print(f"  - {log.accion}: {log.titulo} (Usuario: {log.usuario.correo_bdo if log.usuario else 'Sistema'})")
print()

# Logging: ActivityEvent
print("="*70)
print("🔍 ACTIVITY EVENTS (Audit Trail)")
print("="*70)
events = ActivityEvent.objects.filter(
    cierre_nomina=archivo.cierre,
    resource_type='archivo_novedades'
).order_by('-timestamp')
print(f"Total eventos: {events.count()}")
for event in events[:5]:
    print(f"  - {event.action}: {event.message} (Usuario: {event.user.correo_bdo if event.user else 'Sistema'})")
print()

# VERIFICACIONES
print("="*70)
print("✅ VERIFICACIONES")
print("="*70)

checks = []

# 1. Archivo procesado
checks.append(("Archivo procesado sin errores", archivo.estado == 'procesado'))

# 2. Empleados creados
empleados_count = empleados.count()
checks.append(("Empleados creados (6 esperados)", empleados_count == 6))

# 3. Registros creados
registros_count = registros.count()
registros_esperados = 6 * 5  # 6 empleados × 5 conceptos
checks.append((f"Registros creados ({registros_esperados} esperados)", registros_count == registros_esperados))

# 4. Logging Tarjeta
logs_tarjeta_count = logs_tarjeta.count()
checks.append(("Logging TarjetaActivityLogNomina (>=2 eventos)", logs_tarjeta_count >= 2))

# 5. Logging ActivityEvent
events_count = events.count()
checks.append(("Logging ActivityEvent (>=2 eventos)", events_count >= 2))

# 6. Headers clasificados
if isinstance(archivo.header_json, dict):
    headers_ok = len(archivo.header_json.get('headers_clasificados', [])) > 0
    checks.append(("Headers clasificados", headers_ok))

# Imprimir resultados
total_checks = len(checks)
passed_checks = sum(1 for _, result in checks if result)

for desc, result in checks:
    icon = "✅" if result else "❌"
    print(f"{icon} {desc}")

print()
print("="*70)
print(f"RESULTADO FINAL: {passed_checks}/{total_checks} verificaciones pasadas")
if passed_checks == total_checks:
    print("🎉 FLUJO 6 (NOVEDADES) - EXITOSO")
else:
    print("⚠️  Algunas verificaciones fallaron - Revisar logs")
print("="*70)
```

**Ejecutar:**
```bash
cd /root/SGM/backend
python manage.py shell < verificar_novedades.py
```

**Resultado esperado:**
```
✅ Archivo procesado sin errores
✅ Empleados creados (6 esperados)
✅ Registros creados (30 esperados)
✅ Logging TarjetaActivityLogNomina (>=2 eventos)
✅ Logging ActivityEvent (>=2 eventos)
✅ Headers clasificados

RESULTADO FINAL: 6/6 verificaciones pasadas
🎉 FLUJO 6 (NOVEDADES) - EXITOSO
```

---

## 🐛 TROUBLESHOOTING

### Error: "Headers sin clasificar"

**Problema:** Algunos headers no tienen mapeo en `ConceptoRemuneracionNovedades`

**Solución:**
```python
# Crear mapeos manualmente
from nomina.models import ConceptoRemuneracionNovedades, Cliente, ConceptoRemuneracion

cliente = Cliente.objects.get(id=CLIENTE_ID)

# Para cada header sin clasificar:
ConceptoRemuneracionNovedades.objects.create(
    cliente=cliente,
    nombre_concepto_novedades='Nombre del Header',
    concepto_libro=None,  # O mapear a un ConceptoRemuneracion existente
    usuario_mapea=None
)
```

### Error: "Archivo no encontrado"

**Problema:** El archivo Excel no se guardó correctamente

**Solución:**
- Verificar que existe en `/media/novedades/`
- Revisar permisos del directorio
- Resubir el archivo

### Logs no aparecen

**Problema:** Workers de Celery no están corriendo

**Solución:**
```bash
docker compose logs celery_worker -f
# Verificar que el worker esté activo

# Reiniciar si es necesario
docker compose restart celery_worker
```

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Valor Esperado | Verificación |
|---------|----------------|--------------|
| **Estado archivo** | `procesado` | ✅ archivo.estado |
| **Empleados** | 6 | ✅ EmpleadoCierreNovedades.count() |
| **Conceptos** | 5 | ✅ len(header_json) |
| **Registros** | 30 (6×5) | ✅ RegistroConceptoEmpleadoNovedades.count() |
| **Logs Tarjeta** | ≥2 | ✅ TarjetaActivityLogNomina.count() |
| **Logs Audit** | ≥2 | ✅ ActivityEvent.count() |

---

## ✅ CHECKLIST FINAL

- [ ] Excel generado con 6 empleados y 5 conceptos
- [ ] Archivo subido exitosamente
- [ ] Headers analizados y clasificados
- [ ] Archivo procesado sin errores
- [ ] 6 empleados creados en `EmpleadoCierreNovedades`
- [ ] 30 registros creados en `RegistroConceptoEmpleadoNovedades`
- [ ] Logging dual completo (TarjetaActivityLogNomina + ActivityEvent)
- [ ] Estado final = `procesado`
- [ ] Script de verificación ejecutado: 6/6 checks ✅

---

**Flujo 6 completado:** ✅  
**Tiempo total:** ~30 minutos  
**Resultado:** Sistema validado para novedades de remuneraciones
