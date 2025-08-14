#!/usr/bin/env python3
"""
Test para verificar la búsqueda dinámica de columnas de cuenta
"""

def buscar_columna_codigo_cuenta(headers):
    """
    Busca la primera columna que contenga "Codigo cuenta" (con variaciones como 1, 2, etc.)
    Retorna el índice de la columna o None si no se encuentra
    """
    for i, header in enumerate(headers):
        if header and 'Codigo cuenta' in str(header):
            return i
    return None

def buscar_columna_nombre_cuenta(headers):
    """
    Busca la primera columna que contenga "Nombre cuenta" (con variaciones como 1, 2, etc.)
    Retorna el índice de la columna o None si no se encuentra
    """
    for i, header in enumerate(headers):
        if header and 'Nombre cuenta' in str(header):
            return i
    return None

def test_busqueda_dinamica_cuentas():
    """
    Test para verificar la búsqueda dinámica de columnas de cuenta
    """
    print("🧪 Test: Búsqueda Dinámica de Columnas de Cuenta")
    print("=" * 60)
    
    # Caso 1: Headers tradicionales
    headers_tradicional = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                          "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                          "PyC", "PS", "CO"]
    
    idx_codigo_trad = buscar_columna_codigo_cuenta(headers_tradicional)
    idx_nombre_trad = buscar_columna_nombre_cuenta(headers_tradicional)
    
    print(f"📊 Headers Tradicionales:")
    print(f"   Código cuenta en posición: {idx_codigo_trad} ('{headers_tradicional[idx_codigo_trad] if idx_codigo_trad is not None else 'No encontrado'}')")
    print(f"   Nombre cuenta en posición: {idx_nombre_trad} ('{headers_tradicional[idx_nombre_trad] if idx_nombre_trad is not None else 'No encontrado'}')")
    print()
    
    # Caso 2: Headers con numeración
    headers_numerados = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                        "Fecha Docto", "Monto Total", "Codigo cuenta 1", "Nombre cuenta 1", 
                        "Codigo cuenta 2", "Nombre cuenta 2", "PyC", "PS", "CO"]
    
    idx_codigo_num = buscar_columna_codigo_cuenta(headers_numerados)
    idx_nombre_num = buscar_columna_nombre_cuenta(headers_numerados)
    
    print(f"📊 Headers con Numeración:")
    print(f"   Código cuenta en posición: {idx_codigo_num} ('{headers_numerados[idx_codigo_num] if idx_codigo_num is not None else 'No encontrado'}')")
    print(f"   Nombre cuenta en posición: {idx_nombre_num} ('{headers_numerados[idx_nombre_num] if idx_nombre_num is not None else 'No encontrado'}')")
    print(f"   Nota: Toma el PRIMERO que encuentra ✅")
    print()
    
    # Caso 3: Headers desordenados
    headers_desordenado = ["Nro", "Codigo cuenta 3", "Tipo Doc", "RUT Proveedor", "Nombre cuenta 1", 
                          "Razon Social", "Folio", "Fecha Docto", "Monto Total", "PyC", "PS", "CO"]
    
    idx_codigo_des = buscar_columna_codigo_cuenta(headers_desordenado)
    idx_nombre_des = buscar_columna_nombre_cuenta(headers_desordenado)
    
    print(f"📊 Headers Desordenados:")
    print(f"   Código cuenta en posición: {idx_codigo_des} ('{headers_desordenado[idx_codigo_des] if idx_codigo_des is not None else 'No encontrado'}')")
    print(f"   Nombre cuenta en posición: {idx_nombre_des} ('{headers_desordenado[idx_nombre_des] if idx_nombre_des is not None else 'No encontrado'}')")
    print()
    
    # Caso 4: Headers sin columnas de cuenta
    headers_sin_cuenta = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                         "Fecha Docto", "Monto Total", "PyC", "PS", "CO"]
    
    idx_codigo_sin = buscar_columna_codigo_cuenta(headers_sin_cuenta)
    idx_nombre_sin = buscar_columna_nombre_cuenta(headers_sin_cuenta)
    
    print(f"📊 Headers sin Columnas de Cuenta:")
    print(f"   Código cuenta: {idx_codigo_sin} (debería ser None)")
    print(f"   Nombre cuenta: {idx_nombre_sin} (debería ser None)")
    print()
    
    # Caso 5: Headers con variaciones de nombre
    headers_variaciones = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                          "Fecha Docto", "Monto Total", "Codigo cuenta Principal", "Nombre cuenta Detalle", 
                          "PyC", "PS", "CO"]
    
    idx_codigo_var = buscar_columna_codigo_cuenta(headers_variaciones)
    idx_nombre_var = buscar_columna_nombre_cuenta(headers_variaciones)
    
    print(f"📊 Headers con Variaciones:")
    print(f"   Código cuenta en posición: {idx_codigo_var} ('{headers_variaciones[idx_codigo_var] if idx_codigo_var is not None else 'No encontrado'}')")
    print(f"   Nombre cuenta en posición: {idx_nombre_var} ('{headers_variaciones[idx_nombre_var] if idx_nombre_var is not None else 'No encontrado'}')")
    print()
    
    # Verificaciones
    print("🔍 Verificaciones:")
    print(f"   Caso tradicional: Código={idx_codigo_trad == 7}, Nombre={idx_nombre_trad == 8}")
    print(f"   Caso numerado: Toma el primero - Código={idx_codigo_num == 7}, Nombre={idx_nombre_num == 8}")
    print(f"   Caso desordenado: Encuentra correctamente - Código={idx_codigo_des == 1}, Nombre={idx_nombre_des == 4}")
    print(f"   Caso sin cuenta: Maneja ausencia - Código={idx_codigo_sin is None}, Nombre={idx_nombre_sin is None}")
    print(f"   Caso variaciones: Encuentra por substring - Código={idx_codigo_var == 7}, Nombre={idx_nombre_var == 8}")
    
    print("\n✅ Test de búsqueda dinámica de cuentas completado")
    
    # Simular respuesta del API
    print("\n📡 Ejemplo de respuesta del API:")
    api_response = {
        'headers': headers_numerados,
        'total_columnas': len(headers_numerados),
        'centros_costo': {
            'PyC': {'posicion': 11, 'nombre': 'PyC'},
            'PS': {'posicion': 12, 'nombre': 'PS'},
            'CO': {'posicion': 13, 'nombre': 'CO'}
        },
        'columnas_cuenta': {
            'codigo_cuenta': {'posicion': idx_codigo_num, 'nombre': headers_numerados[idx_codigo_num] if idx_codigo_num is not None else None},
            'nombre_cuenta': {'posicion': idx_nombre_num, 'nombre': headers_numerados[idx_nombre_num] if idx_nombre_num is not None else None}
        },
        'mensaje': 'Headers leídos exitosamente'
    }
    
    print(f"   {api_response}")

if __name__ == "__main__":
    test_busqueda_dinamica_cuentas()
