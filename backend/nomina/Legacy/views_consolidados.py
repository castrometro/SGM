# backend/nomina/views_consolidados.py

"""
🎯 VISTAS PARA INFORMACIÓN CONSOLIDADA

Endpoints para acceder a la información consolidada después de 
procesar un cierre sin discrepancias.

ENDPOINTS:
- POST /api/nomina/consolidar/{cierre_id}/ - Ejecutar consolidación
- GET /api/nomina/consolidados/{cierre_id}/resumen/ - Resumen ejecutivo
- GET /api/nomina/consolidados/{cierre_id}/nomina/ - Nómina consolidada
- GET /api/nomina/consolidados/{cierre_id}/conceptos/ - Conceptos consolidados
- GET /api/nomina/consolidados/{cierre_id}/movimientos/ - Movimientos de personal
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import CierreNomina, DiscrepanciaCierre
from .models_consolidados import (
    NominaConsolidada,
    ConceptoConsolidado, 
    MovimientoPersonal,
    ResumenCierre
)
from .serializers import CierreNominaSerializer
from .utils.ConsolidarInformacion import consolidar_cierre_completo, obtener_resumen_ejecutivo
from .tasks import consolidar_cierre_task


class CierreConsolidadoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para información consolidada de cierres"""
    serializer_class = CierreNominaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CierreNomina.objects.filter(
            estado_consolidacion='consolidado'
        ).select_related('cliente')

    @action(detail=True, methods=['post'], url_path='consolidar')
    def consolidar_cierre(self, request, pk=None):
        """
        🚀 EJECUTAR CONSOLIDACIÓN DE UN CIERRE
        
        Requisitos:
        - Discrepancias = 0
        - Archivos procesados correctamente
        """
        cierre = get_object_or_404(CierreNomina, pk=pk)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verificar discrepancias
        discrepancias_count = DiscrepanciaCierre.objects.filter(cierre=cierre).count()
        if discrepancias_count > 0:
            return Response({
                "error": "No se puede consolidar",
                "message": f"El cierre tiene {discrepancias_count} discrepancias pendientes",
                "discrepancias_pendientes": discrepancias_count
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya está consolidado
        if cierre.estado_consolidacion == 'consolidado':
            return Response({
                "message": "El cierre ya está consolidado",
                "cierre_id": cierre.id,
                "fecha_consolidacion": cierre.fecha_consolidacion
            }, status=status.HTTP_200_OK)
        
        # Ejecutar consolidación en background
        try:
            # Marcar como consolidando
            cierre.estado_consolidacion = 'consolidando'
            cierre.save(update_fields=['estado_consolidacion'])
            
            # Lanzar task
            task = consolidar_cierre_task.delay(cierre.id, request.user.id if request.user else None)
            
            return Response({
                "message": "Consolidación iniciada",
                "task_id": task.id,
                "cierre_id": cierre.id,
                "estado": "consolidando"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            # Revertir estado en caso de error
            cierre.estado_consolidacion = 'error_consolidacion'
            cierre.save(update_fields=['estado_consolidacion'])
            
            return Response({
                "error": "Error al iniciar consolidación",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen_consolidado(self, request, pk=None):
        """📊 OBTENER RESUMEN EJECUTIVO CONSOLIDADO"""
        cierre = get_object_or_404(CierreNomina, pk=pk)
        
        if cierre.estado_consolidacion != 'consolidado':
            return Response({
                "error": "Cierre no consolidado",
                "estado_actual": cierre.estado_consolidacion,
                "message": "Primero debe ejecutar la consolidación"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            resumen = ResumenCierre.objects.get(cierre=cierre)
            
            data = {
                "cierre": {
                    "id": cierre.id,
                    "cliente": cierre.cliente.nombre,
                    "periodo": cierre.periodo,
                    "fecha_consolidacion": resumen.fecha_consolidacion
                },
                "empleados": {
                    "total_activos": resumen.total_empleados_activos,
                    "incorporaciones": resumen.total_incorporaciones,
                    "finiquitos": resumen.total_finiquitos,
                    "ausencias_completas": resumen.total_ausencias_completas,
                    "ausencias_parciales": resumen.total_ausencias_parciales
                },
                "financiero": {
                    "total_haberes": str(resumen.total_haberes_periodo),
                    "total_descuentos": str(resumen.total_descuentos_periodo),
                    "total_liquido": str(resumen.total_liquido_periodo),
                    "promedio_por_empleado": str(resumen.promedio_liquido_empleado),
                    "liquido_minimo": str(resumen.liquido_minimo),
                    "liquido_maximo": str(resumen.liquido_maximo)
                },
                "conceptos": {
                    "total_conceptos_unicos": resumen.total_conceptos_unicos,
                    "conceptos_haberes": resumen.total_conceptos_haberes,
                    "conceptos_descuentos": resumen.total_conceptos_descuentos
                },
                "comparacion": {
                    "variacion_liquido": str(resumen.variacion_total_liquido) if resumen.variacion_total_liquido else None,
                    "variacion_empleados": resumen.variacion_empleados_activos,
                    "porcentaje_variacion": str(resumen.porcentaje_variacion_liquido) if resumen.porcentaje_variacion_liquido else None
                },
                "metadatos": {
                    "consolidacion_completa": resumen.consolidacion_completa,
                    "discrepancias_resueltas": resumen.discrepancias_resueltas,
                    "tiempo_consolidacion_segundos": resumen.tiempo_consolidacion_segundos
                }
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except ResumenCierre.DoesNotExist:
            return Response({
                "error": "Resumen no encontrado",
                "message": "El cierre está marcado como consolidado pero no tiene resumen generado"
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='nomina')
    def nomina_consolidada(self, request, pk=None):
        """👥 OBTENER NÓMINA CONSOLIDADA COMPLETA"""
        cierre = get_object_or_404(CierreNomina, pk=pk)
        
        if cierre.estado_consolidacion != 'consolidado':
            return Response({
                "error": "Cierre no consolidado",
                "message": "Primero debe ejecutar la consolidación"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros opcionales
        estado_empleado = request.query_params.get('estado', None)
        ordenar_por = request.query_params.get('ordenar', 'nombre_empleado')  # nombre_empleado, liquido_a_pagar
        limite = request.query_params.get('limite', None)
        
        # Consulta base
        nominas = NominaConsolidada.objects.filter(cierre=cierre)
        
        # Aplicar filtros
        if estado_empleado:
            nominas = nominas.filter(estado_empleado=estado_empleado)
        
        # Ordenamiento
        if ordenar_por == 'liquido_a_pagar':
            nominas = nominas.order_by('-liquido_a_pagar', 'nombre_empleado')
        else:
            nominas = nominas.order_by('nombre_empleado')
        
        # Limite
        if limite:
            try:
                limite = int(limite)
                nominas = nominas[:limite]
            except ValueError:
                pass
        
        # Serializar datos
        data = []
        for nomina in nominas:
            data.append({
                "rut_empleado": nomina.rut_empleado,
                "nombre_empleado": nomina.nombre_empleado,
                "cargo": nomina.cargo,
                "centro_costo": nomina.centro_costo,
                "estado_empleado": nomina.get_estado_empleado_display(),
                "estado_codigo": nomina.estado_empleado,
                "totales": {
                    "haberes": str(nomina.total_haberes),
                    "descuentos": str(nomina.total_descuentos),
                    "liquido": str(nomina.liquido_a_pagar)
                },
                "dias_trabajados": nomina.dias_trabajados,
                "dias_ausencia": nomina.dias_ausencia,
                "fecha_consolidacion": nomina.fecha_consolidacion
            })
        
        return Response({
            "cierre": {
                "id": cierre.id,
                "cliente": cierre.cliente.nombre,
                "periodo": cierre.periodo
            },
            "filtros_aplicados": {
                "estado_empleado": estado_empleado,
                "ordenar_por": ordenar_por,
                "limite": limite
            },
            "total_registros": len(data),
            "nomina": data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='conceptos')
    def conceptos_consolidados(self, request, pk=None):
        """💰 OBTENER CONCEPTOS CONSOLIDADOS"""
        cierre = get_object_or_404(CierreNomina, pk=pk)
        
        if cierre.estado_consolidacion != 'consolidado':
            return Response({
                "error": "Cierre no consolidado"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros opcionales
        tipo_concepto = request.query_params.get('tipo', None)
        ordenar_por = request.query_params.get('ordenar', 'monto_total')  # monto_total, nombre_concepto, empleados_afectados
        
        # Consulta
        conceptos = ConceptoConsolidado.objects.filter(cierre=cierre)
        
        if tipo_concepto:
            conceptos = conceptos.filter(tipo_concepto=tipo_concepto)
        
        # Ordenamiento
        if ordenar_por == 'nombre_concepto':
            conceptos = conceptos.order_by('nombre_concepto')
        elif ordenar_por == 'empleados_afectados':
            conceptos = conceptos.order_by('-cantidad_empleados_afectados', 'nombre_concepto')
        else:
            conceptos = conceptos.order_by('-monto_total', 'nombre_concepto')
        
        # Serializar
        data = []
        for concepto in conceptos:
            data.append({
                "codigo_concepto": concepto.codigo_concepto,
                "nombre_concepto": concepto.nombre_concepto,
                "tipo_concepto": concepto.get_tipo_concepto_display(),
                "tipo_codigo": concepto.tipo_concepto,
                "estadisticas": {
                    "empleados_afectados": concepto.cantidad_empleados_afectados,
                    "monto_total": str(concepto.monto_total),
                    "monto_promedio": str(concepto.monto_promedio),
                    "monto_minimo": str(concepto.monto_minimo),
                    "monto_maximo": str(concepto.monto_maximo)
                }
            })
        
        return Response({
            "cierre": {
                "id": cierre.id,
                "cliente": cierre.cliente.nombre,
                "periodo": cierre.periodo
            },
            "total_conceptos": len(data),
            "conceptos": data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='movimientos')
    def movimientos_personal(self, request, pk=None):
        """🔄 OBTENER MOVIMIENTOS DE PERSONAL"""
        cierre = get_object_or_404(CierreNomina, pk=pk)
        
        if cierre.estado_consolidacion != 'consolidado':
            return Response({
                "error": "Cierre no consolidado"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros
        tipo_movimiento = request.query_params.get('tipo', None)
        
        movimientos = MovimientoPersonal.objects.filter(cierre=cierre)
        
        if tipo_movimiento:
            movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)
        
        # Serializar
        data = []
        for mov in movimientos:
            data.append({
                "rut_empleado": mov.rut_empleado,
                "nombre_empleado": mov.nombre_empleado,
                "tipo_movimiento": mov.get_tipo_movimiento_display(),
                "tipo_codigo": mov.tipo_movimiento,
                "motivo": mov.motivo,
                "dias_ausencia": mov.dias_ausencia,
                "fecha_movimiento": mov.fecha_movimiento,
                "impacto_liquido": str(mov.impacto_liquido) if mov.impacto_liquido else None,
                "fecha_deteccion": mov.fecha_deteccion
            })
        
        return Response({
            "cierre": {
                "id": cierre.id,
                "cliente": cierre.cliente.nombre,
                "periodo": cierre.periodo
            },
            "total_movimientos": len(data),
            "movimientos": data
        }, status=status.HTTP_200_OK)
