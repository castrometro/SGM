#!/usr/bin/env python3
"""
Script para actualizar todas las llamadas a ActivityEvent.log() 
agregando el parámetro cierre=cierre y removiendo 'cierre_id' de details.
"""

import re
import sys

def actualizar_activity_event_calls(filepath):
    """Actualiza llamadas a ActivityEvent.log en un archivo"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    cambios = 0
    
    # Patrón para encontrar ActivityEvent.log(
    pattern = r'(ActivityEvent\.log\(\s+user=[^,]+,\s+cliente=[^,]+,)'
    
    # Buscar todas las ocurrencias
    matches = list(re.finditer(pattern, content))
    
    # Procesar de atrás hacia adelante para no afectar las posiciones
    for match in reversed(matches):
        start = match.start()
        end = match.end()
        
        # Extraer el contexto completo de la llamada
        # Buscar hacia atrás para encontrar si ya tiene cierre=
        before_text = content[max(0, start-500):start]
        
        # Buscar el bloque completo de la llamada
        paren_count = 1
        i = end
        while i < len(content) and paren_count > 0:
            if content[i] == '(':
                paren_count += 1
            elif content[i] == ')':
                paren_count -= 1
            i += 1
        
        call_block = content[start:i]
        
        # Verificar si ya tiene cierre=
        if 'cierre=cierre' in call_block or 'cierre=instance.cierre' in call_block:
            print(f"  ⏭️  Ya tiene cierre= en posición {start}")
            continue
        
        # Insertar cierre=cierre después de cliente=cliente,
        match_text = match.group(1)
        
        # Determinar qué variable usar para cierre
        if 'instance.cierre' in before_text:
            cierre_var = 'instance.cierre'
        else:
            cierre_var = 'cierre'
        
        # Agregar cierre= después de cliente=
        new_match_text = match_text + f'\n            cierre={cierre_var},  # Normalizado'
        
        # Reemplazar
        content = content[:start] + new_match_text + content[end:]
        cambios += 1
        print(f"  ✅ Agregado cierre={cierre_var} en posición {start}")
    
    # Ahora remover 'cierre_id': ... de los details={}
    # Patrón para encontrar 'cierre_id': cierre.id,
    pattern_cierre_id = r"'cierre_id':\s*cierre\.id,\s*\n"
    matches_cierre_id = list(re.finditer(pattern_cierre_id, content))
    
    for match in reversed(matches_cierre_id):
        content = content[:match.start()] + content[match.end():]
        cambios += 1
        print(f"  🗑️  Removido 'cierre_id': cierre.id en posición {match.start()}")
    
    # Patrón alternativo con movimiento_id
    pattern_cierre_id2 = r"'cierre_id':\s*cierre\.id,?\s*\n?"
    matches_cierre_id2 = list(re.finditer(pattern_cierre_id2, content))
    
    for match in reversed(matches_cierre_id2):
        if match.start() not in [m.start() for m in matches_cierre_id]:
            content = content[:match.start()] + content[match.end():]
            cambios += 1
            print(f"  🗑️  Removido 'cierre_id' alternativo en posición {match.start()}")
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {filepath}: {cambios} cambios aplicados")
        return cambios
    else:
        print(f"⏭️  {filepath}: Sin cambios necesarios")
        return 0

if __name__ == '__main__':
    archivos = [
        'nomina/views_movimientos_mes.py',
        'nomina/tasks.py'
    ]
    
    total_cambios = 0
    for archivo in archivos:
        print(f"\n📝 Procesando {archivo}...")
        cambios = actualizar_activity_event_calls(archivo)
        total_cambios += cambios
    
    print(f"\n🎉 Total: {total_cambios} cambios aplicados")
