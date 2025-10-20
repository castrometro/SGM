# backend/nomina/views_discrepancias.py
"""
ViewSets para el Sistema de Verificación de Datos y Discrepancias

Este módulo contiene los endpoints para:
1. Gestión de discrepancias detectadas (CRUD)
2. Generación y verificación de discrepancias
3. Estados y resúmenes de verificación

Extraído del views.py monolítico para mejor organización.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import CierreNomina, DiscrepanciaCierre
from .serializers import DiscrepanciaCierreSerializer, ResumenDiscrepanciasSerializer

# ✅ Importar tarea refactorizada con logging
from .tasks_refactored.discrepancias import generar_discrepancias_cierre_con_logging

logger = logging.getLogger(__name__)


class DiscrepanciaCierreViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar discrepancias de verificación de datos
    
    Endpoints:
    - GET /discrepancias/ - Lista de discrepancias (con filtros)
    - POST /discrepancias/generar/{cierre_id}/ - Genera discrepancias para un cierre
    - GET /discrepancias/resumen/{cierre_id}/ - Resumen estadístico
    - GET /discrepancias/estado/{cierre_id}/ - Estado actual de verificación
    - DELETE /discrepancias/limpiar/{cierre_id}/ - Limpia discrepancias
    """
    queryset = DiscrepanciaCierre.objects.all()
    serializer_class = DiscrepanciaCierreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtra discrepancias según parámetros de query
        
        Filtros disponibles:
        - cierre: ID del cierre
        - tipo: Tipo de discrepancia
        - rut: RUT del empleado (parcial)
        - grupo: libro_vs_novedades / movimientos_vs_analista
        """
        queryset = super().get_queryset()
        
        # Filtros disponibles
        cierre_id = self.request.query_params.get('cierre')
        tipo_discrepancia = self.request.query_params.get('tipo')
        rut_empleado = self.request.query_params.get('rut')
        grupo = self.request.query_params.get('grupo')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_discrepancia:
            queryset = queryset.filter(tipo_discrepancia=tipo_discrepancia)
        if rut_empleado:
            queryset = queryset.filter(rut_empleado__icontains=rut_empleado)
        if grupo:
            # Filtrar por grupo de discrepancias
            libro_vs_novedades = [
                'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
                'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
            ]
            if grupo == 'libro_vs_novedades':
                queryset = queryset.filter(tipo_discrepancia__in=libro_vs_novedades)
            elif grupo == 'movimientos_vs_analista':
                queryset = queryset.exclude(tipo_discrepancia__in=libro_vs_novedades)
            
        return queryset.select_related('cierre').order_by('-fecha_detectada')
    
    @action(detail=False, methods=['post'], url_path='generar/(?P<cierre_id>[^/.]+)')
    def generar_discrepancias(self, request, cierre_id=None):
        """
        🚀 ENDPOINT REFACTORIZADO: Generar discrepancias con logging dual
        
        POST /nomina/discrepancias/generar/{cierre_id}/
        
        Ejecuta la verificación de consistencia de datos usando tarea Celery refactorizada.
        Implementa logging dual (TarjetaActivityLogNomina + ActivityEvent).
        
        Estados permitidos: 'datos_consolidados', 'discrepancias_detectadas'
        
        Returns:
            202: Tarea iniciada exitosamente con task_id para polling
            400: Estado del cierre no permite verificación
            401: Usuario no autenticado
            404: Cierre no encontrado
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar que el cierre esté en estado adecuado
        # Permitimos: archivos_completos, verificacion_datos, con_discrepancias, datos_consolidados, discrepancias_detectadas
        estados_permitidos = [
            'archivos_completos', 
            'verificacion_datos', 
            'con_discrepancias',
            'datos_consolidados', 
            'discrepancias_detectadas'
        ]
        if cierre.estado not in estados_permitidos:
            return Response({
                "error": f"El cierre debe estar en un estado válido para generar discrepancias. Estado actual: '{cierre.estado}'. Estados permitidos: {', '.join(estados_permitidos)}"
            }, status=400)
        
        # Log para debugging
        logger.info(f"🚀 Generando discrepancias para cierre {cierre_id}")
        
        # Obtener el usuario que ejecuta la verificación
        usuario_id = request.user.id if request.user.is_authenticated else None
        logger.info(
            f"👤 Usuario ejecutor: {request.user.correo_bdo} (ID: {usuario_id})" 
            if usuario_id else "👤 Usuario ejecutor: Anónimo"
        )
        
        # ✅ REFACTORIZADO: Usar tarea con logging dual
        task = generar_discrepancias_cierre_con_logging.delay(cierre_id, usuario_id)
        
        return Response({
            "message": "Verificación de datos iniciada",
            "task_id": task.id,
            "cierre_id": cierre_id,
            "usuario_ejecutor": request.user.correo_bdo if request.user.is_authenticated else "Anónimo"
        }, status=202)
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cierre_id>[^/.]+)')
    def resumen_discrepancias(self, request, cierre_id=None):
        """
        GET /nomina/discrepancias/resumen/{cierre_id}/
        
        Obtiene un resumen estadístico detallado de discrepancias de un cierre.
        Incluye agrupaciones por tipo, empleados afectados, y otros datos.
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        from .utils.GenerarDiscrepancias import obtener_resumen_discrepancias
        resumen = obtener_resumen_discrepancias(cierre)
        
        serializer = ResumenDiscrepanciasSerializer(resumen)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado_discrepancias(self, request, cierre_id=None):
        """
        GET /nomina/discrepancias/estado/{cierre_id}/
        
        Obtiene el estado actual de discrepancias de un cierre.
        Incluye contadores por grupos y empleados afectados.
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        total_discrepancias = cierre.discrepancias.count()
        
        # Clasificar por grupos
        libro_vs_novedades_tipos = [
            'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
            'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
        ]
        
        total_libro_vs_novedades = cierre.discrepancias.filter(
            tipo_discrepancia__in=libro_vs_novedades_tipos
        ).count()
        total_movimientos_vs_analista = total_discrepancias - total_libro_vs_novedades
        
        return Response({
            "cierre_id": cierre.id,
            "estado_cierre": cierre.estado,
            "tiene_discrepancias": total_discrepancias > 0,
            "total_discrepancias": total_discrepancias,
            "discrepancias_por_grupo": {
                "libro_vs_novedades": total_libro_vs_novedades,
                "movimientos_vs_analista": total_movimientos_vs_analista
            },
            "empleados_afectados": cierre.discrepancias.values('rut_empleado').distinct().count(),
            "fecha_ultima_verificacion": (
                cierre.discrepancias.first().fecha_detectada 
                if total_discrepancias > 0 else None
            )
        })
    
    @action(detail=False, methods=['delete'], url_path='limpiar/(?P<cierre_id>[^/.]+)')
    def limpiar_discrepancias(self, request, cierre_id=None):
        """
        DELETE /nomina/discrepancias/limpiar/{cierre_id}/
        
        Elimina todas las discrepancias de un cierre.
        Útil para re-ejecutar verificación desde cero.
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        count_eliminados = cierre.discrepancias.count()
        cierre.discrepancias.all().delete()
        
        logger.info(
            f"🧹 Limpiadas {count_eliminados} discrepancias del cierre {cierre_id} "
            f"por usuario {request.user.correo_bdo}"
        )
        
        return Response({
            "message": f"Se eliminaron {count_eliminados} discrepancias",
            "cierre_id": cierre_id,
            "discrepancias_eliminadas": count_eliminados
        })


class CierreNominaDiscrepanciasViewSet(viewsets.ViewSet):
    """
    ViewSet adicional para operaciones de verificación de datos en cierres
    
    Este ViewSet maneja el estado de verificación y auto-actualización
    del estado del cierre basado en las discrepancias encontradas.
    
    Endpoints:
    - GET /cierres-discrepancias/{pk}/estado_verificacion/ - Estado con auto-actualización
    """
    
    @action(detail=True, methods=['get'])
    def estado_verificacion(self, request, pk=None):
        """
        GET /nomina/cierres-discrepancias/{pk}/estado_verificacion/
        
        Obtiene el estado de verificación de datos de un cierre.
        
        ⚡ AUTO-ACTUALIZACIÓN: Si hay 0 discrepancias y el estado es 'discrepancias_detectadas',
        automáticamente cambia el estado a 'datos_verificados'.
        
        Si hay discrepancias y el estado es 'datos_consolidados' o 'datos_verificados',
        automáticamente cambia el estado a 'discrepancias_detectadas'.
        
        Returns:
            200: Estado de verificación con mensaje descriptivo
            404: Cierre no encontrado
        """
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        total_discrepancias = cierre.discrepancias.count()
        
        # ⚡ Determinar estado automáticamente
        if total_discrepancias == 0:
            if cierre.estado in ['discrepancias_detectadas']:
                cierre.estado = 'datos_verificados'
                cierre.save(update_fields=['estado'])
                logger.info(
                    f"✅ Auto-actualización: Cierre {pk} cambiado a 'datos_verificados' "
                    f"(0 discrepancias)"
                )
        else:
            if cierre.estado in ['datos_consolidados', 'datos_verificados']:
                cierre.estado = 'discrepancias_detectadas'
                cierre.save(update_fields=['estado'])
                logger.info(
                    f"⚠️ Auto-actualización: Cierre {pk} cambiado a 'discrepancias_detectadas' "
                    f"({total_discrepancias} discrepancias)"
                )
        
        return Response({
            "cierre_id": cierre.id,
            "estado_verificacion": cierre.estado,
            "requiere_correccion": total_discrepancias > 0,
            "total_discrepancias": total_discrepancias,
            "mensaje": (
                "Sin discrepancias - datos verificados" 
                if total_discrepancias == 0 
                else f"Se encontraron {total_discrepancias} discrepancias que requieren corrección"
            ),
            "verificacion_completada": True  # ✅ Siempre True cuando se consulta este endpoint
        })
