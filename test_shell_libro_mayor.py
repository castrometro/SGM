"""
Script específico para probar Libro Mayor desde Django shell
Ejecutar:
  docker compose exec backend python manage.py shell
  exec(open('test_shell_libro_mayor.py').read())
"""

print("🧪 Iniciando tests de Libro Mayor...")

# Test 1: Verificar tipos de incidencia válidos
print("\n1. Probando tipos de incidencia...")
from contabilidad.models import Incidencia, CierreContabilidad

cierre = CierreContabilidad.objects.first()
if cierre:
    try:
        # Probar con tipo válido
        inc = Incidencia.objects.create(
            cierre=cierre,
            tipo="negocio",
            descripcion="Test de incidencia",
            resuelta=False
        )
        print(f"✅ Incidencia creada correctamente con tipo: {inc.tipo}")
        inc.delete()  # Limpiar
    except Exception as e:
        print(f"❌ Error creando incidencia: {e}")
else:
    print("❌ No hay cierres disponibles")

# Test 2: Verificar UploadLogs existentes
print("\n2. Verificando UploadLogs existentes...")
from contabilidad.models import UploadLog

uploads = UploadLog.objects.filter(tipo_upload="libro_mayor").order_by('-id')[:3]
print(f"📊 Encontrados {uploads.count()} UploadLogs de libro mayor")

for upload in uploads:
    print(f"\n📋 UploadLog ID: {upload.id}")
    print(f"   - Estado: {upload.estado}")
    print(f"   - Cliente: {upload.cliente.nombre if upload.cliente else 'N/A'}")
    print(f"   - Archivo: {upload.nombre_archivo_original}")
    
    if upload.resumen:
        # Verificar campos críticos para frontend
        mov_creados = upload.resumen.get('movimientos_creados', 'NO ENCONTRADO')
        inc_creadas = upload.resumen.get('incidencias_creadas', 'NO ENCONTRADO')
        
        print(f"   - Movimientos creados: {mov_creados}")
        print(f"   - Incidencias creadas: {inc_creadas}")
        
        if mov_creados == 'NO ENCONTRADO':
            print("   ⚠️  PROBLEMA: Campo movimientos_creados NO encontrado")
        if inc_creadas == 'NO ENCONTRADO':
            print("   ⚠️  PROBLEMA: Campo incidencias_creadas NO encontrado")
    else:
        print("   ⚠️  Sin resumen")

# Test 3: Probar creación de chain
print("\n3. Probando creación de chain...")
from contabilidad.tasks_libro_mayor import crear_chain_libro_mayor

if uploads.exists():
    upload_test = uploads.first()
    try:
        chain = crear_chain_libro_mayor(upload_test.id)
        print(f"✅ Chain creado exitosamente")
        print(f"📋 Tasks en el chain:")
        for i, task in enumerate(chain.tasks, 1):
            print(f"   {i}. {task.name}")
    except Exception as e:
        print(f"❌ Error creando chain: {e}")

# Test 4: Verificar serializer de LibroMayorArchivo
print("\n4. Verificando serializer...")
from contabilidad.models import LibroMayorArchivo
from contabilidad.serializers import LibroMayorArchivoSerializer

archivos = LibroMayorArchivo.objects.order_by('-id')[:2]
print(f"📊 Encontrados {archivos.count()} LibroMayorArchivo")

for archivo in archivos:
    serializer = LibroMayorArchivoSerializer(archivo)
    data = serializer.data
    
    print(f"\n📋 Archivo ID: {archivo.id}")
    print(f"   - Upload log ID: {data.get('upload_log', 'N/A')}")
    print(f"   - Estado: {data.get('estado', 'N/A')}")
    print(f"   - Procesado: {data.get('procesado', 'N/A')}")

print("\n" + "="*50)
print("✅ Tests completados")
print("="*50)

# Funciones auxiliares disponibles después del test
def check_upload(upload_id):
    """Función para verificar un upload específico"""
    try:
        upload = UploadLog.objects.get(id=upload_id)
        print(f"UploadLog {upload_id}:")
        print(f"  Estado: {upload.estado}")
        print(f"  Resumen: {upload.resumen}")
        return upload
    except UploadLog.DoesNotExist:
        print(f"UploadLog {upload_id} no encontrado")
        
def test_chain(upload_id):
    """Función para probar chain con un upload específico"""
    try:
        chain = crear_chain_libro_mayor(upload_id)
        print(f"Chain creado para upload {upload_id}")
        print("Para ejecutar: chain.apply_async()")
        return chain
    except Exception as e:
        print(f"Error: {e}")

print("\n💡 Funciones disponibles:")
print("- check_upload(upload_id)")
print("- test_chain(upload_id)")
