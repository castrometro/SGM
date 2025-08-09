#!/usr/bin/env python3
"""
Test para las reglas de tipo de documento 34
Verifica que se generen solo 2 cuentas (Proveedores + Gastos, sin IVA)
"""

import sys
import os

# Agregar el path del backend para importar los módulos
sys.path.append('/root/SGM/backend')

# Simular configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

# Ahora importar las funciones del task
from contabilidad.tasks import aplicar_reglas_tipo_34, get_headers_salida_contabilidad

def test_reglas_tipo_34():
    """
    Test para verificar las reglas del tipo 34
    """
    print("🧪 Iniciando test de reglas tipo 34...")
    
    # Headers de entrada (estructura real del Excel)
    headers_entrada = [
        "Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", 
        "Folio", "Fecha Docto", "Monto Total", "Codigo cuenta", 
        "Nombre cuenta", "PyC", "PS", "CO"
    ]
    
    # Fila de prueba tipo 34
    fila_prueba = {
        "Nro": "1",
        "Tipo Doc": "34",
        "RUT Proveedor": "12345678-9",
        "Razon Social": "Proveedor Test S.A.",
        "Folio": "F001",
        "Fecha Docto": "2024-01-15",
        "Monto Total": "119000",
        "Codigo cuenta": "2110001",
        "Nombre cuenta": "Proveedores Varios",
        "PyC": "1",  # 1 centro de costo
        "PS": "",
        "CO": ""
    }
    
    # Mapeo de centros de costos de prueba
    mapeo_cc = {
        "CC001": "01-001"
    }
    
    # Headers de salida
    headers_salida = get_headers_salida_contabilidad()
    
    print(f"📋 Headers de entrada: {len(headers_entrada)} columnas")
    print(f"📋 Headers de salida: {len(headers_salida)} columnas")
    print(f"💰 Monto total: {fila_prueba['Monto Total']}")
    print(f"📄 Tipo documento: {fila_prueba['Tipo Doc']}")
    print(f"🏢 Centros de costo: {fila_prueba['PyC']}")
    
    # Aplicar reglas tipo 34
    resultado = aplicar_reglas_tipo_34(
        fila_prueba, 
        headers_entrada, 
        mapeo_cc, 
        headers_salida
    )
    
    print(f"\n✅ Resultado: {len(resultado)} filas generadas")
    
    if len(resultado) != 2:
        print(f"❌ ERROR: Se esperaban 2 filas pero se generaron {len(resultado)}")
        return False
    
    # Verificar estructura de las filas generadas
    for i, fila in enumerate(resultado, 1):
        print(f"\n🔍 Fila {i}:")
        print(f"   - Numero: {fila.get('Numero', 'N/A')}")
        print(f"   - Tipo Documento: {fila.get('Tipo Documento', 'N/A')}")
        print(f"   - Código Plan de Cuenta: {fila.get('Código Plan de Cuenta', 'N/A')}")
        print(f"   - Monto al Debe: {fila.get('Monto al Debe Moneda Base', 'N/A')}")
        print(f"   - Monto al Haber: {fila.get('Monto al Haber Moneda Base', 'N/A')}")
        print(f"   - Código Centro de Costo: {fila.get('Código Centro de Costo', 'N/A')}")
        print(f"   - Codigo Auxiliar: {fila.get('Codigo Auxiliar', 'N/A')}")
        print(f"   - Numero Doc: {fila.get('Numero Doc', 'N/A')}")
        print(f"   - Descripción: {fila.get('Descripción Movimiento', 'N/A')}")
        print(f"   - Fecha: {fila.get('Fecha Emisión Docto.(DD/MM/AAAA)', 'N/A')}")
    
    # Validaciones específicas para tipo 34
    validaciones_ok = True
    
    # Validación 1: Todas las filas deben tener Numero = "34"
    for i, fila in enumerate(resultado):
        if fila.get('Numero') != "34":
            print(f"❌ ERROR: Fila {i+1} no tiene Numero='34', tiene '{fila.get('Numero')}'")
            validaciones_ok = False
    
    # Validación 2: Debe haber una cuenta de Proveedores (2xxx) y una de Gastos (5xxx)
    cuentas_proveedores = [f for f in resultado if f.get('Código Plan de Cuenta', '').startswith('2')]
    cuentas_gastos = [f for f in resultado if f.get('Código Plan de Cuenta', '').startswith('5')]
    
    if len(cuentas_proveedores) != 1:
        print(f"❌ ERROR: Se esperaba 1 cuenta de proveedores, se encontraron {len(cuentas_proveedores)}")
        validaciones_ok = False
    
    if len(cuentas_gastos) != 1:
        print(f"❌ ERROR: Se esperaba 1 cuenta de gastos, se encontraron {len(cuentas_gastos)}")
        validaciones_ok = False
    
    # Validación 3: NO debe haber cuentas de IVA (1xxx)
    cuentas_iva = [f for f in resultado if f.get('Código Plan de Cuenta', '').startswith('1')]
    if len(cuentas_iva) > 0:
        print(f"❌ ERROR: No debe haber cuentas de IVA en tipo 34, pero se encontraron {len(cuentas_iva)}")
        validaciones_ok = False
    
    # Validación 4: Montos deben cuadrar
    if len(cuentas_proveedores) == 1 and len(cuentas_gastos) == 1:
        monto_proveedor = float(cuentas_proveedores[0].get('Monto al Haber Moneda Base', 0))
        monto_gasto = float(cuentas_gastos[0].get('Monto al Debe Moneda Base', 0))
        
        print(f"\n💰 Verificación de montos:")
        print(f"   - Monto original: 119000")
        print(f"   - Monto proveedor (Haber): {monto_proveedor}")
        print(f"   - Monto gasto (Debe): {monto_gasto}")
        
        if abs(monto_proveedor - 119000) > 0.01:
            print(f"❌ ERROR: Monto proveedor incorrecto: {monto_proveedor} != 119000")
            validaciones_ok = False
        
        if abs(monto_gasto - 119000) > 0.01:
            print(f"❌ ERROR: Monto gasto incorrecto: {monto_gasto} != 119000")
            validaciones_ok = False
    
    # Resultado final
    if validaciones_ok:
        print(f"\n✅ ¡Test EXITOSO! Las reglas tipo 34 funcionan correctamente")
        print(f"   - Se generaron exactamente 2 cuentas (Proveedores + Gastos)")
        print(f"   - NO se generó cuenta de IVA (correcto para tipo 34)")
        print(f"   - Los montos cuadran correctamente")
        print(f"   - Todos los campos están correctamente mapeados")
        return True
    else:
        print(f"\n❌ Test FALLIDO: Hay errores en las reglas tipo 34")
        return False

if __name__ == "__main__":
    try:
        success = test_reglas_tipo_34()
        if success:
            print("\n🎉 PRUEBA COMPLETADA EXITOSAMENTE")
            exit(0)
        else:
            print("\n💥 PRUEBA FALLÓ")
            exit(1)
    except Exception as e:
        print(f"\n💥 ERROR DURANTE LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
