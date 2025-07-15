#!/usr/bin/env python3
"""
Script de prueba para verificar la autenticación de Redis desde el módulo Streamlit
"""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar path del loader de Streamlit
sys.path.append('/root/SGM/streamlit_conta/data')

def test_redis_auth():
    """Probar la autenticación de Redis desde el loader de Streamlit"""
    
    logger.info("🧪 Iniciando test de autenticación Redis para Streamlit...")
    
    # Simular variables de entorno como en Docker
    os.environ['REDIS_HOST'] = 'redis'
    os.environ['REDIS_PORT'] = '6379'
    os.environ['REDIS_PASSWORD'] = 'Redis_Password_2025!'
    os.environ['REDIS_DB_CONTABILIDAD'] = '1'
    
    try:
        # Importar el loader
        from loader_contabilidad import conectar_redis, cargar_esf_desde_redis, listar_esf_disponibles
        
        logger.info("✅ Módulos importados correctamente")
        
        # Test 1: Conectar a Redis
        logger.info("🔗 Test 1: Conectando a Redis...")
        redis_client = conectar_redis()
        
        if redis_client:
            logger.info("✅ Conexión a Redis exitosa")
            
            # Test 2: Verificar que hay datos en Redis
            logger.info("📋 Test 2: Listando ESF disponibles...")
            esf_list = listar_esf_disponibles(cliente_id=1)
            
            if esf_list.get('total_esf', 0) > 0:
                logger.info(f"✅ Encontrados {esf_list['total_esf']} ESF en Redis")
                
                # Mostrar primer ESF disponible
                primer_esf = esf_list['esf_disponibles'][0]
                logger.info(f"📊 Primer ESF: {primer_esf['periodo']} - {primer_esf['test_type']}")
                
                # Test 3: Cargar ESF específico
                logger.info("📥 Test 3: Cargando ESF específico...")
                esf_data = cargar_esf_desde_redis(
                    cliente_id=primer_esf['cliente_id'],
                    periodo=primer_esf['periodo'],
                    test_type=primer_esf['test_type']
                )
                
                if esf_data:
                    logger.info("✅ ESF cargado exitosamente")
                    logger.info(f"📈 Total activos: ${esf_data.get('total_activos', 0):,.2f}")
                    logger.info(f"⚖️ Balance cuadrado: {esf_data.get('balance_cuadrado', False)}")
                else:
                    logger.warning("⚠️ No se pudo cargar el ESF específico")
                    
            else:
                logger.warning("⚠️ No se encontraron ESF en Redis")
                
        else:
            logger.error("❌ No se pudo conectar a Redis")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en el test: {e}")
        return False
    
    logger.info("🎉 Test completado exitosamente")
    return True


def test_full_loader():
    """Probar el cargador completo de datos"""
    
    logger.info("🧪 Test del cargador completo de datos...")
    
    try:
        # Simular variables de entorno
        os.environ['REDIS_HOST'] = 'redis'
        os.environ['REDIS_PORT'] = '6379'
        os.environ['REDIS_PASSWORD'] = 'Redis_Password_2025!'
        os.environ['REDIS_DB_CONTABILIDAD'] = '1'
        
        from loader_contabilidad import cargar_datos_redis
        
        # Cargar datos desde Redis
        datos = cargar_datos_redis(cliente_id=1, periodo="2025-07", test_type="finalizacion_automatica")
        
        logger.info(f"📊 Fuente de datos: {datos.get('fuente', 'desconocida')}")
        
        if datos.get('fuente') == 'redis':
            logger.info("✅ Datos cargados desde Redis exitosamente")
            logger.info(f"🏢 Cliente: {datos.get('cliente', {}).get('nombre', 'N/A')}")
            logger.info(f"📅 Período: {datos.get('cierre', {}).get('periodo', 'N/A')}")
            
            # Verificar si hay JSON raw para el sidebar
            if 'raw_json' in datos:
                logger.info("✅ JSON raw disponible para el sidebar")
            else:
                logger.warning("⚠️ No hay JSON raw disponible")
                
        else:
            logger.warning("⚠️ Fallback a datos de ejemplo")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test del cargador: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DE AUTENTICACIÓN REDIS PARA STREAMLIT")
    print("=" * 60)
    
    # Cambiar a host local para pruebas fuera de Docker
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        os.environ['REDIS_HOST'] = 'localhost'
        logger.info("🏠 Usando Redis en localhost para pruebas locales")
    
    success_auth = test_redis_auth()
    print()
    success_loader = test_full_loader()
    
    print("\n" + "=" * 60)
    if success_auth and success_loader:
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        sys.exit(0)
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        sys.exit(1)
