"""
Tareas Celery para generación de reportes financieros
"""
from celery import shared_task
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
import logging

from .models import (
    CierreContabilidad, 
    ReporteFinanciero, 
    CuentaContable, 
    MovimientoContable,
    AperturaCuenta,
    AccountClassification,
    ClasificacionSet,
    ClasificacionOption
)

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generar_estado_situacion_financiera(self, cierre_id, usuario_id=None, regenerar=False):
    """
    Genera el Estado de Situación Financiera para un cierre específico
    
    Args:
        cierre_id: ID del cierre contable
        usuario_id: ID del usuario que solicita el reporte
        regenerar: Si True, regenera aunque ya exista
    """
    try:
        logger.info(f"Iniciando generación ESF para cierre {cierre_id}")
        
        # Obtener el cierre
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
        except CierreContabilidad.DoesNotExist:
            raise Exception(f"Cierre {cierre_id} no encontrado")
        
        # Verificar si ya existe y si no hay que regenerar
        reporte_existente = ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='esf'
        ).first()
        
        if reporte_existente and not regenerar:
            if reporte_existente.estado == 'completado':
                return {
                    'success': True,
                    'mensaje': 'Reporte ya existe y está completado',
                    'reporte_id': reporte_existente.id
                }
        
        # Crear o actualizar el reporte
        with transaction.atomic():
            reporte, created = ReporteFinanciero.objects.get_or_create(
                cierre=cierre,
                tipo_reporte='esf',
                defaults={
                    'usuario_generador_id': usuario_id,
                    'estado': 'generando'
                }
            )
            
            if not created:
                reporte.estado = 'generando'
                reporte.error_mensaje = ''
                reporte.fecha_actualizacion = timezone.now()
                reporte.save()
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Obteniendo clasificaciones ESF', 'progress': 10}
        )
        
        # Obtener el set de clasificación ESF de forma robusta
        set_esf = None
        
        # Estrategia 1: Buscar exactamente "Estado de Situación Financiera"
        try:
            set_esf = ClasificacionSet.objects.filter(
                cliente=cierre.cliente,
                nombre__iexact="Estado de Situación Financiera"
            ).first()
            if set_esf:
                print(f"Encontrado set ESF exacto: {set_esf.nombre}")
        except Exception as e:
            print(f"Error buscando set ESF exacto: {e}")
        
        # Estrategia 2: Buscar que contenga "ESF"
        if not set_esf:
            try:
                sets_esf = ClasificacionSet.objects.filter(
                    cliente=cierre.cliente,
                    nombre__icontains="esf"
                )
                if sets_esf.exists():
                    set_esf = sets_esf.first()
                    print(f"Encontrado set por 'esf': {set_esf.nombre} (de {sets_esf.count()} sets)")
            except Exception as e:
                print(f"Error buscando sets con 'esf': {e}")
        
        # Estrategia 3: Buscar que contenga "estado"
        if not set_esf:
            try:
                sets_estado = ClasificacionSet.objects.filter(
                    cliente=cierre.cliente,
                    nombre__icontains="estado"
                )
                if sets_estado.exists():
                    set_esf = sets_estado.first()
                    print(f"Encontrado set por 'estado': {set_esf.nombre} (de {sets_estado.count()} sets)")
            except Exception as e:
                print(f"Error buscando sets con 'estado': {e}")
        
        # Si no encontramos ningún set
        if not set_esf:
            raise Exception("No se encontró set de clasificación ESF para este cliente")
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Obteniendo cuentas y movimientos', 'progress': 25}
        )
        
        # Obtener todas las cuentas del cierre con sus movimientos
        cuentas_data = _obtener_cuentas_con_datos(cierre)
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Procesando clasificaciones', 'progress': 50}
        )
        
        # Obtener clasificaciones del set ESF
        clasificaciones = _obtener_clasificaciones_esf(set_esf, cuentas_data.keys())
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Agrupando y calculando totales', 'progress': 75}
        )
        
        # Agrupar y estructurar los datos
        datos_esf = _estructurar_datos_esf(cuentas_data, clasificaciones, cierre)
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando reporte', 'progress': 90}
        )
        
        # Guardar el reporte
        metadata = {
            'tiempo_generacion': (timezone.now() - reporte.fecha_actualizacion).total_seconds(),
            'total_cuentas': len(cuentas_data),
            'version': '1.0',
            'set_clasificacion_usado': set_esf.nombre
        }
        
        reporte.marcar_como_completado(datos_esf)
        reporte.metadata = metadata
        reporte.save()
        
        logger.info(f"ESF generado exitosamente para cierre {cierre_id}")
        
        return {
            'success': True,
            'mensaje': 'Estado de Situación Financiera generado exitosamente',
            'reporte_id': reporte.id,
            'metadata': metadata
        }
        
    except Exception as e:
        error_msg = f"Error generando ESF: {str(e)}"
        logger.error(error_msg)
        
        # Marcar reporte como error si existe
        try:
            reporte = ReporteFinanciero.objects.get(
                cierre_id=cierre_id,
                tipo_reporte='esf'
            )
            reporte.marcar_como_error(error_msg)
        except:
            pass
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        
        raise Exception(error_msg)


def _obtener_cuentas_con_datos(cierre):
    """
    Obtiene todas las cuentas del cierre con sus datos calculados
    """
    # Obtener cuentas con movimientos
    cuentas_con_movimientos = MovimientoContable.objects.filter(
        cierre=cierre
    ).values_list('cuenta_id', flat=True).distinct()
    
    # Obtener cuentas con saldo de apertura
    cuentas_con_apertura = AperturaCuenta.objects.filter(
        cierre=cierre
    ).values_list('cuenta_id', flat=True).distinct()
    
    # Unir ambos conjuntos
    cuenta_ids = set(cuentas_con_movimientos) | set(cuentas_con_apertura)
    
    # Obtener datos de las cuentas
    cuentas = CuentaContable.objects.filter(
        id__in=cuenta_ids,
        cliente=cierre.cliente
    ).values('id', 'codigo', 'nombre', 'nombre_en')
    
    # Crear diccionario con datos de cuentas
    cuentas_data = {}
    for cuenta in cuentas:
        cuentas_data[cuenta['id']] = {
            'codigo': cuenta['codigo'],
            'nombre_es': cuenta['nombre'],
            'nombre_en': cuenta['nombre_en'] or cuenta['nombre'],
            'movimientos': [],
            'saldo_anterior': 0,
            'total_debe': 0,
            'total_haber': 0,
            'saldo_final': 0
        }
    
    # Obtener saldos de apertura
    aperturas = AperturaCuenta.objects.filter(
        cierre=cierre,
        cuenta_id__in=cuenta_ids
    ).values('cuenta_id', 'saldo_anterior')
    
    for apertura in aperturas:
        if apertura['cuenta_id'] in cuentas_data:
            cuentas_data[apertura['cuenta_id']]['saldo_anterior'] = float(apertura['saldo_anterior'])
    
    # Obtener movimientos agrupados por cuenta
    movimientos = MovimientoContable.objects.filter(
        cierre=cierre,
        cuenta_id__in=cuenta_ids
    ).values(
        'cuenta_id'
    ).annotate(
        total_debe=models.Sum('debe'),
        total_haber=models.Sum('haber')
    )
    
    # También obtener movimientos detallados
    movimientos_detalle = MovimientoContable.objects.filter(
        cierre=cierre,
        cuenta_id__in=cuenta_ids
    ).select_related('tipo_documento').values(
        'cuenta_id', 'fecha', 'descripcion', 'debe', 'haber',
        'numero_documento', 'tipo_doc_codigo'
    ).order_by('cuenta_id', 'fecha')
    
    # Agrupar movimientos por cuenta
    movimientos_por_cuenta = {}
    for mov in movimientos_detalle:
        cuenta_id = mov['cuenta_id']
        if cuenta_id not in movimientos_por_cuenta:
            movimientos_por_cuenta[cuenta_id] = []
        
        movimientos_por_cuenta[cuenta_id].append({
            'fecha': mov['fecha'].isoformat(),
            'descripcion': mov['descripcion'],
            'debe': float(mov['debe']),
            'haber': float(mov['haber']),
            'numero_documento': mov['numero_documento'],
            'tipo_documento': mov['tipo_doc_codigo']
        })
    
    # Calcular totales y asignar movimientos
    for mov in movimientos:
        cuenta_id = mov['cuenta_id']
        if cuenta_id in cuentas_data:
            cuentas_data[cuenta_id]['total_debe'] = float(mov['total_debe'] or 0)
            cuentas_data[cuenta_id]['total_haber'] = float(mov['total_haber'] or 0)
            cuentas_data[cuenta_id]['movimientos'] = movimientos_por_cuenta.get(cuenta_id, [])
            
            # Calcular saldo final
            saldo_anterior = cuentas_data[cuenta_id]['saldo_anterior']
            total_debe = cuentas_data[cuenta_id]['total_debe']
            total_haber = cuentas_data[cuenta_id]['total_haber']
            cuentas_data[cuenta_id]['saldo_final'] = saldo_anterior + total_debe - total_haber
    
    return cuentas_data


def _obtener_clasificaciones_esf(set_esf, cuenta_ids):
    """
    Obtiene las clasificaciones ESF para las cuentas especificadas
    """
    clasificaciones = AccountClassification.objects.filter(
        set_clas=set_esf,
        cuenta_id__in=cuenta_ids
    ).select_related('opcion').values(
        'cuenta_id', 'opcion__valor', 'opcion__id'
    )
    
    # Crear mapa de clasificaciones
    mapa_clasificaciones = {}
    for cls in clasificaciones:
        mapa_clasificaciones[cls['cuenta_id']] = {
            'opcion_id': cls['opcion__id'],
            'opcion_valor': cls['opcion__valor']
        }
    
    return mapa_clasificaciones


def _estructurar_datos_esf(cuentas_data, clasificaciones, cierre):
    """
    Estructura los datos en el formato del Estado de Situación Financiera
    """
    # Estructura base del ESF con inicialización completa
    esf_data = {
        'metadata': {
            'cliente_id': cierre.cliente.id,
            'cliente_nombre': cierre.cliente.nombre,
            'cierre_id': cierre.id,
            'periodo': cierre.periodo,
            'fecha_generacion': timezone.now().isoformat(),
            'moneda': 'CLP'  # Asumir pesos chilenos por defecto
        },
        'activos': {
            'corrientes': {
                'grupos': {},
                'total': 0
            },
            'no_corrientes': {
                'grupos': {},
                'total': 0
            },
            'total_activos': 0
        },
        'pasivos': {
            'corrientes': {
                'grupos': {},
                'total': 0
            },
            'no_corrientes': {
                'grupos': {},
                'total': 0
            },
            'total_pasivos': 0
        },
        'patrimonio': {
            'capital': {
                'grupos': {},
                'total': 0
            },
            'resultados': {
                'grupos': {},
                'total': 0
            },
            'total_patrimonio': 0
        },
        'totales': {
            'total_pasivos_patrimonio': 0,
            'diferencia': 0  # Debería ser 0 si cuadra
        }
    }
    
    # Agrupar cuentas por clasificación
    for cuenta_id, datos_cuenta in cuentas_data.items():
        clasificacion = clasificaciones.get(cuenta_id)
        
        if not clasificacion:
            continue  # Saltar cuentas sin clasificación ESF
        
        opcion_valor = clasificacion['opcion_valor'].lower()
        
        # Determinar la categoría principal y subcategoría
        categoria_principal, subcategoria = _determinar_categoria_esf(opcion_valor)
        
        if categoria_principal and subcategoria:
            # Las categorías y subcategorías ya están inicializadas en la estructura base
            # Solo necesitamos verificar que existan (para casos de subcategorías dinámicas)
            if categoria_principal not in esf_data:
                esf_data[categoria_principal] = {}
            
            if subcategoria not in esf_data[categoria_principal]:
                esf_data[categoria_principal][subcategoria] = {
                    'grupos': {},
                    'total': 0
                }
            
            # Asegurar que 'grupos' existe (redundante pero seguro)
            if 'grupos' not in esf_data[categoria_principal][subcategoria]:
                esf_data[categoria_principal][subcategoria]['grupos'] = {}
            
            # Agrupar por el valor de la opción
            grupo_nombre = clasificacion['opcion_valor']
            if grupo_nombre not in esf_data[categoria_principal][subcategoria]['grupos']:
                esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre] = {
                    'total': 0,
                    'cuentas': []
                }
            
            # Agregar la cuenta al grupo
            esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre]['cuentas'].append({
                'codigo': datos_cuenta['codigo'],
                'nombre_es': datos_cuenta['nombre_es'],
                'nombre_en': datos_cuenta['nombre_en'],
                'saldo_anterior': datos_cuenta['saldo_anterior'],
                'total_debe': datos_cuenta['total_debe'],
                'total_haber': datos_cuenta['total_haber'],
                'saldo_final': datos_cuenta['saldo_final'],
                'movimientos': datos_cuenta['movimientos']
            })
            
            # Actualizar totales
            saldo_final = datos_cuenta['saldo_final']
            esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre]['total'] += saldo_final
            esf_data[categoria_principal][subcategoria]['total'] += saldo_final
            
            # Actualizar total de la categoría principal
            total_key = f'total_{categoria_principal}'
            esf_data[categoria_principal][total_key] += saldo_final
    
    # Calcular totales finales de forma segura
    total_activos = 0
    total_pasivos = 0
    total_patrimonio = 0
    
    # Sumar activos
    if 'activos' in esf_data:
        for subcategoria, datos in esf_data['activos'].items():
            if isinstance(datos, dict) and 'total' in datos:
                total_activos += datos['total']
        esf_data['activos']['total_activos'] = total_activos
    
    # Sumar pasivos
    if 'pasivos' in esf_data:
        for subcategoria, datos in esf_data['pasivos'].items():
            if isinstance(datos, dict) and 'total' in datos:
                total_pasivos += datos['total']
        esf_data['pasivos']['total_pasivos'] = total_pasivos
    
    # Sumar patrimonio
    if 'patrimonio' in esf_data:
        for subcategoria, datos in esf_data['patrimonio'].items():
            if isinstance(datos, dict) and 'total' in datos:
                total_patrimonio += datos['total']
        esf_data['patrimonio']['total_patrimonio'] = total_patrimonio
    
    # Calcular total pasivos + patrimonio y diferencia
    esf_data['totales']['total_pasivos_patrimonio'] = total_pasivos + total_patrimonio
    esf_data['totales']['diferencia'] = total_activos - esf_data['totales']['total_pasivos_patrimonio']
    
    return esf_data


def _determinar_categoria_esf(opcion_valor):
    """
    Determina la categoría principal y subcategoría basada en el valor de la opción
    """
    opcion_lower = opcion_valor.lower()
    
    # Activos
    if any(term in opcion_lower for term in ['activo corriente', 'current asset', 'efectivo', 'inventario', 'deudor']):
        return 'activos', 'corrientes'
    elif any(term in opcion_lower for term in ['activo no corriente', 'non-current asset', 'propiedad', 'planta', 'equipo']):
        return 'activos', 'no_corrientes'
    elif 'activo' in opcion_lower:
        return 'activos', 'corrientes'  # Por defecto activos corrientes
    
    # Pasivos
    elif any(term in opcion_lower for term in ['pasivo corriente', 'current liabilit', 'cuenta por pagar', 'provision']):
        return 'pasivos', 'corrientes'
    elif any(term in opcion_lower for term in ['pasivo no corriente', 'non-current liabilit', 'deuda largo plazo']):
        return 'pasivos', 'no_corrientes'
    elif 'pasivo' in opcion_lower:
        return 'pasivos', 'corrientes'  # Por defecto pasivos corrientes
    
    # Patrimonio
    elif any(term in opcion_lower for term in ['patrimonio', 'capital', 'resultado', 'utilidad', 'equity']):
        return 'patrimonio', 'capital'
    
    # Si no se puede determinar, asumir activo corriente
    return 'activos', 'corrientes'
