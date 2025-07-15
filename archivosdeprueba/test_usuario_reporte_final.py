#!/usr/bin/env python3
"""
Script de prueba final para verificar que el usuario_generador
se asigne correctamente en ReporteFinanciero
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from contabilidad.models import CierreContabilidad, ReporteFinanciero
from contabilidad.tasks_reportes import generar_estado_situacion_financiera

def test_usuario_reporte():
    """
    Prueba que verifica que el usuario_generador se asigne correctamente
    """
    print("=" * 60)
    print("🧪 TEST: Verificando asignación de usuario_generador en ReporteFinanciero")
    print("=" * 60)
    
    try:
        # 1. Obtener un usuario y un cierre
        usuario = User.objects.first()
        cierre = CierreContabilidad.objects.filter(estado='finalizado').first()
        
        if not usuario:
            print("❌ Error: No hay usuarios disponibles")
            return False
            
        if not cierre:
            print("❌ Error: No hay cierres finalizados disponibles")
            return False
            
        print(f"👤 Usuario: {usuario.username} (ID: {usuario.id})")
        print(f"📊 Cierre: {cierre} (ID: {cierre.id})")
        
        # 2. Eliminar reporte existente si lo hay para hacer prueba limpia
        ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='esf'
        ).delete()
        print("🗑️  Eliminados reportes ESF existentes para este cierre")
        
        # 3. Llamar a la función de generación con usuario_id
        print(f"🚀 Llamando a generar_estado_situacion_financiera con usuario_id={usuario.id}")
        
        # Simular la llamada como se hace en tasks_finalizacion.py
        from contabilidad.tasks_reportes import generar_estado_situacion_financiera
        resultado = generar_estado_situacion_financiera(cierre.id, usuario.id)
        
        print(f"📊 Resultado de generación: {resultado}")
        
        # 4. Verificar que el reporte se creó con el usuario correcto
        reporte = ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='esf'
        ).first()
        
        if not reporte:
            print("❌ Error: No se creó el reporte")
            return False
            
        print(f"📋 Reporte creado:")
        print(f"   - ID: {reporte.id}")
        print(f"   - Tipo: {reporte.tipo_reporte}")
        print(f"   - Estado: {reporte.estado}")
        print(f"   - Usuario generador: {reporte.usuario_generador}")
        print(f"   - Usuario generador ID: {reporte.usuario_generador_id}")
        print(f"   - Fecha generación: {reporte.fecha_generacion}")
        
        # 5. Verificar que el usuario se asignó correctamente
        if reporte.usuario_generador_id == usuario.id:
            print("✅ SUCCESS: El usuario_generador se asignó correctamente")
            
            # 6. Probar regeneración
            print("\n🔄 Probando regeneración del reporte...")
            resultado2 = generar_estado_situacion_financiera(cierre.id, usuario.id, regenerar=True)
            print(f"📊 Resultado de regeneración: {resultado2}")
            
            # Verificar que el usuario sigue siendo correcto
            reporte.refresh_from_db()
            print(f"👤 Usuario después de regeneración: {reporte.usuario_generador}")
            print(f"👤 Usuario ID después de regeneración: {reporte.usuario_generador_id}")
            
            if reporte.usuario_generador_id == usuario.id:
                print("✅ SUCCESS: El usuario se mantiene correcto después de regeneración")
                return True
            else:
                print("❌ ERROR: El usuario NO se mantuvo después de regeneración")
                return False
                
        else:
            print(f"❌ ERROR: Usuario esperado {usuario.id}, pero se asignó {reporte.usuario_generador_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_usuario_reporte()
        print("\n" + "=" * 60)
        if success:
            print("🎉 TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
        else:
            print("💥 ALGUNAS PRUEBAS FALLARON")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n❌ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
