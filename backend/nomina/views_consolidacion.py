"""
🔄 CONSOLIDACIÓN DE DATOS - VIEWS
==================================

ViewSet dedicado a la consolidación de datos de nómina.

Refactorizado desde: views.py (CierreNominaViewSet.consolidar_datos)
Versión: 2.5.0
Fecha: 2025-10-20

Funcionalidades:
- Consolidar datos del cierre (Libro + Movimientos + Analista)
- Validación de estados y archivos
- Lanzamiento de tareas Celery con dual logging
- Consulta de estado de consolidación
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import CierreNomina
from .serializers import CierreNominaSerializer
from .permissions import SupervisorPuedeVerCierresNominaAnalistas
from .models_logging import registrar_actividad_tarjeta_nomina  # ✅ IMPORTACIÓN GLOBAL
from .utils.clientes import get_client_ip
from .tasks_refactored.consolidacion import consolidar_datos_nomina_con_logging

logger = logging.getLogger(__name__)


class ConsolidacionDatosViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar la consolidación de datos de nómina.
    
    Endpoints:
    - POST /consolidacion/{cierre_id}/consolidar/ - Iniciar consolidación
    - GET /consolidacion/{cierre_id}/estado/ - Consultar estado de consolidación
    """
    
    permission_classes = [IsAuthenticated, SupervisorPuedeVerCierresNominaAnalistas]
    
    @action(detail=False, methods=['post'], url_path='(?P<cierre_id>[^/.]+)/consolidar')
    def consolidar_datos(self, request, cierre_id=None):
        """
        🔄 CONSOLIDAR DATOS DE NÓMINA
        
        POST /nomina/consolidacion/{cierre_id}/consolidar/
        
        Ejecuta la consolidación de datos del cierre de forma asíncrona:
        1. Valida estado permitido para consolidación
        2. Valida que existan archivos procesados (Libro + Movimientos)
        3. Lanza tarea Celery de consolidación con logging dual
        4. Retorna inmediatamente con task_id para seguimiento
        
        Body (opcional):
        {
            "modo": "optimizado"  // o "secuencial"
        }
        
        Estados permitidos para consolidación:
        - verificado_sin_discrepancias
        - datos_consolidados (reconsolidación)
        - con_incidencias (consolidación con incidencias pendientes)
        
        Returns:
            202: Consolidación iniciada exitosamente con task_id
            400: Estado inválido o archivos faltantes
            404: Cierre no encontrado
            500: Error interno
        """
        # ✅ Importaciones ya están a nivel global del módulo
        
        # 1. OBTENER CIERRE
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Cierre con ID {cierre_id} no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        estado_anterior = cierre.estado
        
        # 2. VERIFICAR ESTADO VÁLIDO PARA CONSOLIDACIÓN
        estados_permitidos = ['verificado_sin_discrepancias', 'datos_consolidados', 'con_incidencias']
        if cierre.estado not in estados_permitidos:
            return Response({
                "success": False,
                "error": (
                    "El cierre debe estar en estado 'verificado_sin_discrepancias', "
                    "'datos_consolidados' o 'con_incidencias' para consolidar datos. "
                    f"Estado actual: {cierre.estado}"
                ),
                "estado_actual": cierre.estado,
                "estados_permitidos": estados_permitidos
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 3. VERIFICAR QUE HAY ARCHIVOS PROCESADOS
            libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
            movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
            
            if not libro:
                return Response({
                    "success": False,
                    "error": "No hay libro de remuneraciones procesado disponible",
                    "archivos_faltantes": ["libro_remuneraciones"]
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not movimientos:
                return Response({
                    "success": False,
                    "error": "No hay archivo de movimientos procesado disponible",
                    "archivos_faltantes": ["movimientos_mes"]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. OBTENER MODO DE CONSOLIDACIÓN
            # Por defecto usa modo 'optimizado' con Celery Chord para mejor rendimiento
            modo_consolidacion = request.data.get('modo', 'optimizado')
            
            if modo_consolidacion not in ['optimizado', 'secuencial']:
                return Response({
                    "success": False,
                    "error": f"Modo de consolidación inválido: {modo_consolidacion}",
                    "modos_permitidos": ["optimizado", "secuencial"]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 5. LANZAR TAREA ASÍNCRONA DE CONSOLIDACIÓN CON LOGGING DUAL
            task = consolidar_datos_nomina_con_logging.delay(
                cierre_id=cierre.id,
                usuario_id=request.user.id,
                modo=modo_consolidacion
            )
            
            # 6. REGISTRAR INICIO DE LA ACTIVIDAD (Log de UI - usuario visible)
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="consolidacion",
                accion="consolidar_datos_inicio",
                descripcion=f"Iniciando consolidación de datos de nómina (modo: {modo_consolidacion})",
                usuario=request.user,
                detalles={
                    "estado_anterior": estado_anterior,
                    "task_id": task.id,
                    "modo": modo_consolidacion,
                    "archivos_disponibles": {
                        "libro": libro.archivo.name,
                        "movimientos": movimientos.archivo.name
                    }
                },
                resultado="exito",
                ip_address=get_client_ip(request)
            )
            
            logger.info(f"✅ Consolidación iniciada para cierre {cierre.id} - Task ID: {task.id}")
            
            return Response({
                "success": True,
                "mensaje": "Consolidación de datos iniciada",
                "task_id": task.id,
                "cierre_id": cierre.id,
                "estado_inicial": estado_anterior,
                "modo_consolidacion": modo_consolidacion,
                "archivos_procesados": {
                    "libro_remuneraciones": libro.archivo.name,
                    "movimientos_mes": movimientos.archivo.name
                }
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"❌ Error iniciando consolidación para cierre {cierre_id}: {e}")
            
            # REGISTRAR ERROR EN LOG DE ACTIVIDAD
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="consolidacion",
                accion="consolidar_datos_error",
                descripcion=f"Error al intentar iniciar consolidación de datos",
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
                "error": f"Error interno al iniciar consolidación: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='(?P<cierre_id>[^/.]+)/estado')
    def estado_consolidacion(self, request, cierre_id=None):
        """
        GET /nomina/consolidacion/{cierre_id}/estado/
        
        Consulta el estado actual de la consolidación de un cierre.
        
        Returns:
            200: Estado de consolidación con detalles
            404: Cierre no encontrado
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Cierre con ID {cierre_id} no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener información de consolidación
        total_consolidados = cierre.nomina_consolidada.count()
        
        return Response({
            "cierre_id": cierre.id,
            "estado": cierre.estado,
            "estado_consolidacion": getattr(cierre, 'estado_consolidacion', None),
            "consolidacion_completada": cierre.estado in ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'finalizado'],
            "total_registros_consolidados": total_consolidados,
            "puede_consolidar": cierre.puede_consolidar if hasattr(cierre, 'puede_consolidar') else None,
            "archivos_procesados": {
                "libro_remuneraciones": cierre.libros_remuneraciones.filter(estado='procesado').exists(),
                "movimientos_mes": cierre.movimientos_mes.filter(estado='procesado').exists(),
                "archivos_analista": cierre.archivos_analista.filter(estado='procesado').count()
            }
        })
