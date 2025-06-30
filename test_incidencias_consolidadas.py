#!/usr/bin/env python
"""
Script de prueba para el sistema de incidencias consolidadas

Ejecutar desde docker:
docker compose exec django python /root/SGM/test_incidencias_consolidadas.py
"""

import os
import sys
import django
from datetime import datetime, date

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

# Imports después de setup de Django
from contabilidad.models import CuentaContable, TipoDocumento, MovimientoContable
from contabilidad.models_incidencias import IncidenciaResumen, HistorialReprocesamiento, LogResolucionIncidencia
from contabilidad.utils.parsers.parser_libro_mayor_consolidado import (
    analizar_incidencias_consolidadas,
    crear_incidencias_consolidadas,
)
from api.models import Cliente
from contabilidad.models import CierreContabilidad, UploadLog
from django.contrib.auth import get_user_model

User = get_user_model()

def verificar_sistema():
    """Verifica que el sistema esté funcionando correctamente"""
    print("🔍 VERIFICANDO SISTEMA DE INCIDENCIAS CONSOLIDADAS")
    print("=" * 60)
    
    # 1. Verificar que los modelos existen
    print("\n1. ✅ Verificando modelos...")
    try:
        total_incidencias = IncidenciaResumen.objects.count()
        print(f"   📊 Incidencias en BD: {total_incidencias}")
        
        # Mostrar distribución por estado
        for estado in ['activa', 'resuelta', 'obsoleta']:
            count = IncidenciaResumen.objects.filter(estado=estado).count()
            if count > 0:
                print(f"      - {estado.title()}: {count}")
    except Exception as e:
        print(f"   ❌ Error con modelos: {e}")
        return False
    
    # 2. Verificar que hay datos de prueba
    print("\n2. 📋 Verificando datos existentes...")
    clientes = Cliente.objects.count()
    cierres = CierreContabilidad.objects.count()
    upload_logs = UploadLog.objects.count()
    
    print(f"   - Clientes: {clientes}")
    print(f"   - Cierres: {cierres}")
    print(f"   - Upload Logs: {upload_logs}")
    
    if clientes == 0:
        print("   ⚠️  No hay clientes. Creando datos básicos...")
        crear_datos_basicos()
    
    # 3. Probar creación de incidencia
    print("\n3. 🧪 Probando creación de incidencia...")
    try:
        # Buscar o crear un upload_log para probar
        upload_log = UploadLog.objects.first()
        if not upload_log:
            print("   ⚠️  No hay upload_logs. Creando uno básico...")
            cliente = Cliente.objects.first()
            cierre = CierreContabilidad.objects.first()
            if not cliente or not cierre:
                print("   ❌ No se pueden crear datos básicos")
                return False
            
            upload_log = UploadLog.objects.create(
                cliente=cliente,
                cierre=cierre,
                nombre_archivo_original="test_incidencias.xlsx",
                tipo_archivo='libro_mayor',
                estado='procesado',
                resumen={'test': True}
            )
        
        # Crear una incidencia de prueba
        incidencia_test, created = IncidenciaResumen.objects.get_or_create(
            upload_log=upload_log,
            tipo_incidencia='tipos_doc_no_reconocidos',
            codigo_problema='TEST',
            defaults={
                'cantidad_afectada': 5,
                'elementos_afectados': ['1101', '1102', '1103'],
                'detalle_muestra': [
                    {'cuenta': '1101', 'movimiento': 1, 'monto': 1000},
                    {'cuenta': '1102', 'movimiento': 2, 'monto': 2000},
                ],
                'severidad': 'media',
                'mensaje_usuario': 'Incidencia de prueba del sistema',
                'accion_sugerida': 'Esta es una prueba del sistema de incidencias consolidadas',
                'estadisticas_adicionales': {
                    'monto_total_afectado': 3000,
                    'test_mode': True,
                }
            }
        )
        
        if created:
            print(f"   ✅ Incidencia de prueba creada: ID {incidencia_test.id}")
        else:
            print(f"   ✅ Incidencia de prueba existente: ID {incidencia_test.id}")
    
    except Exception as e:
        print(f"   ❌ Error creando incidencia de prueba: {e}")
        return False
    
    # 4. Probar endpoints básicos
    print("\n4. 🌐 Probando estructura de endpoints...")
    try:
        from contabilidad.views.incidencias import (
            obtener_incidencias_consolidadas,
            dashboard_incidencias,
            marcar_incidencia_resuelta,
            historial_reprocesamiento,
            resumen_tipos_incidencia,
        )
        print("   ✅ Todos los endpoints importados correctamente")
    except ImportError as e:
        print(f"   ❌ Error importando endpoints: {e}")
        return False
    
    # 5. Resumen final
    print("\n5. 📈 Resumen del sistema:")
    
    # Estadísticas por tipo
    print("   Incidencias por tipo:")
    for tipo_codigo, tipo_desc in IncidenciaResumen.TIPOS_INCIDENCIA:
        count = IncidenciaResumen.objects.filter(tipo_incidencia=tipo_codigo).count()
        if count > 0:
            print(f"      - {tipo_desc}: {count}")
    
    # Estadísticas por severidad
    print("   Incidencias por severidad:")
    for sev_codigo, sev_desc in IncidenciaResumen.SEVERIDAD_CHOICES:
        count = IncidenciaResumen.objects.filter(severidad=sev_codigo).count()
        if count > 0:
            print(f"      - {sev_desc}: {count}")
    
    print("\n✅ SISTEMA VERIFICADO CORRECTAMENTE")
    return True


def crear_datos_basicos():
    """Crea datos básicos si no existen"""
    # Crear cliente
    cliente, created = Cliente.objects.get_or_create(
        nombre="Cliente Test Incidencias",
        defaults={
            'rut': '12345678-9',
            'email': 'test@incidencias.com',
            'activo': True,
        }
    )
    
    # Crear cierre
    cierre, created = CierreContabilidad.objects.get_or_create(
        cliente=cliente,
        periodo="2024-12",
        defaults={
            'fecha_cierre': date(2024, 12, 31),
            'estado': 'procesado',
        }
    )
    
    print(f"   ✅ Datos básicos creados: Cliente {cliente.nombre}, Cierre {cierre.periodo}")


def mostrar_urls_disponibles():
    """Muestra las URLs disponibles para probar"""
    print("\n🔗 URLs DISPONIBLES PARA PROBAR:")
    print("=" * 50)
    
    # Obtener un cierre y cliente para los ejemplos
    cierre = CierreContabilidad.objects.first()
    cliente = Cliente.objects.first()
    
    if cierre and cliente:
        base_url = "http://localhost:8000/api/contabilidad"
        print(f"📊 Dashboard de incidencias:")
        print(f"   GET {base_url}/dashboard/{cliente.id}/incidencias/")
        
        print(f"\n📋 Incidencias de un cierre:")
        print(f"   GET {base_url}/incidencias/{cierre.id}/")
        print(f"   GET {base_url}/incidencias/{cierre.id}/?estado=activa")
        print(f"   GET {base_url}/incidencias/{cierre.id}/?severidad=alta")
        
        print(f"\n🔧 Gestión de incidencias:")
        incidencia = IncidenciaResumen.objects.first()
        if incidencia:
            print(f"   POST {base_url}/incidencias/{incidencia.id}/resolver/")
        
        upload_log = UploadLog.objects.first()
        if upload_log:
            print(f"   GET {base_url}/upload-log/{upload_log.id}/historial/")
        
        print(f"\n📚 Información del sistema:")
        print(f"   GET {base_url}/incidencias/tipos/")
        print(f"   GET {base_url}/incidencias/estadisticas/")
    else:
        print("   ⚠️  No hay datos para mostrar URLs de ejemplo")


if __name__ == "__main__":
    print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA DE INCIDENCIAS CONSOLIDADAS")
    print("=" * 70)
    
    try:
        # Verificar sistema
        if verificar_sistema():
            # Mostrar URLs para probar
            mostrar_urls_disponibles()
            
            print("\n🎉 VERIFICACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 50)
            print("\n📋 PRÓXIMOS PASOS:")
            print("1. Acceder al admin Django para gestionar incidencias:")
            print("   http://localhost:8000/admin/contabilidad/incidenciaresumen/")
            print("\n2. Probar los endpoints desde el frontend o herramientas como curl/Postman")
            print("\n3. El sistema está listo para procesar libros mayor y generar incidencias automáticamente")
        else:
            print("\n❌ VERIFICACIÓN FALLÓ - Revisar errores arriba")
            
    except Exception as e:
        print(f"\n❌ ERROR EN VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
