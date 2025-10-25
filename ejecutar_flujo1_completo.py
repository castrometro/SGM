"""
Script para ejecutar el FLUJO 1: Libro de Remuneraciones completo
Documenta cada paso y registra qué funciones se llaman
"""
import os
import sys
import django
import time
from pathlib import Path

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from django.core.files import File
from nomina.models import (
    CierreNomina, 
    LibroRemuneracionesUpload,
    EmpleadoCierre,
    RegistroConceptoEmpleado
)
from nomina.tasks import (
    analizar_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
)

# Leer info del entorno
info = {}
with open('/tmp/smoke_test_info.txt', 'r') as f:
    for line in f:
        key, value = line.strip().split('=')
        info[key] = int(value) if value.isdigit() else value

print("=" * 80)
print("FLUJO 1: LIBRO DE REMUNERACIONES - SMOKE TEST")
print("=" * 80)
print(f"Cliente ID: {info['CLIENTE_ID']}")
print(f"Cierre ID: {info['CIERRE_ID']}")
print(f"Usuario ID: {info['USUARIO_ID']}")
print(f"Periodo: {info['PERIODO']}")
print("=" * 80)

# Obtener cierre
cierre = CierreNomina.objects.get(id=info['CIERRE_ID'])

# ============================================================================
# PASO 1: SUBIR ARCHIVO
# ============================================================================
print("\n📤 PASO 1: SUBIR ARCHIVO EXCEL")
print("-" * 80)

excel_path = Path("/tmp/libro_remuneraciones_smoke_test.xlsx")
if not excel_path.exists():
    print("❌ ERROR: Archivo Excel no encontrado. Ejecuta generar_excel_prueba_libro.py")
    sys.exit(1)

# Verificar si ya existe un libro para este cierre
libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
if libro_existente:
    print(f"⚠️  Ya existe libro ID={libro_existente.id} para este cierre")
    print(f"   Estado actual: {libro_existente.estado}")
    libro = libro_existente
else:
    # Crear nuevo registro de libro
    with open(excel_path, 'rb') as f:
        libro = LibroRemuneracionesUpload.objects.create(
            cierre=cierre,
            archivo=File(f, name='libro_smoke_test.xlsx'),
            estado='pendiente',
            nombre_archivo='libro_smoke_test.xlsx'
        )
    print(f"✅ Libro creado: ID={libro.id}")

print(f"   Archivo: {libro.nombre_archivo}")
print(f"   Estado: {libro.estado}")

# ============================================================================
# PASO 2: ANALIZAR HEADERS
# ============================================================================
print("\n🔍 PASO 2: ANALIZAR HEADERS")
print("-" * 80)
print("Función: analizar_headers_libro_remuneraciones_con_logging")

try:
    task = analizar_headers_libro_remuneraciones.delay(
        libro.id, 
        info['USUARIO_ID']
    )
    print(f"✅ Task despachada: {task.id}")
    print("   Esperando resultado...")
    
    # Esperar resultado (max 30 segundos)
    result = task.get(timeout=30)
    print(f"✅ Resultado: {result}")
    
    # Recargar libro
    libro.refresh_from_db()
    print(f"   Nuevo estado: {libro.estado}")
    print(f"   Headers encontrados: {len(libro.header_json or [])}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============================================================================
# PASO 3: CLASIFICAR HEADERS
# ============================================================================
print("\n🏷️  PASO 3: CLASIFICAR HEADERS")
print("-" * 80)
print("Función: clasificar_headers_libro_remuneraciones_con_logging")

try:
    task = clasificar_headers_libro_remuneraciones.delay(
        libro.id,
        info['USUARIO_ID']
    )
    print(f"✅ Task despachada: {task.id}")
    print("   Esperando resultado...")
    
    result = task.get(timeout=30)
    print(f"✅ Resultado: {result}")
    
    # Recargar libro
    libro.refresh_from_db()
    print(f"   Nuevo estado: {libro.estado}")
    print(f"   Columnas creación empleados: {libro.columnas_creacion_empleados}")
    print(f"   Columnas conceptos: {len(libro.columnas_conceptos or [])}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============================================================================
# PASO 4: PROCESAR LIBRO (Chord con chunks paralelos)
# ============================================================================
print("\n⚙️  PASO 4: PROCESAR LIBRO")
print("-" * 80)
print("Función: procesar_libro_remuneraciones (Chord paralelo)")
print("   - procesar_chunk_empleados_task")
print("   - procesar_chunk_registros_task")
print("   - consolidar_empleados_task (callback)")
print("   - consolidar_registros_task (callback)")

# Importar aquí para evitar problemas de importación circular
from nomina.tasks_refactored.libro_remuneraciones import procesar_libro_remuneraciones

try:
    # Contar registros antes
    empleados_antes = EmpleadoCierre.objects.filter(cierre=cierre).count()
    conceptos_antes = RegistroConceptoEmpleado.objects.filter(
        empleado__cierre=cierre
    ).count()
    
    print(f"📊 Estado ANTES del procesamiento:")
    print(f"   Empleados: {empleados_antes}")
    print(f"   Registros de conceptos: {conceptos_antes}")
    
    task_group_id = procesar_libro_remuneraciones(
        libro.id,
        info['USUARIO_ID']
    )
    
    print(f"✅ Chord despachado: {task_group_id}")
    print("   Esperando procesamiento completo (esto puede tomar 20-60 segundos)...")
    
    # Polling del estado del libro
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(2)
        libro.refresh_from_db()
        
        empleados_actual = EmpleadoCierre.objects.filter(cierre=cierre).count()
        conceptos_actual = RegistroConceptoEmpleado.objects.filter(
            empleado__cierre=cierre
        ).count()
        
        print(f"   [{i*2}s] Estado: {libro.estado} | Empleados: {empleados_actual} | Conceptos: {conceptos_actual}")
        
        if libro.estado == 'procesado':
            print("\n✅ PROCESAMIENTO COMPLETADO")
            break
            
        if libro.estado == 'error':
            print(f"\n❌ ERROR en procesamiento: {libro.error_detalle}")
            sys.exit(1)
    else:
        print("\n⚠️  TIMEOUT: Procesamiento tomó más de 2 minutos")
    
    # Estadísticas finales
    print(f"\n📊 Estado DESPUÉS del procesamiento:")
    empleados_final = EmpleadoCierre.objects.filter(cierre=cierre).count()
    conceptos_final = RegistroConceptoEmpleado.objects.filter(
        empleado__cierre=cierre
    ).count()
    
    print(f"   Empleados creados: {empleados_final - empleados_antes}")
    print(f"   Registros de conceptos creados: {conceptos_final - conceptos_antes}")
    print(f"   Total empleados: {empleados_final}")
    print(f"   Total conceptos: {conceptos_final}")
    
    # Verificar datos
    if empleados_final == 5 and conceptos_final == 50:  # 5 empleados * 10 conceptos
        print("\n✅ VERIFICACIÓN: Datos coinciden con lo esperado")
    else:
        print(f"\n⚠️  ADVERTENCIA: Se esperaban 5 empleados y 50 conceptos")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RESUMEN DEL FLUJO 1")
print("=" * 80)
print(f"✅ Libro ID: {libro.id}")
print(f"✅ Estado final: {libro.estado}")
print(f"✅ Empleados procesados: {empleados_final}")
print(f"✅ Conceptos procesados: {conceptos_final}")
print(f"✅ Cierre ID: {cierre.id}")
print("=" * 80)

# Guardar resultado para siguiente flujo
with open('/tmp/flujo1_resultado.txt', 'w') as f:
    f.write(f"LIBRO_ID={libro.id}\n")
    f.write(f"EMPLEADOS={empleados_final}\n")
    f.write(f"CONCEPTOS={conceptos_final}\n")
    f.write(f"ESTADO={libro.estado}\n")

print("\n✅ Flujo 1 completado. Resultado guardado en /tmp/flujo1_resultado.txt")
print("📝 Siguiente paso: Generar documentación FLUJO_1_LIBRO_REMUNERACIONES.md\n")
