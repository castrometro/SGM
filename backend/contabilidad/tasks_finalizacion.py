"""
Tareas de Celery para finalización de cierres contables y generación de reportes.

Este módulo maneja todas las tareas relacionadas con:
- Finalización de cierres contables
- Generación de reportes consolidados
- Cálculos para dashboard
- Consolidación de datos
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='contabilidad.finalizar_cierre_y_generar_reportes')
def finalizar_cierre_y_generar_reportes(self, cierre_id, usuario_id=None):
    """
    Tarea principal para finalizar un cierre contable y generar reportes.
    
    Args:
        cierre_id (int): ID del cierre a finalizar
        usuario_id (int, optional): ID del usuario que inició la finalización
        
    Returns:
        dict: Resultado del procesamiento
    """
    from .models import CierreContabilidad
    from api.models import Usuario
    
    inicio = timezone.now()
    
    try:
        # Obtener el cierre
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        usuario = Usuario.objects.get(id=usuario_id) if usuario_id else None
        
        logger.info(f"[FINALIZACIÓN] Iniciando finalización del cierre {cierre_id} - {cierre.cliente.nombre} - {cierre.periodo}")
        
        # Verificar que el cierre puede ser finalizado
        puede, mensaje = cierre.puede_finalizar()
        if not puede:
            raise ValueError(f"El cierre no puede ser finalizado: {mensaje}")
        
        # Simular procesamiento (por ahora solo prints)
        print(f"🚀 INICIANDO FINALIZACIÓN DEL CIERRE")
        print(f"   Cliente: {cierre.cliente.nombre}")
        print(f"   Período: {cierre.periodo}")
        print(f"   Usuario: {usuario.username if usuario else 'Sistema'}")
        print(f"   Fecha inicio: {inicio}")
        
        # =================== STEP 1: VALIDACIONES FINALES ===================
        print(f"📋 STEP 1: Ejecutando validaciones finales...")
        resultado_validaciones = ejecutar_validaciones_finales(cierre_id)
        print(f"   ✅ Validaciones completadas: {resultado_validaciones['total_validaciones']} checks")
        
        # =================== STEP 2: CÁLCULOS CONTABLES ===================
        print(f"🧮 STEP 2: Ejecutando cálculos contables...")
        resultado_calculos = ejecutar_calculos_contables(cierre_id)
        print(f"   ✅ Cálculos completados: {resultado_calculos['total_cuentas']} cuentas procesadas")
        
        # =================== STEP 3: CONSOLIDACIÓN DE DATOS ===================
        print(f"📊 STEP 3: Consolidando datos para dashboard...")
        resultado_consolidacion = consolidar_datos_dashboard(cierre_id)
        print(f"   ✅ Consolidación completada: {resultado_consolidacion['total_registros']} registros")
        
        # =================== STEP 4: GENERACIÓN DE REPORTES ===================
        print(f"📈 STEP 4: Generando reportes finales...")
        resultado_reportes = generar_reportes_finales(cierre_id)
        print(f"   ✅ Reportes generados: {len(resultado_reportes['reportes'])} archivos")
        
        # =================== STEP 5: FINALIZACIÓN ===================
        print(f"🏁 STEP 5: Marcando cierre como finalizado...")
        cierre.marcar_como_finalizado()
        
        fin = timezone.now()
        duracion = (fin - inicio).total_seconds()
        
        print(f"✅ FINALIZACIÓN COMPLETADA EXITOSAMENTE")
        print(f"   Duración total: {duracion:.2f} segundos")
        print(f"   Estado final: {cierre.estado}")
        print(f"   Fecha finalización: {cierre.fecha_finalizacion}")
        
        # Crear log de actividad
        from .models import TarjetaActivityLog
        TarjetaActivityLog.objects.create(
            cierre=cierre,
            tarjeta='revision',
            accion='process_complete',
            usuario_id=usuario_id,
            descripcion=f'Cierre finalizado y reportes generados exitosamente',
            detalles={
                'duracion_segundos': duracion,
                'validaciones': resultado_validaciones,
                'calculos': resultado_calculos,
                'consolidacion': resultado_consolidacion,
                'reportes': resultado_reportes
            },
            resultado='exito'
        )
        
        return {
            'success': True,
            'mensaje': 'Cierre finalizado exitosamente',
            'cierre_id': cierre_id,
            'duracion_segundos': duracion,
            'resultados': {
                'validaciones': resultado_validaciones,
                'calculos': resultado_calculos,
                'consolidacion': resultado_consolidacion,
                'reportes': resultado_reportes
            }
        }
        
    except Exception as e:
        logger.error(f"[FINALIZACIÓN] Error en cierre {cierre_id}: {str(e)}")
        print(f"❌ ERROR EN FINALIZACIÓN: {str(e)}")
        
        # Revertir estado si es necesario
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
            if cierre.estado == 'generando_reportes':
                cierre.estado = 'sin_incidencias'
                cierre.save(update_fields=['estado'])
                print(f"🔄 Estado revertido a 'sin_incidencias'")
        except:
            pass
        
        # Crear log de error
        try:
            from .models import TarjetaActivityLog
            TarjetaActivityLog.objects.create(
                cierre_id=cierre_id,
                tarjeta='revision',
                accion='process_complete',
                usuario_id=usuario_id,
                descripcion=f'Error en finalización del cierre: {str(e)}',
                detalles={'error': str(e), 'task_id': self.request.id},
                resultado='error'
            )
        except:
            pass
        
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task(name='contabilidad.ejecutar_validaciones_finales')
def ejecutar_validaciones_finales(cierre_id):
    """
    Ejecuta validaciones finales antes de completar el cierre.
    
    Args:
        cierre_id (int): ID del cierre
        
    Returns:
        dict: Resultado de las validaciones
    """
    print(f"   🔍 Validando integridad de datos...")
    print(f"   🔍 Verificando balance contable...")
    print(f"   🔍 Validando clasificaciones completas...")
    print(f"   🔍 Verificando nombres en inglés (si aplica)...")
    
    # Simulación de validaciones
    import time
    time.sleep(2)  # Simular procesamiento
    
    return {
        'total_validaciones': 4,
        'validaciones_exitosas': 4,
        'validaciones_fallidas': 0,
        'detalle': [
            {'tipo': 'integridad_datos', 'estado': 'ok'},
            {'tipo': 'balance_contable', 'estado': 'ok'},
            {'tipo': 'clasificaciones_completas', 'estado': 'ok'},
            {'tipo': 'nombres_ingles', 'estado': 'ok'}
        ]
    }


@shared_task(name='contabilidad.ejecutar_calculos_contables')
def ejecutar_calculos_contables(cierre_id):
    """
    Ejecuta cálculos contables finales.
    
    Args:
        cierre_id (int): ID del cierre
        
    Returns:
        dict: Resultado de los cálculos
    """
    print(f"   📊 Calculando saldos finales...")
    print(f"   📊 Generando balance de comprobación...")
    print(f"   📊 Calculando ratios financieros...")
    print(f"   📊 Procesando movimientos por clasificación...")
    
    # Simulación de cálculos
    import time
    time.sleep(3)  # Simular procesamiento más largo
    
    return {
        'total_cuentas': 150,
        'cuentas_procesadas': 150,
        'saldos_calculados': True,
        'balance_cuadrado': True,
        'ratios_calculados': 12,
        'clasificaciones_procesadas': 8
    }


@shared_task(name='contabilidad.consolidar_datos_dashboard')
def consolidar_datos_dashboard(cierre_id):
    """
    Consolida datos para el dashboard gerencial.
    
    Args:
        cierre_id (int): ID del cierre
        
    Returns:
        dict: Resultado de la consolidación
    """
    print(f"   📈 Consolidando datos por área...")
    print(f"   📈 Generando métricas de gestión...")
    print(f"   📈 Calculando KPIs financieros...")
    print(f"   📈 Preparando datos para gráficos...")
    
    # Simulación de consolidación
    import time
    time.sleep(2)
    
    return {
        'total_registros': 45,
        'areas_procesadas': 5,
        'kpis_generados': 15,
        'graficos_preparados': 8,
        'metricas_consolidadas': True
    }


@shared_task(name='contabilidad.generar_reportes_finales')
def generar_reportes_finales(cierre_id):
    """
    Genera los reportes finales del cierre.
    
    Args:
        cierre_id (int): ID del cierre
        
    Returns:
        dict: Resultado de la generación de reportes
    """
    print(f"   📋 Generando Balance General...")
    print(f"   📋 Generando Estado de Resultados...")
    print(f"   📋 Generando reporte de Clasificaciones...")
    print(f"   📋 Generando reporte Bilingüe (si aplica)...")
    print(f"   📋 Generando Dashboard Ejecutivo...")
    
    # Simulación de generación de reportes
    import time
    time.sleep(2)
    
    return {
        'reportes': [
            {'nombre': 'Balance General', 'formato': 'PDF', 'estado': 'generado'},
            {'nombre': 'Estado de Resultados', 'formato': 'PDF', 'estado': 'generado'},
            {'nombre': 'Reporte de Clasificaciones', 'formato': 'Excel', 'estado': 'generado'},
            {'nombre': 'Reporte Bilingüe', 'formato': 'Excel', 'estado': 'generado'},
            {'nombre': 'Dashboard Ejecutivo', 'formato': 'PDF', 'estado': 'generado'}
        ],
        'total_reportes': 5,
        'reportes_exitosos': 5,
        'reportes_fallidos': 0
    }


@shared_task(name='contabilidad.notificar_finalizacion')
def notificar_finalizacion(cierre_id, usuario_id):
    """
    Envía notificaciones sobre la finalización del cierre.
    
    Args:
        cierre_id (int): ID del cierre
        usuario_id (int): ID del usuario a notificar
    """
    print(f"   📧 Enviando notificación de finalización...")
    print(f"   📧 Notificando a usuario ID: {usuario_id}")
    print(f"   📧 Creando notificación en sistema...")
    
    # Aquí iría la lógica de notificaciones reales
    # Por ejemplo: envío de emails, notificaciones push, etc.
    
    return {
        'notificacion_enviada': True,
        'usuario_notificado': usuario_id,
        'tipo': 'finalizacion_cierre'
    }
