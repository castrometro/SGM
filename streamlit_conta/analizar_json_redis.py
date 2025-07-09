#!/usr/bin/env python3
"""
Script para analizar la estructura del JSON de finalizacion_automatica en Redis
"""

import redis
import json
import pprint
from typing import Any, Dict

def conectar_redis():
    """Conectar a Redis DB 1 (contabilidad)"""
    try:
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=1,
            password='Redis_Password_2025!',
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        if redis_client.ping():
            return redis_client
        else:
            return None
            
    except Exception as e:
        print(f"Error conectando a Redis: {e}")
        return None

def analizar_estructura(obj, nivel=0, max_nivel=3, padre=""):
    """
    Analizar recursivamente la estructura de un objeto JSON
    """
    indent = "  " * nivel
    
    if nivel > max_nivel:
        print(f"{indent}... (nivel máximo alcanzado)")
        return
    
    if isinstance(obj, dict):
        print(f"{indent}DICT con {len(obj)} claves:")
        for key, value in obj.items():
            tipo_valor = type(value).__name__
            
            if isinstance(value, dict):
                print(f"{indent}  '{key}': dict({len(value)} claves)")
                analizar_estructura(value, nivel + 2, max_nivel, f"{padre}.{key}")
            elif isinstance(value, list):
                print(f"{indent}  '{key}': list({len(value)} elementos)")
                if value and nivel < max_nivel:
                    print(f"{indent}    Primer elemento:")
                    analizar_estructura(value[0], nivel + 3, max_nivel, f"{padre}.{key}[0]")
            else:
                valor_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"{indent}  '{key}': {tipo_valor} = {valor_str}")
    
    elif isinstance(obj, list):
        print(f"{indent}LIST con {len(obj)} elementos:")
        if obj and nivel < max_nivel:
            print(f"{indent}  Primer elemento:")
            analizar_estructura(obj[0], nivel + 1, max_nivel, f"{padre}[0]")
    
    else:
        valor_str = str(obj)[:100] + "..." if len(str(obj)) > 100 else str(obj)
        print(f"{indent}{type(obj).__name__}: {valor_str}")

def main():
    print("🔍 Analizando estructura del JSON finalizacion_automatica...")
    
    redis_client = conectar_redis()
    if not redis_client:
        print("❌ No se pudo conectar a Redis")
        return
    
    # Buscar claves de finalizacion_automatica
    pattern = "sgm:contabilidad:*:*:pruebas:esf:finalizacion_automatica"
    keys = redis_client.keys(pattern)
    
    if not keys:
        print(f"❌ No se encontraron claves con patrón: {pattern}")
        return
    
    print(f"✅ Encontradas {len(keys)} claves:")
    for key in keys:
        print(f"  - {key}")
    
    # Analizar la primera clave encontrada
    key_principal = keys[0]
    print(f"\n📊 Analizando estructura de: {key_principal}")
    
    try:
        data_raw = redis_client.get(key_principal)
        if not data_raw:
            print("❌ No se pudo obtener datos de la clave")
            return
        
        data = json.loads(data_raw)
        print(f"\n🧱 ESTRUCTURA COMPLETA:")
        print("=" * 60)
        analizar_estructura(data, max_nivel=4)
        
        # Análisis específico para buscar movimientos
        print(f"\n🔍 BÚSQUEDA DE MOVIMIENTOS:")
        print("=" * 60)
        
        def buscar_movimientos(obj, ruta=""):
            movimientos_encontrados = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    nueva_ruta = f"{ruta}.{key}" if ruta else key
                    
                    if key == "movimientos" and isinstance(value, list):
                        movimientos_encontrados.append({
                            'ruta': nueva_ruta,
                            'cantidad': len(value),
                            'primer_elemento': value[0] if value else None
                        })
                    
                    if isinstance(value, (dict, list)):
                        movimientos_encontrados.extend(buscar_movimientos(value, nueva_ruta))
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    nueva_ruta = f"{ruta}[{i}]"
                    if isinstance(item, (dict, list)):
                        movimientos_encontrados.extend(buscar_movimientos(item, nueva_ruta))
            
            return movimientos_encontrados
        
        movimientos_encontrados = buscar_movimientos(data)
        
        if movimientos_encontrados:
            print(f"✅ Encontrados {len(movimientos_encontrados)} arrays de movimientos:")
            for mov in movimientos_encontrados:
                print(f"  📍 Ruta: {mov['ruta']}")
                print(f"     Cantidad: {mov['cantidad']} movimientos")
                if mov['primer_elemento']:
                    print(f"     Primer elemento:")
                    analizar_estructura(mov['primer_elemento'], nivel=3, max_nivel=1)
                print()
        else:
            print("❌ No se encontraron arrays de movimientos")
        
        # Buscar información del cliente
        print(f"\n👤 INFORMACIÓN DEL CLIENTE:")
        print("=" * 60)
        
        def buscar_cliente_info(obj, ruta=""):
            info_cliente = {}
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    nueva_ruta = f"{ruta}.{key}" if ruta else key
                    
                    if any(palabra in key.lower() for palabra in ['cliente', 'client', 'nombre', 'name']):
                        if isinstance(value, str):
                            info_cliente[nueva_ruta] = value
                    
                    if isinstance(value, dict):
                        info_cliente.update(buscar_cliente_info(value, nueva_ruta))
            
            return info_cliente
        
        info_cliente = buscar_cliente_info(data)
        
        if info_cliente:
            print("✅ Información del cliente encontrada:")
            for ruta, valor in info_cliente.items():
                print(f"  📍 {ruta}: {valor}")
        else:
            print("❌ No se encontró información específica del cliente")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
