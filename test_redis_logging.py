#!/usr/bin/env python
"""
Script para probar el sistema de logging de Redis
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.contabilidad.utils.activity_logger import (
    registrar_actividad_tarjeta,
    ActivityLogStorage,
    redis_client,
    REDIS_AVAILABLE
)
from backend.contabilidad.models import CierreContabilidad, TarjetaActivityLog
from backend.api.models import Cliente
from django.contrib.auth import get_user_model

Usuario = get_user_model()

def test_redis_connection():
    """Test básico de conexión a Redis"""
    print("=== TEST DE CONEXIÓN REDIS ===")
    print(f"Redis disponible: {REDIS_AVAILABLE}")
    
    if not REDIS_AVAILABLE:
        print("❌ Redis no disponible")
        return False
    
    try:
        # Test de ping
        result = redis_client.ping()
        print(f"✅ Redis ping: {result}")
        
        # Test de info
        info = redis_client.info()
        print(f"✅ Redis versión: {info.get('redis_version')}")
        print(f"✅ Redis DB: {info.get('db1', 'No existe DB1')}")
        
        # Test de escritura/lectura
        redis_client.set("test_key", "test_value", ex=10)
        value = redis_client.get("test_key")
        print(f"✅ Test escritura/lectura: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en Redis: {e}")
        return False

def test_activity_logging():
    """Test del sistema de logging de actividad"""
    print("\n=== TEST DE LOGGING DE ACTIVIDAD ===")
    
    # Buscar un cliente y cierre existente
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en la BD")
        return False
    
    print(f"✅ Cliente encontrado: {cliente.id} - {cliente.nombre}")
    
    # Buscar un cierre para este cliente
    cierre = CierreContabilidad.objects.filter(cliente=cliente).first()
    if not cierre:
        print("❌ No hay cierres para este cliente")
        return False
    
    print(f"✅ Cierre encontrado: {cierre.periodo} - {cierre.estado}")
    
    # Buscar un usuario
    usuario = Usuario.objects.first()
    if not usuario:
        print("❌ No hay usuarios en la BD")
        return False
    
    print(f"✅ Usuario encontrado: {usuario.id} - {usuario.nombre}")
    
    # Registrar actividad de prueba
    print("\n--- Registrando actividad de prueba ---")
    log_entry = registrar_actividad_tarjeta(
        cliente_id=cliente.id,
        periodo=cierre.periodo,
        tarjeta="tipo_documento",
        accion="test_action",
        descripcion="Test de logging desde script",
        usuario=usuario,
        detalles={"test": True, "timestamp": datetime.now().isoformat()},
        resultado="exito",
        ip_address="127.0.0.1"
    )
    
    if log_entry:
        print(f"✅ Log creado en PostgreSQL: ID {log_entry.id}")
        
        # Verificar en Redis
        if REDIS_AVAILABLE:
            try:
                # Verificar log individual
                log_data = redis_client.get(f"log:{log_entry.id}")
                if log_data:
                    print(f"✅ Log encontrado en Redis: {log_data[:100]}...")
                else:
                    print("❌ Log NO encontrado en Redis")
                
                # Verificar índices
                global_count = redis_client.zcard("logs:recent:global")
                client_count = redis_client.zcard(f"logs:recent:client:{cliente.id}")
                period_count = redis_client.zcard(f"logs:recent:period:{cierre.periodo}")
                
                print(f"✅ Logs en índice global: {global_count}")
                print(f"✅ Logs en índice cliente: {client_count}")
                print(f"✅ Logs en índice período: {period_count}")
                
                # Probar get_recent_logs
                recent_logs = ActivityLogStorage.get_recent_logs(
                    cliente_id=cliente.id,
                    periodo=cierre.periodo,
                    limit=5
                )
                print(f"✅ Logs recientes obtenidos: {len(recent_logs)}")
                
                if recent_logs:
                    last_log = recent_logs[0]
                    print(f"✅ Último log: {last_log.get('accion')} - {last_log.get('descripcion')}")
                
            except Exception as e:
                print(f"❌ Error verificando Redis: {e}")
        
        return True
    else:
        print("❌ Error creando log")
        return False

def test_redis_keys():
    """Verificar claves existentes en Redis"""
    print("\n=== CLAVES EN REDIS ===")
    
    if not REDIS_AVAILABLE:
        print("❌ Redis no disponible")
        return
    
    try:
        # Buscar claves de logs
        log_keys = redis_client.keys("log:*")
        index_keys = redis_client.keys("logs:*")
        
        print(f"✅ Claves de logs individuales: {len(log_keys)}")
        print(f"✅ Claves de índices: {len(index_keys)}")
        
        # Mostrar algunas claves
        if log_keys:
            print("Ejemplos de claves de logs:")
            for key in log_keys[:5]:
                print(f"  - {key}")
        
        if index_keys:
            print("Claves de índices:")
            for key in index_keys:
                count = redis_client.zcard(key) if key.startswith("logs:recent:") else redis_client.type(key)
                print(f"  - {key}: {count}")
        
        # Estadísticas
        stats = ActivityLogStorage.get_redis_stats()
        print(f"\n✅ Estadísticas Redis: {stats}")
        
    except Exception as e:
        print(f"❌ Error verificando claves: {e}")

def main():
    """Función principal"""
    print("SCRIPT DE TESTING REDIS LOGGING")
    print("=" * 40)
    
    # Test 1: Conexión Redis
    if not test_redis_connection():
        print("\n❌ FALLO: No se puede conectar a Redis")
        return
    
    # Test 2: Logging de actividad
    if not test_activity_logging():
        print("\n❌ FALLO: Error en el logging de actividad")
        return
    
    # Test 3: Verificar claves
    test_redis_keys()
    
    print("\n✅ TODOS LOS TESTS COMPLETADOS")

if __name__ == "__main__":
    main()
