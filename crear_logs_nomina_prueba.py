#!/usr/bin/env python3

"""
Script para crear logs de actividad de prueba en el sistema de nómina
"""

import os
import django
import sys
from datetime import datetime, timedelta
import random

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Cliente
from nomina.models import CierreNomina
from nomina.models_logging import registrar_actividad_tarjeta_nomina, UploadLogNomina

def crear_logs_actividad_nomina():
    """Crear logs de actividad de prueba para nómina"""
    
    print("🔄 Iniciando creación de logs de actividad de nómina...")
    
    # Obtener datos necesarios
    try:
        usuarios = list(User.objects.all()[:5])  # Los primeros 5 usuarios
        clientes = list(Cliente.objects.all()[:3])  # Los primeros 3 clientes
        cierres = list(CierreNomina.objects.all()[:10])  # Los primeros 10 cierres
        
        if not usuarios:
            print("❌ No hay usuarios en el sistema")
            return
            
        if not cierres:
            print("❌ No hay cierres de nómina en el sistema")
            return
            
        print(f"✅ Encontrados: {len(usuarios)} usuarios, {len(clientes)} clientes, {len(cierres)} cierres")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos base: {e}")
        return
    
    # Definir tipos de actividades posibles
    actividades_posibles = [
        {
            'tarjeta': 'libro_remuneraciones',
            'accion': 'upload_excel',
            'descripcion': 'Archivo de Libro de Remuneraciones subido exitosamente',
            'detalles': {'archivo': 'libro_remuneraciones_022024.xlsx', 'registros': 150}
        },
        {
            'tarjeta': 'libro_remuneraciones',
            'accion': 'header_analysis',
            'descripcion': 'Análisis de headers completado',
            'detalles': {'headers_detectados': 15, 'headers_mapeados': 12}
        },
        {
            'tarjeta': 'libro_remuneraciones',
            'accion': 'classification_complete',
            'descripcion': 'Clasificación de conceptos completada',
            'detalles': {'conceptos_clasificados': 25, 'conceptos_pendientes': 3}
        },
        {
            'tarjeta': 'movimientos_mes',
            'accion': 'upload_excel',
            'descripcion': 'Archivo de Movimientos del Mes procesado',
            'detalles': {'archivo': 'movimientos_022024.xlsx', 'empleados_procesados': 89}
        },
        {
            'tarjeta': 'novedades',
            'accion': 'manual_create',
            'descripción': 'Novedad creada manualmente',
            'detalles': {'tipo_novedad': 'ausencia', 'empleado_id': '12345678-9'}
        },
        {
            'tarjeta': 'incidencias',
            'accion': 'validation_error',  
            'descripcion': 'Error de validación detectado y resuelto',
            'detalles': {'tipo_error': 'monto_inconsistente', 'empleado_afectado': '98765432-1'}
        },
        {
            'tarjeta': 'revision',
            'accion': 'view_data',
            'descripcion': 'Revisión de datos de nómina completada',
            'detalles': {'datos_revisados': 'totales_finales', 'estado': 'aprobado'}
        },
        {
            'tarjeta': 'archivos_analista',
            'accion': 'process_complete',
            'descripcion': 'Procesamiento de archivos del analista finalizado',
            'detalles': {'archivos_procesados': 3, 'incidencias_detectadas': 5}
        }
    ]
    
    logs_creados = 0
    
    # Crear logs para cada cierre
    for cierre in cierres:
        print(f"📝 Procesando cierre {cierre.id} (Cliente: {cierre.cliente.nombre})")
        
        # Crear entre 5 y 15 logs por cierre
        num_logs = random.randint(5, 15)
        
        for i in range(num_logs):
            try:
                # Seleccionar actividad aleatoria
                actividad = random.choice(actividades_posibles)
                
                # Seleccionar usuario aleatorio
                usuario = random.choice(usuarios)
                
                # Crear timestamp aleatorio de los últimos 30 días
                fecha_base = datetime.now() - timedelta(days=random.randint(1, 30))
                
                # Crear el log de actividad
                log = registrar_actividad_tarjeta_nomina(
                    cierre_id=cierre.id,
                    tarjeta=actividad['tarjeta'],
                    accion=actividad['accion'],
                    descripcion=actividad['descripcion'],
                    usuario=usuario,
                    detalles=actividad['detalles'],
                    resultado='exito' if random.random() > 0.1 else 'warning',  # 90% éxito, 10% warning
                    ip_address=f"192.168.1.{random.randint(100, 200)}"
                )
                
                # Cambiar la fecha manualmente (Django no permite esto en auto_now_add)
                log.timestamp = fecha_base
                log.save()
                
                logs_creados += 1
                
            except Exception as e:
                print(f"❌ Error creando log para cierre {cierre.id}: {e}")
                continue
    
    print(f"🎉 ¡Creación completada! Se crearon {logs_creados} logs de actividad")
    
    # Mostrar resumen por tarjeta
    from nomina.models_logging import TarjetaActivityLogNomina
    resumen = {}
    for tarjeta_code, tarjeta_name in TarjetaActivityLogNomina.TARJETA_CHOICES:
        count = TarjetaActivityLogNomina.objects.filter(tarjeta=tarjeta_code).count()
        if count > 0:
            resumen[tarjeta_name] = count
    
    print("\n📊 Resumen por tarjeta:")
    for tarjeta, count in resumen.items():
        print(f"   • {tarjeta}: {count} logs")

def crear_logs_upload_nomina():
    """Crear algunos logs de upload para complementar"""
    
    print("\n🔄 Creando logs de upload de prueba...")
    
    try:
        cierres = list(CierreNomina.objects.all()[:5])
        usuarios = list(User.objects.all()[:3])
        
        if not cierres or not usuarios:
            print("❌ No hay cierres o usuarios suficientes")
            return
        
        tipos_upload = [
            'libro_remuneraciones',
            'movimientos_mes', 
            'novedades',
            'archivos_analista'
        ]
        
        uploads_creados = 0
        
        for cierre in cierres:
            # Crear 2-4 uploads por cierre
            num_uploads = random.randint(2, 4)
            
            for i in range(num_uploads):
                try:
                    tipo = random.choice(tipos_upload)
                    usuario = random.choice(usuarios)
                    
                    upload_log = UploadLogNomina.objects.create(
                        tipo_upload=tipo,
                        cliente=cierre.cliente,
                        cierre=cierre,
                        usuario=usuario,
                        nombre_archivo_original=f"{tipo}_{cierre.cliente.rut_limpio}_{random.randint(10000, 99999)}.xlsx",
                        tamaño_archivo=random.randint(50000, 500000),
                        estado=random.choice(['completado', 'procesando', 'clasificado']),
                        registros_procesados=random.randint(50, 500),
                        registros_exitosos=random.randint(45, 495),
                        ip_usuario=f"192.168.1.{random.randint(100, 200)}"
                    )
                    
                    uploads_creados += 1
                    
                except Exception as e:
                    print(f"❌ Error creando upload para cierre {cierre.id}: {e}")
                    continue
        
        print(f"🎉 Se crearon {uploads_creados} logs de upload")
        
    except Exception as e:
        print(f"❌ Error general creando uploads: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando script de creación de logs de nómina")
    crear_logs_actividad_nomina()
    crear_logs_upload_nomina()
    print("\n✅ Script completado")
