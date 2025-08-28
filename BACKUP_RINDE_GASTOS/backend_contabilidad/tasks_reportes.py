"""
Tareas Celery para generación de reportes financieros
"""
from celery import shared_task
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
import logging
import json

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
from .cache_redis import get_cache_system

logger = logging.getLogger(__name__)

def _guardar_reportes_con_retencion(cierre, datos_esf=None, datos_eri=None, datos_ecp=None, ttl_hours=24*30):
    """
    Guarda ESF, ERI y/o ECP en Redis con retención automática de solo los 2 cierres más recientes.
    
    Args:
        cierre: Instancia de CierreContabilidad
        datos_esf: Datos del ESF (opcional)
        datos_eri: Datos del ERI (opcional)
        datos_ecp: Datos del ECP (opcional)
        ttl_hours: TTL en horas (default: 30 días)
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        cache_system = get_cache_system()
        
        # CAMBIO: Guardar individualmente SIN llamar a la función de retención
        resultado = {'success': True, 'metodo': 'individual_sin_retencion'}
        
        # Guardar ESF si se proporciona
        if datos_esf:
            exito_esf = cache_system.set_estado_financiero(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tipo_estado='esf',
                datos=datos_esf,
                ttl=ttl_hours * 3600  # Convertir horas a segundos
            )
            resultado['esf_guardado'] = exito_esf
            logger.info(f"✅ ESF guardado individualmente para período {cierre.periodo}")
            
        # Guardar ERI si se proporciona
        if datos_eri:
            exito_eri = cache_system.set_estado_financiero(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tipo_estado='eri',
                datos=datos_eri,
                ttl=ttl_hours * 3600  # Convertir horas a segundos
            )
            resultado['eri_guardado'] = exito_eri
            logger.info(f"✅ ERI guardado individualmente para período {cierre.periodo}")
        
         # Guardar ECP si se proporciona
        if datos_ecp:
            exito_ecp = cache_system.set_estado_financiero(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tipo_estado='ecp',
                datos=datos_ecp,
                ttl=ttl_hours * 3600  # Convertir horas a segundos
            )
            resultado['ecp_guardado'] = exito_ecp
            logger.info(f"✅ ECP guardado individualmente para período {cierre.periodo}")


        # CAMBIO CLAVE: Solo aplicar retención cuando tenemos MÁS de 2 períodos COMPLETOS ÚNICOS
        # y SOLO cuando se están guardando AMBOS reportes (período completo nuevo)
        if datos_esf and datos_eri and datos_ecp:
            try:
                # Obtener períodos que tienen TANTO ESF como ERI
                periodos_completos = _obtener_periodos_completos(cache_system, cierre.cliente.id)
                
                # IMPORTANTE: Asegurar que el período actual está en la lista
                # Esto maneja el caso donde estamos actualizando un período existente
                periodo_actual = cierre.periodo
                if periodo_actual not in periodos_completos:
                    periodos_completos.append(periodo_actual)
                
                # Obtener lista única de períodos
                periodos_unicos = sorted(list(set(periodos_completos)))
                
                logger.info(f"📊 Períodos únicos encontrados: {periodos_unicos}")
                logger.info(f"📊 Total de períodos únicos: {len(periodos_unicos)} (límite: 2)")
                
                # Solo aplicar retención si tenemos MÁS de 2 períodos únicos
                if len(periodos_unicos) > 2:
                    logger.info(f"🔄 Aplicando retención: {len(periodos_unicos)} períodos encontrados (límite: 2)")
                    
                    # Mantener solo los 2 más recientes
                    periodos_a_eliminar = periodos_unicos[:-2]
                    periodos_a_mantener = periodos_unicos[-2:]
                    
                    for periodo_viejo in periodos_a_eliminar:
                        # Eliminar TODOS los datos de ese período
                        eliminados = cache_system.invalidate_cliente_periodo(cierre.cliente.id, periodo_viejo)
                        if eliminados > 0:
                            logger.info(f"🗑️ Período completo eliminado por retención: {periodo_viejo} ({eliminados} claves)")
                    
                    resultado['retencion_aplicada'] = True
                    resultado['periodos_eliminados'] = periodos_a_eliminar
                    resultado['periodos_mantenidos'] = periodos_a_mantener
                else:
                    logger.info(f"✅ No se aplica retención: {len(periodos_unicos)} períodos únicos (límite: 2)")
                    resultado['retencion_aplicada'] = False
                    resultado['periodos_actuales'] = periodos_unicos
                    
            except Exception as e:
                logger.warning(f"Error aplicando retención manual: {e}")
                resultado['retencion_error'] = str(e)
        
        return resultado
            
    except Exception as e:
        logger.error(f"Error guardando reportes en caché: {e}")
        return {'success': False, 'error': str(e)}


def _obtener_periodos_completos(cache_system, cliente_id):
    """
    Obtiene solo los períodos que tienen TANTO ESF como ERI completos
    
    Args:
        cache_system: Sistema de caché
        cliente_id: ID del cliente
        
    Returns:
        list: Lista de períodos únicos que tienen ambos reportes
    """
    try:
        # Obtener todas las claves del cliente
        pattern_esf = f"sgm:contabilidad:{cliente_id}:*:esf"
        pattern_eri = f"sgm:contabilidad:{cliente_id}:*:eri"
        pattern_ecp = f"sgm:contabilidad:{cliente_id}:*:ecp"

        claves_esf = cache_system.redis_client.keys(pattern_esf)
        claves_eri = cache_system.redis_client.keys(pattern_eri)
        claves_ecp = cache_system.redis_client.keys(pattern_ecp)

        # Extraer períodos de las claves
        periodos_esf = set()
        for clave in claves_esf:
            partes = clave.split(':')
            if len(partes) >= 4:
                periodo = partes[3]  # sgm:contabilidad:{cliente_id}:{periodo}:esf
                periodos_esf.add(periodo)
        
        periodos_eri = set()
        for clave in claves_eri:
            partes = clave.split(':')
            if len(partes) >= 4:
                periodo = partes[3]  # sgm:contabilidad:{cliente_id}:{periodo}:eri
                periodos_eri.add(periodo)

        periodos_ecp = set()
        for clave in claves_ecp:
            partes = clave.split(':')
            if len(partes) >= 4:
                periodo = partes[3]  # sgm:contabilidad:{cliente_id}:{periodo}:ecp
                periodos_ecp.add(periodo)
        
        # Solo devolver períodos que tienen los 3 reportes
        periodos_completos = periodos_esf.intersection(periodos_eri).intersection(periodos_ecp)

        # Convertir a lista y ordenar
        periodos_lista = sorted(list(periodos_completos))
        
        logger.debug(f"Períodos con ESF: {sorted(list(periodos_esf))}")
        logger.debug(f"Períodos con ERI: {sorted(list(periodos_eri))}")
        logger.debug(f"Períodos con ECP: {sorted(list(periodos_ecp))}")
        logger.debug(f"Períodos completos (ESF + ERI + ECP): {periodos_lista}")

        return periodos_lista
        
    except Exception as e:
        logger.error(f"Error obteniendo períodos completos: {e}")
        return []


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
                # IMPORTANTE: Actualizar el usuario generador cuando se regenera
                if usuario_id:
                    reporte.usuario_generador_id = usuario_id
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
        
        # Agrupar y estructurar los datos (la función ahora maneja internamente las clasificaciones completas)
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
        
        # Guardar en Redis con retención automática de cierres
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando en cache Redis con retención', 'progress': 95}
        )
        
        try:
            # Usar función de retención automática (30 días TTL por defecto)
            resultado_cache = _guardar_reportes_con_retencion(
                cierre=cierre,
                datos_esf=datos_esf,
                ttl_hours=24*30  # 30 días
            )
            
            if resultado_cache.get('success'):
                logger.info(f"✅ ESF guardado en Redis con retención automática")
                if resultado_cache.get('cierres_eliminados'):
                    logger.info(f"🗑️ Cierres antiguos eliminados automáticamente: {len(resultado_cache['cierres_eliminados'])}")
            else:
                logger.warning(f"⚠️ Problema guardando ESF con retención: {resultado_cache.get('error', 'Error desconocido')}")
                
            # Mantener guardado de pruebas para compatibilidad
            """ try:
                import redis as redis_lib
                redis_client = redis_lib.Redis(
                    host='redis', port=6379, db=1,
                    password='Redis_Password_2025!',
                    decode_responses=True, socket_connect_timeout=10
                )
                
                clave_pruebas = f"sgm:contabilidad:{cierre.cliente.id}:{cierre.periodo}:pruebas:esf:finalizacion_automatica"
                json_data = json.dumps(datos_esf, ensure_ascii=False, indent=2)
                redis_client.set(clave_pruebas, json_data, ex=14400)  # 4 horas TTL
                
                logger.info(f"📋 ESF también guardado en clave de pruebas: {clave_pruebas}")
                
            except Exception as pruebas_error:
                logger.warning(f"No se pudo guardar ESF en clave de pruebas: {pruebas_error}") """
                
        except Exception as cache_error:
            logger.error(f"Error guardando ESF en Redis: {cache_error}")
            # No fallar la tarea por problemas de cache
        
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


@shared_task(bind=True)
def generar_estado_resultados_integral(self, cierre_id, usuario_id=None, regenerar=False):
    """
    Genera el Estado de Resultados Integral para un cierre específico
    
    Args:
        cierre_id: ID del cierre contable
        usuario_id: ID del usuario que solicita el reporte
        regenerar: Si True, regenera aunque ya exista
    """
    try:
        logger.info(f"Iniciando generación Estado de Resultados Integral para cierre {cierre_id}")
        
        # Obtener el cierre
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
        except CierreContabilidad.DoesNotExist:
            raise Exception(f"Cierre {cierre_id} no encontrado")
        
        # Verificar si ya existe y si no hay que regenerar
        reporte_existente = ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='eri'
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
                tipo_reporte='eri',
                defaults={
                    'usuario_generador_id': usuario_id,
                    'estado': 'generando'
                }
            )
            
            if not created:
                reporte.estado = 'generando'
                reporte.error_mensaje = ''
                reporte.fecha_actualizacion = timezone.now()
                # IMPORTANTE: Actualizar el usuario generador cuando se regenera
                if usuario_id:
                    reporte.usuario_generador_id = usuario_id
                reporte.save()
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Obteniendo clasificaciones ERI', 'progress': 10}
        )
        
        # Obtener el set de clasificación ERI de forma robusta
        set_eri = _obtener_set_eri_del_cierre(cierre)
        
        if not set_eri:
            raise Exception("No se encontró set de clasificación Estado de Resultados Integral para este cliente")
        
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
        
        # Obtener clasificaciones del set ERI
        clasificaciones = _obtener_clasificaciones_eri(set_eri, cuentas_data.keys())
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Agrupando y calculando totales', 'progress': 75}
        )
        
        # Agrupar y estructurar los datos
        datos_eri = _estructurar_datos_eri(cuentas_data, clasificaciones, cierre)
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando reporte', 'progress': 90}
        )
        
        # Guardar el reporte
        metadata = {
            'tiempo_generacion': (timezone.now() - reporte.fecha_actualizacion).total_seconds(),
            'total_cuentas': len(cuentas_data),
            'version': '1.0',
            'set_clasificacion_usado': set_eri.nombre
        }
        
        reporte.marcar_como_completado(datos_eri)
        reporte.metadata = metadata
        reporte.save()
        
        # Guardar en Redis con retención automática de cierres
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando en cache Redis con retención', 'progress': 95}
        )
        
        try:
            # Usar función de retención automática (30 días TTL por defecto)
            resultado_cache = _guardar_reportes_con_retencion(
                cierre=cierre,
                datos_eri=datos_eri,
                ttl_hours=24*30  # 30 días
            )
            
            if resultado_cache.get('success'):
                logger.info(f"✅ ERI guardado en Redis con retención automática")
                if resultado_cache.get('cierres_eliminados'):
                    logger.info(f"🗑️ Cierres antiguos eliminados automáticamente: {len(resultado_cache['cierres_eliminados'])}")
            else:
                logger.warning(f"⚠️ Problema guardando ERI con retención: {resultado_cache.get('error', 'Error desconocido')}")
                
            # Mantener guardado de pruebas para compatibilidad
            
                
        except Exception as cache_error:
            logger.error(f"Error guardando ERI en Redis: {cache_error}")
            # No fallar la tarea por problemas de cache
        
        logger.info(f"Estado de Resultados Integral generado exitosamente para cierre {cierre_id}")
        
        return {
            'success': True,
            'mensaje': 'Estado de Resultados Integral generado exitosamente',
            'reporte_id': reporte.id,
            'metadata': metadata
        }
        
    except Exception as e:
        error_msg = f"Error generando Estado de Resultados Integral: {str(e)}"
        logger.error(error_msg)
        
        # Marcar reporte como error si existe
        try:
            reporte = ReporteFinanciero.objects.get(
                cierre_id=cierre_id,
                tipo_reporte='eri'
            )
            reporte.marcar_como_error(error_msg)
        except:
            pass
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        
        raise Exception(error_msg)

def _obtener_clasificaciones_completas_ecp(cuenta_ids, cliente, set_ecp, sets_cliente):
    """
    Obtiene todas las clasificaciones de las cuentas para ECP y sets del cliente
    
    Returns:
        dict: {
            cuenta_id: {
                'ecp': {'opcion_valor': '...', 'opcion_id': ...},
                'cliente_sets': {
                    'set_nombre': {'opcion_valor': '...', 'opcion_id': ...}
                }
            }
        }
    """
    clasificaciones_completas = {}
    
    # Inicializar estructura para todas las cuentas
    for cuenta_id in cuenta_ids:
        clasificaciones_completas[cuenta_id] = {
            'ecp': None,
            'cliente_sets': {}
        }
    
    try:
        # Obtener todas las clasificaciones ECP
        if set_ecp:
            clasificaciones_ecp = AccountClassification.objects.filter(
                cuenta_id__in=cuenta_ids,
                set_clas=set_ecp
            ).select_related('opcion', 'cuenta')
            
            for clasificacion in clasificaciones_ecp:
                cuenta_id = clasificacion.cuenta_id
                if cuenta_id in clasificaciones_completas:
                    clasificaciones_completas[cuenta_id]['ecp'] = {
                        'opcion_valor': clasificacion.opcion.valor,
                        'opcion_id': clasificacion.opcion.id
                    }
        
        # Obtener clasificaciones de sets del cliente
        if sets_cliente:
            for set_cliente in sets_cliente:
                clasificaciones_cliente = AccountClassification.objects.filter(
                    cuenta_id__in=cuenta_ids,
                    set_clas=set_cliente
                ).select_related('opcion', 'cuenta')
                
                for clasificacion in clasificaciones_cliente:
                    cuenta_id = clasificacion.cuenta_id
                    if cuenta_id in clasificaciones_completas:
                        clasificaciones_completas[cuenta_id]['cliente_sets'][set_cliente.nombre] = {
                            'opcion_valor': clasificacion.opcion.valor,
                            'opcion_id': clasificacion.opcion.id
                        }
        
        return clasificaciones_completas
        
    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones completas ECP: {str(e)}")
        return clasificaciones_completas

def _obtener_sets_cliente_para_agrupacion_ecp(cliente, set_ecp_excluir):
    """
    Obtiene todos los sets de clasificación del cliente, excluyendo ESF, ERI y ECP
    para usar en la agrupación detallada de cuentas
    """
    try:
        # Excluir sets predefinidos (ESF, ERI y ECP)
        nombres_excluir = [
            'Estado de Situación Financiera',
            'Estado Situacion Financiera', 
            'Estado de Resultados Integral',
            'Estado de Resultados',
            'Estado de Cambio Patrimonial',
            'Estado de Cambios en el Patrimonio',
            'ESF',
            'ERI',
            'ECP'
        ]
        
        sets_cliente = ClasificacionSet.objects.filter(
            cliente=cliente
        ).exclude(
            nombre__in=nombres_excluir
        )
        
        # También excluir el set ECP específico si se encontró
        if set_ecp_excluir:
            sets_cliente = sets_cliente.exclude(id=set_ecp_excluir.id)
        
        return list(sets_cliente)
        
    except Exception as e:
        logger.warning(f"Error obteniendo sets del cliente: {e}")
        return []
    

def _determinar_categoria_ecp_con_molde(opcion_valor, set_ecp, es_bilingue=False):
    """
    Determina la categoría usando el molde del set predefinido ECP
    
    Args:
        opcion_valor: Valor de la opción de clasificación
        set_ecp: ClasificacionSet del ECP
        es_bilingue: Si el cliente maneja nombres bilingües
        
    Returns:
        tuple: (categoria, nombres_bilingues)
    """
    nombres_bilingues = {}
    
    # Si tenemos el set ECP, buscar la opción exacta para obtener nombres bilingües
    if set_ecp:
        try:
            opcion = ClasificacionOption.objects.filter(
                set_clas=set_ecp,
                valor=opcion_valor
            ).first()
            
            if opcion:
                nombres_bilingues = {
                    'valor_es': opcion.valor,
                    'valor_en': opcion.valor_en if es_bilingue and opcion.valor_en else opcion.valor,
                    'descripcion_es': opcion.descripcion,
                    'descripcion_en': opcion.descripcion_en if es_bilingue and opcion.descripcion_en else opcion.descripcion
                }
        except Exception:
            pass
    
    # Mapeo directo basado en el set predefinido de "Estado de Cambio Patrimonial"
    mapeo_predefinido = {
        'Capital': ('capital', {
            'nombre_es': 'Capital',
            'nombre_en': 'Capital'
        }),
        'Otras reservas': ('otras_reservas', {
            'nombre_es': 'Otras Reservas',
            'nombre_en': 'Other Reserves'
        }),
        'Otras Reservas': ('otras_reservas', {  # Variante con mayúscula
            'nombre_es': 'Otras Reservas',
            'nombre_en': 'Other Reserves'
        }),
        'Resultados acumulados': ('resultados_acumulados', {
            'nombre_es': 'Resultados Acumulados',
            'nombre_en': 'Accumulated Results'
        }),
    }
    
    # Buscar mapeo exacto
    if opcion_valor in mapeo_predefinido:
        categoria, nombres_categoria = mapeo_predefinido[opcion_valor]
        nombres_bilingues.update(nombres_categoria)
        return categoria, nombres_bilingues
    
    # Fallback: verificar contenido para determinar categoría
    opcion_lower = opcion_valor.lower()
    
    if 'capital' in opcion_lower:
        nombres_bilingues.update({'nombre_es': 'Capital', 'nombre_en': 'Capital'})
        return 'capital', nombres_bilingues
    elif 'reserva' in opcion_lower or 'reserve' in opcion_lower:
        nombres_bilingues.update({'nombre_es': 'Otras Reservas', 'nombre_en': 'Other Reserves'})
        return 'otras_reservas', nombres_bilingues

    elif 'resultado' in opcion_lower or 'result' in opcion_lower:
        nombres_bilingues.update({'nombre_es': 'Resultados Acumulados', 'nombre_en': 'Accumulated Results'})
        return 'resultados_acumulados', nombres_bilingues

    # Si no se puede determinar, no retornar categoría
    return None, nombres_bilingues

def _estructurar_datos_ecp(cuentas_data, clasificaciones, cierre):
    """
    Estructura los datos en el formato del Estado de Cambios en el Patrimonio
    usando el set predefinido como molde y los sets del cliente para agrupación detallada
    """
    # Obtener el set ECP para usar sus opciones como molde
    set_ecp = _obtener_set_ecp_del_cierre(cierre)
    
    # Obtener todos los sets de clasificación del cliente (excluyendo ESF, ERI y ECP)
    sets_cliente = _obtener_sets_cliente_para_agrupacion_ecp(cierre.cliente, set_ecp)
    
    # Obtener todas las clasificaciones de las cuentas para todos los sets
    clasificaciones_completas = _obtener_clasificaciones_completas_ecp(cuentas_data.keys(), cierre.cliente, set_ecp, sets_cliente)
    
    # Estructura base del ECP con inicialización completa usando el molde predefinido
    ecp_data = {
        'metadata': {
            'cliente_id': cierre.cliente.id,
            'cliente_nombre': cierre.cliente.nombre,
            'cierre_id': cierre.id,
            'periodo': cierre.periodo,
            'fecha_generacion': timezone.now().isoformat(),
            'moneda': 'CLP',
            'es_bilingue': cierre.cliente.bilingue,
            'set_clasificacion_usado': set_ecp.nombre if set_ecp else 'No encontrado',
            'sets_agrupacion_cliente': [s.nombre for s in sets_cliente] if sets_cliente else []
        },
        'capital': {
            'nombre_es': 'Capital',
            'nombre_en': 'Capital',
            'grupos': {},
            'total': 0,
            'saldo_inicial': 0,
            'cambios': 0,
            'saldo_final': 0
        },
        'otras_reservas': {
            'nombre_es': 'Otras Reservas',
            'nombre_en': 'Other Reserves',
            'grupos': {},
            'total': 0,
            'saldo_inicial': 0,
            'cambios': 0,
            'saldo_final': 0
        },
        'resultados_acumulados': {
            'nombre_es': 'Resultados Acumulados',
            'nombre_en': 'Accumulated Results',
            'grupos': {},
            'total': 0,
            'saldo_inicial': 0,
            'cambios': 0,
            'saldo_final': 0
        },
        'totales': {
            'total_patrimonio_inicial': 0,
            'total_cambios': 0,
            'total_patrimonio_final': 0
        }
    }
    
    # Agrupar cuentas por clasificación usando ECP como estructura principal y sets del cliente para agrupación detallada
    for cuenta_id, datos_cuenta in cuentas_data.items():
        clasificacion_cuenta = clasificaciones_completas.get(cuenta_id)
        
        if not clasificacion_cuenta or not clasificacion_cuenta['ecp']:
            continue  # Saltar cuentas sin clasificación ECP
        
        # Obtener clasificación ECP principal
        clasificacion_ecp = clasificacion_cuenta['ecp']
        opcion_valor_ecp = clasificacion_ecp['opcion_valor']
        
        # Determinar la categoría usando el valor exacto del set
        categoria, nombres_bilingues = _determinar_categoria_ecp_con_molde(opcion_valor_ecp, set_ecp, cierre.cliente.bilingue)
        
        if categoria:
            # Asegurar que la estructura existe
            if categoria not in ecp_data:
                continue  # Saltar si no es una categoría válida
            
            # Determinar el nombre del grupo usando sets del cliente
            grupo_nombre = _determinar_nombre_grupo_detallado(clasificacion_cuenta, sets_cliente, opcion_valor_ecp)
            grupo_nombre_es = grupo_nombre['nombre_es']
            grupo_nombre_en = grupo_nombre['nombre_en']
            
            # Crear la clave del grupo usando el nombre detallado
            if grupo_nombre_es not in ecp_data[categoria]['grupos']:
                ecp_data[categoria]['grupos'][grupo_nombre_es] = {
                    'nombre_es': grupo_nombre_es,
                    'nombre_en': grupo_nombre_en,
                    'clasificacion_origen': grupo_nombre['origen'],  # Para auditabilidad
                    'saldo_inicial': 0,
                    'cambios': 0,
                    'saldo_final': 0,
                    'cuentas': []
                }
            
            # Calcular cambios (movimientos del período)
            cambios = datos_cuenta['total_debe'] - datos_cuenta['total_haber']
            
            # Agregar la cuenta al grupo
            ecp_data[categoria]['grupos'][grupo_nombre_es]['cuentas'].append({
                'codigo': datos_cuenta['codigo'],
                'nombre_es': datos_cuenta['nombre_es'],
                'nombre_en': datos_cuenta['nombre_en'],
                'saldo_anterior': datos_cuenta['saldo_anterior'],
                'total_debe': datos_cuenta['total_debe'],
                'total_haber': datos_cuenta['total_haber'],
                'cambios': cambios,
                'saldo_final': datos_cuenta['saldo_final'],
                'movimientos': datos_cuenta['movimientos'],
                'clasificaciones_cliente': {
                    set_nombre: cls_data['opcion_valor'] 
                    for set_nombre, cls_data in clasificacion_cuenta['cliente_sets'].items()
                }  # Para referencia
            })
            
            # Actualizar totales del grupo
            ecp_data[categoria]['grupos'][grupo_nombre_es]['saldo_inicial'] += datos_cuenta['saldo_anterior']
            ecp_data[categoria]['grupos'][grupo_nombre_es]['cambios'] += cambios
            ecp_data[categoria]['grupos'][grupo_nombre_es]['saldo_final'] += datos_cuenta['saldo_final']
            
            # Actualizar totales de la categoría
            ecp_data[categoria]['saldo_inicial'] += datos_cuenta['saldo_anterior']
            ecp_data[categoria]['cambios'] += cambios
            ecp_data[categoria]['saldo_final'] += datos_cuenta['saldo_final']
            ecp_data[categoria]['total'] = ecp_data[categoria]['saldo_final']
    
    # Calcular totales finales
    ecp_data['totales']['total_patrimonio_inicial'] = (
        ecp_data['capital']['saldo_inicial'] + 
        ecp_data['otras_reservas']['saldo_inicial']
    )
    ecp_data['totales']['total_cambios'] = (
        ecp_data['capital']['cambios'] + 
        ecp_data['otras_reservas']['cambios']
    )
    ecp_data['totales']['total_patrimonio_final'] = (
        ecp_data['capital']['saldo_final'] + 
        ecp_data['otras_reservas']['saldo_final']
    )
    
    return ecp_data
    

def _obtener_set_ecp_del_cierre(cierre):
    """
    Obtiene el set de clasificación Estado de Cambio Patrimonial para el cierre
    """
    # Estrategia 1: Buscar exactamente "Estado de Cambio Patrimonial"
    try:
        set_ecp = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__iexact="Estado de Cambio Patrimonial"
        ).first()
        if set_ecp:
            return set_ecp
    except Exception:
        pass
    
    # Estrategia 2: Buscar que contenga "cambio" y "patrimonial"
    try:
        set_ecp = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="cambio"
        ).filter(
            nombre__icontains="patrimonial"
        ).first()
        if set_ecp:
            return set_ecp
    except Exception:
        pass
    
    # Estrategia 3: Buscar que contenga "ECP"
    try:
        set_ecp = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="ecp"
        ).first()
        if set_ecp:
            return set_ecp
    except Exception:
        pass
    
    # Estrategia 4: Buscar variaciones comunes
    try:
        nombres_posibles = [
            "Estado de Cambios en el Patrimonio",
            "Estado Cambios Patrimonio",
            "Cambios en el Patrimonio"
        ]
        set_ecp = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__in=nombres_posibles
        ).first()
        if set_ecp:
            return set_ecp
    except Exception:
        pass
    
    return None

def _obtener_clasificaciones_ecp(set_ecp, cuenta_ids):
    """
    Obtiene las clasificaciones ECP para las cuentas especificadas
    """
    clasificaciones = AccountClassification.objects.filter(
        set_clas=set_ecp,
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
    
@shared_task(bind=True)
def generar_estado_cambios_patrimonio(self, cierre_id, usuario_id=None, regenerar=False):
    """
    Genera el Estado de Cambios en el Patrimonio para un cierre específico
    
    Args:
        cierre_id: ID del cierre contable
        usuario_id: ID del usuario que solicita el reporte
        regenerar: Si True, regenera aunque ya exista
    """
    try:
        logger.info(f"Iniciando generación Estado de Cambios en el Patrimonio para cierre {cierre_id}")
        
        # Obtener el cierre
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
        except CierreContabilidad.DoesNotExist:
            raise Exception(f"Cierre {cierre_id} no encontrado")
        
        # Verificar si ya existe y si no hay que regenerar
        reporte_existente = ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='ecp'
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
                tipo_reporte='ecp',
                defaults={
                    'usuario_generador_id': usuario_id,
                    'estado': 'generando'
                }
            )
            
            if not created:
                reporte.estado = 'generando'
                reporte.error_mensaje = ''
                reporte.fecha_actualizacion = timezone.now()
                # IMPORTANTE: Actualizar el usuario generador cuando se regenera
                if usuario_id:
                    reporte.usuario_generador_id = usuario_id
                reporte.save()
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Obteniendo clasificaciones ECP', 'progress': 10}
        )
        
        # Obtener el set de clasificación ECP de forma robusta
        set_ecp = _obtener_set_ecp_del_cierre(cierre)
        
        if not set_ecp:
            raise Exception("No se encontró set de clasificación Estado de Cambio Patrimonial para este cliente")
        
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
        
        # Obtener clasificaciones del set ECP
        clasificaciones = _obtener_clasificaciones_ecp(set_ecp, cuentas_data.keys())
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Agrupando y calculando totales', 'progress': 75}
        )
        
        # Agrupar y estructurar los datos
        datos_ecp = _estructurar_datos_ecp(cuentas_data, clasificaciones, cierre)
        
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando reporte', 'progress': 90}
        )
        
        # Guardar el reporte
        metadata = {
            'tiempo_generacion': (timezone.now() - reporte.fecha_actualizacion).total_seconds(),
            'total_cuentas': len(cuentas_data),
            'version': '1.0',
            'set_clasificacion_usado': set_ecp.nombre
        }
        
        reporte.marcar_como_completado(datos_ecp)
        reporte.metadata = metadata
        reporte.save()
        
        # Guardar en Redis con retención automática de cierres
        self.update_state(
            state='PROGRESS',
            meta={'step': 'Guardando en cache Redis con retención', 'progress': 95}
        )
        
        try:
            # Usar función de retención automática (30 días TTL por defecto)
            resultado_cache = _guardar_reportes_con_retencion(
                cierre=cierre,
                datos_ecp=datos_ecp,
                ttl_hours=24*30  # 30 días
            )
            
            if resultado_cache.get('success'):
                logger.info(f"✅ ECP guardado en Redis con retención automática")
                if resultado_cache.get('cierres_eliminados'):
                    logger.info(f"🗑️ Cierres antiguos eliminados automáticamente: {len(resultado_cache['cierres_eliminados'])}")
            else:
                logger.warning(f"⚠️ Problema guardando ECP con retención: {resultado_cache.get('error', 'Error desconocido')}")
                
        except Exception as cache_error:
            logger.error(f"Error guardando ECP en Redis: {cache_error}")
            # No fallar la tarea por problemas de cache
        
        logger.info(f"Estado de Cambios en el Patrimonio generado exitosamente para cierre {cierre_id}")
        
        return {
            'success': True,
            'mensaje': 'Estado de Cambios en el Patrimonio generado exitosamente',
            'reporte_id': reporte.id,
            'metadata': metadata
        }
        
    except Exception as e:
        error_msg = f"Error generando Estado de Cambios en el Patrimonio: {str(e)}"
        logger.error(error_msg)
        
        # Marcar reporte como error si existe
        try:
            reporte = ReporteFinanciero.objects.get(
                cierre_id=cierre_id,
                tipo_reporte='ecp'
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
    
    # Calcular totales y asignar movimientos para cuentas con movimientos
    for mov in movimientos:
        cuenta_id = mov['cuenta_id']
        if cuenta_id in cuentas_data:
            cuentas_data[cuenta_id]['total_debe'] = float(mov['total_debe'] or 0)
            cuentas_data[cuenta_id]['total_haber'] = float(mov['total_haber'] or 0)
            cuentas_data[cuenta_id]['movimientos'] = movimientos_por_cuenta.get(cuenta_id, [])
    
    # ✅ CORREGIDO: Calcular saldo final para TODAS las cuentas (con y sin movimientos)
    for cuenta_id, datos_cuenta in cuentas_data.items():
        saldo_anterior = datos_cuenta['saldo_anterior']
        total_debe = datos_cuenta['total_debe']
        total_haber = datos_cuenta['total_haber']
        datos_cuenta['saldo_final'] = saldo_anterior + total_debe - total_haber
        
        # Asegurar que las cuentas sin movimientos tengan lista vacía
        if 'movimientos' not in datos_cuenta:
            datos_cuenta['movimientos'] = []
    
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
    usando el set predefinido ESF como molde y los sets del cliente para agrupación detallada
    """
    # Obtener el set ESF para usar sus opciones como molde
    set_esf = _obtener_set_esf_del_cierre(cierre)
    
    # Obtener todos los sets de clasificación del cliente (excluyendo ESF y ERI)
    sets_cliente = _obtener_sets_cliente_para_agrupacion(cierre.cliente, set_esf)
    
    # Obtener todas las clasificaciones de las cuentas para todos los sets
    clasificaciones_completas = _obtener_clasificaciones_completas(cuentas_data.keys(), cierre.cliente, set_esf, sets_cliente)
    
    # Estructura base del ESF con inicialización completa usando el molde predefinido
    esf_data = {
        'metadata': {
            'cliente_id': cierre.cliente.id,
            'cliente_nombre': cierre.cliente.nombre,
            'cierre_id': cierre.id,
            'periodo': cierre.periodo,
            'fecha_generacion': timezone.now().isoformat(),
            'moneda': 'CLP',  # Asumir pesos chilenos por defecto
            'es_bilingue': cierre.cliente.bilingue,
            'set_clasificacion_esf': set_esf.nombre if set_esf else 'No encontrado',
            'sets_agrupacion_cliente': [s.nombre for s in sets_cliente] if sets_cliente else []
        },
        'activos': {
            'corrientes': {
                'nombre_es': 'Activos Corrientes',
                'nombre_en': 'Current Assets',
                'grupos': {},
                'total': 0
            },
            'no_corrientes': {
                'nombre_es': 'Activos No Corrientes', 
                'nombre_en': 'Non-Current Assets',
                'grupos': {},
                'total': 0
            },
            'total_activos': 0
        },
        'pasivos': {
            'corrientes': {
                'nombre_es': 'Pasivos Corrientes',
                'nombre_en': 'Current Liabilities',
                'grupos': {},
                'total': 0
            },
            'no_corrientes': {
                'nombre_es': 'Pasivos No Corrientes',
                'nombre_en': 'Non-Current Liabilities', 
                'grupos': {},
                'total': 0
            },
            'total_pasivos': 0
        },
        'patrimonio': {
            'capital': {
                'nombre_es': 'Patrimonio',
                'nombre_en': 'Patrimony',
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
    
    # Agrupar cuentas por clasificación usando ESF como estructura principal y sets del cliente para agrupación detallada
    for cuenta_id, datos_cuenta in cuentas_data.items():
        clasificacion_cuenta = clasificaciones_completas.get(cuenta_id)
        
        if not clasificacion_cuenta or not clasificacion_cuenta['esf']:
            continue  # Saltar cuentas sin clasificación ESF
        
        # Obtener clasificación ESF principal
        clasificacion_esf = clasificacion_cuenta['esf']
        opcion_valor_esf = clasificacion_esf['opcion_valor']
        
        # Determinar la categoría principal y subcategoría usando ESF
        categoria_principal, subcategoria, nombres_bilingues = _determinar_categoria_esf_con_molde(
            opcion_valor_esf, set_esf, cierre.cliente.bilingue
        )
        
        if categoria_principal and subcategoria:
            # Asegurar que la estructura principal existe
            if categoria_principal not in esf_data:
                esf_data[categoria_principal] = {}
            
            if subcategoria not in esf_data[categoria_principal]:
                esf_data[categoria_principal][subcategoria] = {
                    'nombre_es': nombres_bilingues.get('nombre_es', subcategoria),
                    'nombre_en': nombres_bilingues.get('nombre_en', subcategoria),
                    'grupos': {},
                    'total': 0
                }
            
            # Asegurar que 'grupos' existe
            if 'grupos' not in esf_data[categoria_principal][subcategoria]:
                esf_data[categoria_principal][subcategoria]['grupos'] = {}
            
            # Determinar el nombre del grupo usando sets del cliente
            grupo_nombre = _determinar_nombre_grupo_detallado(clasificacion_cuenta, sets_cliente, opcion_valor_esf)
            grupo_nombre_es = grupo_nombre['nombre_es']
            grupo_nombre_en = grupo_nombre['nombre_en']
            
            # Crear la clave del grupo usando el nombre detallado
            if grupo_nombre_es not in esf_data[categoria_principal][subcategoria]['grupos']:
                esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre_es] = {
                    'nombre_es': grupo_nombre_es,
                    'nombre_en': grupo_nombre_en,
                    'clasificacion_origen': grupo_nombre['origen'],  # Para auditabilidad
                    'total': 0,
                    'cuentas': []
                }
            
            # Agregar la cuenta al grupo
            esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre_es]['cuentas'].append({
                'codigo': datos_cuenta['codigo'],
                'nombre_es': datos_cuenta['nombre_es'],
                'nombre_en': datos_cuenta['nombre_en'],
                'saldo_anterior': datos_cuenta['saldo_anterior'],
                'total_debe': datos_cuenta['total_debe'],
                'total_haber': datos_cuenta['total_haber'],
                'saldo_final': datos_cuenta['saldo_final'],
                'movimientos': datos_cuenta['movimientos'],
                'clasificaciones_cliente': {
                    set_nombre: cls_data['opcion_valor'] 
                    for set_nombre, cls_data in clasificacion_cuenta['cliente_sets'].items()
                }  # Para referencia
            })
            
            # Actualizar totales
            saldo_final = datos_cuenta['saldo_final']
            esf_data[categoria_principal][subcategoria]['grupos'][grupo_nombre_es]['total'] += saldo_final
            esf_data[categoria_principal][subcategoria]['total'] += saldo_final
            
            # Actualizar total de la categoría principal
            total_key = f'total_{categoria_principal}'
            if total_key not in esf_data[categoria_principal]:
                esf_data[categoria_principal][total_key] = 0
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


def _determinar_nombre_grupo_detallado(clasificacion_cuenta, sets_cliente, opcion_valor):
    """
    Determina el nombre del grupo detallado para organizar las cuentas en los reportes.
    
    Args:
        clasificacion_cuenta: Dict con estructura {
            'esf': {'opcion_valor': '...', 'opcion_id': ...},
            'cliente_sets': {
                'set_nombre': {'opcion_valor': '...', 'opcion_id': ...}
            }
        }
        sets_cliente: Lista de sets de clasificación del cliente  
        opcion_valor: Valor de la opción de clasificación ESF/ERI
        
    Returns:
        dict: {'nombre_es': str, 'nombre_en': str, 'origen': str}
    """
    try:
        # 1. PRIORIDAD: Usar las clasificaciones de sets del cliente para crear grupos detallados
        if clasificacion_cuenta and 'cliente_sets' in clasificacion_cuenta:
            cliente_sets = clasificacion_cuenta['cliente_sets']
            
            # Buscar el primer set del cliente que tenga una clasificación
            for set_nombre, clasificacion_data in cliente_sets.items():
                if clasificacion_data and 'opcion_valor' in clasificacion_data:
                    nombre_grupo = clasificacion_data['opcion_valor']
                    return {
                        'nombre_es': nombre_grupo,
                        'nombre_en': nombre_grupo,  # Usar el mismo para ambos idiomas
                        'origen': set_nombre
                    }
        
        # 2. Fallback: usar mapeo predefinido basado en opcion_valor ESF/ERI
        mapeo_nombres = {
            'Activo Corriente': {
                'nombre_es': 'Activos Corrientes',
                'nombre_en': 'Current Assets'
            },
            'Activo No Corriente': {
                'nombre_es': 'Activos No Corrientes',
                'nombre_en': 'Non-Current Assets'
            },
            'Pasivo Corriente': {
                'nombre_es': 'Pasivos Corrientes', 
                'nombre_en': 'Current Liabilities'
            },
            'Pasivo No Corriente': {
                'nombre_es': 'Pasivos No Corrientes',
                'nombre_en': 'Non-Current Liabilities'
            },
            'Patrimonio': {
                'nombre_es': 'Patrimonio',
                'nombre_en': 'Patrimony'
            },
            # Para ERI
            'Ganancias Brutas': {
                'nombre_es': 'Ganancias Brutas',
                'nombre_en': 'Gross Earnings'
            },
            'Ganancia (perdida)': {
                'nombre_es': 'Ganancia (Pérdida)',
                'nombre_en': 'Earnings (Loss)'
            },
            'Ganancia (perdida) antes de Impuestos': {
                'nombre_es': 'Ganancia (Pérdida) antes de Impuestos',
                'nombre_en': 'Earnings (Loss) Before Taxes'
            }
        }
        
        if opcion_valor in mapeo_nombres:
            nombres = mapeo_nombres[opcion_valor]
            return {
                'nombre_es': nombres['nombre_es'],
                'nombre_en': nombres['nombre_en'],
                'origen': 'mapeo_predefinido'
            }
        
        # 3. Fallback final: usar el opcion_valor tal como está
        return {
            'nombre_es': opcion_valor,
            'nombre_en': opcion_valor,
            'origen': 'valor_original'
        }
        
    except Exception as e:
        logger.warning(f"Error determinando nombre de grupo: {e}, usando fallback")
        # Fallback de emergencia
        return {
            'nombre_es': opcion_valor or 'Sin Clasificar',
            'nombre_en': opcion_valor or 'Unclassified',
            'origen': 'fallback_error'
        }


def _determinar_categoria_esf_con_molde(opcion_valor, set_esf, es_bilingue=False):
    """
    Determina la categoría principal y subcategoría usando el molde del set predefinido ESF
    
    Args:
        opcion_valor: Valor de la opción de clasificación
        set_esf: ClasificacionSet del ESF
        es_bilingue: Si el cliente maneja nombres bilingües
        
    Returns:
        tuple: (categoria_principal, subcategoria, nombres_bilingues)
    """
    nombres_bilingues = {}
    
    # Si tenemos el set ESF, buscar la opción exacta para obtener nombres bilingües
    if set_esf:
        try:
            opcion = ClasificacionOption.objects.filter(
                set_clas=set_esf,
                valor=opcion_valor
            ).first()
            
            if opcion:
                nombres_bilingues = {
                    'valor_es': opcion.valor,
                    'valor_en': opcion.valor_en if es_bilingue and opcion.valor_en else opcion.valor,
                    'descripcion_es': opcion.descripcion,
                    'descripcion_en': opcion.descripcion_en if es_bilingue and opcion.descripcion_en else opcion.descripcion
                }
        except Exception:
            pass
    
    # Mapeo directo basado en el set predefinido de "Estado Situacion Financiera"
    mapeo_predefinido = {
        'Activo Corriente': ('activos', 'corrientes', {
            'nombre_es': 'Activos Corrientes',
            'nombre_en': 'Current Assets'
        }),
        'Activo No Corriente': ('activos', 'no_corrientes', {
            'nombre_es': 'Activos No Corrientes', 
            'nombre_en': 'Non-Current Assets'
        }),
        'Pasivo Corriente': ('pasivos', 'corrientes', {
            'nombre_es': 'Pasivos Corrientes',
            'nombre_en': 'Current Liabilities'
        }),
        'Pasivo No Corriente': ('pasivos', 'no_corrientes', {
            'nombre_es': 'Pasivos No Corrientes',
            'nombre_en': 'Non-Current Liabilities'
        }),
        'Patrimonio': ('patrimonio', 'capital', {
            'nombre_es': 'Patrimonio',
            'nombre_en': 'Patrimony'
        })
    }
    
    # Buscar mapeo exacto
    if opcion_valor in mapeo_predefinido:
        categoria, subcategoria, nombres_seccion = mapeo_predefinido[opcion_valor]
        # Combinar nombres de sección con nombres de opción
        nombres_bilingues.update(nombres_seccion)
        return categoria, subcategoria, nombres_bilingues
    
    # Fallback: usar la lógica anterior pero mejorada
    opcion_lower = opcion_valor.lower()
    
    # Activos
    if any(term in opcion_lower for term in ['activo corriente', 'current asset', 'efectivo', 'inventario', 'deudor']):
        nombres_bilingues.update({'nombre_es': 'Activos Corrientes', 'nombre_en': 'Current Assets'})
        return 'activos', 'corrientes', nombres_bilingues
    elif any(term in opcion_lower for term in ['activo no corriente', 'non-current asset', 'propiedad', 'planta', 'equipo']):
        nombres_bilingues.update({'nombre_es': 'Activos No Corrientes', 'nombre_en': 'Non-Current Assets'})
        return 'activos', 'no_corrientes', nombres_bilingues
    elif 'activo' in opcion_lower:
        nombres_bilingues.update({'nombre_es': 'Activos Corrientes', 'nombre_en': 'Current Assets'})
        return 'activos', 'corrientes', nombres_bilingues  # Por defecto activos corrientes
    
    # Pasivos
    elif any(term in opcion_lower for term in ['pasivo corriente', 'current liabilit', 'cuenta por pagar', 'provision']):
        nombres_bilingues.update({'nombre_es': 'Pasivos Corrientes', 'nombre_en': 'Current Liabilities'})
        return 'pasivos', 'corrientes', nombres_bilingues
    elif any(term in opcion_lower for term in ['pasivo no corriente', 'non-current liabilit', 'deuda largo plazo']):
        nombres_bilingues.update({'nombre_es': 'Pasivos No Corrientes', 'nombre_en': 'Non-Current Liabilities'})
        return 'pasivos', 'no_corrientes', nombres_bilingues
    elif 'pasivo' in opcion_lower:
        nombres_bilingues.update({'nombre_es': 'Pasivos Corrientes', 'nombre_en': 'Current Liabilities'})
        return 'pasivos', 'corrientes', nombres_bilingues  # Por defecto pasivos corrientes
    
    # Patrimonio
    elif any(term in opcion_lower for term in ['patrimonio', 'capital', 'resultado', 'utilidad', 'equity']):
        nombres_bilingues.update({'nombre_es': 'Patrimonio', 'nombre_en': 'Patrimony'})
        return 'patrimonio', 'capital', nombres_bilingues
    
    # Si no se puede determinar, asumir activo corriente
    nombres_bilingues.update({'nombre_es': 'Activos Corrientes', 'nombre_en': 'Current Assets'})
    return 'activos', 'corrientes', nombres_bilingues


def _determinar_categoria_esf(opcion_valor):
    """
    DEPRECATED: Mantener por compatibilidad. Use _determinar_categoria_esf_con_molde en su lugar.
    """
    categoria, subcategoria, _ = _determinar_categoria_esf_con_molde(opcion_valor, None, False)
    return categoria, subcategoria


def _obtener_set_esf_del_cierre(cierre):
    """
    Obtiene el set de clasificación ESF para el cierre, usando múltiples estrategias de búsqueda
    """
    # Estrategia 1: Buscar exactamente "Estado de Situación Financiera" o "Estado Situacion Financiera"
    try:
        set_esf = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__in=["Estado de Situación Financiera", "Estado Situacion Financiera"]
        ).first()
        if set_esf:
            return set_esf
    except Exception:
        pass
    
    # Estrategia 2: Buscar que contenga "ESF"
    try:
        set_esf = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="esf"
        ).first()
        if set_esf:
            return set_esf
    except Exception:
        pass
    
    # Estrategia 3: Buscar que contenga "estado" y "situacion"
    try:
        set_esf = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="estado"
        ).filter(
            nombre__icontains="situacion"
        ).first()
        if set_esf:
            return set_esf
    except Exception:
        pass
    
    return None


def _obtener_set_eri_del_cierre(cierre):
    """
    Obtiene el set de clasificación Estado de Resultados Integral para el cierre
    """
    # Estrategia 1: Buscar exactamente "Estado de Resultados Integral"
    try:
        set_eri = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__iexact="Estado de Resultados Integral"
        ).first()
        if set_eri:
            return set_eri
    except Exception:
        pass
    
    # Estrategia 2: Buscar que contenga "resultados" y "integral"
    try:
        set_eri = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="resultado"
        ).filter(
            nombre__icontains="integral"
        ).first()
        if set_eri:
            return set_eri
    except Exception:
        pass
    
    # Estrategia 3: Buscar que contenga "ERI"
    try:
        set_eri = ClasificacionSet.objects.filter(
            cliente=cierre.cliente,
            nombre__icontains="eri"
        ).first()
        if set_eri:
            return set_eri
    except Exception:
        pass
    
    return None


def _obtener_clasificaciones_eri(set_eri, cuenta_ids):
    """
    Obtiene las clasificaciones ERI para las cuentas especificadas
    """
    clasificaciones = AccountClassification.objects.filter(
        set_clas=set_eri,
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


def _estructurar_datos_eri(cuentas_data, clasificaciones, cierre):
    """
    Estructura los datos en el formato del Estado de Resultados Integral
    usando el set predefinido como molde y los sets del cliente para agrupación detallada
    """
    # Obtener el set ERI para usar sus opciones como molde
    set_eri = _obtener_set_eri_del_cierre(cierre)
    
    # Obtener todos los sets de clasificación del cliente (excluyendo ESF y ERI)
    sets_cliente = _obtener_sets_cliente_para_agrupacion(cierre.cliente, set_eri)
    
    # Obtener todas las clasificaciones de las cuentas para todos los sets
    clasificaciones_completas = _obtener_clasificaciones_completas_eri(cuentas_data.keys(), cierre.cliente, set_eri, sets_cliente)
    
    # Estructura base del ERI con inicialización completa usando el molde predefinido
    eri_data = {
        'metadata': {
            'cliente_id': cierre.cliente.id,
            'cliente_nombre': cierre.cliente.nombre,
            'cierre_id': cierre.id,
            'periodo': cierre.periodo,
            'fecha_generacion': timezone.now().isoformat(),
            'moneda': 'CLP',
            'es_bilingue': cierre.cliente.bilingue,
            'set_clasificacion_usado': set_eri.nombre if set_eri else 'No encontrado',
            'sets_agrupacion_cliente': [s.nombre for s in sets_cliente] if sets_cliente else []
        },
        'ganancias_brutas': {
            'nombre_es': 'Ganancias Brutas',
            'nombre_en': 'Gross Earnings',
            'grupos': {},
            'total': 0
        },
        'ganancia_perdida': {
            'nombre_es': 'Ganancia (Pérdida)',
            'nombre_en': 'Earnings (Loss)',
            'grupos': {},
            'total': 0
        },
        'ganancia_perdida_antes_impuestos': {
            'nombre_es': 'Ganancia (Pérdida) antes de Impuestos',
            'nombre_en': 'Earnings (Loss) Before Taxes',
            'grupos': {},
            'total': 0
        },
        'totales': {
            'ingresos_totales': 0,
            'gastos_totales': 0,
            'resultado_final': 0
        }
    }
    
    # Agrupar cuentas por clasificación usando ERI como estructura principal y sets del cliente para agrupación detallada
    for cuenta_id, datos_cuenta in cuentas_data.items():
        clasificacion_cuenta = clasificaciones_completas.get(cuenta_id)
        
        if not clasificacion_cuenta or not clasificacion_cuenta['eri']:
            continue  # Saltar cuentas sin clasificación ERI
        
        # Obtener clasificación ERI principal
        clasificacion_eri = clasificacion_cuenta['eri']
        opcion_valor_eri = clasificacion_eri['opcion_valor']
        
        # Determinar la categoría usando el valor exacto del set
        categoria, nombres_bilingues = _determinar_categoria_eri_con_molde(opcion_valor_eri, set_eri, cierre.cliente.bilingue)
        
        if categoria:
            # Asegurar que la estructura existe
            if categoria not in eri_data:
                eri_data[categoria] = {
                    'nombre_es': nombres_bilingues.get('nombre_es', categoria),
                    'nombre_en': nombres_bilingues.get('nombre_en', categoria),
                    'grupos': {},
                    'total': 0
                }
            
            # Asegurar que 'grupos' existe
            if 'grupos' not in eri_data[categoria]:
                eri_data[categoria]['grupos'] = {}
            
            # Determinar el nombre del grupo usando sets del cliente
            grupo_nombre = _determinar_nombre_grupo_detallado(clasificacion_cuenta, sets_cliente, opcion_valor_eri)
            grupo_nombre_es = grupo_nombre['nombre_es']
            grupo_nombre_en = grupo_nombre['nombre_en']
            
            # Crear la clave del grupo usando el nombre detallado
            if grupo_nombre_es not in eri_data[categoria]['grupos']:
                eri_data[categoria]['grupos'][grupo_nombre_es] = {
                    'nombre_es': grupo_nombre_es,
                    'nombre_en': grupo_nombre_en,
                    'clasificacion_origen': grupo_nombre['origen'],  # Para auditabilidad
                    'total': 0,
                    'cuentas': []
                }
            
            # Agregar la cuenta al grupo
            eri_data[categoria]['grupos'][grupo_nombre_es]['cuentas'].append({
                'codigo': datos_cuenta['codigo'],
                'nombre_es': datos_cuenta['nombre_es'],
                'nombre_en': datos_cuenta['nombre_en'],
                'saldo_anterior': datos_cuenta['saldo_anterior'],
                'total_debe': datos_cuenta['total_debe'],
                'total_haber': datos_cuenta['total_haber'],
                'saldo_final': datos_cuenta['saldo_final'],
                'movimientos': datos_cuenta['movimientos'],
                'clasificaciones_cliente': {
                    set_nombre: cls_data['opcion_valor'] 
                    for set_nombre, cls_data in clasificacion_cuenta['cliente_sets'].items()
                }  # Para referencia
            })
            
            # Actualizar totales
            saldo_final = datos_cuenta['saldo_final']
            eri_data[categoria]['grupos'][grupo_nombre_es]['total'] += saldo_final
            eri_data[categoria]['total'] += saldo_final
    
    # Calcular totales finales
    eri_data['totales']['resultado_final'] = (
        eri_data['ganancias_brutas']['total'] + 
        eri_data['ganancia_perdida']['total'] + 
        eri_data['ganancia_perdida_antes_impuestos']['total']
    )
    
    return eri_data


def _determinar_categoria_eri_con_molde(opcion_valor, set_eri, es_bilingue=False):
    """
    Determina la categoría usando el molde del set predefinido ERI
    
    Args:
        opcion_valor: Valor de la opción de clasificación
        set_eri: ClasificacionSet del ERI
        es_bilingue: Si el cliente maneja nombres bilingües
        
    Returns:
        tuple: (categoria, nombres_bilingues)
    """
    nombres_bilingues = {}
    
    # Si tenemos el set ERI, buscar la opción exacta para obtener nombres bilingües
    if set_eri:
        try:
            opcion = ClasificacionOption.objects.filter(
                set_clas=set_eri,
                valor=opcion_valor
            ).first()
            
            if opcion:
                nombres_bilingues = {
                    'valor_es': opcion.valor,
                    'valor_en': opcion.valor_en if es_bilingue and opcion.valor_en else opcion.valor,
                    'descripcion_es': opcion.descripcion,
                    'descripcion_en': opcion.descripcion_en if es_bilingue and opcion.descripcion_en else opcion.descripcion
                }
        except Exception:
            pass
    
    # Mapeo directo basado en el set predefinido de "Estado de Resultados Integral"
    mapeo_predefinido = {
        'Ganancias Brutas': ('ganancias_brutas', {
            'nombre_es': 'Ganancias Brutas',
            'nombre_en': 'Gross Earnings'
        }),
        'Ganancia (perdida)': ('ganancia_perdida', {
            'nombre_es': 'Ganancia (Pérdida)',
            'nombre_en': 'Earnings (Loss)'
        }),
        'Ganancia (perdida) antes de Impuestos': ('ganancia_perdida_antes_impuestos', {
            'nombre_es': 'Ganancia (Pérdida) antes de Impuestos',
            'nombre_en': 'Earnings (Loss) Before Taxes'
        })
    }
    
    # Buscar mapeo exacto
    if opcion_valor in mapeo_predefinido:
        categoria, nombres_categoria = mapeo_predefinido[opcion_valor]
        nombres_bilingues.update(nombres_categoria)
        return categoria, nombres_bilingues
    
    # Fallback: usar la primera categoría por defecto
    nombres_bilingues.update({'nombre_es': 'Ganancias Brutas', 'nombre_en': 'Gross Earnings'})
    return 'ganancias_brutas', nombres_bilingues


def _obtener_sets_cliente_para_agrupacion(cliente, set_esf_excluir):
    """
    Obtiene todos los sets de clasificación del cliente, excluyendo ESF y ERI
    para usar en la agrupación detallada de cuentas
    """
    try:
        # Excluir sets predefinidos (ESF y ERI)
        nombres_excluir = [
            'Estado de Situación Financiera',
            'Estado Situacion Financiera', 
            'Estado de Resultados Integral',
            'Estado de Resultados',
            'ESF',
            'ERI'
        ]
        
        sets_cliente = ClasificacionSet.objects.filter(
            cliente=cliente
        ).exclude(
            nombre__in=nombres_excluir
        )
        
        # También excluir el set ESF específico si se encontró
        if set_esf_excluir:
            sets_cliente = sets_cliente.exclude(id=set_esf_excluir.id)
        
        return list(sets_cliente)
        
    except Exception as e:
        logger.warning(f"Error obteniendo sets del cliente: {e}")
        return []


def _obtener_clasificaciones_completas(cuenta_ids, cliente, set_esf, sets_cliente):
    """
    Obtiene todas las clasificaciones de las cuentas para ESF y sets del cliente
    
    Returns:
        dict: {
            cuenta_id: {
                'esf': {'opcion_valor': '...', 'opcion_id': ...},
                'cliente_sets': {
                    'set_nombre': {'opcion_valor': '...', 'opcion_id': ...}
                }
            }
        }
    """
    clasificaciones_completas = {}
    
    # Inicializar estructura para todas las cuentas
    for cuenta_id in cuenta_ids:
        clasificaciones_completas[cuenta_id] = {
            'esf': None,
            'cliente_sets': {}
        }
    
    try:
        # Obtener todas las clasificaciones ESF
        if set_esf:
            clasificaciones_esf = AccountClassification.objects.filter(
                cuenta_id__in=cuenta_ids,
                set_clas=set_esf
            ).select_related('opcion', 'cuenta')
            
            for clasificacion in clasificaciones_esf:
                cuenta_id = clasificacion.cuenta_id
                if cuenta_id in clasificaciones_completas:
                    clasificaciones_completas[cuenta_id]['esf'] = {
                        'opcion_valor': clasificacion.opcion.valor,
                        'opcion_id': clasificacion.opcion.id
                    }
        
        # Obtener clasificaciones de sets del cliente
        if sets_cliente:
            for set_cliente in sets_cliente:
                clasificaciones_cliente = AccountClassification.objects.filter(
                    cuenta_id__in=cuenta_ids,
                    set_clas=set_cliente
                ).select_related('opcion', 'cuenta')
                
                for clasificacion in clasificaciones_cliente:
                    cuenta_id = clasificacion.cuenta_id
                    if cuenta_id in clasificaciones_completas:
                        clasificaciones_completas[cuenta_id]['cliente_sets'][set_cliente.nombre] = {
                            'opcion_valor': clasificacion.opcion.valor,
                            'opcion_id': clasificacion.opcion.id
                        }
        
        return clasificaciones_completas
        
    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones completas: {str(e)}")
        return clasificaciones_completas


def _obtener_clasificaciones_completas_eri(cuenta_ids, cliente, set_eri, sets_cliente):
    """
    Obtiene todas las clasificaciones de las cuentas para ERI y sets del cliente
    
    Returns:
        dict: {
            cuenta_id: {
                'eri': {'opcion_valor': '...', 'opcion_id': ...},
                'cliente_sets': {
                    'set_nombre': {'opcion_valor': '...', 'opcion_id': ...}
                }
            }
        }
    """
    clasificaciones_completas = {}
    
    # Inicializar estructura para todas las cuentas
    for cuenta_id in cuenta_ids:
        clasificaciones_completas[cuenta_id] = {
            'eri': None,
            'cliente_sets': {}
        }
    
    try:
        # Obtener todas las clasificaciones ERI
        if set_eri:
            clasificaciones_eri = AccountClassification.objects.filter(
                cuenta_id__in=cuenta_ids,
                set_clas=set_eri
            ).select_related('opcion', 'cuenta')
            
            for clasificacion in clasificaciones_eri:
                cuenta_id = clasificacion.cuenta_id
                if cuenta_id in clasificaciones_completas:
                    clasificaciones_completas[cuenta_id]['eri'] = {
                        'opcion_valor': clasificacion.opcion.valor,
                        'opcion_id': clasificacion.opcion.id
                    }
        
        # Obtener clasificaciones de sets del cliente
        if sets_cliente:
            for set_cliente in sets_cliente:
                clasificaciones_cliente = AccountClassification.objects.filter(
                    cuenta_id__in=cuenta_ids,
                    set_clas=set_cliente
                ).select_related('opcion', 'cuenta')
                
                for clasificacion in clasificaciones_cliente:
                    cuenta_id = clasificacion.cuenta_id
                    if cuenta_id in clasificaciones_completas:
                        clasificaciones_completas[cuenta_id]['cliente_sets'][set_cliente.nombre] = {
                            'opcion_valor': clasificacion.opcion.valor,
                            'opcion_id': clasificacion.opcion.id
                        }
        
        return clasificaciones_completas
        
    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones completas ERI: {str(e)}")
        return clasificaciones_completas
