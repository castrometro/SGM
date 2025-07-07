#!/usr/bin/env python3
"""
Script de prueba para validar el archivo 202503_libro_remuneraciones_completo.xlsx
"""

import os
import sys
import django

# Setup Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.nomina.utils.validaciones import validar_nombre_archivo_libro_remuneraciones

def probar_archivo_202503():
    """
    Prueba específica para el archivo que falló
    """
    print("🧪 PRUEBA DEL ARCHIVO 202503_libro_remuneraciones_completo.xlsx")
    print("=" * 60)
    
    nombre_archivo = "202503_libro_remuneraciones_completo.xlsx"
    
    # Caso 1: Sin período del cierre
    print("\n1. Validación sin período del cierre:")
    resultado = validar_nombre_archivo_libro_remuneraciones(nombre_archivo)
    print(f"   ¿Es válido? {resultado['es_valido']}")
    print(f"   Errores: {resultado['errores']}")
    print(f"   Advertencias: {resultado['advertencias']}")
    print(f"   Estadísticas: {resultado['estadisticas']}")
    
    # Caso 2: Con período del cierre coincidente
    print("\n2. Validación con período del cierre coincidente (202503):")
    resultado = validar_nombre_archivo_libro_remuneraciones(nombre_archivo, periodo_cierre="202503")
    print(f"   ¿Es válido? {resultado['es_valido']}")
    print(f"   Errores: {resultado['errores']}")
    print(f"   Advertencias: {resultado['advertencias']}")
    print(f"   Estadísticas: {resultado['estadisticas']}")
    
    # Caso 3: Con período del cierre NO coincidente
    print("\n3. Validación con período del cierre NO coincidente (202504):")
    resultado = validar_nombre_archivo_libro_remuneraciones(nombre_archivo, periodo_cierre="202504")
    print(f"   ¿Es válido? {resultado['es_valido']}")
    print(f"   Errores: {resultado['errores']}")
    print(f"   Advertencias: {resultado['advertencias']}")
    print(f"   Estadísticas: {resultado['estadisticas']}")
    
    # Caso 4: Con período del cierre en formato alternativo
    print("\n4. Validación con período del cierre en formato MM/AAAA (03/2025):")
    resultado = validar_nombre_archivo_libro_remuneraciones(nombre_archivo, periodo_cierre="03/2025")
    print(f"   ¿Es válido? {resultado['es_valido']}")
    print(f"   Errores: {resultado['errores']}")
    print(f"   Advertencias: {resultado['advertencias']}")
    print(f"   Estadísticas: {resultado['estadisticas']}")

def probar_otros_formatos():
    """
    Prueba otros formatos de archivos
    """
    print("\n\n🧪 PRUEBAS DE OTROS FORMATOS DE ARCHIVO")
    print("=" * 60)
    
    casos = [
        ("12345678_LibroRemuneraciones.xlsx", None, "Formato básico con RUT"),
        ("12345678_LibroRemuneraciones_202503.xlsx", "202503", "Formato con RUT y período"),
        ("87654321_LibroRemuneraciones_202504.xlsx", "202503", "Formato con RUT y período NO coincidente"),
        ("12345678_LibroRemuneraciones_202503.xlsx", "03/2025", "Formato con RUT y período en formato alternativo"),
    ]
    
    for nombre_archivo, periodo_cierre, descripcion in casos:
        print(f"\n📋 {descripcion}:")
        print(f"   Archivo: {nombre_archivo}")
        print(f"   Período cierre: {periodo_cierre}")
        
        resultado = validar_nombre_archivo_libro_remuneraciones(
            nombre_archivo, 
            rut_cliente="12.345.678-9", 
            periodo_cierre=periodo_cierre
        )
        
        print(f"   ¿Es válido? {resultado['es_valido']}")
        if resultado['errores']:
            print(f"   Errores: {resultado['errores']}")
        if resultado['advertencias']:
            print(f"   Advertencias: {resultado['advertencias']}")
        print(f"   Estadísticas: {resultado['estadisticas']}")

def main():
    """
    Función principal
    """
    print("🔍 VALIDACIÓN DE NOMBRES DE ARCHIVO - LIBRO DE REMUNERACIONES")
    print("=" * 70)
    
    try:
        probar_archivo_202503()
        probar_otros_formatos()
        print("\n✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
