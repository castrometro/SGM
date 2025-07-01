#!/usr/bin/env python3
"""
Script de prueba para validar la refactorización de nombres en inglés.
Verifica que todos los componentes estén correctamente implementados.
"""

import sys
import os

# Agregar el path del proyecto
sys.path.append('/root/SGM/backend')

def test_imports():
    """Prueba que todos los imports necesarios funcionen correctamente."""
    print("🔍 Probando imports...")
    
    try:
        # Test import del nuevo archivo de tasks
        from contabilidad.tasks_nombres_ingles import (
            crear_chain_nombres_ingles,
            validar_nombre_archivo_nombres_ingles,
            verificar_archivo_nombres_ingles,
            validar_contenido_nombres_ingles,
            procesar_nombres_ingles_raw,
            finalizar_procesamiento_nombres_ingles,
            _validar_archivo_nombres_ingles_excel
        )
        print("✅ Tasks de nombres en inglés importadas correctamente")
        
        # Test import de las vistas
        from contabilidad.views.nombres_ingles import (
            NombreInglesViewSet,
            cargar_nombres_ingles,
            NombresEnInglesView,
            NombresEnInglesUploadViewSet
        )
        print("✅ Vistas de nombres en inglés importadas correctamente")
        
        # Test import de modelos
        from contabilidad.models import NombreIngles, UploadLog
        print("✅ Modelos importados correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_chain_structure():
    """Prueba que la estructura del chain esté correcta."""
    print("\n🔍 Probando estructura del chain...")
    
    try:
        from contabilidad.tasks_nombres_ingles import crear_chain_nombres_ingles
        
        # Crear un chain de prueba (sin ejecutar)
        chain_test = crear_chain_nombres_ingles(1)
        
        # Verificar que es un objeto chain
        from celery import chain
        if isinstance(chain_test, chain):
            print("✅ Chain creado correctamente")
            print(f"✅ Número de tasks en el chain: {len(chain_test.tasks)}")
            return True
        else:
            print("❌ El objeto retornado no es un chain válido")
            return False
            
    except Exception as e:
        print(f"❌ Error creando chain: {e}")
        return False

def test_validation_function():
    """Prueba la función de validación auxiliar."""
    print("\n🔍 Probando función de validación...")
    
    try:
        from contabilidad.tasks_nombres_ingles import _validar_archivo_nombres_ingles_excel
        
        # Crear archivo de prueba temporal
        import tempfile
        import pandas as pd
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Crear un Excel de prueba
            df_test = pd.DataFrame({
                'codigo': ['1000', '2000', '3000'],
                'nombre_en': ['Cash', 'Inventory', 'Assets']
            })
            df_test.to_excel(tmp.name, index=False)
            
            # Probar validación
            resultado = _validar_archivo_nombres_ingles_excel(tmp.name)
            
            if isinstance(resultado, dict) and 'es_valido' in resultado:
                print(f"✅ Función de validación funciona correctamente")
                print(f"   - Es válido: {resultado['es_valido']}")
                print(f"   - Estadísticas: {resultado.get('estadisticas', {})}")
                
                # Limpiar archivo temporal
                os.unlink(tmp.name)
                return True
            else:
                print("❌ La función de validación no retorna el formato esperado")
                os.unlink(tmp.name)
                return False
                
    except Exception as e:
        print(f"❌ Error probando validación: {e}")
        return False

def test_file_structure():
    """Verifica que todos los archivos necesarios existan."""
    print("\n🔍 Verificando estructura de archivos...")
    
    files_to_check = [
        '/root/SGM/backend/contabilidad/tasks_nombres_ingles.py',
        '/root/SGM/backend/contabilidad/views/nombres_ingles.py',
        '/root/SGM/REFACTORIZACION_NOMBRES_INGLES_COMPLETADA.md'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - No encontrado")
            all_exist = False
    
    return all_exist

def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas de refactorización de nombres en inglés...")
    print("=" * 60)
    
    tests = [
        ("Estructura de archivos", test_file_structure),
        ("Imports", test_imports),
        ("Estructura del Chain", test_chain_structure),
        ("Función de validación", test_validation_function),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La refactorización está completa.")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar implementación.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
