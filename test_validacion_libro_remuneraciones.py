#!/usr/bin/env python3
"""
Script para probar el sistema de validación del libro de remuneraciones
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Setup Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.nomina.utils.validaciones import (
    validar_archivo_libro_remuneraciones_excel,
    validar_nombre_archivo_libro_remuneraciones
)

def crear_archivo_excel_prueba(ruta_archivo: str, tipo_archivo: str = "valido"):
    """
    Crea archivos Excel de prueba para validar el sistema
    """
    print(f"📄 Creando archivo de prueba: {ruta_archivo} (tipo: {tipo_archivo})")
    
    if tipo_archivo == "valido":
        # Crear archivo válido
        data = {
            "Año": [2024] * 5,
            "Mes": [12] * 5,
            "Rut de la Empresa": ["12345678-9"] * 5,
            "Rut del Trabajador": ["98765432-1", "87654321-2", "76543210-3", "65432109-4", "54321098-5"],
            "Nombre": ["Juan", "María", "Carlos", "Ana", "Pedro"],
            "Apellido Paterno": ["Pérez", "González", "Rodríguez", "Martínez", "López"],
            "Apellido Materno": ["Silva", "Morales", "Hernández", "Castillo", "Vargas"],
            "Sueldo Base": [800000, 900000, 750000, 850000, 700000],
            "Horas Extras": [50000, 75000, 0, 25000, 100000],
            "Bono Asistencia": [30000, 30000, 30000, 30000, 30000],
            "Descuento AFP": [80000, 90000, 75000, 85000, 70000],
            "Descuento Salud": [64000, 72000, 60000, 68000, 56000],
        }
        
    elif tipo_archivo == "sin_columnas_obligatorias":
        # Archivo sin columnas obligatorias
        data = {
            "Sueldo Base": [800000, 900000, 750000],
            "Horas Extras": [50000, 75000, 0],
            "Bono Asistencia": [30000, 30000, 30000],
        }
        
    elif tipo_archivo == "ruts_invalidos":
        # Archivo con RUTs inválidos
        data = {
            "Año": [2024] * 3,
            "Mes": [12] * 3,
            "Rut de la Empresa": ["12345678-9"] * 3,
            "Rut del Trabajador": ["INVALID-RUT", "123", "98765432-X"],
            "Nombre": ["Juan", "María", "Carlos"],
            "Apellido Paterno": ["Pérez", "González", "Rodríguez"],
            "Apellido Materno": ["Silva", "Morales", "Hernández"],
            "Sueldo Base": [800000, 900000, 750000],
        }
        
    elif tipo_archivo == "sin_conceptos":
        # Archivo sin conceptos (solo datos de empleado)
        data = {
            "Año": [2024] * 3,
            "Mes": [12] * 3,
            "Rut de la Empresa": ["12345678-9"] * 3,
            "Rut del Trabajador": ["98765432-1", "87654321-2", "76543210-3"],
            "Nombre": ["Juan", "María", "Carlos"],
            "Apellido Paterno": ["Pérez", "González", "Rodríguez"],
            "Apellido Materno": ["Silva", "Morales", "Hernández"],
        }
        
    elif tipo_archivo == "vacio":
        # Archivo vacío
        data = {}
        
    else:
        raise ValueError(f"Tipo de archivo no reconocido: {tipo_archivo}")
    
    # Crear DataFrame y guardar
    df = pd.DataFrame(data)
    df.to_excel(ruta_archivo, index=False, engine='openpyxl')
    print(f"✅ Archivo creado exitosamente: {ruta_archivo}")


def probar_validacion_nombre_archivo():
    """
    Prueba la validación de nombres de archivo
    """
    print("\n🔍 PRUEBAS DE VALIDACIÓN DE NOMBRES DE ARCHIVO")
    print("=" * 60)
    
    casos_prueba = [
        # (nombre_archivo, rut_cliente, debe_pasar, descripcion)
        ("12345678_LibroRemuneraciones.xlsx", "12.345.678-9", True, "Archivo válido formato 1 con RUT coincidente"),
        ("12345678_LibroRemuneraciones_122024.xlsx", "12.345.678-9", True, "Archivo válido formato 2 con RUT y fecha"),
        ("202503_libro_remuneraciones_completo.xlsx", None, True, "Archivo válido formato 3 con fecha"),
        ("12345678_LibroRemuneraciones.xlsx", None, True, "Archivo válido formato 1 sin RUT cliente"),
        ("12345678_LibroRemuneraciones.xls", None, True, "Archivo válido con extensión .xls"),
        ("archivo_incorrecto.xlsx", None, False, "Nombre incorrecto"),
        ("12345678_LibroRemuneraciones.pdf", None, False, "Extensión incorrecta"),
        ("12345678_LibroRemuneraciones.xlsx", "87.654.321-0", False, "RUT no coincidente"),
        ("123456789_LibroRemuneraciones.xlsx", None, True, "RUT con 9 dígitos"),
        ("LibroRemuneraciones.xlsx", None, False, "Sin RUT en el nombre"),
        ("", None, False, "Nombre vacío"),
        ("12345678_LibroRemuneraciones<test>.xlsx", None, False, "Caracteres inválidos"),
        ("12345678_LibroRemuneraciones_012024.xlsx", None, True, "Formato 2 con mes válido"),
        ("12345678_LibroRemuneraciones_132024.xlsx", None, True, "Formato 2 con mes inválido (debería generar advertencia)"),
        ("202412_libro_remuneraciones_completo.xlsx", None, True, "Formato 3 con fecha diciembre 2024"),
        ("20241_libro_remuneraciones_completo.xlsx", None, False, "Formato 3 con fecha incompleta"),
    ]
    
    for nombre_archivo, rut_cliente, debe_pasar, descripcion in casos_prueba:
        print(f"\n🧪 Probando: {descripcion}")
        print(f"   Archivo: {nombre_archivo}")
        print(f"   RUT Cliente: {rut_cliente}")
        
        try:
            resultado = validar_nombre_archivo_libro_remuneraciones(nombre_archivo, rut_cliente)
            es_valido = resultado['es_valido']
            
            if es_valido == debe_pasar:
                print(f"   ✅ CORRECTO: {'Pasó' if es_valido else 'Falló'} como se esperaba")
            else:
                print(f"   ❌ ERROR: Se esperaba {'pasar' if debe_pasar else 'fallar'} pero {'pasó' if es_valido else 'falló'}")
            
            if not es_valido:
                print(f"   📋 Errores: {', '.join(resultado['errores'])}")
                
        except Exception as e:
            print(f"   💥 EXCEPCIÓN: {str(e)}")


def probar_validacion_contenido_archivo():
    """
    Prueba la validación del contenido de archivos
    """
    print("\n🔍 PRUEBAS DE VALIDACIÓN DE CONTENIDO DE ARCHIVO")
    print("=" * 60)
    
    # Directorio temporal para archivos de prueba
    dir_temp = "/tmp/test_validacion"
    os.makedirs(dir_temp, exist_ok=True)
    
    casos_prueba = [
        ("valido", True, "Archivo Excel válido"),
        ("sin_columnas_obligatorias", False, "Archivo sin columnas obligatorias"),
        ("ruts_invalidos", False, "Archivo con RUTs inválidos"),
        ("sin_conceptos", False, "Archivo sin conceptos de remuneración"),
        ("vacio", False, "Archivo vacío"),
    ]
    
    for tipo_archivo, debe_pasar, descripcion in casos_prueba:
        print(f"\n🧪 Probando: {descripcion}")
        
        archivo_prueba = os.path.join(dir_temp, f"test_{tipo_archivo}.xlsx")
        
        try:
            # Crear archivo de prueba
            crear_archivo_excel_prueba(archivo_prueba, tipo_archivo)
            
            # Validar contenido
            resultado = validar_archivo_libro_remuneraciones_excel(archivo_prueba)
            es_valido = resultado['es_valido']
            
            if es_valido == debe_pasar:
                print(f"   ✅ CORRECTO: {'Pasó' if es_valido else 'Falló'} como se esperaba")
            else:
                print(f"   ❌ ERROR: Se esperaba {'pasar' if debe_pasar else 'fallar'} pero {'pasó' if es_valido else 'falló'}")
            
            # Mostrar detalles
            print(f"   📊 Estadísticas: {resultado['estadisticas']}")
            
            if resultado['errores']:
                print(f"   🚨 Errores: {', '.join(resultado['errores'])}")
                
            if resultado['advertencias']:
                print(f"   ⚠️  Advertencias: {', '.join(resultado['advertencias'])}")
                
        except Exception as e:
            print(f"   💥 EXCEPCIÓN: {str(e)}")
        finally:
            # Limpiar archivo de prueba
            if os.path.exists(archivo_prueba):
                os.remove(archivo_prueba)


def probar_archivo_no_existente():
    """
    Prueba validación de archivo que no existe
    """
    print("\n🔍 PRUEBA DE ARCHIVO NO EXISTENTE")
    print("=" * 60)
    
    archivo_inexistente = "/tmp/archivo_que_no_existe.xlsx"
    
    try:
        resultado = validar_archivo_libro_remuneraciones_excel(archivo_inexistente)
        es_valido = resultado['es_valido']
        
        if not es_valido:
            print("   ✅ CORRECTO: Archivo no existente fue rechazado")
            print(f"   📋 Errores: {', '.join(resultado['errores'])}")
        else:
            print("   ❌ ERROR: Archivo no existente fue aceptado")
            
    except Exception as e:
        print(f"   💥 EXCEPCIÓN: {str(e)}")


def main():
    """
    Función principal para ejecutar todas las pruebas
    """
    print("🧪 SISTEMA DE PRUEBAS DE VALIDACIÓN DEL LIBRO DE REMUNERACIONES")
    print("=" * 70)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Ejecutar pruebas
        probar_validacion_nombre_archivo()
        probar_validacion_contenido_archivo()
        probar_archivo_no_existente()
        
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar directorio temporal
        dir_temp = "/tmp/test_validacion"
        if os.path.exists(dir_temp):
            import shutil
            shutil.rmtree(dir_temp)
            print(f"🧹 Directorio temporal limpiado: {dir_temp}")


if __name__ == "__main__":
    main()
