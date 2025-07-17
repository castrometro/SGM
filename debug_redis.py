#!/usr/bin/env python
"""
Script de diagnóstico para Redis logging
Usar desde Django shell: python manage.py shell < debug_redis.py
"""

from datetime import datetime
import json

# Importaciones correctas para Django
from contabilidad.utils.activity_logger import (
    registrar_actividad_tarjeta,
    ActivityLogStorage,
    redis_client,
    REDIS_AVAILABLE
)
from contabilidad.models import CierreContabilidad, TarjetaActivityLog
from api.models import Cliente
from django.contrib.auth import get_user_model

Usuario = get_user_model()

print('=== DIAGNÓSTICO REDIS LOGGING ===')
print(f'Redis disponible: {REDIS_AVAILABLE}')

if not REDIS_AVAILABLE:
    print('❌ Redis no está disponible')
    exit(1)

# Test de conexión básico
try:
    result = redis_client.ping()
    print(f'✅ Redis ping: {result}')
    
    # Verificar DB actual
    info = redis_client.info()
    print(f'Redis versión: {info.get("redis_version")}')
    
    # Verificar claves existentes
    all_keys = redis_client.keys('*')
    log_keys = redis_client.keys('log:*')
    index_keys = redis_client.keys('logs:*')
    
    print(f'Total claves en Redis: {len(all_keys)}')
    print(f'Claves de logs: {len(log_keys)}')
    print(f'Claves de índices: {len(index_keys)}')
    
    if all_keys:
        print('Primeras 10 claves:')
        for key in all_keys[:10]:
            print(f'  - {key}')
    
except Exception as e:
    print(f'❌ Error en Redis: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

# Buscar un cliente con cierre
cliente = Cliente.objects.first()
if not cliente:
    print('❌ No hay clientes en la BD')
    exit(1)

cierre = CierreContabilidad.objects.filter(cliente=cliente).first()
if not cierre:
    print('❌ No hay cierres para el cliente')
    exit(1)

usuario = Usuario.objects.first()
if not usuario:
    print('❌ No hay usuarios en la BD')
    exit(1)

print(f'✅ Cliente: {cliente.id} - {cliente.nombre}')
print(f'✅ Cierre: {cierre.periodo} - {cierre.estado}')
print(f'✅ Usuario: {usuario.id} - {usuario.nombre}')

# Registrar actividad de prueba
print('--- Registrando actividad de prueba ---')
log_entry = registrar_actividad_tarjeta(
    cliente_id=cliente.id,
    periodo=cierre.periodo,
    tarjeta='tipo_documento',
    accion='test_debug',
    descripcion='Test desde diagnóstico Redis',
    usuario=usuario,
    detalles={'test': True, 'debug': True},
    resultado='exito',
    ip_address='127.0.0.1'
)

if log_entry:
    print(f'✅ Log creado en PostgreSQL: ID {log_entry.id}')
    
    # Verificar en Redis inmediatamente
    try:
        log_data = redis_client.get(f'log:{log_entry.id}')
        if log_data:
            print(f'✅ Log encontrado en Redis')
            parsed = json.loads(log_data)
            print(f'   Acción: {parsed.get("accion")}')
            print(f'   Descripción: {parsed.get("descripcion")}')
        else:
            print('❌ Log NO encontrado en Redis')
            
        # Verificar índices
        global_count = redis_client.zcard('logs:recent:global')
        client_count = redis_client.zcard(f'logs:recent:client:{cliente.id}')
        period_count = redis_client.zcard(f'logs:recent:period:{cierre.periodo}')
        
        print(f'Índice global: {global_count} logs')
        print(f'Índice cliente: {client_count} logs')
        print(f'Índice período: {period_count} logs')
        
        # Obtener logs recientes
        recent_logs = ActivityLogStorage.get_recent_logs(
            cliente_id=cliente.id,
            periodo=cierre.periodo,
            limit=5
        )
        print(f'Logs recientes obtenidos: {len(recent_logs)}')
        
        # Verificar todos los logs en PostgreSQL
        all_logs = TarjetaActivityLog.objects.filter(cierre=cierre).count()
        print(f'Total logs en PostgreSQL para este cierre: {all_logs}')
        
    except Exception as e:
        print(f'❌ Error verificando Redis: {e}')
        import traceback
        traceback.print_exc()
        
else:
    print('❌ Error creando log')

print('=== FIN DIAGNÓSTICO ===')
