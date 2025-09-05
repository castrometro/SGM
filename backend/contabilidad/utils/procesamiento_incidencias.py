# backend/contabilidad/utils/procesamiento_incidencias.py
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
import logging
from collections import defaultdict

from contabilidad.models import (
    MovimientoContable,
    TipoDocumento,
    AccountClassification,
    UploadLog,
)
from contabilidad.models_incidencias import (
    IncidenciaResumen, 
    HistorialReprocesamiento, 
    LogResolucionIncidencia
)

logger = logging.getLogger(__name__)


def reprocesar_con_incidencias_consolidadas(upload_log, usuario, trigger='user_manual', notas=''):
    """
    Función principal para reprocesar el libro mayor y actualizar incidencias consolidadas.
    """
    logger.info(f"Iniciando reprocesamiento consolidado para upload_log {upload_log.id}")
    
    inicio_proceso = timezone.now()
    
    # 1. Obtener iteración actual
    iteracion_anterior = HistorialReprocesamiento.objects.filter(
        upload_log=upload_log
    ).aggregate(max_iter=models.Max('iteracion'))['max_iter'] or 0
    
    nueva_iteracion = iteracion_anterior + 1
    
    # 2. Snapshot de incidencias previas
    incidencias_previas = IncidenciaResumen.objects.filter(
        upload_log=upload_log,
        estado='activa'
    )
    
    snapshot_previas = []
    for inc in incidencias_previas:
        snapshot_previas.append({
            'id': inc.id,
            'tipo_incidencia': inc.tipo_incidencia,
            'codigo_problema': inc.codigo_problema,
            'cantidad_afectada': inc.cantidad_afectada,
            'estado': inc.estado,
            'severidad': inc.severidad
        })
    
    # 3. Marcar incidencias previas como obsoletas
    incidencias_previas.update(estado='obsoleta')
    
    # 4. Re-analizar situación actual
    from contabilidad.utils.parser_libro_mayor_consolidado import (
        analizar_incidencias_consolidadas,
        crear_incidencias_consolidadas,
        marcar_movimientos_incompletos
    )
    
    # Obtener todos los movimientos actuales
    movimientos_count = MovimientoContable.objects.filter(cierre=upload_log.cierre).count()
    
    # Análisis de incidencias actual
    incidencias_acumuladas = analizar_incidencias_consolidadas(upload_log, movimientos_count)
    
    # 5. Crear nuevas incidencias
    incidencias_nuevas = crear_incidencias_consolidadas(
        upload_log, 
        incidencias_acumuladas, 
        iteracion=nueva_iteracion
    )
    
    # 6. Actualizar flag de movimientos incompletos
    movimientos_corregidos = marcar_movimientos_incompletos(upload_log)
    
    # 7. Detectar resoluciones
    incidencias_resueltas = detectar_incidencias_resueltas(
        snapshot_previas, 
        incidencias_nuevas
    )
    
    # 8. Crear historial de reprocesamiento
    tiempo_procesamiento = timezone.now() - inicio_proceso
    
    historial = HistorialReprocesamiento.objects.create(
        upload_log=upload_log,
        usuario=usuario,
        iteracion=nueva_iteracion,
        incidencias_previas=snapshot_previas,
        incidencias_previas_count=len(snapshot_previas),
        incidencias_nuevas=[{
            'id': inc.id,
            'tipo_incidencia': inc.tipo_incidencia,
            'cantidad_afectada': inc.cantidad_afectada
        } for inc in incidencias_nuevas],
        incidencias_nuevas_count=len(incidencias_nuevas),
        incidencias_resueltas=incidencias_resueltas,
        incidencias_resueltas_count=len(incidencias_resueltas),
        movimientos_corregidos=movimientos_corregidos,
        movimientos_total=movimientos_count,
        tiempo_procesamiento=tiempo_procesamiento,
        trigger_reprocesamiento=trigger,
        notas=notas
    )
    
    logger.info(
        f"Reprocesamiento completado: {len(incidencias_resueltas)} resueltas, "
        f"{len(incidencias_nuevas)} nuevas, {movimientos_corregidos} movimientos corregidos"
    )
    
    return historial


def detectar_incidencias_resueltas(snapshot_previas, incidencias_nuevas):
    """
    Compara incidencias previas vs nuevas para detectar resoluciones.
    """
    # Crear mapas por tipo e identificador
    previas_map = {}
    for inc in snapshot_previas:
        key = f"{inc['tipo_incidencia']}_{inc.get('codigo_problema', 'general')}"
        previas_map[key] = inc
    
    nuevas_map = {}
    for inc in incidencias_nuevas:
        key = f"{inc.tipo_incidencia}_{inc.codigo_problema or 'general'}"
        nuevas_map[key] = inc
    
    resueltas = []
    
    # Detectar incidencias que desaparecieron completamente
    for key, inc_previa in previas_map.items():
        if key not in nuevas_map:
            resueltas.append({
                'incidencia_previa_id': inc_previa['id'],
                'tipo_resolucion': 'completa',
                'cantidad_resuelta': inc_previa['cantidad_afectada'],
                'descripcion': f"Incidencia {inc_previa['tipo_incidencia']} resuelta completamente"
            })
        else:
            # Detectar reducciones en cantidad
            inc_nueva = nuevas_map[key]
            if inc_nueva.cantidad_afectada < inc_previa['cantidad_afectada']:
                cantidad_resuelta = inc_previa['cantidad_afectada'] - inc_nueva.cantidad_afectada
                resueltas.append({
                    'incidencia_previa_id': inc_previa['id'],
                    'incidencia_nueva_id': inc_nueva.id,
                    'tipo_resolucion': 'parcial',
                    'cantidad_resuelta': cantidad_resuelta,
                    'descripcion': f"Incidencia {inc_previa['tipo_incidencia']} reducida en {cantidad_resuelta} elementos"
                })
    
    return resueltas


def registrar_resolucion_por_tarjeta(upload_log_tarjeta, tipo_tarjeta, usuario):
    """
    Registra automáticamente la resolución de incidencias cuando se sube una tarjeta.
    """
    logger.info(f"Registrando resolución por tarjeta {tipo_tarjeta}")
    
    # Mapeo de tipos de tarjeta a tipos de incidencia que resuelven
    mapeo_resolucion = {
        'tipo_documento': ['tipos_doc_no_reconocidos'],
        'nombres_ingles': ['cuentas_sin_nombre_ingles'],
        'clasificacion': ['cuentas_sin_clasificacion'],
    }
    
    tipos_incidencia_relacionados = mapeo_resolucion.get(tipo_tarjeta, [])
    if not tipos_incidencia_relacionados:
        return
    
    # Buscar upload_logs de libro mayor del mismo cliente y cierre
    if hasattr(upload_log_tarjeta, 'cierre'):
        libro_mayor_logs = UploadLog.objects.filter(
            cierre=upload_log_tarjeta.cierre,
            tipo_upload='libro_mayor',
            estado='completado'
        ).order_by('-fecha_subida')
        
        for libro_log in libro_mayor_logs:
            # Buscar incidencias activas que esta tarjeta puede resolver
            incidencias_relacionadas = IncidenciaResumen.objects.filter(
                upload_log=libro_log,
                tipo_incidencia__in=tipos_incidencia_relacionados,
                estado='activa'
            )
            
            for incidencia in incidencias_relacionadas:
                # Crear log de resolución
                LogResolucionIncidencia.objects.create(
                    incidencia_resumen=incidencia,
                    accion_realizada=f"Subida de tarjeta {tipo_tarjeta}",
                    usuario=usuario,
                    elementos_resueltos=[],  # Se completará en el reprocesamiento
                    cantidad_resuelta=0,  # Se completará en el reprocesamiento
                    upload_log_relacionado=upload_log_tarjeta,
                    observaciones=f"Tarjeta {tipo_tarjeta} subida, disparando reprocesamiento automático"
                )
        
        # Disparar reprocesamiento automático para el libro mayor más reciente
        if libro_mayor_logs.exists():
            libro_log = libro_mayor_logs.first()
            reprocesar_con_incidencias_consolidadas(
                libro_log,
                usuario,
                trigger='auto_after_upload',
                notas=f'Reprocesamiento automático después de subir {tipo_tarjeta}'
            )


def obtener_resumen_incidencias(upload_log):
    """
    Obtiene un resumen actualizado de las incidencias para el frontend.
    """
    incidencias_activas = IncidenciaResumen.objects.filter(
        upload_log=upload_log,
        estado='activa'
    ).order_by('severidad', '-cantidad_afectada')
    
    resumen = {
        'total_incidencias': incidencias_activas.count(),
        'incidencias_alta': incidencias_activas.filter(severidad='alta').count(),
        'incidencias_media': incidencias_activas.filter(severidad='media').count(),
        'incidencias_baja': incidencias_activas.filter(severidad='baja').count(),
        'elementos_afectados_total': sum(inc.cantidad_afectada for inc in incidencias_activas),
        'tipos_incidencia': {},
        'acciones_sugeridas': []
    }
    
    for incidencia in incidencias_activas:
        tipo = incidencia.get_tipo_incidencia_display()
        if tipo not in resumen['tipos_incidencia']:
            resumen['tipos_incidencia'][tipo] = {
                'cantidad': 0,
                'elementos_afectados': 0,
                'severidad_maxima': 'baja'
            }
        
        resumen['tipos_incidencia'][tipo]['cantidad'] += 1
        resumen['tipos_incidencia'][tipo]['elementos_afectados'] += incidencia.cantidad_afectada
        
        if incidencia.severidad == 'alta':
            resumen['tipos_incidencia'][tipo]['severidad_maxima'] = 'alta'
        elif incidencia.severidad == 'media' and resumen['tipos_incidencia'][tipo]['severidad_maxima'] != 'alta':
            resumen['tipos_incidencia'][tipo]['severidad_maxima'] = 'media'
        
        # Agregar acción sugerida si no está ya
        if incidencia.accion_sugerida not in resumen['acciones_sugeridas']:
            resumen['acciones_sugeridas'].append(incidencia.accion_sugerida)
    
    return resumen
