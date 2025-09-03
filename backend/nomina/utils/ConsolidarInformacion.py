# backend/nomina/utils/ConsolidarInformacion.py

"""
🎯 PROCESO DE CONSOLIDACIÓN DE INFORMACIÓN

Este módulo se ejecuta DESPUÉS de que las discrepancias = 0 para generar
los modelos consolidados con toda la información procesada.

FLUJO:
1. Validar que discrepancias = 0
2. Recopilar datos de todos los archivos procesados  
3. Generar registros consolidados
4. Crear resumen ejecutivo

USO:
    from .utils.ConsolidarInformacion import consolidar_cierre_completo
    resultado = consolidar_cierre_completo(cierre_id)
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import CierreNomina, DiscrepanciaCierre
from ..models_consolidados import (
    NominaConsolidada, 
    ConceptoConsolidado, 
    MovimientoPersonal, 
    ResumenCierre,
    ConceptoEmpleadoConsolidado
)

logger = logging.getLogger(__name__)


def consolidar_cierre_completo(cierre_id, usuario=None):
    """
    🎯 PROCESO PRINCIPAL DE CONSOLIDACIÓN
    
    Consolida toda la información de un cierre después de resolver discrepancias.
    
    Args:
        cierre_id (int): ID del cierre a consolidar
        usuario: Usuario que ejecuta la consolidación
    
    Returns:
        dict: Resultado del proceso con estadísticas
    """
    inicio = timezone.now()
    
    try:
        # 1. Validaciones previas
        cierre = CierreNomina.objects.get(id=cierre_id)
        _validar_precondiciones_consolidacion(cierre)
        
        with transaction.atomic():
            # 2. Limpiar consolidación previa si existe
            _limpiar_consolidacion_previa(cierre)
            
            # 3. Consolidar nómina
            nominas_creadas = _consolidar_nomina(cierre)
            
            # 4. Consolidar conceptos
            conceptos_creados = _consolidar_conceptos(cierre)
            
            # 5. Detectar movimientos de personal
            movimientos_detectados = _detectar_movimientos_personal(cierre)
            
            # 6. Crear detalle de conceptos por empleado
            detalles_creados = _crear_detalle_conceptos_empleados(cierre)
            
            # 7. Generar resumen ejecutivo
            resumen = _generar_resumen_ejecutivo(cierre, usuario)
            
            # 8. Marcar cierre como consolidado
            cierre.estado_consolidacion = 'consolidado'
            cierre.fecha_consolidacion = timezone.now()
            cierre.save(update_fields=['estado_consolidacion', 'fecha_consolidacion'])
        
        tiempo_total = (timezone.now() - inicio).total_seconds()
        
        resultado = {
            'success': True,
            'cierre_id': cierre_id,
            'periodo': cierre.periodo,
            'cliente': cierre.cliente.nombre,
            'estadisticas': {
                'nominas_consolidadas': nominas_creadas,
                'conceptos_consolidados': conceptos_creados,
                'movimientos_detectados': movimientos_detectados,
                'detalles_creados': detalles_creados,
                'tiempo_segundos': tiempo_total,
            },
            'resumen': {
                'total_empleados': resumen.total_empleados_activos,
                'total_liquido': float(resumen.total_liquido_periodo),
                'incorporaciones': resumen.total_incorporaciones,
                'finiquitos': resumen.total_finiquitos,
            }
        }
        
        logger.info(f"Consolidación exitosa para cierre {cierre_id}: {nominas_creadas} nóminas, {conceptos_creados} conceptos")
        return resultado
        
    except Exception as e:
        logger.error(f"Error en consolidación de cierre {cierre_id}: {e}")
        raise


def _validar_precondiciones_consolidacion(cierre):
    """Valida que el cierre esté listo para consolidación"""
    
    # 1. Verificar que no hay discrepancias pendientes
    discrepancias_pendientes = DiscrepanciaCierre.objects.filter(cierre=cierre).count()
    if discrepancias_pendientes > 0:
        raise ValueError(f"No se puede consolidar: {discrepancias_pendientes} discrepancias pendientes")
    
    # 2. Verificar archivos procesados
    if not cierre.libro_remuneraciones.filter(estado='procesado').exists():
        raise ValueError("Libro de remuneraciones no procesado")
    
    if not cierre.movimientos_mes.filter(estado='procesado').exists():
        raise ValueError("Movimientos del mes no procesados")
    
    logger.info(f"Precondiciones validadas para cierre {cierre.id}")


def _limpiar_consolidacion_previa(cierre):
    """Limpia cualquier consolidación previa"""
    
    # Eliminar registros consolidados previos
    NominaConsolidada.objects.filter(cierre=cierre).delete()
    ConceptoConsolidado.objects.filter(cierre=cierre).delete()
    MovimientoPersonal.objects.filter(cierre=cierre).delete()
    
    if hasattr(cierre, 'resumen_consolidado'):
        cierre.resumen_consolidado.delete()
    
    logger.info(f"Consolidación previa limpiada para cierre {cierre.id}")


def _consolidar_nomina(cierre):
    """Consolida la nómina final combinando todos los archivos"""
    
    from ..models import LibroRemuneracionesRegistro, MovimientosMesRegistro
    
    nominas_consolidadas = []
    
    # Obtener todos los empleados únicos de los archivos procesados
    empleados_libro = set(LibroRemuneracionesRegistro.objects.filter(
        archivo__cierre=cierre,
        archivo__estado='procesado'
    ).values_list('rut_empleado', flat=True))
    
    empleados_movimientos = set(MovimientosMesRegistro.objects.filter(
        archivo__cierre=cierre,
        archivo__estado='procesado'
    ).values_list('rut_empleado', flat=True))
    
    # Union de todos los empleados
    todos_empleados = empleados_libro.union(empleados_movimientos)
    
    for rut_empleado in todos_empleados:
        nomina = _consolidar_empleado_individual(cierre, rut_empleado)
        if nomina:
            nominas_consolidadas.append(nomina)
    
    # Bulk create para eficiencia
    NominaConsolidada.objects.bulk_create(nominas_consolidadas, batch_size=100)
    
    logger.info(f"Consolidadas {len(nominas_consolidadas)} nóminas para cierre {cierre.id}")
    return len(nominas_consolidadas)


def _consolidar_empleado_individual(cierre, rut_empleado):
    """Consolida la información de un empleado específico"""
    
    from ..models import LibroRemuneracionesRegistro, MovimientosMesRegistro
    
    # Obtener datos del empleado desde el libro
    registro_libro = LibroRemuneracionesRegistro.objects.filter(
        archivo__cierre=cierre,
        archivo__estado='procesado',
        rut_empleado=rut_empleado
    ).first()
    
    # Obtener movimientos del empleado
    movimientos_empleado = MovimientosMesRegistro.objects.filter(
        archivo__cierre=cierre,
        archivo__estado='procesado',
        rut_empleado=rut_empleado
    )
    
    if not registro_libro and not movimientos_empleado.exists():
        return None
    
    # Calcular totales por categoría (mapeo temporal desde las fuentes existentes)
    total_haberes_imponibles = Decimal('0')
    total_haberes_no_imponibles = Decimal('0')
    total_descuentos = Decimal('0')
    
    # Sumar desde libro de remuneraciones
    if registro_libro:
        # Mapear el total_haberes del registro del libro a haberes_imponibles por compatibilidad
        if registro_libro.total_haberes:
            total_haberes_imponibles += Decimal(str(registro_libro.total_haberes))
        if registro_libro.total_descuentos:
            total_descuentos += Decimal(str(registro_libro.total_descuentos))
    
    # Sumar desde movimientos
    for mov in movimientos_empleado:
        if mov.tipo_valor == 'haber' and mov.valor:
            # Asumir haberes imponibles para importes provenientes de movimientos
            total_haberes_imponibles += Decimal(str(mov.valor))
        elif mov.tipo_valor == 'descuento' and mov.valor:
            total_descuentos += Decimal(str(mov.valor))
    
    # Crear registro consolidado
    nomina = NominaConsolidada(
        cierre=cierre,
        rut_empleado=rut_empleado,
        nombre_empleado=registro_libro.nombre_empleado if registro_libro else f"Empleado {rut_empleado}",
        cargo=getattr(registro_libro, 'cargo', None),
        centro_costo=getattr(registro_libro, 'centro_costo', None),
        estado_empleado=_determinar_estado_empleado(cierre, rut_empleado),
        haberes_imponibles=total_haberes_imponibles,
        haberes_no_imponibles=total_haberes_no_imponibles,
        dctos_legales=total_descuentos,
        liquido_a_pagar=total_haberes_imponibles - total_descuentos,
        fuente_datos={
            'libro_remuneraciones': bool(registro_libro),
            'movimientos_mes': movimientos_empleado.count(),
            'fecha_consolidacion': timezone.now().isoformat()
        }
    )
    
    return nomina


def _determinar_estado_empleado(cierre, rut_empleado):
    """Determina el estado del empleado en este periodo"""
    
    # Por ahora, marcar como activo
    # TODO: Implementar lógica para detectar nuevas incorporaciones, finiquitos, etc.
    return 'activo'


def _consolidar_conceptos(cierre):
    """Consolida estadísticas de conceptos"""
    
    from django.db.models import Count, Sum, Avg, Min, Max
    from ..models import LibroRemuneracionesRegistro
    
    conceptos_consolidados = []
    
    # Obtener conceptos únicos del libro de remuneraciones
    # TODO: Expandir para incluir otros archivos según estructura real
    conceptos_stats = LibroRemuneracionesRegistro.objects.filter(
        archivo__cierre=cierre,
        archivo__estado='procesado'
    ).values(
        'concepto_codigo', 'concepto_nombre'
    ).annotate(
        empleados_count=Count('rut_empleado', distinct=True),
        monto_total=Sum('valor'),
        monto_promedio=Avg('valor'),
        monto_minimo=Min('valor'),
        monto_maximo=Max('valor')
    )
    
    for concepto in conceptos_stats:
        concepto_consolidado = ConceptoConsolidado(
            cierre=cierre,
            codigo_concepto=concepto['concepto_codigo'] or 'SIN_CODIGO',
            nombre_concepto=concepto['concepto_nombre'] or 'Sin Nombre',
            tipo_concepto='informativo',  # TODO: Clasificar según código
            cantidad_empleados_afectados=concepto['empleados_count'],
            monto_total=concepto['monto_total'] or Decimal('0'),
            monto_promedio=concepto['monto_promedio'] or Decimal('0'),
            monto_minimo=concepto['monto_minimo'] or Decimal('0'),
            monto_maximo=concepto['monto_maximo'] or Decimal('0'),
        )
        conceptos_consolidados.append(concepto_consolidado)
    
    # Bulk create
    ConceptoConsolidado.objects.bulk_create(conceptos_consolidados, batch_size=100)
    
    logger.info(f"Consolidados {len(conceptos_consolidados)} conceptos para cierre {cierre.id}")
    return len(conceptos_consolidados)


def _detectar_movimientos_personal(cierre):
    """Detecta movimientos de personal comparando con periodo anterior"""
    
    # TODO: Implementar detección de incorporaciones, finiquitos, ausencias
    # Por ahora retornar 0
    logger.info(f"Detección de movimientos pendiente de implementar para cierre {cierre.id}")
    return 0


def _crear_detalle_conceptos_empleados(cierre):
    """Crea el detalle de conceptos por empleado"""
    
    # TODO: Implementar creación de detalles granulares
    logger.info(f"Detalle de conceptos por empleado pendiente de implementar para cierre {cierre.id}")
    return 0


def _generar_resumen_ejecutivo(cierre, usuario):
    """Genera el resumen ejecutivo final"""
    
    from django.db.models import Sum, Avg, Min, Max, Count
    
    # Calcular estadísticas desde nómina consolidada
    nominas = NominaConsolidada.objects.filter(cierre=cierre)
    
    stats = nominas.aggregate(
        total_empleados=Count('id'),
        total_haberes=Sum('total_haberes'),
        total_descuentos=Sum('total_descuentos'), 
        total_liquido=Sum('liquido_a_pagar'),
        promedio_liquido=Avg('liquido_a_pagar'),
        liquido_min=Min('liquido_a_pagar'),
        liquido_max=Max('liquido_a_pagar')
    )
    
    # Contar conceptos
    conceptos_stats = ConceptoConsolidado.objects.filter(cierre=cierre).aggregate(
        total_conceptos=Count('id'),
        conceptos_haberes=Count('id', filter=models.Q(tipo_concepto__contains='haber')),
        conceptos_descuentos=Count('id', filter=models.Q(tipo_concepto__contains='descuento'))
    )
    
    # Crear resumen
    resumen = ResumenCierre.objects.create(
        cierre=cierre,
        total_empleados_activos=stats['total_empleados'] or 0,
        total_haberes_periodo=stats['total_haberes'] or Decimal('0'),
        total_descuentos_periodo=stats['total_descuentos'] or Decimal('0'),
        total_liquido_periodo=stats['total_liquido'] or Decimal('0'),
        promedio_liquido_empleado=stats['promedio_liquido'] or Decimal('0'),
        liquido_minimo=stats['liquido_min'] or Decimal('0'),
        liquido_maximo=stats['liquido_max'] or Decimal('0'),
        total_conceptos_unicos=conceptos_stats['total_conceptos'] or 0,
        total_conceptos_haberes=conceptos_stats['conceptos_haberes'] or 0,
        total_conceptos_descuentos=conceptos_stats['conceptos_descuentos'] or 0,
        consolidado_por=usuario,
        discrepancias_resueltas=True,
        archivos_validados=True,
        consolidacion_completa=True,
    )
    
    logger.info(f"Resumen ejecutivo generado para cierre {cierre.id}: {resumen.total_empleados_activos} empleados")
    return resumen


# === FUNCIONES DE CONSULTA CONSOLIDADA ===

def obtener_nomina_consolidada(cierre_id):
    """Obtiene la nómina consolidada completa de un cierre"""
    return NominaConsolidada.objects.filter(cierre_id=cierre_id).select_related('cierre')


def obtener_empleados_por_estado(cierre_id, estado):
    """Obtiene empleados filtrados por estado"""
    return NominaConsolidada.objects.filter(
        cierre_id=cierre_id,
        estado_empleado=estado
    ).order_by('nombre_empleado')


def obtener_conceptos_por_tipo(cierre_id, tipo_concepto):
    """Obtiene conceptos filtrados por tipo"""
    return ConceptoConsolidado.objects.filter(
        cierre_id=cierre_id,
        tipo_concepto=tipo_concepto
    ).order_by('-monto_total')


def obtener_resumen_ejecutivo(cierre_id):
    """Obtiene el resumen ejecutivo de un cierre"""
    try:
        return ResumenCierre.objects.get(cierre_id=cierre_id)
    except ResumenCierre.DoesNotExist:
        return None
