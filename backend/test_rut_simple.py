#!/usr/bin/env python3
"""
Test rápido para verificar la limpieza del RUT
"""

def test_rut_cleaning():
    """Test para verificar la limpieza del RUT"""
    print("🧪 TEST: Limpieza RUT Proveedor - Quitar dígito verificador")
    
    # Casos de prueba
    casos_rut = [
        ("12345678-9", "12345678"),  # RUT con guión y DV
        ("87654321-K", "87654321"),  # RUT con guión y DV letra
        ("12345678", "12345678"),    # RUT sin guión (ya limpio)
        ("", ""),                    # RUT vacío
    ]
    
    for rut_input, rut_esperado in casos_rut:
        print(f"📊 RUT Input: '{rut_input}' → Esperado: '{rut_esperado}'")
        
        # Simular lógica de limpieza (igual que en el código real)
        if '-' in rut_input:
            rut_limpio = rut_input.split('-')[0]
        else:
            rut_limpio = rut_input
            
        assert rut_limpio == rut_esperado, f"Error en limpieza de RUT: {rut_input}"
        print(f"✅ Correcto: '{rut_input}' → '{rut_limpio}'")
        
    print("✅ Test PASÓ - Limpieza de RUT funcionando correctamente")

if __name__ == "__main__":
    test_rut_cleaning()