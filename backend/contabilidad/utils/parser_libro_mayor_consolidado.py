# backend/contabilidad/utils/parser_libro_mayor_consolidado.py
import logging
from collections import defaultdict
from django.utils import timezone
from django.db import transaction, models

from contabilidad.models import (
    MovimientoContable, 
    TipoDocumento, 
    AccountClassification,
    CuentaContable,
    ExcepcionValidacion
)
from contabilidad.models_incidencias import (
    IncidenciaResumen, 
    HistorialReprocesamiento, 
    LogResolucionIncidencia
)

logger = logging.getLogger(__name__)


def analizar_incidencias_consolidadas(upload_log, total_movimientos):
    """
    Analiza un upload_log procesado y consolida las incidencias por tipo
    Retorna un diccionario con incidencias agrupadas para crear IncidenciaResumen
    """
    logger.info(f"Iniciando análisis consolidado para upload_log {upload_log.id}")
    
    # Obtener excepciones existentes para este cliente
    excepciones_tipo_doc = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion__in=['tipos_doc_no_reconocidos', 'movimientos_tipodoc_nulo'],
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_clasificacion = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_clasificacion',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_nombre_ingles = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_nombre_ingles',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    logger.info(f"Excepciones cargadas: {len(excepciones_tipo_doc)} tipo_doc, "
                f"{len(excepciones_clasificacion)} clasificacion, "
                f"{len(excepciones_nombre_ingles)} nombre_ingles")
    
    incidencias_acumuladas = {
        'tipos_doc_no_reconocidos': defaultdict(lambda: {
            'movimientos': [],
            'cuentas_afectadas': set(),
            'monto_total': 0
        }),
        'movimientos_tipodoc_nulo': {
            'movimientos': [],
            'cuentas_afectadas': set(),
            'monto_total': 0
        },
        'cuentas_sin_clasificacion': {
            'cuentas': [],
            'movimientos_afectados': 0,
            'monto_total': 0
        },
        'cuentas_sin_nombre_ingles': {
            'cuentas': [],
            'movimientos_afectados': 0,
            'monto_total': 0
        },
        'cuentas_nuevas_detectadas': {
            'cuentas': [],
            'movimientos_afectados': 0,
            'monto_total': 0
        }
    }
    
    # Analizar movimientos marcados como incompletos
    movimientos_incompletos = MovimientoContable.objects.filter(
        cierre=upload_log.cierre,
        flag_incompleto=True
    ).select_related('cuenta', 'tipo_documento')
    
    logger.info(f"Analizando {movimientos_incompletos.count()} movimientos incompletos")
    
    for mov in movimientos_incompletos:
        monto_movimiento = (mov.debe or 0) + (mov.haber or 0)
        
        # 1. TIPOS DE DOCUMENTO PROBLEMÁTICOS
        # Solo considerar como incidencia si la cuenta NO tiene excepción
        if not mov.tipo_documento and mov.tipo_doc_codigo and mov.cuenta.codigo not in excepciones_tipo_doc:
            # Código existe pero no está en BD
            codigo = mov.tipo_doc_codigo
            incidencias_acumuladas['tipos_doc_no_reconocidos'][codigo]['movimientos'].append({
                'id': mov.id,
                'fila_excel': None,  # Se puede agregar si está disponible
                'cuenta': mov.cuenta.codigo,
                'numero_comprobante': mov.numero_comprobante,
                'fecha': mov.fecha.isoformat(),
                'monto': float(monto_movimiento),
                'descripcion': mov.descripcion[:100] if mov.descripcion else ''
            })
            incidencias_acumuladas['tipos_doc_no_reconocidos'][codigo]['cuentas_afectadas'].add(mov.cuenta.codigo)
            incidencias_acumuladas['tipos_doc_no_reconocidos'][codigo]['monto_total'] += float(monto_movimiento)
        
        elif not mov.tipo_documento and not mov.tipo_doc_codigo and mov.cuenta.codigo not in excepciones_tipo_doc:
            # Campo TIPODOC completamente vacío - solo si no hay excepción
            incidencias_acumuladas['movimientos_tipodoc_nulo']['movimientos'].append({
                'id': mov.id,
                'cuenta': mov.cuenta.codigo,
                'numero_comprobante': mov.numero_comprobante,
                'fecha': mov.fecha.isoformat(),
                'monto': float(monto_movimiento),
                'descripcion': mov.descripcion[:100] if mov.descripcion else ''
            })
            incidencias_acumuladas['movimientos_tipodoc_nulo']['cuentas_afectadas'].add(mov.cuenta.codigo)
            incidencias_acumuladas['movimientos_tipodoc_nulo']['monto_total'] += float(monto_movimiento)
        
        # 2. CUENTAS SIN CLASIFICACIÓN - solo si no hay excepción
        if (not AccountClassification.objects.filter(cuenta=mov.cuenta).exists() and 
            mov.cuenta.codigo not in excepciones_clasificacion):
            if mov.cuenta.codigo not in [c['codigo'] for c in incidencias_acumuladas['cuentas_sin_clasificacion']['cuentas']]:
                # Contar movimientos de esta cuenta
                mov_cuenta = MovimientoContable.objects.filter(
                    cierre=upload_log.cierre,
                    cuenta=mov.cuenta
                ).count()
                
                monto_cuenta = MovimientoContable.objects.filter(
                    cierre=upload_log.cierre,
                    cuenta=mov.cuenta
                ).aggregate(
                    total=models.Sum('debe') + models.Sum('haber')
                )['total'] or 0
                
                incidencias_acumuladas['cuentas_sin_clasificacion']['cuentas'].append({
                    'codigo': mov.cuenta.codigo,
                    'nombre': mov.cuenta.nombre,
                    'movimientos_count': mov_cuenta,
                    'monto_total': float(monto_cuenta)
                })
                incidencias_acumuladas['cuentas_sin_clasificacion']['movimientos_afectados'] += mov_cuenta
                incidencias_acumuladas['cuentas_sin_clasificacion']['monto_total'] += float(monto_cuenta)
        
        # 3. CUENTAS SIN NOMBRE EN INGLÉS - solo si no hay excepción
        if (upload_log.cliente.bilingue and not mov.cuenta.nombre_en and 
            mov.cuenta.codigo not in excepciones_nombre_ingles):
            if mov.cuenta.codigo not in [c['codigo'] for c in incidencias_acumuladas['cuentas_sin_nombre_ingles']['cuentas']]:
                # Contar movimientos de esta cuenta
                mov_cuenta = MovimientoContable.objects.filter(
                    cierre=upload_log.cierre,
                    cuenta=mov.cuenta
                ).count()
                
                monto_cuenta = MovimientoContable.objects.filter(
                    cierre=upload_log.cierre,
                    cuenta=mov.cuenta
                ).aggregate(
                    total=models.Sum('debe') + models.Sum('haber')
                )['total'] or 0
                
                incidencias_acumuladas['cuentas_sin_nombre_ingles']['cuentas'].append({
                    'codigo': mov.cuenta.codigo,
                    'nombre': mov.cuenta.nombre,
                    'movimientos_count': mov_cuenta,
                    'monto_total': float(monto_cuenta)
                })
                incidencias_acumuladas['cuentas_sin_nombre_ingles']['movimientos_afectados'] += mov_cuenta
                incidencias_acumuladas['cuentas_sin_nombre_ingles']['monto_total'] += float(monto_cuenta)
    
    # 4. DETECTAR CUENTAS NUEVAS
    # Obtener cuentas que se crearon en este procesamiento
    if hasattr(upload_log, 'resumen') and upload_log.resumen:
        codigos_nuevos = upload_log.resumen.get('codigos_cuentas_nuevas', [])
        if codigos_nuevos:
            for codigo in codigos_nuevos:
                try:
                    cuenta = CuentaContable.objects.get(
                        cliente=upload_log.cliente,
                        codigo=codigo
                    )
                    mov_cuenta = MovimientoContable.objects.filter(
                        cierre=upload_log.cierre,
                        cuenta=cuenta
                    ).count()
                    
                    monto_cuenta = MovimientoContable.objects.filter(
                        cierre=upload_log.cierre,
                        cuenta=cuenta
                    ).aggregate(
                        total=models.Sum('debe') + models.Sum('haber')
                    )['total'] or 0
                    
                    incidencias_acumuladas['cuentas_nuevas_detectadas']['cuentas'].append({
                        'codigo': cuenta.codigo,
                        'nombre': cuenta.nombre,
                        'movimientos_count': mov_cuenta,
                        'monto_total': float(monto_cuenta)
                    })
                    incidencias_acumuladas['cuentas_nuevas_detectadas']['movimientos_afectados'] += mov_cuenta
                    incidencias_acumuladas['cuentas_nuevas_detectadas']['monto_total'] += float(monto_cuenta)
                except CuentaContable.DoesNotExist:
                    continue
    
    # Convertir sets a listas para JSON
    for tipo_doc, data in incidencias_acumuladas['tipos_doc_no_reconocidos'].items():
        data['cuentas_afectadas'] = list(data['cuentas_afectadas'])
    
    incidencias_acumuladas['movimientos_tipodoc_nulo']['cuentas_afectadas'] = list(
        incidencias_acumuladas['movimientos_tipodoc_nulo']['cuentas_afectadas']
    )
    
    logger.info(f"Análisis completado. Tipos detectados: {len(incidencias_acumuladas)}")
    return incidencias_acumuladas


def crear_incidencias_consolidadas(upload_log, incidencias_acumuladas, iteracion=1):
    """
    Crea registros de IncidenciaResumen basados en el análisis consolidado
    """
    logger.info(f"Creando incidencias consolidadas para upload_log {upload_log.id}")
    
    incidencias_creadas = []
    
    with transaction.atomic():
        # 1. TIPOS DE DOCUMENTO NO RECONOCIDOS
        for codigo_td, data in incidencias_acumuladas['tipos_doc_no_reconocidos'].items():
            if data['movimientos']:  # Solo crear si hay movimientos afectados
                incidencia = IncidenciaResumen.objects.create(
                    upload_log=upload_log,
                    tipo_incidencia='tipos_doc_no_reconocidos',
                    codigo_problema=codigo_td,
                    cantidad_afectada=len(data['movimientos']),
                    elementos_afectados=data['cuentas_afectadas'],
                    detalle_muestra=data['movimientos'][:5],  # Primeros 5 ejemplos
                    severidad='alta',
                    mensaje_usuario=f"Código de tipo de documento '{codigo_td}' no existe en el catálogo",
                    accion_sugerida=f"Crear tipo de documento con código '{codigo_td}' o corregir archivo Excel",
                    estadisticas_adicionales={
                        'total_movimientos': len(data['movimientos']),
                        'cuentas_distintas': len(data['cuentas_afectadas']),
                        'monto_total_afectado': data['monto_total'],
                        'codigo_problematico': codigo_td,
                        'iteracion': iteracion
                    }
                )
                incidencias_creadas.append(incidencia)
        
        # 2. MOVIMIENTOS CON TIPODOC NULO
        data_nulo = incidencias_acumuladas['movimientos_tipodoc_nulo']
        if data_nulo['movimientos']:
            incidencia = IncidenciaResumen.objects.create(
                upload_log=upload_log,
                tipo_incidencia='movimientos_tipodoc_nulo',
                codigo_problema=None,
                cantidad_afectada=len(data_nulo['movimientos']),
                elementos_afectados=data_nulo['cuentas_afectadas'],
                detalle_muestra=data_nulo['movimientos'][:5],
                severidad='media',
                mensaje_usuario="Movimientos sin código de tipo de documento en archivo Excel",
                accion_sugerida="Completar columna TIPODOC en archivo Excel antes de procesar",
                estadisticas_adicionales={
                    'total_movimientos': len(data_nulo['movimientos']),
                    'cuentas_distintas': len(data_nulo['cuentas_afectadas']),
                    'monto_total_afectado': data_nulo['monto_total'],
                    'iteracion': iteracion
                }
            )
            incidencias_creadas.append(incidencia)
        
        # 3. CUENTAS SIN CLASIFICACIÓN
        data_clasif = incidencias_acumuladas['cuentas_sin_clasificacion']
        if data_clasif['cuentas']:
            incidencia = IncidenciaResumen.objects.create(
                upload_log=upload_log,
                tipo_incidencia='cuentas_sin_clasificacion',
                codigo_problema=None,
                cantidad_afectada=len(data_clasif['cuentas']),
                elementos_afectados=[c['codigo'] for c in data_clasif['cuentas']],
                detalle_muestra=data_clasif['cuentas'][:5],
                severidad='alta',
                mensaje_usuario=f"{len(data_clasif['cuentas'])} cuentas sin clasificación asignada",
                accion_sugerida="Subir tarjeta de clasificaciones o clasificar manualmente",
                estadisticas_adicionales={
                    'total_cuentas': len(data_clasif['cuentas']),
                    'movimientos_afectados': data_clasif['movimientos_afectados'],
                    'monto_total_afectado': data_clasif['monto_total'],
                    'iteracion': iteracion
                }
            )
            incidencias_creadas.append(incidencia)
        
        # 4. CUENTAS SIN NOMBRE EN INGLÉS
        if upload_log.cliente.bilingue:
            data_ingles = incidencias_acumuladas['cuentas_sin_nombre_ingles']
            if data_ingles['cuentas']:
                incidencia = IncidenciaResumen.objects.create(
                    upload_log=upload_log,
                    tipo_incidencia='cuentas_sin_nombre_ingles',
                    codigo_problema=None,
                    cantidad_afectada=len(data_ingles['cuentas']),
                    elementos_afectados=[c['codigo'] for c in data_ingles['cuentas']],
                    detalle_muestra=data_ingles['cuentas'][:5],
                    severidad='media',
                    mensaje_usuario=f"{len(data_ingles['cuentas'])} cuentas sin nombre en inglés",
                    accion_sugerida="Subir tarjeta de nombres en inglés",
                    estadisticas_adicionales={
                        'total_cuentas': len(data_ingles['cuentas']),
                        'movimientos_afectados': data_ingles['movimientos_afectados'],
                        'monto_total_afectado': data_ingles['monto_total'],
                        'iteracion': iteracion
                    }
                )
                incidencias_creadas.append(incidencia)
        
        # 5. CUENTAS NUEVAS DETECTADAS
        data_nuevas = incidencias_acumuladas['cuentas_nuevas_detectadas']
        if data_nuevas['cuentas']:
            incidencia = IncidenciaResumen.objects.create(
                upload_log=upload_log,
                tipo_incidencia='cuentas_nuevas_detectadas',
                codigo_problema=None,
                cantidad_afectada=len(data_nuevas['cuentas']),
                elementos_afectados=[c['codigo'] for c in data_nuevas['cuentas']],
                detalle_muestra=data_nuevas['cuentas'][:5],
                severidad='baja',
                mensaje_usuario=f"{len(data_nuevas['cuentas'])} cuentas nuevas detectadas en el libro",
                accion_sugerida="Revisar y clasificar las nuevas cuentas detectadas",
                estadisticas_adicionales={
                    'total_cuentas': len(data_nuevas['cuentas']),
                    'movimientos_afectados': data_nuevas['movimientos_afectados'],
                    'monto_total_afectado': data_nuevas['monto_total'],
                    'iteracion': iteracion
                }
            )
            incidencias_creadas.append(incidencia)
    
    logger.info(f"Creadas {len(incidencias_creadas)} incidencias consolidadas")
    return incidencias_creadas


def marcar_movimientos_incompletos(upload_log):
    """
    Re-evalúa y actualiza el flag_incompleto de movimientos después de reprocesamiento
    """
    logger.info(f"Re-marcando movimientos incompletos para upload_log {upload_log.id}")
    
    # Obtener excepciones existentes para este cliente
    excepciones_tipo_doc = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion__in=['tipos_doc_no_reconocidos', 'movimientos_tipodoc_nulo'],
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_clasificacion = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_clasificacion',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_nombre_ingles = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_nombre_ingles',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    movimientos_corregidos = 0
    
    # Obtener todos los movimientos del cierre
    movimientos = MovimientoContable.objects.filter(
        cierre=upload_log.cierre
    ).select_related('cuenta', 'tipo_documento')
    
    for mov in movimientos:
        flag_anterior = mov.flag_incompleto
        
        # Re-evaluar si el movimiento está incompleto
        problemas = []
        
        # 1. Verificar tipo de documento - solo si no hay excepción
        if (mov.tipo_doc_codigo and not mov.tipo_documento and 
            mov.cuenta.codigo not in excepciones_tipo_doc):
            problemas.append('tipo_documento')
        
        # 2. Verificar nombre en inglés - solo si cliente es bilingüe y no hay excepción
        if (upload_log.cliente.bilingue and not mov.cuenta.nombre_en and 
            mov.cuenta.codigo not in excepciones_nombre_ingles):
            problemas.append('nombre_ingles')
        
        # 3. Verificar clasificación - solo si no hay excepción
        if (not AccountClassification.objects.filter(cuenta=mov.cuenta).exists() and 
            mov.cuenta.codigo not in excepciones_clasificacion):
            problemas.append('clasificacion')
        
        # Actualizar flag
        nuevo_flag = len(problemas) > 0
        
        if flag_anterior and not nuevo_flag:
            # Movimiento se corrigió
            mov.flag_incompleto = False
            mov.save(update_fields=['flag_incompleto'])
            movimientos_corregidos += 1
        elif not flag_anterior and nuevo_flag:
            # Movimiento se volvió problemático (raro, pero posible)
            mov.flag_incompleto = True
            mov.save(update_fields=['flag_incompleto'])
    
    logger.info(f"Corregidos {movimientos_corregidos} movimientos")
    return movimientos_corregidos
