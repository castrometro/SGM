"""
🔍 GENERACIÓN DE INCIDENCIAS - VIEWS
=====================================

ViewSet dedicado a la generación y gestión de incidencias de nómina.

Refactorizado desde: views.py (IncidenciaCierreViewSet.generar_incidencias)
Versión: 2.5.0
Fecha: 2025-10-20

Funcionalidades:
- Generación de incidencias (comparación mes actual vs anterior)
- Validación de estados y datos consolidados
- Lanzamiento de tareas Celery con dual logging
- Consulta de estado de generación

Tipos de incidencias detectadas:
- Variaciones de conceptos >±30%
- Ausentismos continuos
- Ingresos del mes anterior faltantes
- Finiquitos del mes anterior presentes
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import CierreNomina, IncidenciaCierre
from .serializers import IncidenciaCierreSerializer
from .permissions import SupervisorPuedeVerCierresNominaAnalistas

logger = logging.getLogger(__name__)


class GeneracionIncidenciasViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar la generación de incidencias de nómina.
    
    Endpoints:
    - POST /incidencias-v2/{cierre_id}/generar/ - Generar incidencias
    - GET /incidencias-v2/{cierre_id}/estado/ - Consultar estado de generación
    - GET /incidencias-v2/{cierre_id}/resumen/ - Resumen de incidencias generadas
    """
    
    permission_classes = [IsAuthenticated, SupervisorPuedeVerCierresNominaAnalistas]
    
    @action(detail=False, methods=['post'], url_path='(?P<cierre_id>[^/.]+)/generar')
    def generar_incidencias(self, request, cierre_id=None):
        """
        🔍 GENERAR INCIDENCIAS DE NÓMINA
        
        POST /nomina/incidencias-v2/{cierre_id}/generar/
        
        Ejecuta la detección de incidencias comparando datos consolidados:
        1. Valida estado permitido para generación
        2. Valida que existan datos consolidados del mes actual
        3. Lanza tarea Celery de generación con logging dual
        4. Retorna inmediatamente con task_id para seguimiento
        
        Body (opcional):
        {
            "clasificaciones_seleccionadas": [1, 2, 3]  // IDs de clasificaciones específicas
        }
        
        Tipos de incidencias detectadas:
        - Variaciones de conceptos >±30%
        - Ausentismos continuos entre períodos
        - Ingresos del período anterior que faltan
        - Finiquitos del período anterior que persisten
        
        Estados permitidos para generación:
        - datos_consolidados
        - con_incidencias (regeneración)
        - incidencias_resueltas (regeneración)
        
        Returns:
            202: Generación iniciada exitosamente con task_id
            400: Estado inválido o datos consolidados faltantes
            404: Cierre no encontrado
            500: Error interno
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from .tasks_refactored.incidencias import generar_incidencias_con_logging
        
        # 1. OBTENER CIERRE
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Cierre con ID {cierre_id} no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        estado_anterior = cierre.estado
        
        # 2. VERIFICAR ESTADO VÁLIDO PARA GENERACIÓN DE INCIDENCIAS
        estados_permitidos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas']
        if cierre.estado not in estados_permitidos:
            return Response({
                "success": False,
                "error": (
                    "El cierre debe estar en estado 'datos_consolidados', 'con_incidencias' "
                    "o 'incidencias_resueltas' para generar incidencias"
                ),
                "estado_actual": cierre.estado,
                "estados_permitidos": estados_permitidos
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 3. VERIFICAR QUE EXISTAN DATOS CONSOLIDADOS
        total_consolidados = cierre.nomina_consolidada.count()
        if total_consolidados == 0:
            return Response({
                "success": False,
                "error": "No se encontraron datos consolidados para este cierre. Ejecute la consolidación primero.",
                "total_consolidados": total_consolidados
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 4. OBTENER CLASIFICACIONES SELECCIONADAS (OPCIONAL)
        clasificaciones_seleccionadas = request.data.get('clasificaciones_seleccionadas', None)
        
        # Validar que sea una lista si se proporciona
        if clasificaciones_seleccionadas is not None and not isinstance(clasificaciones_seleccionadas, list):
            return Response({
                "success": False,
                "error": "clasificaciones_seleccionadas debe ser una lista de IDs"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 5. LANZAR TAREA CELERY DE GENERACIÓN DE INCIDENCIAS
            logger.info(f"🔍 Lanzando generación de incidencias para cierre {cierre.id}")
            
            task = generar_incidencias_con_logging.delay(
                cierre_id=cierre.id,
                usuario_id=request.user.id,
                clasificaciones_seleccionadas=clasificaciones_seleccionadas
            )
            
            # 6. REGISTRAR INICIO DE LA ACTIVIDAD (Log de UI - usuario visible)
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="process_start",  # ✅ Acción válida existente (max 25 chars)
                descripcion=f"Iniciando generación de incidencias de nómina (comparación con período anterior)",
                usuario=request.user,
                detalles={
                    "estado_anterior": estado_anterior,
                    "task_id": task.id,
                    "clasificaciones_seleccionadas": clasificaciones_seleccionadas,
                    "total_consolidados": total_consolidados,
                    "modo_procesamiento": "dual_v2" if clasificaciones_seleccionadas is None else "filtrado",
                    "tipo_proceso": "generar_incidencias"
                },
                resultado="exito",
                ip_address=get_client_ip(request)
            )
            
            logger.info(f"✅ Generación de incidencias iniciada para cierre {cierre.id} - Task ID: {task.id}")
            
            return Response({
                "success": True,
                "mensaje": "Generación de incidencias iniciada",
                "task_id": task.id,
                "cierre_id": cierre.id,
                "estado_inicial": estado_anterior,
                "modo_procesamiento": "dual_v2" if clasificaciones_seleccionadas is None else "filtrado",
                "clasificaciones_count": len(clasificaciones_seleccionadas) if clasificaciones_seleccionadas else None,
                "datos_disponibles": {
                    "total_consolidados": total_consolidados
                }
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"❌ Error iniciando generación de incidencias para cierre {cierre_id}: {e}")
            
            # REGISTRAR ERROR EN LOG DE ACTIVIDAD
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="generar_incidencias_error",
                descripcion=f"Error al intentar iniciar generación de incidencias",
                usuario=request.user,
                detalles={
                    "estado_cierre": estado_anterior,
                    "error": str(e),
                    "tipo_error": type(e).__name__
                },
                resultado="error",
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": False,
                "error": f"Error interno al iniciar generación de incidencias: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='(?P<cierre_id>[^/.]+)/estado')
    def estado_generacion(self, request, cierre_id=None):
        """
        GET /nomina/incidencias-v2/{cierre_id}/estado/
        
        Consulta el estado actual de la generación de incidencias de un cierre.
        
        Returns:
            200: Estado de generación con detalles
            404: Cierre no encontrado
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Cierre con ID {cierre_id} no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener información de incidencias
        total_incidencias = cierre.incidencias.count()
        incidencias_pendientes = cierre.incidencias.filter(estado='pendiente').count()
        incidencias_resueltas = cierre.incidencias.filter(estado='resuelto').count()
        incidencias_criticas = cierre.incidencias.filter(prioridad='alta').count()
        
        return Response({
            "cierre_id": cierre.id,
            "estado": cierre.estado,
            "estado_incidencias": getattr(cierre, 'estado_incidencias', None),
            "generacion_completada": cierre.estado in ['con_incidencias', 'incidencias_resueltas', 'finalizado'],
            "total_incidencias": total_incidencias,
            "incidencias_pendientes": incidencias_pendientes,
            "incidencias_resueltas": incidencias_resueltas,
            "incidencias_criticas": incidencias_criticas,
            "datos_consolidados_disponibles": cierre.nomina_consolidada.exists()
        })
    
    @action(detail=False, methods=['get'], url_path='(?P<cierre_id>[^/.]+)/resumen')
    def resumen_incidencias(self, request, cierre_id=None):
        """
        GET /nomina/incidencias-v2/{cierre_id}/resumen/
        
        Obtiene un resumen estadístico de las incidencias generadas.
        
        Returns:
            200: Resumen con estadísticas por tipo, prioridad y estado
            404: Cierre no encontrado
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Cierre con ID {cierre_id} no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        from django.db.models import Count
        
        # Estadísticas por tipo de comparación
        por_tipo = cierre.incidencias.values('tipo_comparacion').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas por prioridad
        por_prioridad = cierre.incidencias.values('prioridad').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas por estado
        por_estado = cierre.incidencias.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')
        
        return Response({
            "cierre_id": cierre.id,
            "total_incidencias": cierre.incidencias.count(),
            "por_tipo": list(por_tipo),
            "por_prioridad": list(por_prioridad),
            "por_estado": list(por_estado),
            "fecha_generacion": cierre.updated_at
        })
