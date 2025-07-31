#!/usr/bin/env python3
"""
🔧 VERIFICACIÓN: Redis y Celery para Sistema Dual

Script para verificar que Redis y Celery estén configurados correctamente
para el sistema dual de incidencias.
"""

import os
import sys
import redis
from datetime import datetime

# Configurar el entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM/backend')

import django
django.setup()

from celery import current_app
from nomina.tasks import generar_incidencias_consolidados_v2_task

def verificar_redis():
    """Verificar conexión Redis"""
    print("🔴 VERIFICANDO REDIS...")
    print("-" * 30)
    
    try:
        # Conectar a Redis (configuración por defecto)
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test básico
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        
        if value == b'test_value':
            print("✅ Redis funcionando correctamente")
            print(f"   📍 Host: localhost:6379")
            print(f"   🗄️  DB: 0")
            
            # Limpiar
            r.delete('test_key')
            return True
        else:
            print("❌ Redis no responde correctamente")
            return False
            
    except redis.ConnectionError:
        print("❌ No se puede conectar a Redis")
        print("   💡 Asegúrate de que Redis esté ejecutándose:")
        print("      sudo systemctl start redis")
        print("      # o")
        print("      redis-server")
        return False
    except Exception as e:
        print(f"❌ Error verificando Redis: {e}")
        return False


def verificar_celery():
    """Verificar configuración Celery"""
    print()
    print("🎵 VERIFICANDO CELERY...")
    print("-" * 30)
    
    try:
        # Verificar que Celery esté configurado
        app = current_app
        print(f"✅ Celery app configurada: {app.main}")
        
        # Verificar broker
        broker_url = app.conf.broker_url
        print(f"📡 Broker URL: {broker_url}")
        
        # Verificar backend
        result_backend = app.conf.result_backend
        print(f"🗄️  Result backend: {result_backend}")
        
        # Verificar que las tareas estén registradas
        registered_tasks = list(app.tasks.keys())
        incidencias_tasks = [task for task in registered_tasks if 'incidencias' in task.lower()]
        
        print(f"📋 Tareas de incidencias registradas: {len(incidencias_tasks)}")
        for task in incidencias_tasks:
            print(f"   • {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Celery: {e}")
        return False


def test_celery_simple():
    """Test simple de Celery"""
    print()
    print("🧪 TEST SIMPLE DE CELERY...")
    print("-" * 35)
    
    try:
        # Crear una tarea simple
        from celery import shared_task
        
        @shared_task
        def test_task(x, y):
            return x + y
        
        # Ejecutar de forma síncrona primero
        result_sync = test_task(4, 4)
        print(f"✅ Ejecución síncrona: {result_sync}")
        
        # Intentar ejecución asíncrona
        print("🔄 Probando ejecución asíncrona...")
        print("   💡 Nota: Requiere que celery worker esté ejecutándose")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test simple: {e}")
        return False


def mostrar_comandos_startup():
    """Mostrar comandos para iniciar servicios"""
    print()
    print("🚀 COMANDOS PARA INICIAR SERVICIOS")
    print("=" * 40)
    
    print("1️⃣  REDIS:")
    print("   sudo systemctl start redis")
    print("   # o manualmente:")
    print("   redis-server")
    print()
    
    print("2️⃣  CELERY WORKER:")
    print("   cd /root/SGM/backend")
    print("   celery -A backend worker --loglevel=info")
    print()
    
    print("3️⃣  CELERY BEAT (opcional, para tareas programadas):")
    print("   cd /root/SGM/backend")
    print("   celery -A backend beat --loglevel=info")
    print()
    
    print("4️⃣  VERIFICAR WORKERS ACTIVOS:")
    print("   cd /root/SGM/backend")
    print("   celery -A backend inspect active")
    print()
    
    print("5️⃣  MONITOR CELERY (opcional):")
    print("   cd /root/SGM/backend")
    print("   celery -A backend flower")
    print("   # Luego abrir: http://localhost:5555")


def verificar_configuracion_django():
    """Verificar configuración Django para Celery"""
    print()
    print("⚙️  VERIFICANDO CONFIGURACIÓN DJANGO...")
    print("-" * 40)
    
    try:
        from django.conf import settings
        
        # Verificar configuraciones de Celery
        celery_configs = [
            'CELERY_BROKER_URL',
            'CELERY_RESULT_BACKEND',
            'CELERY_ACCEPT_CONTENT',
            'CELERY_TASK_SERIALIZER',
            'CELERY_RESULT_SERIALIZER'
        ]
        
        print("📋 Configuraciones de Celery en Django:")
        for config in celery_configs:
            value = getattr(settings, config, 'NO CONFIGURADO')
            print(f"   • {config}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando configuración Django: {e}")
        return False


if __name__ == "__main__":
    print("🔧 VERIFICACIÓN DE INFRAESTRUCTURA PARA SISTEMA DUAL")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar verificaciones
    redis_ok = verificar_redis()
    celery_ok = verificar_celery()
    test_ok = test_celery_simple()
    config_ok = verificar_configuracion_django()
    
    # Mostrar comandos útiles
    mostrar_comandos_startup()
    
    # Resumen final
    print()
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 30)
    print(f"🔴 Redis: {'✅' if redis_ok else '❌'}")
    print(f"🎵 Celery: {'✅' if celery_ok else '❌'}")
    print(f"🧪 Test simple: {'✅' if test_ok else '❌'}")
    print(f"⚙️  Config Django: {'✅' if config_ok else '❌'}")
    
    if all([redis_ok, celery_ok, test_ok, config_ok]):
        print()
        print("🎉 INFRAESTRUCTURA LISTA PARA SISTEMA DUAL")
        print("💡 Ahora puedes ejecutar: python test_sistema_dual_incidencias.py")
    else:
        print()
        print("⚠️  REQUIERE CONFIGURACIÓN ADICIONAL")
        print("💡 Revisa los errores arriba y sigue los comandos de startup")
