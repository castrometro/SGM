"""
Script para completar la creación de datos de prueba para Libro Mayor
Ejecutar desde Django shell:
  docker compose exec backend python manage.py shell
  exec(open('completar_datos_prueba.py').read())
"""

print("🔧 Completando datos de prueba para Libro Mayor...")

from django.utils import timezone
from contabilidad.models import Cliente, CierreContabilidad, UploadLog, LibroMayorArchivo

# Buscar el UploadLog recién creado (ID 126)
try:
    upload_log = UploadLog.objects.get(id=126)
    print(f"✅ UploadLog encontrado: ID {upload_log.id}")
    print(f"   - Estado: {upload_log.estado}")
    print(f"   - Cliente: {upload_log.cliente.nombre}")
    
    # Verificar que tenga resumen
    if upload_log.resumen:
        mov_creados = upload_log.resumen.get('movimientos_creados')
        inc_creadas = upload_log.resumen.get('incidencias_creadas')
        print(f"   - Movimientos: {mov_creados}")
        print(f"   - Incidencias: {inc_creadas}")
    else:
        print("   ⚠️  Sin resumen")
        
except UploadLog.DoesNotExist:
    print("❌ UploadLog 126 no encontrado")
    exit()

# Verificar si ya existe LibroMayorArchivo para este UploadLog
archivo_existente = LibroMayorArchivo.objects.filter(upload_log=upload_log).first()

if archivo_existente:
    print(f"✅ LibroMayorArchivo ya existe: ID {archivo_existente.id}")
    archivo_obj = archivo_existente
else:
    # Crear LibroMayorArchivo
    try:
        archivo_obj = LibroMayorArchivo.objects.create(
            upload_log=upload_log,
            nombre_archivo=upload_log.nombre_archivo_original,
            estado="procesado",
            procesado=True,
            fecha_procesamiento=timezone.now(),
            resumen_procesamiento={
                'movimientos_creados': upload_log.resumen.get('movimientos_creados', 0),
                'incidencias_creadas': upload_log.resumen.get('incidencias_creadas', 0),
                'aperturas_creadas': upload_log.resumen.get('aperturas_creadas', 0),
                'cuentas_nuevas': upload_log.resumen.get('cuentas_nuevas', 0),
            }
        )
        print(f"✅ LibroMayorArchivo creado: ID {archivo_obj.id}")
        print(f"   - Upload log asociado: {archivo_obj.upload_log.id}")
        print(f"   - Estado: {archivo_obj.estado}")
        print(f"   - Procesado: {archivo_obj.procesado}")
    except Exception as e:
        print(f"❌ Error creando LibroMayorArchivo: {e}")
        exit()

# Verificar el cierre (completar si falló antes)
if not upload_log.cierre:
    print("\n🔧 Creando cierre faltante...")
    try:
        cierre = CierreContabilidad.objects.create(
            cliente=upload_log.cliente,
            periodo="2024-12",
            estado="procesando",
            fecha_creacion=timezone.now()
        )
        upload_log.cierre = cierre
        upload_log.save()
        print(f"✅ Cierre creado y asociado: {cierre.periodo} (ID: {cierre.id})")
    except Exception as e:
        print(f"❌ Error creando cierre: {e}")
else:
    print(f"✅ Cierre ya existe: {upload_log.cierre.periodo} (ID: {upload_log.cierre.id})")

# Verificar serialización para frontend
print("\n🔍 Verificando serialización para frontend...")
from contabilidad.serializers import LibroMayorArchivoSerializer

serializer = LibroMayorArchivoSerializer(archivo_obj)
data = serializer.data

print("📋 Datos serializados:")
print(f"   - ID: {data.get('id')}")
print(f"   - Upload log ID: {data.get('upload_log')}")
print(f"   - Estado: {data.get('estado')}")
print(f"   - Procesado: {data.get('procesado')}")
print(f"   - Nombre archivo: {data.get('nombre_archivo')}")

# Verificar estructura completa del UploadLog
print(f"\n📊 Resumen completo del UploadLog {upload_log.id}:")
for key, value in upload_log.resumen.items():
    print(f"   - {key}: {value}")

print("\n" + "="*60)
print("✅ DATOS DE PRUEBA COMPLETADOS")
print("="*60)
print("📋 Resumen:")
print(f"   - Cliente: {upload_log.cliente.nombre} (ID: {upload_log.cliente.id})")
print(f"   - Cierre: {upload_log.cierre.periodo if upload_log.cierre else 'SIN CIERRE'} (ID: {upload_log.cierre.id if upload_log.cierre else 'N/A'})")
print(f"   - UploadLog: ID {upload_log.id} - Estado: {upload_log.estado}")
print(f"   - LibroMayorArchivo: ID {archivo_obj.id} - Estado: {archivo_obj.estado}")
print(f"   - Movimientos simulados: {upload_log.resumen.get('movimientos_creados', 0)}")
print(f"   - Incidencias simuladas: {upload_log.resumen.get('incidencias_creadas', 0)}")

print("\n💡 Para probar el frontend:")
print("   1. Ir a la sección de Libro Mayor")
print("   2. Verificar que aparezca el archivo procesado")
print("   3. Verificar que se muestren los movimientos e incidencias")
