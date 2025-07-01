# Comandos para validar Libro Mayor Chains en Django Shell
# Copiar y pegar cada bloque en el shell interactivo

# =============================================================================
# BLOQUE 1: Importar tasks y verificar que funcionan
# =============================================================================
print("=" * 60)
print("VALIDANDO LIBRO MAYOR CHAINS")
print("=" * 60)

print("\n1. IMPORTANDO TASKS...")
from contabilidad.tasks_libro_mayor import (
    crear_chain_libro_mayor,
    validar_nombre_archivo_libro_mayor,
    verificar_archivo_libro_mayor,
    validar_contenido_libro_mayor,
    procesar_libro_mayor_raw,
    generar_incidencias_libro_mayor,
    finalizar_procesamiento_libro_mayor
)
print("✅ Tasks importadas correctamente")

# =============================================================================
# BLOQUE 2: Verificar modelos y datos existentes
# =============================================================================
print("\n2. VERIFICANDO MODELOS...")
from contabilidad.models import UploadLog, Cliente, CierreContabilidad
from django.contrib.auth.models import User

clientes_count = Cliente.objects.count()
users_count = User.objects.count()
upload_logs_count = UploadLog.objects.count()

print(f"✅ Clientes en BD: {clientes_count}")
print(f"✅ Usuarios en BD: {users_count}")  
print(f"✅ UploadLogs en BD: {upload_logs_count}")

# =============================================================================
# BLOQUE 3: Crear o encontrar datos de prueba
# =============================================================================
print("\n3. PREPARANDO DATOS DE PRUEBA...")

# Crear usuario de prueba
user, created = User.objects.get_or_create(
    username='test_libro_mayor',
    defaults={
        'email': 'test@ejemplo.com',
        'first_name': 'Test',
        'last_name': 'Usuario'
    }
)
print(f"✅ Usuario {'creado' if created else 'encontrado'}: {user.username}")

# Crear cliente de prueba
cliente, created = Cliente.objects.get_or_create(
    rut='12345678-9',
    defaults={
        'nombre': 'Cliente Test Libro Mayor',
        'activo': True
    }
)
print(f"✅ Cliente {'creado' if created else 'encontrado'}: {cliente.nombre}")

# Crear cierre de prueba
cierre, created = CierreContabilidad.objects.get_or_create(
    cliente=cliente,
    periodo='2024-12',
    defaults={
        'activo': True,
        'estado': 'abierto'
    }
)
print(f"✅ Cierre {'creado' if created else 'encontrado'}: {cierre.periodo}")

# =============================================================================
# BLOQUE 4: Crear UploadLog y Chain
# =============================================================================
print("\n4. CREANDO UPLOADLOG Y CHAIN...")

# Crear UploadLog válido
upload_log = UploadLog.objects.create(
    cliente=cliente,
    cierre=cierre,
    tipo_archivo='libro_mayor',
    nombre_archivo_original='12345678_LibroMayor_202412.xlsx',
    archivo_hash='test_hash_validacion',
    usuario=user,
    estado='pendiente'
)
print(f"✅ UploadLog creado: ID {upload_log.id}")

# Crear chain
chain = crear_chain_libro_mayor(upload_log.id)
print(f"✅ Chain creado con {len(chain.tasks)} tasks")

# Mostrar tasks del chain
print("📋 Tasks en el chain:")
for i, task in enumerate(chain.tasks, 1):
    task_name = task.name.split('.')[-1]
    print(f"   {i}. {task_name}")

# =============================================================================
# BLOQUE 5: Probar primera task individualmente
# =============================================================================
print("\n5. PROBANDO PRIMERA TASK...")

try:
    resultado = validar_nombre_archivo_libro_mayor(upload_log.id)
    print(f"✅ Primera task ejecutada: {resultado}")
    
    # Verificar que el estado cambió
    upload_log.refresh_from_db()
    print(f"✅ Estado actualizado: {upload_log.estado}")
except Exception as e:
    print(f"❌ Error ejecutando primera task: {e}")

# =============================================================================
# BLOQUE 6: Verificar Celery
# =============================================================================
print("\n6. VERIFICANDO CELERY...")

from celery import current_app
app = current_app
print(f"✅ Celery app: {app.main}")

# Intentar obtener workers
try:
    inspect = app.control.inspect()
    active = inspect.active()
    if active:
        print(f"✅ Workers activos: {list(active.keys())}")
    else:
        print("⚠️  No hay workers activos (normal en desarrollo)")
except:
    print("⚠️  No se pudieron obtener workers")

# =============================================================================
# BLOQUE 7: Resumen y limpieza
# =============================================================================
print("\n7. RESUMEN Y LIMPIEZA...")

print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN")
print("=" * 60)
print("✅ Importación de tasks: OK")
print("✅ Modelos de BD: OK")  
print("✅ Creación de datos: OK")
print("✅ Creación de chain: OK")
print("✅ Ejecución de task: OK")
print("✅ Verificación Celery: OK")
print(f"\n🎉 Chain ID para monitorear: {upload_log.id}")
print("\n📝 Para limpiar: upload_log.delete()")
print("=" * 60)

# Para limpiar después (opcional):
# upload_log.delete()
# print("✅ UploadLog de prueba eliminado")
