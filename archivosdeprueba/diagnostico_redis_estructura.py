#!/usr/bin/env python3
"""
Script de diagnóstico para entender la estructura de datos en Redis
y la discrepancia con lo que espera Streamlit
"""

import json
import redis
import os
from pprint import pprint

def conectar_redis():
    """Conectar a Redis DB 1 (contabilidad)"""
    try:
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', 'Redis_Password_2025!')
        redis_db = int(os.getenv('REDIS_DB_CONTABILIDAD', '1'))
        
        print(f"🔗 Conectando a Redis: {redis_host}:{redis_port} DB:{redis_db}")
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        if redis_client.ping():
            print("✅ Conectado a Redis")
            return redis_client
        else:
            print("❌ No se pudo conectar a Redis")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return None

def analizar_estructura_redis():
    """Analizar la estructura de datos en Redis"""
    redis_client = conectar_redis()
    if not redis_client:
        return
    
    print("\n" + "="*60)
    print("📊 DIAGNÓSTICO DE ESTRUCTURA DE DATOS EN REDIS")
    print("="*60)
    
    # Buscar todas las claves relacionadas con contabilidad
    patterns = [
        "sgm:contabilidad:*",
        "sgm:contabilidad:*:movimientos",
        "sgm:contabilidad:*:esf",
        "sgm:contabilidad:*:pruebas:*"
    ]
    
    for pattern in patterns:
        print(f"\n🔍 Buscando claves con patrón: {pattern}")
        keys = redis_client.keys(pattern)
        print(f"   Encontradas {len(keys)} claves")
        
        for key in keys[:5]:  # Mostrar solo las primeras 5
            print(f"   - {key}")
            try:
                data = redis_client.get(key)
                if data:
                    json_data = json.loads(data)
                    print(f"     Tipo: {type(json_data)}")
                    if isinstance(json_data, dict):
                        print(f"     Claves principales: {list(json_data.keys())[:10]}")
                        
                        # Buscar específicamente 'movimientos'
                        if 'movimientos' in json_data:
                            movs = json_data['movimientos']
                            print(f"     ✅ Tiene 'movimientos': {type(movs)}, longitud: {len(movs) if isinstance(movs, list) else 'N/A'}")
                            if isinstance(movs, list) and len(movs) > 0:
                                print(f"     Primer movimiento: {list(movs[0].keys()) if isinstance(movs[0], dict) else movs[0]}")
                        
                        # Analizar estructura de ESF
                        if 'activos' in json_data:
                            print(f"     ✅ Estructura ESF detectada")
                            activos = json_data['activos']
                            if 'corrientes' in activos and 'grupos' in activos['corrientes']:
                                grupos = activos['corrientes']['grupos']
                                for grupo_nombre, grupo_data in grupos.items():
                                    if 'cuentas' in grupo_data:
                                        cuentas = grupo_data['cuentas']
                                        print(f"       Grupo '{grupo_nombre}': {len(cuentas)} cuentas")
                                        
                                        # Analizar movimientos en cuentas
                                        total_movimientos = 0
                                        for cuenta in cuentas:
                                            if 'movimientos' in cuenta:
                                                movs_cuenta = cuenta['movimientos']
                                                total_movimientos += len(movs_cuenta)
                                        
                                        if total_movimientos > 0:
                                            print(f"       Total movimientos en cuentas: {total_movimientos}")
                                            # Mostrar estructura del primer movimiento
                                            for cuenta in cuentas:
                                                if 'movimientos' in cuenta and len(cuenta['movimientos']) > 0:
                                                    primer_mov = cuenta['movimientos'][0]
                                                    print(f"       Estructura movimiento: {list(primer_mov.keys()) if isinstance(primer_mov, dict) else type(primer_mov)}")
                                                    break
                        
            except Exception as e:
                print(f"     ❌ Error leyendo datos: {e}")
        
        if len(keys) > 5:
            print(f"   ... y {len(keys) - 5} claves más")

def analizar_archivo_ejemplo():
    """Analizar el archivo de ejemplo para comparar estructuras"""
    print("\n" + "="*60)
    print("📁 ANÁLISIS DEL ARCHIVO DE EJEMPLO")
    print("="*60)
    
    try:
        with open('/root/SGM/streamlit_conta/data/contabilidad_ejemplo.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ Archivo de ejemplo cargado exitosamente")
        print(f"Claves principales: {list(data.keys())}")
        
        if 'cierres' in data and len(data['cierres']) > 0:
            cierre = data['cierres'][0]
            if 'movimientos' in cierre:
                movimientos = cierre['movimientos']
                print(f"Movimientos en ejemplo: {len(movimientos)}")
                if len(movimientos) > 0:
                    primer_mov = movimientos[0]
                    print(f"Estructura movimiento ejemplo: {list(primer_mov.keys())}")
                    print("Primer movimiento:")
                    pprint(primer_mov)
        
    except Exception as e:
        print(f"❌ Error leyendo archivo de ejemplo: {e}")

def analizar_json_adjunto():
    """Analizar el JSON adjunto que representa la estructura real"""
    print("\n" + "="*60)
    print("📄 ANÁLISIS DEL JSON ADJUNTO (ESTRUCTURA REAL)")
    print("="*60)
    
    try:
        with open('/root/SGM/streamlit_conta/data/FRASER_ALEXANDER_CHILE_S.A._2025-08_Estado_de_Situación_Financiera___State_of_Financial_Situation_7.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON adjunto cargado exitosamente")
        print(f"Claves principales: {list(data.keys())}")
        
        # Analizar estructura
        total_movimientos = 0
        estructura_movimiento = None
        
        for seccion in ['activos', 'pasivos', 'patrimonio']:
            if seccion in data:
                print(f"\n📊 Analizando sección: {seccion}")
                seccion_data = data[seccion]
                
                for categoria in ['corrientes', 'no_corrientes', 'capital', 'resultados']:
                    if categoria in seccion_data and 'grupos' in seccion_data[categoria]:
                        grupos = seccion_data[categoria]['grupos']
                        
                        for grupo_nombre, grupo_data in grupos.items():
                            if 'cuentas' in grupo_data:
                                cuentas = grupo_data['cuentas']
                                print(f"  Grupo '{grupo_nombre}': {len(cuentas)} cuentas")
                                
                                for cuenta in cuentas:
                                    if 'movimientos' in cuenta:
                                        movs = cuenta['movimientos']
                                        total_movimientos += len(movs)
                                        
                                        if estructura_movimiento is None and len(movs) > 0:
                                            estructura_movimiento = movs[0]
        
        print(f"\n📈 Total de movimientos encontrados: {total_movimientos}")
        if estructura_movimiento:
            print("🔍 Estructura de movimiento encontrada:")
            print(f"  Claves: {list(estructura_movimiento.keys())}")
            print("  Ejemplo:")
            pprint(estructura_movimiento)
        else:
            print("⚠️ No se encontraron movimientos con datos")
            
        # Buscar movimientos con datos reales
        print("\n🔍 Buscando movimientos con datos más completos...")
        for seccion in ['activos', 'pasivos', 'patrimonio']:
            if seccion in data:
                seccion_data = data[seccion]
                for categoria in ['corrientes', 'no_corrientes', 'capital', 'resultados']:
                    if categoria in seccion_data and 'grupos' in seccion_data[categoria]:
                        grupos = seccion_data[categoria]['grupos']
                        for grupo_nombre, grupo_data in grupos.items():
                            if 'cuentas' in grupo_data:
                                for cuenta in grupo_data['cuentas']:
                                    if 'movimientos' in cuenta and len(cuenta['movimientos']) > 0:
                                        mov = cuenta['movimientos'][0]
                                        if len(mov.keys()) > 1:  # Movimiento con más datos
                                            print(f"  Cuenta {cuenta.get('codigo', 'N/A')}: {len(cuenta['movimientos'])} movimientos")
                                            print(f"    Estructura: {list(mov.keys())}")
                                            print(f"    Ejemplo: {mov}")
                                            return  # Solo mostrar el primero que encontremos
        
    except Exception as e:
        print(f"❌ Error leyendo JSON adjunto: {e}")

def generar_recomendaciones():
    """Generar recomendaciones para solucionar el problema"""
    print("\n" + "="*60)
    print("💡 RECOMENDACIONES PARA SOLUCIONAR EL PROBLEMA")
    print("="*60)
    
    print("""
1. 🔍 PROBLEMA IDENTIFICADO:
   - Streamlit espera una lista plana de movimientos con columnas específicas
   - Redis contiene ESF (Estado de Situación Financiera) con estructura jerárquica
   - Los movimientos están anidados dentro de cuentas, dentro de grupos, dentro de categorías

2. 🛠️ SOLUCIONES PROPUESTAS:

   A) ADAPTAR EL CÓDIGO DE STREAMLIT:
      - Modificar la función mostrar() para extraer movimientos de la estructura ESF
      - Aplanar la estructura jerárquica en una lista de movimientos
      - Agregar campos derivados (cuenta, grupo, categoría)

   B) CREAR TRANSFORMADOR DE DATOS:
      - Función que convierta ESF → lista de movimientos
      - Preservar información de contexto (cuenta, saldo, etc.)
      - Validar y completar campos faltantes

   C) MEJORAR VALIDACIÓN:
      - Detectar automáticamente el tipo de estructura
      - Mostrar errores informativos al usuario
      - Fallback a datos de ejemplo si es necesario

3. 📋 CAMPOS DISPONIBLES VS ESPERADOS:
   
   Esperados por Streamlit:
   - fecha, centro_costo, tipo_documento, debe, haber, descripcion
   
   Disponibles en ESF:
   - numero_documento (en movimientos)
   - codigo, nombre_es, nombre_en (en cuenta)
   - total_debe, total_haber, saldo_final (en cuenta)
   - movimientos[] (lista)

4. 🎯 ACCIÓN RECOMENDADA:
   - Implementar función esf_to_movimientos()
   - Actualizar views/movimientos.py para detectar y manejar ambos formatos
   - Agregar logging para depuración
""")

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico de estructura de datos Redis vs Streamlit")
    
    analizar_archivo_ejemplo()
    analizar_json_adjunto()
    analizar_estructura_redis()
    generar_recomendaciones()
    
    print("\n✅ Diagnóstico completado")
