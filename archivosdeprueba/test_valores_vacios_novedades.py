# Script de testing para validar la nueva lógica de valores vacíos en novedades

def test_es_valor_vacio():
    """Prueba la función _es_valor_vacio con diferentes casos"""
    from backend.nomina.utils.GenerarDiscrepancias import _es_valor_vacio
    
    # Casos que DEBEN ser considerados vacíos (sin novedad)
    casos_vacios = [
        None,           # Null
        "",            # String vacío
        "   ",         # Solo espacios
        "-",           # Guión
        "N/A",         # Not available
        "n/a",         # Minúsculas
        "NULL",        # Null explícito
        "null",        # Null minúsculas
        "0",           # Cero como string
        "0.0",         # Cero decimal
        "0,0",         # Cero con coma
        "0.00",        # Cero con decimales
        "0,00",        # Cero con coma y decimales
        0,             # Cero numérico
        0.0,           # Cero float
    ]
    
    # Casos que NO deben ser considerados vacíos (hay novedad real)
    casos_con_valor = [
        "100",         # Valor numérico positivo
        "-50",         # Valor numérico negativo
        "1000.50",     # Decimal positivo
        "-250.75",     # Decimal negativo
        "1,500.00",    # Con separadores de miles
        "PENDIENTE",   # Texto no vacío
        "OBSERVAR",    # Otro texto
        "X",           # Caracter simple
        " 100 ",       # Número con espacios
    ]
    
    print("=== TESTING _es_valor_vacio ===\n")
    
    print("📋 Casos que DEBEN ser vacíos (sin novedad):")
    for caso in casos_vacios:
        resultado = _es_valor_vacio(caso)
        status = "✅ CORRECTO" if resultado else "❌ ERROR"
        print(f"  {repr(caso):15} → {resultado:5} {status}")
    
    print("\n📋 Casos que NO deben ser vacíos (con novedad):")  
    for caso in casos_con_valor:
        resultado = _es_valor_vacio(caso)
        status = "✅ CORRECTO" if not resultado else "❌ ERROR"
        print(f"  {repr(caso):15} → {resultado:5} {status}")
    
    # Contador de errores
    errores_vacios = sum(1 for caso in casos_vacios if not _es_valor_vacio(caso))
    errores_con_valor = sum(1 for caso in casos_con_valor if _es_valor_vacio(caso))
    total_errores = errores_vacios + errores_con_valor
    
    print(f"\n📊 RESUMEN:")
    print(f"   Casos vacíos testeados: {len(casos_vacios)}")
    print(f"   Casos con valor testeados: {len(casos_con_valor)}")
    print(f"   Errores en casos vacíos: {errores_vacios}")
    print(f"   Errores en casos con valor: {errores_con_valor}")
    print(f"   Total errores: {total_errores}")
    
    if total_errores == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print(f"⚠️  {total_errores} tests fallaron - revisar lógica")

def test_comparacion_escenarios():
    """Ejemplifica los escenarios de comparación"""
    
    print("\n=== ESCENARIOS DE COMPARACIÓN ===\n")
    
    escenarios = [
        {
            "descripcion": "Empleado sin novedad (valor vacío)",
            "libro": "150000",
            "novedades": "0",
            "expectativa": "OMITIR - No es discrepancia (sin novedad)"
        },
        {
            "descripcion": "Empleado con novedad diferente",
            "libro": "150000", 
            "novedades": "180000",
            "expectativa": "DISCREPANCIA - Valores diferentes"
        },
        {
            "descripcion": "Empleado con novedad igual",
            "libro": "150000",
            "novedades": "150000", 
            "expectativa": "OK - Sin discrepancia"
        },
        {
            "descripcion": "Novedad con valor null/vacío",
            "libro": "75000",
            "novedades": "",
            "expectativa": "OMITIR - No es discrepancia (sin novedad)"
        },
        {
            "descripcion": "Novedad con guión",
            "libro": "200000",
            "novedades": "-",
            "expectativa": "OMITIR - No es discrepancia (sin novedad)"
        },
        {
            "descripcion": "Novedad con N/A", 
            "libro": "120000",
            "novedades": "N/A",
            "expectativa": "OMITIR - No es discrepancia (sin novedad)"
        }
    ]
    
    for i, escenario in enumerate(escenarios, 1):
        from backend.nomina.utils.GenerarDiscrepancias import _es_valor_vacio
        
        es_vacio = _es_valor_vacio(escenario["novedades"])
        
        print(f"📝 Escenario {i}: {escenario['descripcion']}")
        print(f"   Libro: {escenario['libro']}")
        print(f"   Novedades: {repr(escenario['novedades'])}")
        print(f"   ¿Valor vacío? {es_vacio}")
        print(f"   Acción: {'OMITIR comparación' if es_vacio else 'COMPARAR valores'}")
        print(f"   Expectativa: {escenario['expectativa']}")
        print()

if __name__ == "__main__":
    test_es_valor_vacio()
    test_comparacion_escenarios()
