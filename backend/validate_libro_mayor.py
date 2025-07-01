#!/usr/bin/env python3
"""
Script de validación para el flujo de Libro Mayor con Celery Chains.
Ejecutar dentro del contenedor Docker.

Uso:
docker exec -it sgm-backend python /app/validate_libro_mayor.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
sys.path.append('/app')

django.setup()

from contabilidad.tasks_libro_mayor import (
    crear_chain_libro_mayor,
    validar_nombre_archivo_libro_mayor,
    verificar_archivo_libro_mayor,
    validar_contenido_libro_mayor,
    procesar_libro_mayor_raw,
    generar_incidencias_libro_mayor,
    finalizar_procesamiento_libro_mayor
)
from contabilidad.models import UploadLog, Cliente, CierreContabilidad
from django.contrib.auth.models import User
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chain_creation():
    """Test básico de creación del chain"""
    print("=" * 60)
    print("TEST 1: CREACIÓN DEL CHAIN")
    print("=" * 60)
    
    try:
        # Crear datos mínimos de prueba
        user, created = User.objects.get_or_create(
            username='test_libro_mayor',
            defaults={'email': 'test@example.com'}
        )
        
        cliente, created = Cliente.objects.get_or_create(
            rut='12345678-9',
            defaults={'nombre': 'Cliente Test Libro Mayor', 'activo': True}
        )
        
        cierre, created = CierreContabilidad.objects.get_or_create(
            cliente=cliente,
            periodo='2024-12',
            defaults={'activo': True, 'estado': 'abierto'}
        )
        
        # Crear UploadLog de prueba
        upload_log = UploadLog.objects.create(
            cliente=cliente,
            cierre=cierre,
            tipo_archivo='libro_mayor',
            nombre_archivo_original='12345678_LibroMayor_202412.xlsx',
            archivo_hash='test_hash_libro_mayor',
            usuario=user,
            estado='pendiente'
        )
        
        print(f"✓ UploadLog creado: ID {upload_log.id}")
        
        # Crear chain
        chain = crear_chain_libro_mayor(upload_log.id)
        print(f"✓ Chain creado con {len(chain.tasks)} tasks")
        
        # Listar tasks del chain
        print("\nTasks en el chain:")
        for i, task in enumerate(chain.tasks, 1):
            task_name = task.name.split('.')[-1]  # Solo el nombre final
            print(f"  {i}. {task_name}")
        
        print("✓ Test de creación EXITOSO")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de creación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_nombre_validation():
    """Test de validación de nombres de archivo"""
    print("\n" + "=" * 60)
    print("TEST 2: VALIDACIÓN DE NOMBRES")
    print("=" * 60)
    
    try:
        user, _ = User.objects.get_or_create(
            username='test_validation',
            defaults={'email': 'validation@example.com'}
        )
        
        cliente, _ = Cliente.objects.get_or_create(
            rut='87654321-0',
            defaults={'nombre': 'Cliente Validación', 'activo': True}
        )
        
        cierre, _ = CierreContabilidad.objects.get_or_create(
            cliente=cliente,
            periodo='2024-11',
            defaults={'activo': True, 'estado': 'abierto'}
        )
        
        # Test con nombre válido
        upload_log_valido = UploadLog.objects.create(
            cliente=cliente,
            cierre=cierre,
            tipo_archivo='libro_mayor',
            nombre_archivo_original='87654321_LibroMayor_202411.xlsx',
            archivo_hash='test_hash_valido',
            usuario=user,
            estado='pendiente'
        )
        
        resultado = validar_nombre_archivo_libro_mayor(upload_log_valido.id)
        print(f"✓ Validación nombre válido: {resultado}")
        
        # Test con nombre inválido
        upload_log_invalido = UploadLog.objects.create(
            cliente=cliente,
            cierre=cierre,
            tipo_archivo='libro_mayor',
            nombre_archivo_original='archivo_incorrecto.xlsx',
            archivo_hash='test_hash_invalido',
            usuario=user,
            estado='pendiente'
        )
        
        try:
            validar_nombre_archivo_libro_mayor(upload_log_invalido.id)
            print("✗ FALLO: Debería haber rechazado nombre inválido")
            return False
        except Exception as e:
            print(f"✓ Validación rechazó nombre inválido correctamente: {str(e)[:100]}...")
        
        print("✓ Test de validación EXITOSO")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de validación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_connection():
    """Test de conexión con Celery"""
    print("\n" + "=" * 60)
    print("TEST 3: CONEXIÓN CELERY")
    print("=" * 60)
    
    try:
        from celery import current_app
        
        # Verificar que Celery esté disponible
        app = current_app
        print(f"✓ Celery app configurada: {app.main}")
        
        # Verificar workers activos
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✓ Workers activos: {list(active_workers.keys())}")
        else:
            print("⚠ No hay workers activos detectados")
        
        # Verificar tasks registradas
        registered_tasks = inspect.registered()
        if registered_tasks:
            libro_mayor_tasks = []
            for worker, tasks in registered_tasks.items():
                for task in tasks:
                    if 'libro_mayor' in task:
                        libro_mayor_tasks.append(task)
                        
            if libro_mayor_tasks:
                print(f"✓ Tasks de libro mayor registradas: {len(libro_mayor_tasks)}")
                for task in libro_mayor_tasks:
                    task_name = task.split('.')[-1]
                    print(f"  - {task_name}")
            else:
                print("⚠ No se encontraron tasks de libro mayor registradas")
        else:
            print("⚠ No se pudieron obtener tasks registradas")
        
        print("✓ Test de conexión Celery COMPLETADO")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de Celery: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """Test de modelos de base de datos"""
    print("\n" + "=" * 60)
    print("TEST 4: MODELOS DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        from contabilidad.models import (
            UploadLog, Cliente, CierreContabilidad, 
            LibroMayorArchivo, MovimientoContable,
            CuentaContable, Incidencia
        )
        
        # Contar registros existentes
        clientes_count = Cliente.objects.count()
        cierres_count = CierreContabilidad.objects.count()
        upload_logs_count = UploadLog.objects.count()
        movimientos_count = MovimientoContable.objects.count()
        
        print(f"✓ Clientes en BD: {clientes_count}")
        print(f"✓ Cierres en BD: {cierres_count}")
        print(f"✓ UploadLogs en BD: {upload_logs_count}")
        print(f"✓ Movimientos en BD: {movimientos_count}")
        
        # Verificar que podemos crear registros
        test_cliente = Cliente.objects.create(
            rut='99999999-9',
            nombre='Cliente Test DB',
            activo=True
        )
        print(f"✓ Cliente de prueba creado: {test_cliente.id}")
        
        # Limpiar registro de prueba
        test_cliente.delete()
        print("✓ Cliente de prueba eliminado")
        
        print("✓ Test de modelos EXITOSO")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de modelos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests de validación"""
    print("INICIANDO VALIDACIÓN DE LIBRO MAYOR CHAINS")
    print("=" * 60)
    
    tests = [
        ("Creación del Chain", test_chain_creation),
        ("Validación de Nombres", test_nombre_validation),
        ("Conexión Celery", test_celery_connection),
        ("Modelos de BD", test_database_models),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} FALLÓ: {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 TODOS LOS TESTS PASARON - El flujo está listo para usar")
        return 0
    else:
        print("⚠️  ALGUNOS TESTS FALLARON - Revisar configuración")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
