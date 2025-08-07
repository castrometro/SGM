"""
🚀 TASKS DE CELERY PARA GENERACIÓN DE INFORMES DE NÓMINA

Este módulo maneja todas las tareas asíncronas relacionadas con:
- Finalización de cierres de nómina
- Generación de informes comprehensivos
- Cálculo de KPIs y métricas
- Envío automático a Redis

Autor: Sistema SGM
Fecha: Agosto 2024
"""

from celery import shared_task, group, chord
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
import logging
import json
import time

from .models import CierreNomina, NominaConsolidada, ConceptoConsolidado, MovimientoPersonal
from .models_informe import ReporteNomina
from api.models import Usuario

logger = logging.getLogger(__name__)

# ============================================================================
#                           TASK PRINCIPAL
# ============================================================================

@shared_task(bind=True, name='nomina.generar_informe_completo')
def generar_informe_nomina_completo(self, cierre_id, usuario_id=None, modo='completo'):
    """
    🎯 TASK PRINCIPAL: Genera informe completo de nómina de forma asíncrona
    
    Args:
        self: Contexto de Celery
        cierre_id (int): ID del cierre de nómina
        usuario_id (int): ID del usuario que inició el proceso
        modo (str): 'completo', 'rapido', 'solo_kpis'
        
    Returns:
        dict: Resultado del procesamiento con datos del informe
    """
    
    inicio = timezone.now()
    
    def actualizar_progreso(paso, total, descripcion, porcentaje):
        """Actualiza el progreso del task"""
        try:
            self.update_state(
                state='PROGRESS',
                meta={
                    'paso_actual': paso,
                    'total_pasos': total,
                    'descripcion': descripcion,
                    'porcentaje': porcentaje,
                    'cierre_id': cierre_id,
                    'tiempo_transcurrido': (timezone.now() - inicio).total_seconds()
                }
            )
            logger.info(f"📊 [{paso}/{total}] {descripcion} ({porcentaje}%)")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo actualizar progreso: {e}")
    
    try:
        # =================== PASO 1: VALIDACIÓN INICIAL ===================
        actualizar_progreso(1, 8, 'Validando cierre y obteniendo datos...', 5)
        
        # Obtener el cierre
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = Usuario.objects.get(id=usuario_id) if usuario_id else None
        
        logger.info(f"🚀 Iniciando generación de informe para {cierre.cliente.nombre} - {cierre.periodo}")
        
        # Validar que se puede procesar
        if cierre.estado not in ['incidencias_resueltas', 'generando_informe']:
            raise ValueError(f"El cierre debe estar en estado 'incidencias_resueltas', actual: {cierre.estado}")
        
        # Cambiar estado si no está ya en generando_informe
        if cierre.estado != 'generando_informe':
            cierre.estado = 'generando_informe'
            cierre.save(update_fields=['estado'])
        
        # =================== PASO 2: PREPARACIÓN DE DATOS ===================
        actualizar_progreso(2, 8, 'Obteniendo datos de base de datos...', 15)
        
        # Contar empleados para estimar tiempo
        total_empleados = NominaConsolidada.objects.filter(cierre=cierre).count()
        total_conceptos = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=cierre).count()
        
        logger.info(f"📊 Procesando {total_empleados} empleados y {total_conceptos} conceptos")
        
        # =================== PASO 3: CREACIÓN DEL INFORME ===================
        actualizar_progreso(3, 8, 'Creando estructura del informe...', 25)
        
        # Obtener o crear el informe
        informe, created = ReporteNomina.objects.get_or_create(
            cierre=cierre,
            defaults={
                'datos_cierre': {},
                'version_calculo': '2.0_async'
            }
        )
        
        if created:
            logger.info(f"✅ Nuevo informe creado")
        else:
            logger.info(f"📋 Regenerando informe existente")
        
        # =================== PASO 4: CÁLCULO DE KPIS BÁSICOS ===================
        actualizar_progreso(4, 8, 'Calculando KPIs principales...', 40)
        
        # Calcular datos del cierre usando el método optimizado
        datos_cierre = informe._calcular_datos_cierre()
        
        # =================== PASO 5: GENERACIÓN DE LISTA DE EMPLEADOS ===================
        if modo in ['completo']:
            actualizar_progreso(5, 8, 'Generando lista detallada de empleados...', 60)
            
            # Verificar que la lista de empleados esté incluida
            if 'empleados' not in datos_cierre or not datos_cierre['empleados'].get('detalle'):
                logger.info("🔄 Regenerando lista de empleados...")
                datos_cierre['empleados'] = informe._generar_lista_empleados()
        
        # =================== PASO 6: CÁLCULOS AVANZADOS ===================
        actualizar_progreso(6, 8, 'Ejecutando cálculos avanzados...', 75)
        
        if modo in ['completo']:
            # Agregar métricas adicionales
            try:
                datos_cierre['estadisticas_empleados'] = informe.obtener_estadisticas_empleados()
                datos_cierre['dias_trabajados'] = informe.calcular_dias_trabajados_por_empleado()
            except Exception as e:
                logger.warning(f"⚠️ Error en cálculos avanzados: {e}")
        
        # =================== PASO 7: GUARDADO Y REDIS ===================
        actualizar_progreso(7, 8, 'Guardando informe y enviando a Redis...', 90)
        
        # Guardar informe
        informe.datos_cierre = datos_cierre
        informe.tiempo_calculo = timezone.now() - inicio
        informe.fecha_generacion = timezone.now()
        informe.save()
        
        # Enviar a Redis automáticamente
        resultado_redis = None
        try:
            resultado_redis = informe.enviar_a_redis(ttl_hours=24)
            if resultado_redis.get('success'):
                logger.info(f"✅ Informe enviado a Redis: {resultado_redis['clave_redis']}")
            else:
                logger.warning(f"⚠️ Error enviando a Redis: {resultado_redis.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️ Error al enviar a Redis: {e}")
        
        # =================== PASO 8: FINALIZACIÓN ===================
        actualizar_progreso(8, 8, 'Finalizando cierre...', 100)
        
        # Actualizar estado del cierre y metadatos
        cierre.estado = 'finalizado'
        cierre.fecha_finalizacion = timezone.now()
        cierre.usuario_finalizacion = usuario
        cierre.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
        
        # Calcular métricas finales
        fin = timezone.now()
        duracion = (fin - inicio).total_seconds()
        
        logger.info(f"✅ INFORME GENERADO EXITOSAMENTE")
        logger.info(f"   Duración: {duracion:.2f} segundos")
        logger.info(f"   Empleados procesados: {total_empleados}")
        logger.info(f"   KPIs calculados: {len(datos_cierre.get('kpis_principales', {}))}")
        logger.info(f"   Tamaño informe: {len(str(datos_cierre)) / 1024:.1f} KB")
        
        # Resultado final
        resultado = {
            'success': True,
            'mensaje': 'Informe de nómina generado exitosamente',
            'informe_id': informe.id,
            'cierre_id': cierre_id,
            'duracion_segundos': duracion,
            'estadisticas': {
                'total_empleados': total_empleados,
                'total_conceptos': total_conceptos,
                'kpis_calculados': len(datos_cierre.get('kpis_principales', {})),
                'tamaño_kb': len(str(datos_cierre)) / 1024,
                'modo_calculo': modo,
                'redis_enviado': resultado_redis.get('success', False) if resultado_redis else False
            },
            'kpis_principales': datos_cierre.get('kpis_principales', {}),
            'datos_resumen': {
                'costo_empresa_total': informe.get_kpi_principal('costo_empresa_total'),
                'dotacion_calculada': informe.get_kpi_principal('dotacion_calculada'),
                'remuneracion_promedio': informe.get_kpi_principal('remuneracion_promedio_mes'),
                'tasa_ausentismo': informe.get_kpi_principal('tasa_ausentismo_porcentaje')
            }
        }
        
        return resultado
        
    except Exception as e:
        error_msg = f"Error generando informe para cierre {cierre_id}: {str(e)}"
        logger.error(error_msg)
        
        # Revertir estado del cierre
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            if cierre.estado == 'generando_informe':
                cierre.estado = 'incidencias_resueltas'
                cierre.save(update_fields=['estado'])
                logger.info(f"🔄 Estado revertido a 'incidencias_resueltas'")
        except:
            pass
        
        # Actualizar estado del task
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'cierre_id': cierre_id,
                'tiempo_transcurrido': (timezone.now() - inicio).total_seconds()
            }
        )
        
        raise Exception(error_msg)

# ============================================================================
#                           TASKS AUXILIARES
# ============================================================================

@shared_task(bind=True, name='nomina.regenerar_informe')
def regenerar_informe_existente(self, cierre_id, usuario_id=None, forzar=False):
    """
    🔄 TASK: Regenera un informe existente
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        forzar: Si True, regenera aunque ya exista
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        if cierre.estado != 'finalizado' and not forzar:
            raise ValueError("Solo se pueden regenerar informes de cierres finalizados")
        
        # Usar el task principal en modo completo
        resultado = generar_informe_nomina_completo.apply_async(
            args=[cierre_id, usuario_id, 'completo']
        ).get()
        
        return {
            'success': True,
            'mensaje': 'Informe regenerado exitosamente',
            'resultado': resultado
        }
        
    except Exception as e:
        logger.error(f"Error regenerando informe {cierre_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@shared_task(name='nomina.verificar_estado_informe')
def verificar_estado_informe(cierre_id):
    """
    🔍 TASK: Verifica el estado actual de un informe
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        try:
            informe = InformeNomina.objects.get(cierre=cierre)
            estado_informe = 'generado'
            fecha_generacion = informe.fecha_generacion
            tiempo_calculo = informe.tiempo_calculo.total_seconds() if informe.tiempo_calculo else 0
        except InformeNomina.DoesNotExist:
            estado_informe = 'no_generado'
            fecha_generacion = None
            tiempo_calculo = 0
        
        return {
            'cierre_id': cierre_id,
            'estado_cierre': cierre.estado,
            'estado_informe': estado_informe,
            'fecha_generacion': fecha_generacion.isoformat() if fecha_generacion else None,
            'tiempo_calculo_segundos': tiempo_calculo,
            'tiene_informe': estado_informe == 'generado'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'cierre_id': cierre_id
        }

@shared_task(bind=True, name='nomina.calcular_solo_kpis')
def calcular_solo_kpis_basicos(self, cierre_id):
    """
    ⚡ TASK RÁPIDO: Calcula solo KPIs básicos sin lista de empleados
    """
    try:
        self.update_state(state='PROGRESS', meta={'descripcion': 'Calculando KPIs básicos...', 'porcentaje': 50})
        
        # Usar el task principal en modo rápido
        resultado = generar_informe_nomina_completo.apply_async(
            args=[cierre_id, None, 'solo_kpis']
        ).get()
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error calculando KPIs para cierre {cierre_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

# ============================================================================
#                           TASKS DE MONITOREO
# ============================================================================

@shared_task(name='nomina.limpiar_informes_antiguos')
def limpiar_informes_antiguos(dias_antiguedad=90):
    """
    🧹 TASK DE MANTENIMIENTO: Limpia informes antiguos
    """
    from datetime import timedelta
    
    fecha_limite = timezone.now() - timedelta(days=dias_antiguedad)
    
    informes_antiguos = InformeNomina.objects.filter(
        fecha_generacion__lt=fecha_limite
    )
    
    total_eliminados = informes_antiguos.count()
    informes_antiguos.delete()
    
    logger.info(f"🧹 Limpieza completada: {total_eliminados} informes eliminados")
    
    return {
        'informes_eliminados': total_eliminados,
        'fecha_limite': fecha_limite.isoformat()
    }

@shared_task(name='nomina.estadisticas_informes')
def generar_estadisticas_informes():
    """
    📊 TASK: Genera estadísticas de uso de informes
    """
    from django.db.models import Count, Avg, Max, Min
    
    stats = InformeNomina.objects.aggregate(
        total_informes=Count('id'),
        tiempo_promedio=Avg('tiempo_calculo'),
        tiempo_maximo=Max('tiempo_calculo'),
        tiempo_minimo=Min('tiempo_calculo')
    )
    
    # Estadísticas por cliente
    por_cliente = InformeNomina.objects.values(
        'cierre__cliente__nombre'
    ).annotate(
        total=Count('id'),
        tiempo_promedio=Avg('tiempo_calculo')
    ).order_by('-total')[:10]
    
    return {
        'estadisticas_generales': stats,
        'top_clientes': list(por_cliente),
        'fecha_generacion': timezone.now().isoformat()
    }

# ============================================================================
#                           UTILIDADES
# ============================================================================

def obtener_progreso_task(task_id):
    """
    📈 Obtiene el progreso de un task por su ID
    """
    from celery.result import AsyncResult
    
    try:
        result = AsyncResult(task_id)
        
        if result.state == 'PENDING':
            return {
                'state': 'PENDING',
                'descripcion': 'Tarea en cola...',
                'porcentaje': 0
            }
        elif result.state == 'PROGRESS':
            return {
                'state': 'PROGRESS',
                **result.result
            }
        elif result.state == 'SUCCESS':
            return {
                'state': 'SUCCESS',
                'descripcion': 'Completado exitosamente',
                'porcentaje': 100,
                'resultado': result.result
            }
        elif result.state == 'FAILURE':
            return {
                'state': 'FAILURE',
                'descripcion': 'Error en el procesamiento',
                'error': str(result.result)
            }
        else:
            return {
                'state': result.state,
                'descripcion': f'Estado: {result.state}'
            }
            
    except Exception as e:
        return {
            'state': 'ERROR',
            'error': f'Error obteniendo progreso: {str(e)}'
        }
