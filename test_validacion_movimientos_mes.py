# Test de Validación de Nombre de Archivo - MovimientosMes

from backend.nomina.utils.validaciones import validar_nombre_archivo_movimientos_mes

def test_validacion_movimientos_mes():
    """Test de validación de nombres de archivo para MovimientosMes"""
    
    print("🧪 TESTING: Validación de nombres de archivo MovimientosMes")
    print("=" * 60)
    
    # Casos de prueba
    casos_prueba = [
        # ✅ CASOS VÁLIDOS
        {
            "nombre": "202503_movimientos_mes_12345678.xlsx",
            "rut_cliente": "12345678-9",
            "periodo": "2025-03",
            "esperado": True,
            "descripcion": "✅ Formato correcto completo"
        },
        {
            "nombre": "202412_movimientos_mes_87654321.xlsx",
            "rut_cliente": "87654321-0",
            "periodo": "2024-12",
            "esperado": True,
            "descripcion": "✅ Formato correcto diciembre"
        },
        {
            "nombre": "202501_movimientos_mes_99999999.xls",
            "rut_cliente": None,
            "periodo": None,
            "esperado": True,
            "descripcion": "✅ Formato .xls válido"
        },
        
        # ❌ CASOS INVÁLIDOS - Formato
        {
            "nombre": "202503-movimientos-mes-12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Guiones en lugar de guión bajo"
        },
        {
            "nombre": "movimientos_mes_202503_12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Orden incorrecto"
        },
        {
            "nombre": "202503_libro_remuneraciones_12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Tipo de archivo incorrecto"
        },
        
        # ❌ CASOS INVÁLIDOS - Fecha
        {
            "nombre": "202513_movimientos_mes_12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Mes inválido (13)"
        },
        {
            "nombre": "201912_movimientos_mes_12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Año fuera de rango"
        },
        {
            "nombre": "20250_movimientos_mes_12345678.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Formato de fecha incorrecto"
        },
        
        # ❌ CASOS INVÁLIDOS - RUT
        {
            "nombre": "202503_movimientos_mes_12345678.xlsx",
            "rut_cliente": "87654321-0",
            "periodo": "2025-03",
            "esperado": False,
            "descripcion": "❌ RUT no coincide"
        },
        {
            "nombre": "202503_movimientos_mes_123456789.xlsx",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ RUT muy largo"
        },
        
        # ❌ CASOS INVÁLIDOS - Período
        {
            "nombre": "202503_movimientos_mes_12345678.xlsx",
            "rut_cliente": "12345678-9",
            "periodo": "2025-04",
            "esperado": False,
            "descripcion": "❌ Período no coincide"
        },
        
        # ❌ CASOS INVÁLIDOS - Extensión
        {
            "nombre": "202503_movimientos_mes_12345678.pdf",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Extensión incorrecta"
        },
        {
            "nombre": "202503_movimientos_mes_12345678",
            "rut_cliente": None,
            "periodo": None,
            "esperado": False,
            "descripcion": "❌ Sin extensión"
        }
    ]
    
    # Ejecutar pruebas
    total_casos = len(casos_prueba)
    casos_exitosos = 0
    casos_fallidos = 0
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"\n📝 Caso {i}/{total_casos}: {caso['descripcion']}")
        print(f"   Archivo: {caso['nombre']}")
        
        resultado = validar_nombre_archivo_movimientos_mes(
            caso['nombre'],
            rut_cliente=caso['rut_cliente'],
            periodo_cierre=caso['periodo']
        )
        
        es_valido = resultado['es_valido']
        
        if es_valido == caso['esperado']:
            print(f"   ✅ ÉXITO: Resultado esperado ({caso['esperado']})")
            casos_exitosos += 1
        else:
            print(f"   ❌ FALLO: Esperado {caso['esperado']}, obtuvo {es_valido}")
            if not es_valido and resultado.get('errores'):
                print(f"   📋 Errores: {resultado['errores']}")
            casos_fallidos += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN DE PRUEBAS:")
    print(f"   ✅ Casos exitosos: {casos_exitosos}/{total_casos}")
    print(f"   ❌ Casos fallidos: {casos_fallidos}/{total_casos}")
    print(f"   📈 Porcentaje de éxito: {(casos_exitosos/total_casos)*100:.1f}%")
    
    if casos_fallidos == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! La validación funciona correctamente.")
    else:
        print(f"\n⚠️  {casos_fallidos} pruebas fallaron. Revisar implementación.")
    
    return casos_fallidos == 0

if __name__ == "__main__":
    test_validacion_movimientos_mes()
