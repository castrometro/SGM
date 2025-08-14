#!/usr/bin/env python3
"""
Test para verificar la detección automática de centros de costo por nombre
en lugar de posición fija
"""

import sys
import os

# Agregar el directorio backend al path de Python
sys.path.append('/root/SGM/backend')

def test_deteccion_centros_costo():
    """
    Test para verificar que la detección de centros de costo funciona con diferentes layouts
    """
    # Simulamos la función detectar_posiciones_centros_costo
    def detectar_posiciones_centros_costo(headers):
        mapeo_dinamico = {}
        
        for i, header in enumerate(headers):
            if header == 'PyC':
                mapeo_dinamico['PyC'] = i
            elif header in ['PS', 'EB']:  # PS y EB son equivalentes
                mapeo_dinamico['PS'] = i
            elif header == 'CO':
                mapeo_dinamico['CO'] = i
        
        return mapeo_dinamico

    def contar_centros_costos_dinamico(fila, headers):
        posiciones_cc = detectar_posiciones_centros_costo(headers)
        count = 0
        
        for tipo_cc, posicion in posiciones_cc.items():
            if posicion < len(headers):
                header_name = headers[posicion]
                valor = fila.get(header_name)
                
                if (valor is not None and 
                    valor != "-" and 
                    valor != 0 and 
                    valor != "0" and 
                    str(valor).strip() != ""):
                    count += 1
        
        return count

    print("🧪 Test: Detección Automática de Centros de Costo")
    print("=" * 60)
    
    # Caso 1: Layout tradicional
    headers_tradicional = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                          "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                          "PyC", "PS", "CO"]
    
    fila_tradicional = {
        "PyC": "100",
        "PS": "200", 
        "CO": "300"
    }
    
    posiciones_trad = detectar_posiciones_centros_costo(headers_tradicional)
    count_trad = contar_centros_costos_dinamico(fila_tradicional, headers_tradicional)
    
    print(f"📊 Layout Tradicional:")
    print(f"   Headers: {headers_tradicional}")
    print(f"   Posiciones detectadas: {posiciones_trad}")
    print(f"   Count centros: {count_trad}")
    print()
    
    # Caso 2: Layout con EB en lugar de PS
    headers_eb = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                  "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                  "PyC", "EB", "CO"]
    
    fila_eb = {
        "PyC": "100",
        "EB": "200",  # EB en lugar de PS
        "CO": "300"
    }
    
    posiciones_eb = detectar_posiciones_centros_costo(headers_eb)
    count_eb = contar_centros_costos_dinamico(fila_eb, headers_eb)
    
    print(f"📊 Layout con EB:")
    print(f"   Headers: {headers_eb}")
    print(f"   Posiciones detectadas: {posiciones_eb}")
    print(f"   Count centros: {count_eb}")
    print()
    
    # Caso 3: Layout desordenado (diferente orden de columnas)
    headers_desordenado = ["Nro", "Tipo Doc", "CO", "RUT Proveedor", "PyC", "Razon Social", 
                          "Folio", "EB", "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta"]
    
    fila_desordenado = {
        "PyC": "100",
        "EB": "200",
        "CO": "300"
    }
    
    posiciones_des = detectar_posiciones_centros_costo(headers_desordenado)
    count_des = contar_centros_costos_dinamico(fila_desordenado, headers_desordenado)
    
    print(f"📊 Layout Desordenado:")
    print(f"   Headers: {headers_desordenado}")
    print(f"   Posiciones detectadas: {posiciones_des}")
    print(f"   Count centros: {count_des}")
    print()
    
    # Caso 4: Layout con columnas faltantes
    headers_incompleto = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                         "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                         "PyC", "CO"]  # Falta PS/EB
    
    fila_incompleto = {
        "PyC": "100",
        "CO": "300"
        # No hay PS/EB
    }
    
    posiciones_inc = detectar_posiciones_centros_costo(headers_incompleto)
    count_inc = contar_centros_costos_dinamico(fila_incompleto, headers_incompleto)
    
    print(f"📊 Layout Incompleto (sin PS/EB):")
    print(f"   Headers: {headers_incompleto}")
    print(f"   Posiciones detectadas: {posiciones_inc}")
    print(f"   Count centros: {count_inc}")
    print()
    
    # Caso 5: Layout con columnas adicionales
    headers_extendido = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                        "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                        "PyC", "PS", "CO", "Extra1", "Extra2"]
    
    fila_extendido = {
        "PyC": "100",
        "PS": "200",
        "CO": "300",
        "Extra1": "999",
        "Extra2": "888"
    }
    
    posiciones_ext = detectar_posiciones_centros_costo(headers_extendido)
    count_ext = contar_centros_costos_dinamico(fila_extendido, headers_extendido)
    
    print(f"📊 Layout Extendido (con columnas adicionales):")
    print(f"   Headers: {headers_extendido}")
    print(f"   Posiciones detectadas: {posiciones_ext}")
    print(f"   Count centros: {count_ext}")
    print()
    
    # Verificaciones
    print("🔍 Verificaciones:")
    print(f"   Todos detectan 3 centros (cuando están presentes): {count_trad == count_eb == count_des == count_ext == 3}")
    print(f"   Layout incompleto detecta 2 centros: {count_inc == 2}")
    print(f"   PS y EB son reconocidos como equivalentes: {'PS' in posiciones_trad and 'PS' in posiciones_eb}")
    print(f"   Detección funciona independiente del orden: {len(posiciones_des) == 3}")
    
    print("\n✅ Test de detección automática completado")
    
    # Simular respuesta del API
    print("\n📡 Ejemplo de respuesta del API:")
    api_response = {
        'headers': headers_eb,
        'total_columnas': len(headers_eb),
        'centros_costo': {
            'PyC': {'posicion': posiciones_eb.get('PyC', -1), 'nombre': 'PyC'},
            'PS': {'posicion': posiciones_eb.get('PS', -1), 'nombre': 'EB'},  # EB detectado como PS
            'CO': {'posicion': posiciones_eb.get('CO', -1), 'nombre': 'CO'}
        },
        'mensaje': 'Headers leídos exitosamente'
    }
    
    print(f"   {api_response}")

if __name__ == "__main__":
    test_deteccion_centros_costo()
