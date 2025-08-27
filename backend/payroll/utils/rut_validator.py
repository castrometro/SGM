# backend/payroll/utils/rut_validator.py
# Utilidades para validación y limpieza de RUTs chilenos

import re


def limpiar_rut(rut_str):
    """
    Limpia y formatea un RUT chileno removiendo puntos, guiones y espacios.
    
    Args:
        rut_str: String con el RUT a limpiar
        
    Returns:
        String con RUT limpio en formato 12345678-9 o vacío si es inválido
    """
    if not rut_str or str(rut_str).lower() in ['nan', 'none', '']:
        return ""
    
    # Convertir a string y remover puntos, guiones y espacios
    rut_clean = re.sub(r'[.\-\s]', '', str(rut_str))
    
    # Verificar que tenga al menos 8 caracteres (7 números + 1 dígito verificador)
    if len(rut_clean) < 8:
        return ""
    
    # Verificar que los primeros 7-8 caracteres sean números
    numeros = rut_clean[:-1]
    digito_verificador = rut_clean[-1]
    
    if not numeros.isdigit():
        return ""
    
    # Verificar dígito verificador válido (número o K)
    if not (digito_verificador.isdigit() or digito_verificador.upper() == 'K'):
        return ""
    
    # Formatear con guión
    return f"{numeros}-{digito_verificador.upper()}"


def validar_rut(rut_str):
    """
    Valida un RUT chileno verificando el dígito verificador.
    
    Args:
        rut_str: String con el RUT a validar (formato: 12345678-9)
        
    Returns:
        Boolean: True si el RUT es válido, False en caso contrario
    """
    if not rut_str:
        return False
    
    try:
        # Separar número y dígito verificador
        if '-' not in rut_str:
            return False
            
        partes = rut_str.split('-')
        if len(partes) != 2:
            return False
            
        numero = partes[0]
        dv_esperado = partes[1].upper()
        
        # Verificar que el número sea válido
        if not numero.isdigit() or len(numero) < 7:
            return False
        
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        # Procesar número de derecha a izquierda
        for i in range(len(numero) - 1, -1, -1):
            suma += int(numero[i]) * multiplicador
            multiplicador += 1
            if multiplicador > 7:
                multiplicador = 2
        
        # Calcular resto y dígito verificador
        resto = suma % 11
        dv_calculado = 11 - resto
        
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        return dv_esperado == dv_calculado
        
    except Exception:
        return False


def formatear_rut_con_puntos(rut_str):
    """
    Formatea un RUT con puntos de miles.
    
    Args:
        rut_str: String con RUT limpio (formato: 12345678-9)
        
    Returns:
        String con RUT formateado (formato: 12.345.678-9)
    """
    if not rut_str or '-' not in rut_str:
        return rut_str
    
    partes = rut_str.split('-')
    numero = partes[0]
    dv = partes[1]
    
    # Agregar puntos cada 3 dígitos de derecha a izquierda
    numero_con_puntos = ""
    for i, digito in enumerate(reversed(numero)):
        if i > 0 and i % 3 == 0:
            numero_con_puntos = "." + numero_con_puntos
        numero_con_puntos = digito + numero_con_puntos
    
    return f"{numero_con_puntos}-{dv}"


def extraer_numero_rut(rut_str):
    """
    Extrae solo la parte numérica del RUT (sin dígito verificador).
    
    Args:
        rut_str: String con RUT
        
    Returns:
        String con solo números del RUT
    """
    rut_limpio = limpiar_rut(rut_str)
    if not rut_limpio or '-' not in rut_limpio:
        return ""
    
    return rut_limpio.split('-')[0]
