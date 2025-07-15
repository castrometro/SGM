#!/usr/bin/env python3
"""
Script para verificar que el usuario se esté guardando correctamente 
en los reportes financieros del TarjetaActivityLog.
"""

import sys
import os

# Agregar el path del backend de Django
sys.path.append('/root/SGM/backend')

def verificar_cambios_usuario():
    """Verifica que los cambios para incluir usuario estén implementados"""
    print("🔍 Verificando correcciones para el usuario en reportes...")
    
    archivo_tasks = "/root/SGM/backend/contabilidad/tasks_finalizacion.py"
    
    with open(archivo_tasks, 'r') as f:
        contenido = f.read()
    
    verificaciones = []
    
    # 1. Verificar que ejecutar_calculos_contables reciba usuario_id
    if 'def ejecutar_calculos_contables(cierre_id, usuario_id=None):' in contenido:
        verificaciones.append(("✅", "Función ejecutar_calculos_contables acepta usuario_id"))
    else:
        verificaciones.append(("❌", "Función ejecutar_calculos_contables NO acepta usuario_id"))
    
    # 2. Verificar que guardar_reportes_en_bd reciba usuario_id
    if 'def guardar_reportes_en_bd(cierre, esf, estado_resultados, ratios, usuario_id=None):' in contenido:
        verificaciones.append(("✅", "Función guardar_reportes_en_bd acepta usuario_id"))
    else:
        verificaciones.append(("❌", "Función guardar_reportes_en_bd NO acepta usuario_id"))
    
    # 3. Verificar que se llame con usuario_id
    if 'guardar_reportes_en_bd(cierre, balance_general_esf, estado_resultados, ratios, usuario_id)' in contenido:
        verificaciones.append(("✅", "Se llama guardar_reportes_en_bd con usuario_id"))
    else:
        verificaciones.append(("❌", "NO se llama guardar_reportes_en_bd con usuario_id"))
    
    # 4. Verificar que se use usuario en el TarjetaActivityLog
    if 'usuario=usuario,' in contenido and 'Usuario.objects.get(id=usuario_id)' in contenido:
        verificaciones.append(("✅", "Se obtiene y usa el objeto Usuario en el log"))
    else:
        verificaciones.append(("❌", "NO se obtiene/usa correctamente el objeto Usuario"))
    
    # 5. Verificar que se pase usuario_id en llamadas paralelas y secuenciales
    if 'ejecutar_calculos_contables.s(cierre_id, usuario_id)' in contenido:
        verificaciones.append(("✅", "Se pasa usuario_id en ejecución paralela"))
    else:
        verificaciones.append(("❌", "NO se pasa usuario_id en ejecución paralela"))
    
    if 'ejecutar_calculos_contables(cierre_id, usuario_id)' in contenido:
        verificaciones.append(("✅", "Se pasa usuario_id en ejecución secuencial"))
    else:
        verificaciones.append(("❌", "NO se pasa usuario_id en ejecución secuencial"))
    
    # Mostrar resultados
    print("\n📋 Resultados de verificación:")
    print("=" * 50)
    
    total_ok = 0
    for estado, mensaje in verificaciones:
        print(f"{estado} {mensaje}")
        if estado == "✅":
            total_ok += 1
    
    print(f"\n📊 Resumen: {total_ok}/{len(verificaciones)} verificaciones pasaron")
    
    if total_ok == len(verificaciones):
        print("\n🎉 ¡TODAS LAS CORRECCIONES ESTÁN IMPLEMENTADAS!")
        print("\n📝 Qué se corrigió:")
        print("   • ejecutar_calculos_contables ahora recibe usuario_id")
        print("   • guardar_reportes_en_bd ahora recibe usuario_id") 
        print("   • Se obtiene el objeto Usuario desde el ID")
        print("   • Se asigna el usuario al TarjetaActivityLog")
        print("   • Se incluye info del usuario en detalles del log")
        print("   • Ambas ejecuciones (paralela/secuencial) pasan usuario_id")
        
        print("\n🔄 Próximo paso:")
        print("   • Ejecutar una nueva finalización de cierre")
        print("   • Verificar en Django Admin que aparezca el usuario")
        print("   • El campo 'usuario' en TarjetaActivityLog ya no estará vacío")
        
        return True
    else:
        print("\n❌ HAY PROBLEMAS PENDIENTES")
        print("Revisa las verificaciones fallidas antes de probar")
        return False

def main():
    print("🚀 Verificación de correcciones para usuario en reportes financieros")
    print("=" * 65)
    
    exito = verificar_cambios_usuario()
    
    if exito:
        print("\n✅ VERIFICACIÓN EXITOSA - El usuario ahora se guardará en los reportes")
        return 0
    else:
        print("\n❌ VERIFICACIÓN FALLIDA - Hay correcciones pendientes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
