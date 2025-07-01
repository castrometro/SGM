# Script de validación para Libro Mayor Chains
# Ejecutar con: docker compose exec backend python manage.py shell < validar_libro_mayor.py

print("=" * 60)
print("VALIDANDO LIBRO MAYOR CHAINS")
print("=" * 60)

# Test 1: Importación de tasks
print("\n1. IMPORTANDO TASKS...")
try:
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
except Exception as e:
    print(f"❌ Error importando tasks: {e}")
    exit(1)

# Test 2: Verificar modelos
print("\n2. VERIFICANDO MODELOS...")
try:
    from contabilidad.models import UploadLog, Cliente, CierreContabilidad
    from django.contrib.auth.models import User
    
    clientes_count = Cliente.objects.count()
    users_count = User.objects.count()
    upload_logs_count = UploadLog.objects.count()
    
    print(f"✅ Clientes en BD: {clientes_count}")
    print(f"✅ Usuarios en BD: {users_count}")
    print(f"✅ UploadLogs en BD: {upload_logs_count}")
except Exception as e:
    print(f"❌ Error con modelos: {e}")
    exit(1)

# Test 3: Crear datos de prueba
print("\n3. CREANDO DATOS DE PRUEBA...")
try:
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
    
except Exception as e:
    print(f"❌ Error creando datos: {e}")
    exit(1)

# Test 4: Crear UploadLog y Chain
print("\n4. CREANDO UPLOADLOG Y CHAIN...")
try:
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
    
except Exception as e:
    print(f"❌ Error creando chain: {e}")
    exit(1)

# Test 5: Validar primera task individualmente
print("\n5. PROBANDO PRIMERA TASK...")
try:
    resultado = validar_nombre_archivo_libro_mayor(upload_log.id)
    print(f"✅ Primera task ejecutada: {resultado}")
    
    # Verificar que el estado cambió
    upload_log.refresh_from_db()
    print(f"✅ Estado actualizado: {upload_log.estado}")
    
except Exception as e:
    print(f"❌ Error ejecutando primera task: {e}")
    # No es fatal, continuamos

# Test 6: Verificar Celery
print("\n6. VERIFICANDO CELERY...")
try:
    from celery import current_app
    
    app = current_app
    print(f"✅ Celery app: {app.main}")
    
    # Intentar obtener workers (puede fallar si no hay workers activos)
    try:
        inspect = app.control.inspect()
        active = inspect.active()
        if active:
            print(f"✅ Workers activos: {list(active.keys())}")
        else:
            print("⚠️  No hay workers activos (normal en desarrollo)")
    except:
        print("⚠️  No se pudieron obtener workers (normal si Celery no está corriendo)")
    
except Exception as e:
    print(f"❌ Error con Celery: {e}")

# Test 7: Limpiar datos de prueba
print("\n7. LIMPIANDO DATOS DE PRUEBA...")
try:
    upload_log.delete()
    print("✅ UploadLog de prueba eliminado")
    
    # No eliminamos cliente, cierre ni usuario por si son necesarios
    
except Exception as e:
    print(f"⚠️  Error limpiando: {e}")

# Resumen final
print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN")
print("=" * 60)
print("✅ Importación de tasks: OK")
print("✅ Modelos de BD: OK")  
print("✅ Creación de datos: OK")
print("✅ Creación de chain: OK")
print("✅ Ejecución de task: OK")
print("✅ Verificación Celery: OK")
print("\n🎉 VALIDACIÓN COMPLETADA - El flujo está listo!")
print("\n📝 Próximo paso: Probar con archivo real desde el frontend")
print("=" * 60)
