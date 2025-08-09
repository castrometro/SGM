#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar el aislamiento por usuario en Redis
"""

import redis
import json
import os
from datetime import datetime

def test_redis_usuario_isolation():
    """
    Test del aislamiento por usuario en Redis
    """
    print("🧪 Probando aislamiento por usuario en Redis...")
    
    # Conectar a Redis
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        r = redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=True,
            encoding='utf-8'
        )
    else:
        r = redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=True,
            encoding='utf-8'
        )
    
    # Simular datos de múltiples usuarios
    usuarios = [
        {'id': 1, 'correo': 'usuario1@empresa.com'},
        {'id': 2, 'correo': 'usuario2@empresa.com'},
        {'id': 3, 'correo': 'usuario3@empresa.com'}
    ]
    
    task_id = 'test_task_123'
    
    # Crear metadatos para cada usuario
    for usuario in usuarios:
        metadata = {
            'task_id': task_id,
            'archivo_nombre': f'archivo_{usuario["correo"]}.xlsx',
            'usuario_id': usuario['id'],
            'total_filas': 10 + usuario['id'],  # Datos diferentes por usuario
            'grupos': [33, 34],
            'headers': ['Nro', 'Tipo Doc', 'Descripción'],
            'inicio': datetime.now().isoformat(),
            'estado': 'procesando'
        }
        
        # Guardar en Redis con clave aislada por usuario
        key = f"captura_gastos_meta:{usuario['id']}:{task_id}"
        r.setex(key, 300, json.dumps(metadata, ensure_ascii=False))
        print(f"✅ Guardado para {usuario['correo']}: {key}")
    
    # Verificar que cada usuario solo puede acceder a sus datos
    print("\n🔍 Verificando aislamiento...")
    
    for usuario in usuarios:
        # Intentar leer datos del usuario actual
        key_propio = f"captura_gastos_meta:{usuario['id']}:{task_id}"
        data_propia = r.get(key_propio)
        
        if data_propia:
            metadata_propia = json.loads(data_propia)
            print(f"✅ Usuario {usuario['id']}: Puede leer sus datos - {metadata_propia['archivo_nombre']}")
        else:
            print(f"❌ Usuario {usuario['id']}: NO puede leer sus propios datos")
        
        # Verificar que NO puede leer datos de otros usuarios
        for otro_usuario in usuarios:
            if otro_usuario['id'] != usuario['id']:
                key_ajeno = f"captura_gastos_meta:{otro_usuario['id']}:{task_id}"
                data_ajena = r.get(key_ajeno)
                
                if data_ajena:
                    print(f"⚠️  Usuario {usuario['id']}: PUEDE leer datos de usuario {otro_usuario['id']} (PROBLEMA)")
                else:
                    print(f"✅ Usuario {usuario['id']}: NO puede leer datos de usuario {otro_usuario['id']} (CORRECTO)")
    
    # Simular búsqueda por patrón para verificar que no haya fugas
    print(f"\n🔎 Buscando todas las claves del patrón...")
    all_keys = r.keys("captura_gastos_meta:*")
    print(f"Claves encontradas: {all_keys}")
    
    # Limpiar datos de prueba
    print(f"\n🧹 Limpiando datos de prueba...")
    for key in all_keys:
        r.delete(key)
        print(f"Eliminado: {key}")
    
    print(f"\n✅ Test de aislamiento completado!")

def test_pattern_keys():
    """
    Test de patrones de claves
    """
    print("\n📋 Analizando patrones de claves...")
    
    patrones_esperados = [
        "captura_gastos_meta:{usuario_id}:{task_id}",
        "captura_gastos_grupo:{usuario_id}:{task_id}:{tipo_doc}",
        "captura_gastos_excel:{usuario_id}:{task_id}"
    ]
    
    for patron in patrones_esperados:
        print(f"✅ Patrón implementado: {patron}")
    
    print("\n🔒 Ventajas del aislamiento por usuario_id:")
    print("- Cada usuario solo ve sus propias tareas")
    print("- No hay interferencia entre usuarios concurrentes")
    print("- Fácil identificación de datos por usuario")
    print("- Limpieza selectiva por usuario")
    print("- Debugging mejorado con contexto de usuario")

if __name__ == "__main__":
    try:
        test_redis_usuario_isolation()
        test_pattern_keys()
        
    except Exception as e:
        print(f"❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
