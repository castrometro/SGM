#!/usr/bin/env python

# Script para probar el logging de actividad desde dentro del contenedor
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.utils.activity_logger import (
    registrar_actividad_tarjeta,
    ActivityLogStorage,
    REDIS_AVAILABLE
)
from contabilidad.models import CierreContabilidad
from api.models import Cliente
from django.contrib.auth import get_user_model
from datetime import datetime

Usuario = get_user_model()

def test_logging_system():
    print("=== TEST SISTEMA DE LOGGING ===")
    print(f"Redis disponible: {REDIS_AVAILABLE}")
    
    # Buscar datos existentes
    cliente = Cliente.objects.first()
    cierre = CierreContabilidad.objects.first()
    usuario = Usuario.objects.first()
    
    if not cliente or not cierre or not usuario:
        print("❌ Faltan datos básicos (cliente, cierre, usuario)")
        return False
    
    print(f"Cliente: {cliente.nombre}")
    print(f"Cierre: {cierre.periodo}")
    print(f"Usuario: {usuario.nombre}")
    
    # Registrar actividad de prueba
    print("\n--- Registrando actividad ---")
    log_entry = registrar_actividad_tarjeta(
        cliente_id=cliente.id,
        periodo=cierre.periodo,
        tarjeta="tipo_documento",
        accion="test_cache",
        descripcion="Prueba de cache Django Redis",
        usuario=usuario,
        detalles={"test": True, "cache": "django"},
        resultado="exito"
    )
    
    if log_entry:
        print(f"✅ Log creado: ID {log_entry.id}")
        
        # Verificar en cache
        logs = ActivityLogStorage.get_recent_logs(
            cliente_id=cliente.id,
            periodo=cierre.periodo,
            limit=5
        )
        
        print(f"✅ Logs obtenidos desde cache: {len(logs)}")
        
        if logs:
            for log in logs:
                print(f"  - {log.get('accion')}: {log.get('descripcion')}")
        
        # Estadísticas
        stats = ActivityLogStorage.get_redis_stats()
        print(f"✅ Stats: {stats}")
        
        return True
    else:
        print("❌ Error creando log")
        return False

if __name__ == "__main__":
    success = test_logging_system()
    if success:
        print("\n✅ Test completado exitosamente")
    else:
        print("\n❌ Test falló")
        sys.exit(1)
