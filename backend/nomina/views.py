"""
Views para Nueva Arquitectura de Nómina SGM
==========================================

ViewSets para modelos rediseñados centrados en CierreNomina:
- CierreNomina: CRUD + acciones especiales (consolidar, cerrar, inicializar Redis)
- EmpleadoNomina: Lista, detalle con búsqueda avanzada
- Incidencias: Sistema completo de gestión con workflow
- KPINomina: Métricas y dashboards

Integración con Redis DB 2 para cache y optimizaciones.

Autor: Sistema SGM - Módulo Nómina  
Fecha: 20 de julio de 2025
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import (
    # Modelos principales
    CierreNomina,
    EmpleadoNomina, 
    EmpleadoConcepto,
    Ausentismo,
    Incidencia,
    InteraccionIncidencia,
    
    # Optimizaciones y KPIs
    KPINomina,
    EmpleadoOfuscado,
    IndiceEmpleadoBusqueda,
    ComparacionMensual,
    CacheConsultas,
    
    # Mapeos y utilidades
    MapeoConcepto,
    MapeoNovedades,
    LogArchivo,
)

from .serializers import (
    CierreNominaListSerializer,
    CierreNominaDetailSerializer,
    CierreNominaCreateSerializer,
    EmpleadoNominaListSerializer,
    EmpleadoNominaDetailSerializer,
    EmpleadoConceptoSerializer,
    AusentismoSerializer,
    IncidenciaListSerializer,
    IncidenciaDetailSerializer,
    InteraccionIncidenciaSerializer,
    KPINominaSerializer,
    MapeoConceptoSerializer,
    LogArchivoSerializer,
)

from .cache_redis import CacheNominaSGM
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()

# ========== VIEWSET ESPECÍFICO PARA LIBRO DE REMUNERACIONES ==========

class LibroRemuneracionesViewSet(viewsets.ViewSet):
    """
    ViewSet específico para manejo de libros de remuneraciones.
    
    Mantiene compatibilidad con las rutas esperadas por el frontend:
    - POST /nomina/libros-remuneraciones/
    - GET /nomina/libros-remuneraciones/estado/{cierreId}/
    - POST /nomina/libros-remuneraciones/{libroId}/procesar/
    """
    
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """
        POST /nomina/libros-remuneraciones/
        Subir archivo de libro de remuneraciones.
        """
        from .tasks import crear_chain_procesamiento_libro
        
        # Validar datos requeridos
        cierre_id = request.data.get('cierre')
        if not cierre_id:
            return Response({
                'error': 'Debe proporcionar el ID del cierre en el campo "cierre"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'archivo' not in request.FILES:
            return Response({
                'error': 'Debe proporcionar un archivo en el campo "archivo"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        archivo = request.FILES['archivo']
        
        try:
            # Obtener el cierre
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar extensión
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'El archivo debe ser formato Excel (.xlsx, .xls)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Leer archivo en memoria
            archivo_content = archivo.read()
            
            # Crear chain de Celery
            chain_task = crear_chain_procesamiento_libro(
                cierre_id=cierre.id,
                archivo_data=archivo_content,
                filename=archivo.name
            )
            
            # Ejecutar chain
            result = chain_task.apply_async()
            
            # Actualizar estado inicial en Redis
            cache = CacheNominaSGM()
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre.id,
                estado='subido',
                info_adicional={
                    'filename': archivo.name,
                    'size': len(archivo_content),
                    'celery_task_id': result.id,
                    'progreso': 5,
                    'mensaje': 'Archivo recibido, iniciando análisis...'
                }
            )
            
            return Response({
                'success': True,
                'mensaje': f'Archivo {archivo.name} recibido, procesando en background',
                'data': {
                    'libro_id': cierre.id,  # Usamos cierre_id como libro_id
                    'filename': archivo.name,
                    'size': len(archivo_content),
                    'task_id': result.id,
                    'cierre_id': cierre.id,
                    'estado': 'subido'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error subiendo libro para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error procesando archivo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def obtener_estado(self, request, cierre_id=None):
        """
        GET /nomina/libros-remuneraciones/estado/{cierreId}/
        Obtener estado del libro de remuneraciones.
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cache = CacheNominaSGM()
            
            # Obtener información completa
            estado = cache.obtener_estado_libro(cierre.cliente.id, cierre_id)
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre_id)
            mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre_id)
            empleados = cache.obtener_empleados_procesados(cierre.cliente.id, cierre_id)
            
            # Construir respuesta compatible con frontend
            respuesta = {
                'libro_id': cierre_id,
                'cierre_id': cierre_id,
                'cliente': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': estado.get('estado', 'pendiente') if estado else 'pendiente',
                'progreso': self._calcular_progreso_libro(estado, analisis, mapeos_manuales, empleados),
                'mensaje': estado.get('info', {}).get('mensaje', '') if estado else '',
                'timestamp': estado.get('timestamp') if estado else None
            }
            
            # Añadir detalles según el estado
            if analisis:
                respuesta['headers_analysis'] = {
                    'headers_mapeados': len(analisis.get('headers_mapeados', [])),
                    'headers_no_mapeados': len(analisis.get('headers_no_mapeados', [])),
                    'headers_no_mapeados_lista': analisis.get('headers_no_mapeados', []),
                    'requiere_mapeo_manual': len(analisis.get('headers_no_mapeados', [])) > 0
                }
            
            if empleados:
                respuesta['empleados_procesados'] = {
                    'total_empleados': empleados.get('total_empleados', 0),
                    'total_conceptos': empleados.get('total_conceptos', 0)
                }
            
            return Response(respuesta)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado libro para cierre {cierre_id}: {e}")
            return Response({
                'error': f'Error obteniendo estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='procesar')
    def procesar(self, request, pk=None):
        """
        POST /nomina/libros-remuneraciones/{libroId}/procesar/
        Procesar empleados con mapeos aplicados.
        """
        from .tasks import procesar_empleados_libro
        
        cierre_id = pk  # En nuestro caso, libro_id = cierre_id
        
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cache = CacheNominaSGM()
            
            # Verificar estado actual
            estado_actual = cache.obtener_estado_libro(cierre.cliente.id, cierre_id)
            if not estado_actual:
                return Response({
                    'error': 'No se encontró información del libro. Debe subir un archivo primero.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if estado_actual.get('estado') not in ['listo_procesar', 'mapeo_requerido']:
                return Response({
                    'error': f'El libro no está listo para procesar. Estado actual: {estado_actual.get("estado")}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Iniciar tarea de procesamiento
            task_result = procesar_empleados_libro.delay(cierre_id)
            
            # Actualizar estado
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                estado='procesando',
                info_adicional={
                    'task_id': task_result.id,
                    'progreso': 60,
                    'mensaje': 'Procesando empleados con mapeos aplicados...'
                }
            )
            
            return Response({
                'success': True,
                'mensaje': 'Procesamiento iniciado exitosamente',
                'data': {
                    'task_id': task_result.id,
                    'estado': 'procesando',
                    'libro_id': cierre_id
                }
            })
            
        except Exception as e:
            logger.error(f"Error iniciando procesamiento para cierre {cierre_id}: {e}")
            return Response({
                'error': f'Error iniciando procesamiento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calcular_progreso_libro(self, estado, analisis, mapeos_manuales, empleados):
        """Calcula el progreso general de la tarjeta libro"""
        if not estado:
            return {'porcentaje': 0, 'fase': 'pendiente'}
        
        estado_actual = estado.get('estado', 'pendiente')
        
        if estado_actual == 'pendiente':
            return {'porcentaje': 0, 'fase': 'Esperando archivo'}
        elif estado_actual in ['subido', 'analizando']:
            return {'porcentaje': 20, 'fase': 'Analizando archivo'}
        elif estado_actual == 'mapeo_requerido':
            return {'porcentaje': 40, 'fase': 'Requiere mapeo manual'}
        elif estado_actual in ['listo_procesar', 'mapeo_parcial']:
            return {'porcentaje': 60, 'fase': 'Listo para procesar'}
        elif estado_actual == 'procesando':
            return {'porcentaje': 80, 'fase': 'Procesando empleados'}
        elif estado_actual == 'procesado':
            return {'porcentaje': 100, 'fase': 'Completado'}
        elif estado_actual == 'error':
            return {'porcentaje': 0, 'fase': 'Error', 'error': estado.get('info', {}).get('error')}
        else:
            return {'porcentaje': 0, 'fase': estado_actual}
    
    @action(detail=False, methods=['get'], url_path='headers/(?P<cierre_id>[^/.]+)')
    def obtener_headers_clasificacion(self, request, cierre_id=None):
        """
        GET /nomina/libros-remuneraciones/headers/{cierreId}/
        Obtener headers para modal de clasificación.
        """
        try:
            # Obtener el cierre
            cierre = CierreNomina.objects.get(id=cierre_id)
            cache = CacheNominaSGM()
            
            # Obtener análisis de headers
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre_id)
            mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre_id)
            mapeo_final = cache.obtener_mapeo_final(cierre.cliente.id, cierre_id)
            
            if not analisis:
                return Response({
                    'error': 'No se encontró análisis de headers. Debe subir un archivo primero.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            headers_no_mapeados = analisis.get('headers_no_mapeados', [])
            headers_mapeados = analisis.get('headers_mapeados', [])
            
            # Construir respuesta para modal
            respuesta = {
                'headers_sin_clasificar': headers_no_mapeados,
                'headers_clasificados': headers_mapeados,
                'mapeos_automaticos': {h: h for h in headers_mapeados},
                'mapeos_manuales': mapeos_manuales.get('mapeos', {}) if mapeos_manuales else {},
                'mapeos_completos': mapeo_final.get('mapeos_completos', {}) if mapeo_final else {},
                'total_headers': len(headers_no_mapeados) + len(headers_mapeados),
                'requiere_mapeo_manual': len(headers_no_mapeados) > 0,
                'estado': 'disponible'
            }
            
            return Response(respuesta)
            
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error obteniendo headers para cierre {cierre_id}: {e}")
            return Response({
                'error': f'Error obteniendo headers: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='mapeos/(?P<cierre_id>[^/.]+)')
    def guardar_mapeos_manuales(self, request, cierre_id=None):
        """
        POST /nomina/libros-remuneraciones/mapeos/{cierreId}/
        Guardar mapeos manuales en Redis (PHASE 1) Y en BD (permanente).
        
        ESTRATEGIA DUAL:
        1. Redis → Para procesamiento rápido PHASE 1
        2. BD → Para memoria permanente del cliente
        """
        try:
            # Obtener el cierre
            cierre = CierreNomina.objects.get(id=cierre_id)
            cache = CacheNominaSGM()
            
            # Obtener mapeos del request
            mapeos = request.data.get('mapeos', {})
            
            if not mapeos:
                return Response({
                    'error': 'Debe proporcionar mapeos para guardar'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ===== CAPA 1: REDIS (PHASE 1 - Rápido) =====
            resultado_redis = cache.guardar_mapeos_manuales(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                mapeos=mapeos
            )
            
            if not resultado_redis:
                return Response({
                    'error': 'Error guardando mapeos en Redis'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # ===== CAPA 2: BD (Permanente - Memoria eterna) =====
            mapeos_guardados_bd = 0
            for header_excel, clasificacion in mapeos.items():
                # Crear o actualizar mapeo permanente
                mapeo, created = MapeoConcepto.objects.update_or_create(
                    cliente=cierre.cliente,
                    header_excel=header_excel,
                    defaults={
                        'clasificacion_sugerida': clasificacion,
                        'es_automatico': False,  # Es mapeo manual
                        'fecha_creacion': timezone.now() if created else None
                    }
                )
                mapeos_guardados_bd += 1
                
                if created:
                    logger.info(f"💾 Nuevo mapeo permanente: {header_excel} → {clasificacion} (Cliente {cierre.cliente.id})")
                else:
                    logger.info(f"🔄 Mapeo actualizado: {header_excel} → {clasificacion} (Cliente {cierre.cliente.id})")
            
            # ===== RECALCULAR MAPEO FINAL =====
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre_id)
            mapeos_manuales_actualizados = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre_id)
            
            # Generar mapeo final combinando automáticos + manuales
            headers_mapeados = analisis.get('headers_mapeados', []) if analisis else []
            mapeos_automaticos = {h: h for h in headers_mapeados}
            mapeos_manuales = mapeos_manuales_actualizados.get('mapeos', {}) if mapeos_manuales_actualizados else {}
            
            mapeos_completos = {**mapeos_automaticos, **mapeos_manuales}
            
            # Guardar mapeo final
            cache.guardar_mapeo_final(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                mapeos_completos=mapeos_completos
            )
            
            # ===== DETERMINAR NUEVO ESTADO =====
            headers_no_mapeados = analisis.get('headers_no_mapeados', []) if analisis else []
            headers_pendientes = [h for h in headers_no_mapeados if h not in mapeos_manuales]
            
            if len(headers_pendientes) == 0:
                nuevo_estado = 'listo_procesar'
                mensaje = '✅ Todos los headers han sido mapeados - listo para procesar'
            else:
                nuevo_estado = 'mapeo_requerido'
                mensaje = f'⚠️ {len(headers_pendientes)} headers aún requieren mapeo'
            
            # Actualizar estado
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                estado=nuevo_estado,
                info_adicional={
                    'progreso': 70 if nuevo_estado == 'listo_procesar' else 50,
                    'mensaje': mensaje,
                    'headers_mapeados_total': len(mapeos_completos),
                    'headers_pendientes': len(headers_pendientes)
                }
            )
            
            return Response({
                'success': True,
                'mensaje': f'✅ Mapeos guardados: Redis (PHASE 1) + BD (permanente)',
                'data': {
                    'mapeos_guardados_redis': len(mapeos),
                    'mapeos_guardados_bd': mapeos_guardados_bd,
                    'mapeos_completos': len(mapeos_completos),
                    'headers_pendientes': len(headers_pendientes),
                    'nuevo_estado': nuevo_estado,
                    'listo_procesar': nuevo_estado == 'listo_procesar',
                    'memoria_permanente': True  # ✨ Confirmación de que se guardó en BD
                }
            })
            
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error guardando mapeos para cierre {cierre_id}: {e}")
            return Response({
                'error': f'Error guardando mapeos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'], url_path='mapeos/(?P<cierre_id>[^/.]+)/(?P<header_name>[^/.]+)')
    def eliminar_mapeo_manual(self, request, cierre_id=None, header_name=None):
        """
        DELETE /nomina/libros-remuneraciones/mapeos/{cierreId}/{headerName}/
        Eliminar mapeo manual de Redis y BD.
        
        OPERACIÓN CRUD: DELETE
        - Redis: Elimina del mapeo actual 
        - BD: Marca como inactivo (soft delete) para mantener historial
        """
        try:
            # Obtener el cierre
            cierre = CierreNomina.objects.get(id=cierre_id)
            cache = CacheNominaSGM()
            
            # Decodificar nombre del header
            import urllib.parse
            header_decodificado = urllib.parse.unquote(header_name)
            
            # ===== CAPA 1: REDIS (PHASE 1) =====
            # Eliminar de mapeos manuales actuales
            mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre_id)
            mapeos_actuales = mapeos_manuales.get('mapeos', {}) if mapeos_manuales else {}
            
            if header_decodificado in mapeos_actuales:
                del mapeos_actuales[header_decodificado]
                
                # Guardar mapeos actualizados
                cache.guardar_mapeos_manuales(
                    cliente_id=cierre.cliente.id,
                    cierre_id=cierre_id,
                    mapeos=mapeos_actuales
                )
                
                logger.info(f"🗑️ Eliminado mapeo de Redis: {header_decodificado}")
            
            # ===== CAPA 2: BD (Soft Delete) =====
            mapeos_bd = MapeoConcepto.objects.filter(
                cliente=cierre.cliente,
                header_excel=header_decodificado
            )
            
            mapeos_eliminados_bd = 0
            for mapeo in mapeos_bd:
                mapeo.activo = False  # Soft delete
                mapeo.fecha_eliminacion = timezone.now()
                mapeo.save(update_fields=['activo', 'fecha_eliminacion'])
                mapeos_eliminados_bd += 1
                
            logger.info(f"🗑️ Marcados como inactivos {mapeos_eliminados_bd} mapeos en BD para: {header_decodificado}")
            
            # ===== RECALCULAR ESTADO =====
            # Recalcular mapeo final
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre_id)
            headers_mapeados = analisis.get('headers_mapeados', []) if analisis else []
            mapeos_automaticos = {h: h for h in headers_mapeados}
            
            mapeos_completos = {**mapeos_automaticos, **mapeos_actuales}
            
            # Guardar mapeo final actualizado
            cache.guardar_mapeo_final(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                mapeos_completos=mapeos_completos
            )
            
            # Determinar nuevo estado
            headers_no_mapeados = analisis.get('headers_no_mapeados', []) if analisis else []
            headers_pendientes = [h for h in headers_no_mapeados if h not in mapeos_actuales]
            
            if len(headers_pendientes) == 0:
                nuevo_estado = 'listo_procesar'
                mensaje = '✅ Todos los headers siguen mapeados'
            else:
                nuevo_estado = 'mapeo_requerido'
                mensaje = f'⚠️ {len(headers_pendientes)} headers requieren mapeo tras eliminación'
            
            # Actualizar estado
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre_id,
                estado=nuevo_estado,
                info_adicional={
                    'progreso': 70 if nuevo_estado == 'listo_procesar' else 50,
                    'mensaje': mensaje,
                    'headers_mapeados_total': len(mapeos_completos),
                    'headers_pendientes': len(headers_pendientes)
                }
            )
            
            return Response({
                'success': True,
                'mensaje': f'✅ Mapeo eliminado: {header_decodificado}',
                'data': {
                    'header_eliminado': header_decodificado,
                    'mapeos_restantes_redis': len(mapeos_actuales),
                    'mapeos_desactivados_bd': mapeos_eliminados_bd,
                    'nuevo_estado': nuevo_estado,
                    'headers_pendientes': len(headers_pendientes),
                    'listo_procesar': nuevo_estado == 'listo_procesar'
                }
            })
            
        except CierreNomina.DoesNotExist:
            return Response({
                'error': f'Cierre con ID {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error eliminando mapeo {header_name} para cierre {cierre_id}: {e}")
            return Response({
                'error': f'Error eliminando mapeo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== VIEWSET PRINCIPAL - CIERRE NOMINA ==========

class CierreNominaViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para gestión de cierres de nómina
    
    Funcionalidades:
    - CRUD básico de cierres
    - Consolidación automática con Redis
    - Cálculo de KPIs
    - Apertura/Cierre workflow
    - Dashboard con métricas
    """
    
    queryset = CierreNomina.objects.all().select_related('cliente', 'analista_responsable')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente__nombre', 'periodo', 'analista_responsable__correo_bdo']
    ordering_fields = ['fecha_creacion', 'periodo', 'estado']
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CierreNominaListSerializer
        elif self.action == 'create':
            return CierreNominaCreateSerializer
        return CierreNominaDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """Lista de cierres con filtros"""
        
        # Si hay filtro de cliente, usar ORM normal ahora que está corregido
        cliente_id = self.request.query_params.get('cliente')
        
        if cliente_id:
            try:
                # Usar ORM normal con optimizaciones
                cierres = CierreNomina.objects.filter(
                    cliente_id=cliente_id
                ).select_related('cliente', 'analista_responsable').order_by('-periodo')
                
                cierres_data = []
                for cierre in cierres:
                    analista_info = None
                    if cierre.analista_responsable:
                        analista_info = {
                            'id': cierre.analista_responsable.id,
                            'correo_bdo': cierre.analista_responsable.correo_bdo,
                            'full_name': f"{cierre.analista_responsable.nombre} {cierre.analista_responsable.apellido}".strip()
                        }
                    
                    cierres_data.append({
                        'id': cierre.id,
                        'periodo': cierre.periodo,
                        'estado': cierre.estado,
                        'fecha_creacion': cierre.fecha_creacion,
                        'fecha_consolidacion': cierre.fecha_consolidacion,
                        'fecha_cierre': cierre.fecha_cierre,
                        'total_empleados_activos': cierre.total_empleados_activos or 0,
                        'discrepancias_detectadas': cierre.discrepancias_detectadas or 0,
                        'tiene_discrepancias': (cierre.discrepancias_detectadas or 0) > 0,
                        'cliente': {
                            'id': cierre.cliente.id,
                            'nombre': cierre.cliente.nombre
                        },
                        'analista_responsable': analista_info
                    })
                
                logger.info(f"Obtenidos {len(cierres_data)} cierres para cliente {cliente_id} con ORM")
                
                return Response(cierres_data)
                
            except Exception as e:
                logger.error(f"Error obteniendo cierres para cliente {cliente_id}: {str(e)}", exc_info=True)
                return Response(
                    {'error': f'Error obteniendo cierres: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Para otros casos sin filtro de cliente, usar método original
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtrar cierres según permisos de usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtros por parámetros de URL
        cliente_id = self.request.query_params.get('cliente')
        periodo = self.request.query_params.get('periodo')
        estado = self.request.query_params.get('estado')
        
        if cliente_id:
            queryset = queryset.filter(cliente=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Control de acceso por tipo de usuario
        if user.tipo_usuario == 'gerente':
            # Gerentes ven todo
            pass
        elif user.tipo_usuario == 'supervisor':
            # Supervisores ven cierres de sus analistas
            analistas_supervisados = user.get_analistas_supervisados()
            queryset = queryset.filter(analista_responsable__in=analistas_supervisados)
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas solo ven sus propios cierres
            queryset = queryset.filter(analista_responsable=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Crear cierre e inicializar en Redis con mapeos del cliente"""
        # Si no se proporciona analista_responsable, asignar el usuario actual
        if not serializer.validated_data.get('analista_responsable'):
            serializer.validated_data['analista_responsable'] = self.request.user
        
        cierre = serializer.save()
        
        # Crear checklist por defecto
        try:
            from .models import ChecklistItem
            ChecklistItem.crear_checklist_por_defecto(cierre)
            logger.info(f"Checklist creado para cierre {cierre.id}")
        except Exception as e:
            logger.error(f"Error creando checklist para cierre {cierre.id}: {e}")
        
        # ✨ NUEVA FUNCIONALIDAD: Pre-cargar mapeos del cliente en Redis
        try:
            self._precargar_mapeos_cliente_en_redis(cierre)
        except Exception as e:
            logger.error(f"Error precargando mapeos para cierre {cierre.id}: {e}")
        
        # Inicializar en Redis (comentado hasta implementar el método)
        try:
            # cache = CacheNominaSGM()
            # cache.inicializar_cierre(cierre.id)
            
            logger.info(f"Cierre {cierre.id} creado exitosamente con mapeos precargados")
        except Exception as e:
            logger.error(f"Error inicializando cierre {cierre.id} en Redis: {e}")
    
    def _precargar_mapeos_cliente_en_redis(self, cierre):
        """
        Pre-carga mapeos de BD a Redis para procesamiento eficiente.
        
        ESTRATEGIA:
        1. Obtener todos los mapeos del cliente desde BD
        2. Cargar en Redis como 'mapeos_conocidos' 
        3. Análisis posterior usa Redis (no consulta BD concepto x concepto)
        """
        try:
            from .cache_redis import CacheNominaSGM
            
            cache = CacheNominaSGM()
            
            # Obtener mapeos existentes del cliente desde BD
            mapeos_bd = MapeoConcepto.objects.filter(cliente=cierre.cliente)
            
            if mapeos_bd.exists():
                # Convertir a diccionario para Redis
                mapeos_conocidos = {}
                for mapeo in mapeos_bd:
                    mapeos_conocidos[mapeo.header_excel] = mapeo.clasificacion_sugerida
                
                # Guardar en Redis como "mapeos conocidos" del cliente
                key_mapeos_conocidos = f"sgm:nomina:{cierre.cliente.id}:{cierre.id}:mapeos_conocidos"
                cache.redis_client.hset(key_mapeos_conocidos, mapping=mapeos_conocidos)
                cache.redis_client.expire(key_mapeos_conocidos, 604800)  # 7 días
                
                logger.info(f"💾 Pre-cargados {len(mapeos_conocidos)} mapeos conocidos para cliente {cierre.cliente.id} en Redis")
                
                # Log de mapeos cargados para debug
                for header, clasificacion in list(mapeos_conocidos.items())[:5]:  # Solo mostrar primeros 5
                    logger.info(f"  📋 {header} → {clasificacion}")
                    
                if len(mapeos_conocidos) > 5:
                    logger.info(f"  ... y {len(mapeos_conocidos) - 5} mapeos más")
                    
            else:
                logger.info(f"📝 Cliente {cierre.cliente.id} no tiene mapeos previos - primera vez")
                
        except Exception as e:
            logger.error(f"Error precargando mapeos para cierre {cierre.id}: {e}")
            raise
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cliente_id>[^/.]+)')
    def resumen(self, request, cliente_id=None):
        """
        Obtener resumen de nómina para un cliente específico
        
        Devuelve información del último cierre y estado actual:
        - ultimo_cierre: período del último cierre
        - estado_cierre_actual: estado del cierre más reciente
        """
        try:
            # Log para debug
            logger.info(f"Obteniendo resumen de nómina para cliente_id: {cliente_id}")
            
            # Usar ORM normal ahora que está corregido
            ultimo_cierre = CierreNomina.objects.filter(
                cliente_id=cliente_id
            ).select_related('analista_responsable').order_by('-periodo').first()
            
            if ultimo_cierre:
                analista_correo = ultimo_cierre.analista_responsable.correo_bdo if ultimo_cierre.analista_responsable else None
                
                response_data = {
                    'ultimo_cierre': ultimo_cierre.periodo,
                    'estado_cierre_actual': ultimo_cierre.estado,
                    'fecha_ultima_actividad': ultimo_cierre.fecha_creacion,
                    'total_empleados': ultimo_cierre.total_empleados_activos or 0,
                    'tiene_discrepancias': (ultimo_cierre.discrepancias_detectadas or 0) > 0,
                    'analista_responsable': analista_correo
                }
                
                logger.info(f"Respuesta preparada: {response_data}")
                return Response(response_data)
            else:
                logger.info(f"No se encontraron cierres para cliente {cliente_id}")
                return Response({
                    'ultimo_cierre': None,
                    'estado_cierre_actual': None,
                    'fecha_ultima_actividad': None,
                    'total_empleados': 0,
                    'tiene_discrepancias': False,
                    'analista_responsable': None
                })
                
        except Exception as e:
            logger.error(f'Error obteniendo resumen para cliente {cliente_id}: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error obteniendo resumen: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='consolidar')
    def consolidar(self, request, pk=None):
        """
        Consolidar datos del cierre y calcular KPIs
        """
        cierre = self.get_object()
        
        if cierre.estado != 'abierto':
            return Response({
                'error': f'No se puede consolidar un cierre en estado {cierre.estado}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # 1. Cambiar estado a consolidando
                cierre.estado = 'consolidando'
                cierre.save(update_fields=['estado'])
                
                # 2. Ejecutar consolidación en Redis
                cache = CacheNominaSGM()
                resultado_consolidacion = cache.consolidar_cierre(cierre.id)
                
                # 3. Calcular KPIs
                self._calcular_kpis_cierre(cierre)
                
                # 4. Actualizar estado final
                cierre.estado = 'consolidado'
                cierre.fecha_consolidacion = timezone.now()
                cierre.save(update_fields=['estado', 'fecha_consolidacion'])
                
                # 5. Actualizar cache con estado final
                cache.actualizar_estado_cierre(cierre.id, 'consolidado')
                
                logger.info(f"Cierre {cierre.id} consolidado exitosamente")
                
                return Response({
                    'success': True,
                    'mensaje': 'Cierre consolidado exitosamente',
                    'resultado_consolidacion': resultado_consolidacion,
                    'estado': cierre.estado,
                    'fecha_consolidacion': cierre.fecha_consolidacion
                })
                
        except Exception as e:
            logger.error(f"Error consolidando cierre {cierre.id}: {e}")
            
            # Revertir estado si hay error
            cierre.estado = 'abierto'
            cierre.save(update_fields=['estado'])
            
            return Response({
                'error': f'Error durante consolidación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='cerrar')
    def cerrar(self, request, pk=None):
        """
        Cerrar definitivamente el cierre de nómina
        """
        cierre = self.get_object()
        
        if cierre.estado != 'consolidado':
            return Response({
                'error': f'Solo se puede cerrar un cierre consolidado. Estado actual: {cierre.estado}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que no hay incidencias pendientes críticas
        incidencias_criticas = cierre.incidencias.filter(
            estado='pendiente',
            tipo_incidencia__in=['VARIACION_CRITICA', 'EMPLEADO_DUPLICADO']
        ).count()
        
        if incidencias_criticas > 0:
            return Response({
                'error': f'No se puede cerrar. Hay {incidencias_criticas} incidencias críticas pendientes',
                'incidencias_criticas': incidencias_criticas
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                cierre.estado = 'cerrado'
                cierre.fecha_cierre = timezone.now()
                cierre.usuario_cierre = request.user
                cierre.save(update_fields=['estado', 'fecha_cierre', 'usuario_cierre'])
                
                # Actualizar en Redis
                cache = CacheNominaSGM()
                cache.actualizar_estado_cierre(cierre.id, 'cerrado')
                
                # Archivar datos en Redis (opcional - solo para optimización)
                cache.archivar_cierre(cierre.id)
                
                logger.info(f"Cierre {cierre.id} cerrado por usuario {request.user.id}")
                
                return Response({
                    'success': True,
                    'mensaje': 'Cierre cerrado exitosamente',
                    'estado': cierre.estado,
                    'fecha_cierre': cierre.fecha_cierre,
                    'usuario_cierre': request.user.get_full_name()
                })
                
        except Exception as e:
            logger.error(f"Error cerrando cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error durante cierre: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='reabrir')
    def reabrir(self, request, pk=None):
        """
        Reabrir un cierre cerrado (solo gerentes/supervisores)
        """
        cierre = self.get_object()
        user = request.user
        motivo = request.data.get('motivo', '')
        
        # Solo gerentes y supervisores pueden reabrir
        if user.tipo_usuario not in ['gerente', 'supervisor']:
            return Response({
                'error': 'Solo gerentes y supervisores pueden reabrir cierres'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if cierre.estado != 'cerrado':
            return Response({
                'error': f'Solo se pueden reabrir cierres cerrados. Estado actual: {cierre.estado}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not motivo:
            return Response({
                'error': 'Debe proporcionar un motivo para la reapertura'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                cierre.estado = 'consolidado'  # Volver a consolidado
                cierre.fecha_reapertura = timezone.now()
                cierre.motivo_reapertura = motivo
                cierre.save(update_fields=['estado', 'fecha_reapertura', 'motivo_reapertura'])
                
                # Actualizar en Redis
                cache = CacheNominaSGM()
                cache.actualizar_estado_cierre(cierre.id, 'consolidado')
                
                logger.info(f"Cierre {cierre.id} reabierto por {user.id}. Motivo: {motivo}")
                
                return Response({
                    'success': True,
                    'mensaje': 'Cierre reabierto exitosamente',
                    'estado': cierre.estado,
                    'fecha_reapertura': cierre.fecha_reapertura,
                    'motivo': motivo
                })
                
        except Exception as e:
            logger.error(f"Error reabriendo cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error durante reapertura: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        """
        Dashboard con métricas y KPIs del cierre
        """
        cierre = self.get_object()
        
        try:
            # Obtener KPIs calculados
            kpis = KPINomina.objects.filter(cierre=cierre)
            kpis_data = {}
            
            for kpi in kpis:
                kpis_data[kpi.tipo_kpi] = {
                    'valor': kpi.valor_numerico,
                    'valor_anterior': kpi.valor_comparativo_anterior,
                    'variacion': kpi.variacion_porcentual,
                    'metadatos': kpi.metadatos_kpi,
                    'fecha_calculo': kpi.fecha_calculo
                }
            
            # Resumen de empleados
            resumen_empleados = {
                'total_empleados': cierre.empleados_nomina.count(),
                'por_tipo': {
                    'planta': cierre.empleados_nomina.filter(tipo_empleado='planta').count(),
                    'honorarios': cierre.empleados_nomina.filter(tipo_empleado='honorarios').count(),
                    'finiquito': cierre.empleados_nomina.filter(tipo_empleado='finiquito').count(),
                    'ingreso': cierre.empleados_nomina.filter(tipo_empleado='ingreso').count(),
                }
            }
            
            # Resumen de incidencias
            resumen_incidencias = {
                'total': cierre.incidencias.count(),
                'por_estado': {
                    'pendiente': cierre.incidencias.filter(estado='pendiente').count(),
                    'en_revision': cierre.incidencias.filter(estado='en_revision').count(),
                    'resuelta': cierre.incidencias.filter(estado='resuelta').count(),
                },
                'por_tipo': {}
            }
            
            # Contar por tipo de incidencia
            tipos_incidencia = cierre.incidencias.values('tipo_incidencia').annotate(count=Count('id'))
            for tipo in tipos_incidencia:
                resumen_incidencias['por_tipo'][tipo['tipo_incidencia']] = tipo['count']
            
            # Estado del cache Redis
            cache = CacheNominaSGM()
            estado_cache = cache.obtener_estado_cierre(cierre.id)
            
            dashboard_data = {
                'cierre_info': {
                    'id': cierre.id,
                    'periodo': cierre.periodo,
                    'estado': cierre.estado,
                    'cliente': cierre.cliente.nombre,
                    'analista': cierre.analista_responsable.get_full_name(),
                    'fecha_creacion': cierre.fecha_creacion,
                    'fecha_consolidacion': cierre.fecha_consolidacion,
                    'fecha_cierre': cierre.fecha_cierre,
                },
                'kpis': kpis_data,
                'resumen_empleados': resumen_empleados,
                'resumen_incidencias': resumen_incidencias,
                'estado_cache': estado_cache,
                'puede_consolidar': cierre.estado == 'abierto',
                'puede_cerrar': cierre.estado == 'consolidado',
                'puede_reabrir': cierre.estado == 'cerrado' and request.user.tipo_usuario in ['gerente', 'supervisor']
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            logger.error(f"Error generando dashboard para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error generando dashboard: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='inicializar-redis')
    def inicializar_redis(self, request, pk=None):
        """
        Inicializar/reinicializar cierre en Redis
        """
        cierre = self.get_object()
        
        try:
            cache = CacheNominaSGM()
            resultado = cache.inicializar_cierre(cierre.id, forzar=True)
            
            return Response({
                'success': True,
                'mensaje': 'Cierre inicializado en Redis exitosamente',
                'resultado': resultado
            })
            
        except Exception as e:
            logger.error(f"Error inicializando cierre {cierre.id} en Redis: {e}")
            return Response({
                'error': f'Error inicializando Redis: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ===========================================
    # ENDPOINTS PARA TARJETA LIBRO DE REMUNERACIONES
    # ===========================================
    
    @action(detail=True, methods=['post'], url_path='libro/subir')
    def subir_libro(self, request, pk=None):
        """
        Subir archivo Excel de libro de remuneraciones.
        
        Inicia Celery chain: analizar_headers → procesar_empleados (si está todo mapeado)
        """
        from .tasks import crear_chain_procesamiento_libro
        
        cierre = self.get_object()
        
        # Validar archivo
        if 'archivo' not in request.FILES:
            return Response({
                'error': 'Debe proporcionar un archivo en el campo "archivo"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        archivo = request.FILES['archivo']
        
        # Validar extensión
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'El archivo debe ser formato Excel (.xlsx, .xls)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Leer archivo en memoria
            archivo_content = archivo.read()
            
            # Crear chain de Celery
            chain_task = crear_chain_procesamiento_libro(
                cierre_id=cierre.id,
                archivo_data=archivo_content,
                filename=archivo.name
            )
            
            # Ejecutar chain
            result = chain_task.apply_async()
            
            # Actualizar estado inicial en Redis
            cache = CacheNominaSGM()
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre.id,
                estado='subido',
                info_adicional={
                    'filename': archivo.name,
                    'size': len(archivo_content),
                    'celery_task_id': result.id,
                    'progreso': 5,
                    'mensaje': 'Archivo recibido, iniciando análisis...'
                }
            )
            
            return Response({
                'success': True,
                'mensaje': f'Archivo {archivo.name} recibido, procesando en background',
                'datos': {
                    'filename': archivo.name,
                    'size': len(archivo_content),
                    'task_id': result.id,
                    'cierre_id': cierre.id,
                    'estado': 'subido'
                }
            })
            
        except Exception as e:
            logger.error(f"Error subiendo libro para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error procesando archivo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='libro/mapear')
    def mapear_conceptos_libro(self, request, pk=None):
        """
        Guardar mapeos manuales de conceptos no clasificados automáticamente.
        """
        cierre = self.get_object()
        
        # Validar datos
        mapeos = request.data.get('mapeos')
        if not mapeos or not isinstance(mapeos, dict):
            return Response({
                'error': 'Debe proporcionar un diccionario de mapeos en el campo "mapeos"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cache = CacheNominaSGM()
            
            # Verificar que hay análisis previo de headers
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre.id)
            if not analisis:
                return Response({
                    'error': 'No se encontró análisis de headers. Debe subir un archivo primero.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Guardar mapeos manuales
            exito = cache.guardar_mapeos_manuales(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre.id,
                mapeos=mapeos
            )
            
            if not exito:
                return Response({
                    'error': 'Error guardando mapeos en Redis'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verificar si todos los conceptos están mapeados
            headers_no_mapeados = analisis.get('headers_no_mapeados', [])
            conceptos_mapeados = set(mapeos.keys())
            conceptos_pendientes = set(headers_no_mapeados) - conceptos_mapeados
            
            todos_mapeados = len(conceptos_pendientes) == 0
            
            # Actualizar estado
            if todos_mapeados:
                estado = 'listo_procesar'
                mensaje = 'Todos los conceptos están mapeados. Listo para procesar.'
            else:
                estado = 'mapeo_parcial'
                mensaje = f'Faltan {len(conceptos_pendientes)} conceptos por mapear'
            
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre.id,
                estado=estado,
                info_adicional={
                    'mapeos_guardados': len(mapeos),
                    'conceptos_pendientes': len(conceptos_pendientes),
                    'todos_mapeados': todos_mapeados,
                    'mensaje': mensaje
                }
            )
            
            return Response({
                'success': True,
                'mensaje': mensaje,
                'datos': {
                    'mapeos_guardados': len(mapeos),
                    'conceptos_pendientes': list(conceptos_pendientes),
                    'todos_mapeados': todos_mapeados,
                    'puede_procesar': todos_mapeados
                }
            })
            
        except Exception as e:
            logger.error(f"Error guardando mapeos para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error guardando mapeos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='libro/procesar')
    def procesar_libro(self, request, pk=None):
        """
        Procesar empleados con todos los mapeos aplicados.
        Solo funciona si todos los conceptos están mapeados.
        """
        from .tasks import procesar_empleados_libro
        
        cierre = self.get_object()
        
        try:
            cache = CacheNominaSGM()
            
            # Verificar estado actual
            estado_actual = cache.obtener_estado_libro(cierre.cliente.id, cierre.id)
            if not estado_actual:
                return Response({
                    'error': 'No se encontró información del libro. Debe subir un archivo primero.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if estado_actual.get('estado') not in ['listo_procesar', 'mapeo_requerido']:
                return Response({
                    'error': f'El libro no está listo para procesar. Estado actual: {estado_actual.get("estado")}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar que todos los conceptos estén mapeados
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre.id)
            if analisis and analisis.get('headers_no_mapeados'):
                mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre.id)
                
                if not mapeos_manuales:
                    return Response({
                        'error': 'Hay conceptos sin mapear y no se han proporcionado mapeos manuales'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                conceptos_sin_mapear = set(analisis['headers_no_mapeados']) - set(mapeos_manuales.get('mapeos', {}).keys())
                if conceptos_sin_mapear:
                    return Response({
                        'error': f'Conceptos sin mapear: {list(conceptos_sin_mapear)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Iniciar tarea de procesamiento
            task_result = procesar_empleados_libro.delay(cierre.id)
            
            # Actualizar estado
            cache.actualizar_estado_libro(
                cliente_id=cierre.cliente.id,
                cierre_id=cierre.id,
                estado='procesando',
                info_adicional={
                    'task_id': task_result.id,
                    'progreso': 60,
                    'mensaje': 'Procesando empleados con mapeos aplicados...'
                }
            )
            
            return Response({
                'success': True,
                'mensaje': 'Procesamiento iniciado exitosamente',
                'datos': {
                    'task_id': task_result.id,
                    'estado': 'procesando',
                    'cierre_id': cierre.id
                }
            })
            
        except Exception as e:
            logger.error(f"Error iniciando procesamiento para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error iniciando procesamiento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='libro/estado')
    def estado_libro(self, request, pk=None):
        """
        Obtener estado completo de la tarjeta libro de remuneraciones.
        """
        cierre = self.get_object()
        
        try:
            cache = CacheNominaSGM()
            
            # Obtener información completa
            estado = cache.obtener_estado_libro(cierre.cliente.id, cierre.id)
            analisis = cache.obtener_analisis_headers(cierre.cliente.id, cierre.id)
            mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre.id)
            mapeo_final = cache.obtener_mapeo_final(cierre.cliente.id, cierre.id)
            empleados = cache.obtener_libro_empleados_conceptos(cierre.cliente.id, cierre.id)
            
            # ✅ CONSTRUCCIÓN COMPATIBLE CON FRONTEND
            # Construir header_json en formato esperado por frontend
            header_json = {}
            if analisis:
                headers_no_mapeados = analisis.get('headers_no_mapeados', [])
                headers_mapeados = analisis.get('headers_mapeados', [])
                
                # Headers sin clasificar son los que no están mapeados
                header_json['headers_sin_clasificar'] = headers_no_mapeados
                # Headers clasificados son los que sí están mapeados
                header_json['headers_clasificados'] = headers_mapeados
                
                # Si hay mapeos manuales, incluir info adicional
                if mapeos_manuales:
                    header_json['mapeos_manuales'] = mapeos_manuales.get('mapeos', {})
                
                # Si hay mapeo final, incluir mapeos completos
                if mapeo_final:
                    header_json['mapeos_completos'] = mapeo_final.get('mapeos_completos', {})
            
            # Construir respuesta completa
            respuesta = {
                'id': cierre.id,  # Agregamos ID para compatibilidad
                'cierre_id': cierre.id,
                'cliente': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': estado.get('estado', 'pendiente') if estado else 'pendiente',
                'estado_libro': estado,
                'header_json': header_json,  # ✅ FORMATO ESPERADO POR FRONTEND
                'progreso_completo': self._calcular_progreso_libro(estado, analisis, mapeos_manuales, empleados)
            }
            
            # Añadir detalles según el estado
            if analisis:
                respuesta['headers_analysis'] = {
                    'headers_mapeados': len(analisis.get('headers_mapeados', [])),
                    'headers_no_mapeados': len(analisis.get('headers_no_mapeados', [])),
                    'requiere_mapeo_manual': len(analisis.get('headers_no_mapeados', [])) > 0
                }
            
            if mapeos_manuales:
                respuesta['mapeos_manuales'] = {
                    'total_mapeos': len(mapeos_manuales.get('mapeos', {})),
                    'timestamp': mapeos_manuales.get('timestamp')
                }
            
            if empleados:
                respuesta['empleados_procesados'] = {
                    'total_empleados': empleados.get('total_empleados', 0),
                    'total_conceptos': empleados.get('total_conceptos', 0),
                    'timestamp': empleados.get('timestamp')
                }
            
            return Response(respuesta)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado libro para cierre {cierre.id}: {e}")
            return Response({
                'error': f'Error obteniendo estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calcular_progreso_libro(self, estado, analisis, mapeos_manuales, empleados):
        """Calcula el progreso general de la tarjeta libro"""
        if not estado:
            return {'porcentaje': 0, 'fase': 'pendiente'}
        
        estado_actual = estado.get('estado', 'pendiente')
        
        if estado_actual == 'pendiente':
            return {'porcentaje': 0, 'fase': 'Esperando archivo'}
        elif estado_actual in ['subido', 'analizando']:
            return {'porcentaje': 20, 'fase': 'Analizando archivo'}
        elif estado_actual == 'mapeo_requerido':
            return {'porcentaje': 40, 'fase': 'Requiere mapeo manual'}
        elif estado_actual in ['listo_procesar', 'mapeo_parcial']:
            return {'porcentaje': 60, 'fase': 'Listo para procesar'}
        elif estado_actual == 'procesando':
            return {'porcentaje': 80, 'fase': 'Procesando empleados'}
        elif estado_actual == 'procesado':
            return {'porcentaje': 100, 'fase': 'Completado'}
        elif estado_actual == 'error':
            return {'porcentaje': 0, 'fase': 'Error', 'error': estado.get('info', {}).get('error')}
        else:
            return {'porcentaje': 0, 'fase': estado_actual}
    
    def _calcular_kpis_cierre(self, cierre):
        """Método interno para calcular KPIs del cierre"""
        try:
            # Obtener período anterior para comparaciones
            periodo_anterior = self._obtener_periodo_anterior(cierre.periodo)
            cierre_anterior = None
            
            if periodo_anterior:
                cierre_anterior = CierreNomina.objects.filter(
                    cliente=cierre.cliente,
                    periodo=periodo_anterior,
                    estado='cerrado'
                ).first()
            
            # KPI: Total empleados
            total_empleados = cierre.empleados_nomina.count()
            total_empleados_anterior = cierre_anterior.empleados_nomina.count() if cierre_anterior else None
            
            self._crear_actualizar_kpi(
                cierre=cierre,
                tipo_kpi='TOTAL_EMPLEADOS',
                valor_actual=total_empleados,
                valor_anterior=total_empleados_anterior
            )
            
            # KPI: Total masa salarial (suma de todos los conceptos de sueldo base)
            masa_salarial = cierre.empleados_nomina.filter(
                conceptos__concepto__icontains='sueldo'
            ).aggregate(total=Sum('conceptos__valor_numerico'))['total'] or 0
            
            masa_salarial_anterior = None
            if cierre_anterior:
                masa_salarial_anterior = cierre_anterior.empleados_nomina.filter(
                    conceptos__concepto__icontains='sueldo'
                ).aggregate(total=Sum('conceptos__valor_numerico'))['total'] or 0
            
            self._crear_actualizar_kpi(
                cierre=cierre,
                tipo_kpi='MASA_SALARIAL',
                valor_actual=masa_salarial,
                valor_anterior=masa_salarial_anterior
            )
            
            # KPI: Promedio salarial
            promedio_salarial = masa_salarial / total_empleados if total_empleados > 0 else 0
            promedio_salarial_anterior = None
            
            if cierre_anterior and total_empleados_anterior and total_empleados_anterior > 0:
                promedio_salarial_anterior = masa_salarial_anterior / total_empleados_anterior
            
            self._crear_actualizar_kpi(
                cierre=cierre,
                tipo_kpi='PROMEDIO_SALARIAL',
                valor_actual=promedio_salarial,
                valor_anterior=promedio_salarial_anterior
            )
            
            # KPI: Total incidencias
            total_incidencias = cierre.incidencias.count()
            total_incidencias_anterior = cierre_anterior.incidencias.count() if cierre_anterior else None
            
            self._crear_actualizar_kpi(
                cierre=cierre,
                tipo_kpi='TOTAL_INCIDENCIAS',
                valor_actual=total_incidencias,
                valor_anterior=total_incidencias_anterior
            )
            
            logger.info(f"KPIs calculados para cierre {cierre.id}")
            
        except Exception as e:
            logger.error(f"Error calculando KPIs para cierre {cierre.id}: {e}")
            raise
    
    def _crear_actualizar_kpi(self, cierre, tipo_kpi, valor_actual, valor_anterior=None):
        """Crear o actualizar un KPI específico"""
        variacion = None
        if valor_anterior is not None and valor_anterior != 0:
            variacion = ((valor_actual - valor_anterior) / valor_anterior) * 100
        
        KPINomina.objects.update_or_create(
            cierre=cierre,
            tipo_kpi=tipo_kpi,
            defaults={
                'valor_numerico': valor_actual,
                'valor_comparativo_anterior': valor_anterior,
                'variacion_porcentual': variacion,
                'fecha_calculo': timezone.now(),
                'metadatos_kpi': {
                    'calculado_por': 'sistema',
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
    
    def _obtener_periodo_anterior(self, periodo):
        """Obtener período anterior en formato YYYY-MM"""
        try:
            year, month = periodo.split('-')
            year = int(year)
            month = int(month)
            
            if month == 1:
                return f"{year-1}-12"
            else:
                return f"{year}-{month-1:02d}"
        except:
            return None

    @action(detail=False, methods=['get'], url_path='conceptos-remuneracion')
    def obtener_conceptos_remuneracion(self, request):
        """
        GET /nomina/cierres/conceptos-remuneracion/?cliente_id=X
        Obtener conceptos de remuneración clasificados por cliente.
        """
        cliente_id = request.query_params.get('cliente_id')
        
        if not cliente_id:
            return Response({
                'error': 'Parámetro cliente_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener mapeos de conceptos para el cliente
            mapeos = MapeoConcepto.objects.filter(cliente_id=cliente_id)
            
            # Construir respuesta
            conceptos = []
            for mapeo in mapeos:
                concepto = {
                    'nombre_concepto': mapeo.header_excel,
                    'clasificacion': mapeo.clasificacion_sugerida or 'pendiente',
                    'hashtags': []  # Los hashtags se pueden agregar después si es necesario
                }
                conceptos.append(concepto)
            
            return Response(conceptos)
            
        except Exception as e:
            logger.error(f"Error obteniendo conceptos para cliente {cliente_id}: {e}")
            return Response({
                'error': f'Error obteniendo conceptos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== EMPLEADOS NOMINA ==========

class EmpleadoNominaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de empleados de nómina
    """
    
    queryset = EmpleadoNomina.objects.all().select_related('cierre__cliente').prefetch_related('conceptos')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['rut_empleado', 'nombre_empleado', 'cierre__periodo']
    ordering_fields = ['nombre_empleado', 'fecha_ingreso', 'fecha_consolidacion']
    ordering = ['nombre_empleado']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmpleadoNominaListSerializer
        return EmpleadoNominaDetailSerializer
    
    def get_queryset(self):
        """Filtrar empleados según acceso del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtros por parámetros
        cierre_id = self.request.query_params.get('cierre')
        tipo_empleado = self.request.query_params.get('tipo_empleado')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_empleado:
            queryset = queryset.filter(tipo_empleado=tipo_empleado)
        
        # Control de acceso por usuario
        if user.tipo_usuario == 'gerente':
            pass  # Gerentes ven todo
        elif user.tipo_usuario == 'supervisor':
            # Supervisores ven empleados de cierres de sus analistas
            analistas_supervisados = user.get_analistas_supervisados()
            queryset = queryset.filter(cierre__analista_responsable__in=analistas_supervisados)
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas solo ven empleados de sus propios cierres
            queryset = queryset.filter(cierre__analista_responsable=user)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='buscar-avanzada')
    def buscar_avanzada(self, request):
        """
        Búsqueda avanzada de empleados con múltiples criterios
        """
        try:
            # Parámetros de búsqueda
            rut = request.query_params.get('rut', '').strip()
            nombre = request.query_params.get('nombre', '').strip()
            concepto = request.query_params.get('concepto', '').strip()
            valor_min = request.query_params.get('valor_min')
            valor_max = request.query_params.get('valor_max')
            cliente_id = request.query_params.get('cliente_id')
            periodo = request.query_params.get('periodo')
            
            queryset = self.get_queryset()
            
            # Aplicar filtros
            if rut:
                queryset = queryset.filter(rut_empleado__icontains=rut)
            
            if nombre:
                queryset = queryset.filter(nombre_empleado__icontains=nombre)
            
            if cliente_id:
                queryset = queryset.filter(cierre__cliente_id=cliente_id)
            
            if periodo:
                queryset = queryset.filter(cierre__periodo=periodo)
            
            if concepto:
                queryset = queryset.filter(conceptos__concepto__icontains=concepto)
            
            if valor_min or valor_max:
                if valor_min:
                    queryset = queryset.filter(conceptos__valor_numerico__gte=float(valor_min))
                if valor_max:
                    queryset = queryset.filter(conceptos__valor_numerico__lte=float(valor_max))
            
            # Aplicar paginación
            queryset = queryset.distinct()[:50]  # Limitar a 50 resultados
            
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'resultados': serializer.data,
                'total_encontrados': len(serializer.data),
                'limitado_a_50': len(serializer.data) == 50
            })
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {e}")
            return Response({
                'error': f'Error en búsqueda: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== INCIDENCIAS ==========

class IncidenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de incidencias
    """
    
    queryset = Incidencia.objects.all().select_related(
        'cierre', 'analista_asignado', 'supervisor_asignado'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['empleado_rut', 'empleado_nombre', 'concepto_afectado']
    ordering_fields = ['fecha_deteccion', 'fecha_resolucion', 'diferencia_absoluta']
    ordering = ['-fecha_deteccion']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IncidenciaListSerializer
        return IncidenciaDetailSerializer
    
    def get_queryset(self):
        """Filtrar incidencias según acceso del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtros por parámetros
        cierre_id = self.request.query_params.get('cierre')
        estado = self.request.query_params.get('estado')
        tipo_incidencia = self.request.query_params.get('tipo')
        asignado_a_mi = self.request.query_params.get('asignado_a_mi') == 'true'
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo_incidencia:
            queryset = queryset.filter(tipo_incidencia=tipo_incidencia)
        if asignado_a_mi:
            queryset = queryset.filter(
                Q(analista_asignado=user) | Q(supervisor_asignado=user)
            )
        
        # Control de acceso por usuario
        if user.tipo_usuario == 'gerente':
            pass  # Gerentes ven todo
        elif user.tipo_usuario == 'supervisor':
            # Supervisores ven incidencias de sus analistas
            analistas_supervisados = user.get_analistas_supervisados()
            queryset = queryset.filter(
                Q(cierre__analista_responsable__in=analistas_supervisados) |
                Q(supervisor_asignado=user)
            )
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas ven sus propias incidencias
            queryset = queryset.filter(
                Q(cierre__analista_responsable=user) |
                Q(analista_asignado=user)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='asignar')
    def asignar(self, request, pk=None):
        """Asignar incidencia a analista/supervisor"""
        incidencia = self.get_object()
        analista_id = request.data.get('analista_id')
        supervisor_id = request.data.get('supervisor_id')
        
        try:
            if analista_id:
                analista = User.objects.get(id=analista_id)
                incidencia.analista_asignado = analista
            
            if supervisor_id:
                supervisor = User.objects.get(id=supervisor_id)
                incidencia.supervisor_asignado = supervisor
            
            incidencia.save(update_fields=['analista_asignado', 'supervisor_asignado'])
            
            # Crear interacción
            InteraccionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_interaccion='asignacion',
                mensaje=f"Incidencia asignada. Analista: {analista.get_full_name() if analista_id else 'N/A'}, Supervisor: {supervisor.get_full_name() if supervisor_id else 'N/A'}"
            )
            
            serializer = self.get_serializer(incidencia)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error asignando incidencia: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='resolver')
    def resolver(self, request, pk=None):
        """Resolver una incidencia"""
        incidencia = self.get_object()
        observaciones = request.data.get('observaciones', '')
        
        if incidencia.estado == 'resuelta':
            return Response({
                'error': 'La incidencia ya está resuelta'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            incidencia.estado = 'resuelta'
            incidencia.fecha_resolucion = timezone.now()
            incidencia.usuario_resolucion = request.user
            incidencia.observaciones_resolucion = observaciones
            incidencia.save(update_fields=[
                'estado', 'fecha_resolucion', 'usuario_resolucion', 'observaciones_resolucion'
            ])
            
            # Crear interacción
            InteraccionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_interaccion='resolucion',
                mensaje=f"Incidencia resuelta: {observaciones}"
            )
            
            serializer = self.get_serializer(incidencia)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Error resolviendo incidencia: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='comentar')
    def comentar(self, request, pk=None):
        """Agregar comentario a incidencia"""
        incidencia = self.get_object()
        mensaje = request.data.get('mensaje', '')
        
        if not mensaje:
            return Response({
                'error': 'El mensaje es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            interaccion = InteraccionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_interaccion='comentario',
                mensaje=mensaje
            )
            
            serializer = InteraccionIncidenciaSerializer(interaccion)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Error agregando comentario: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========== KPIS ==========

class KPINominaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de KPIs de nómina
    """
    
    queryset = KPINomina.objects.all().select_related('cierre')
    serializer_class = KPINominaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_calculo', 'tipo_kpi']
    ordering = ['-fecha_calculo']
    
    def get_queryset(self):
        """Filtrar KPIs según acceso del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtros por parámetros
        cierre_id = self.request.query_params.get('cierre')
        tipo_kpi = self.request.query_params.get('tipo')
        cliente_id = self.request.query_params.get('cliente')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_kpi:
            queryset = queryset.filter(tipo_kpi=tipo_kpi)
        if cliente_id:
            queryset = queryset.filter(cierre__cliente_id=cliente_id)
        
        # Control de acceso por usuario
        if user.tipo_usuario == 'gerente':
            pass  # Gerentes ven todo
        elif user.tipo_usuario == 'supervisor':
            # Supervisores ven KPIs de sus analistas
            analistas_supervisados = user.get_analistas_supervisados()
            queryset = queryset.filter(cierre__analista_responsable__in=analistas_supervisados)
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas ven KPIs de sus propios cierres
            queryset = queryset.filter(cierre__analista_responsable=user)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='comparacion-mensual')
    def comparacion_mensual(self, request):
        """Comparación de KPIs entre meses para un cliente"""
        cliente_id = request.query_params.get('cliente_id')
        tipo_kpi = request.query_params.get('tipo_kpi')
        meses = request.query_params.get('meses', '6')  # Últimos 6 meses por defecto
        
        if not cliente_id:
            return Response({
                'error': 'cliente_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            queryset = self.get_queryset().filter(
                cierre__cliente_id=cliente_id
            ).order_by('-cierre__periodo')
            
            if tipo_kpi:
                queryset = queryset.filter(tipo_kpi=tipo_kpi)
            
            # Limitar a los últimos N meses
            queryset = queryset[:int(meses)]
            
            # Agrupar por período
            datos_comparacion = {}
            for kpi in queryset:
                periodo = kpi.cierre.periodo
                if periodo not in datos_comparacion:
                    datos_comparacion[periodo] = {}
                
                datos_comparacion[periodo][kpi.tipo_kpi] = {
                    'valor': kpi.valor_numerico,
                    'valor_anterior': kpi.valor_comparativo_anterior,
                    'variacion': kpi.variacion_porcentual,
                    'fecha_calculo': kpi.fecha_calculo
                }
            
            return Response({
                'cliente_id': cliente_id,
                'meses_analizados': len(datos_comparacion),
                'datos': datos_comparacion
            })
            
        except Exception as e:
            logger.error(f"Error en comparación mensual: {e}")
            return Response({
                'error': f'Error generando comparación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
