#!/usr/bin/env python3
"""
Script para probar el endpoint de incidencias consolidadas directamente desde el backend
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.models import Incidencia, CierreContabilidad
from django.db.models import Count

def test_incidencias_endpoint(cierre_id=73):
    """Simular el endpoint de incidencias consolidadas"""
    
    print(f"🔍 Testing incidencias consolidadas para cierre {cierre_id}")
    print("=" * 60)
    
    try:
        # Verificar que existe el cierre
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        print(f"✅ Cierre encontrado: {cierre}")
        
        # Buscar todas las incidencias para este cierre
        incidencias_query = Incidencia.objects.filter(cierre=cierre)
        total_incidencias = incidencias_query.count()
        print(f"📊 Total incidencias en DB: {total_incidencias}")
        
        # Buscar solo las no resueltas
        incidencias_no_resueltas = incidencias_query.filter(resuelta=False)
        total_no_resueltas = incidencias_no_resueltas.count()
        print(f"📊 Incidencias no resueltas: {total_no_resueltas}")
        
        # Mostrar algunas incidencias de muestra
        print("\n📝 Muestra de incidencias:")
        for i, inc in enumerate(incidencias_no_resueltas[:5]):
            print(f"   {i+1}. {inc.descripcion}")
        
        # Simular la lógica del endpoint
        incidencias_consolidadas = []
        
        # Agrupar incidencias de nombres en inglés
        incidencias_nombres = incidencias_no_resueltas.filter(
            descripcion__icontains="Nombre en inglés faltante"
        )
        
        print(f"\n🏷️  Incidencias de nombres en inglés: {incidencias_nombres.count()}")
        
        if incidencias_nombres.exists():
            incidencias_consolidadas.append({
                'tipo_incidencia': 'cuentas_sin_nombre_ingles',
                'codigo_problema': 'nombres_ingles_faltantes',
                'cantidad_afectada': incidencias_nombres.count(),
                'detalle_muestra': [
                    inc.descripcion for inc in incidencias_nombres[:5]
                ],
                'severidad': 'media',
                'mensaje_usuario': f"Se encontraron {incidencias_nombres.count()} cuentas sin nombres en inglés",
                'accion_sugerida': "Subir tarjeta de nombres en inglés o marcar cuentas como 'No aplica'",
            })
        
        # Agrupar incidencias de tipos de documento
        incidencias_tipodoc = incidencias_no_resueltas.filter(
            descripcion__icontains="Tipo de documento"
        )
        
        print(f"📄 Incidencias de tipos de documento: {incidencias_tipodoc.count()}")
        
        if incidencias_tipodoc.exists():
            incidencias_consolidadas.append({
                'tipo_incidencia': 'tipos_doc_no_reconocidos',
                'codigo_problema': 'tipos_documento_faltantes',
                'cantidad_afectada': incidencias_tipodoc.count(),
                'detalle_muestra': [
                    inc.descripcion for inc in incidencias_tipodoc[:5]
                ],
                'severidad': 'alta',
                'mensaje_usuario': f"Se encontraron {incidencias_tipodoc.count()} códigos de tipo documento no reconocidos",
                'accion_sugerida': "Subir tarjeta de tipos de documento o marcar códigos como 'No aplica'",
            })
        
        print(f"\n📋 Incidencias consolidadas generadas: {len(incidencias_consolidadas)}")
        for i, inc_cons in enumerate(incidencias_consolidadas):
            print(f"   {i+1}. {inc_cons['tipo_incidencia']}: {inc_cons['cantidad_afectada']} afectadas")
        
        return incidencias_consolidadas
        
    except CierreContabilidad.DoesNotExist:
        print(f"❌ Cierre {cierre_id} no encontrado")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    result = test_incidencias_endpoint()
    print(f"\n🎯 Resultado final: {len(result)} grupos de incidencias consolidadas")
