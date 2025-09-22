from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.utils import timezone
import logging

from .models import (
    CierreNomina,
    ConceptoConsolidado,
    IncidenciaCierre,
    ResolucionIncidencia,
    TipoIncidencia,
)
from .serializers import (
    ResolucionIncidenciaSerializer,
    CrearResolucionSerializer,
    IncidenciaCierreSerializer,
)
from .views_resumen_libro import libro_resumen_v2

UMBRAL_PCT = 30.0  # Variación mínima absoluta en porcentaje


def _obtener_conceptos_por_cierre(cierre_id: int):
    """Devuelve dict {nombre_concepto: monto_total_float} para un cierre"""
    from django.db.models import Sum, Value, DecimalField
    from django.db.models.functions import Coalesce

    qs = (
        ConceptoConsolidado.objects
        .filter(nomina_consolidada__cierre_id=cierre_id)
        .values('nombre_concepto')
        .annotate(
            total=Coalesce(
                Sum('monto_total'),
                Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
            )
        )
    )
    return {r['nombre_concepto']: float(r['total']) for r in qs}


def _buscar_cierre_anterior(cierre: CierreNomina):
    return (CierreNomina.objects
            .filter(cliente=cierre.cliente, periodo__lt=cierre.periodo, estado__in=['finalizado', 'incidencias_resueltas'])
            .order_by('-periodo')
            .first())


def _obtener_clasificacion_concepto(nombre_concepto: str, cierre_id: int):
    """Obtiene la clasificación de un concepto basado en los datos consolidados del cierre"""
    try:
        concepto = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre_id=cierre_id,
            nombre_concepto=nombre_concepto
        ).first()
        
        if concepto and concepto.tipo_concepto:
            # Mapear el tipo_concepto interno a las clasificaciones que usa el frontend
            mapeo_clasificaciones = {
                'haber_imponible': 'haberes_imponibles',
                'haber_no_imponible': 'haberes_no_imponibles', 
                'descuento_legal': 'descuentos_legales',
                'otro_descuento': 'otros_descuentos',
                'aporte_patronal': 'aportes_patronales',
                'impuesto': 'impuestos',
                'informativo': 'informacion_adicional'
            }
            return mapeo_clasificaciones.get(concepto.tipo_concepto, 'otros_descuentos')
        
        # Si no se encuentra, intentar clasificar por nombre del concepto (fallback básico)
        nombre_lower = nombre_concepto.lower()
        if any(palabra in nombre_lower for palabra in ['sueldo', 'asignacion', 'bono', 'gratificacion']):
            return 'haberes_imponibles'
        elif any(palabra in nombre_lower for palabra in ['anticipo', 'descuento', 'prestamo']):
            return 'otros_descuentos'
        elif any(palabra in nombre_lower for palabra in ['seguro', 'prevision', 'salud']):
            return 'descuentos_legales'
        else:
            return 'otros_descuentos'  # Clasificación por defecto
            
    except Exception:
        return 'otros_descuentos'  # Fallback seguro


def _obtener_usuario_analista_por_defecto():
    """
    Obtiene un usuario analista por defecto para asignar incidencias automáticamente.
    NOTA: Se prefiere usar request.user cuando esté disponible.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Buscar usuarios que no sean staff (analistas)
    analista = User.objects.filter(
        is_active=True,
        is_staff=False
    ).first()
    
    return analista

# ============================================================================
# ViewSets para Gestión de Resoluciones de Incidencias
# ============================================================================

logger = logging.getLogger(__name__)

class ResolucionIncidenciaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar resoluciones de incidencias"""
    queryset = ResolucionIncidencia.objects.all()
    serializer_class = ResolucionIncidenciaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        incidencia_id = self.request.query_params.get('incidencia')
        usuario_id = self.request.query_params.get('usuario')
        
        if incidencia_id:
            queryset = queryset.filter(incidencia_id=incidencia_id)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
            
        return queryset.select_related('incidencia', 'usuario').order_by('-fecha_resolucion')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearResolucionSerializer
        return ResolucionIncidenciaSerializer
    
    def perform_create(self, serializer):
        """
        Crear una nueva resolución con arquitectura simplificada
        """
        # Con el nuevo serializer, la validación se hace automáticamente
        serializer.save(usuario=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='historial/(?P<incidencia_id>[^/.]+)')
    def historial_incidencia(self, request, incidencia_id=None):
        """Obtiene el historial completo de resoluciones de una incidencia"""
        try:
            incidencia = IncidenciaCierre.objects.get(id=incidencia_id)
        except IncidenciaCierre.DoesNotExist:
            return Response({"error": "Incidencia no encontrada"}, status=404)
        
        resoluciones = ResolucionIncidencia.objects.filter(
            incidencia=incidencia
        ).select_related('usuario').order_by('fecha_resolucion')
        
        serializer = ResolucionIncidenciaSerializer(resoluciones, many=True)
        
        # Información adicional sobre el estado de la conversación
        estado_conversacion = self._obtener_estado_conversacion(incidencia, resoluciones)
        
        return Response({
            "incidencia_id": incidencia_id,
            "resoluciones": serializer.data,
            "total_resoluciones": resoluciones.count(),
            "estado_actual": incidencia.estado,
            "estado_conversacion": estado_conversacion,
            "puede_aprobar": request.user.is_staff or request.user.is_superuser,
            "puede_resolver": True  # Todos pueden agregar comentarios/justificaciones
        })
    
    def _obtener_nombre_usuario(self, usuario):
        """Obtiene el correo del usuario para identificación"""
        return usuario.correo_bdo
    
    def _obtener_estado_conversacion(self, incidencia, resoluciones):
        """Determina el estado de la conversación para la UI"""
        if not resoluciones.exists():
            return {
                "estado": "pendiente_analista",
                "mensaje": "Esperando justificación del analista",
                "accion_siguiente": "El analista debe justificar esta incidencia"
            }
        
        ultima_resolucion = resoluciones.last()
        
        if incidencia.estado == 'resuelta_analista':
            return {
                "estado": "esperando_supervisor",
                "mensaje": "Esperando revisión del supervisor",
                "accion_siguiente": "El supervisor debe aprobar o rechazar la justificación",
                "ultima_accion": f"Justificada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        elif incidencia.estado == 'rechazada_supervisor':
            return {
                "estado": "rechazada",
                "mensaje": "Justificación rechazada por supervisor",
                "accion_siguiente": "El analista debe mejorar la justificación o corregir en Talana",
                "ultima_accion": f"Rechazada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        elif incidencia.estado == 'aprobada_supervisor':
            return {
                "estado": "aprobada",
                "mensaje": "Incidencia resuelta y aprobada",
                "accion_siguiente": "No se requieren más acciones",
                "ultima_accion": f"Aprobada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        else:
            return {
                "estado": "en_proceso",
                "mensaje": "Conversación en progreso",
                "accion_siguiente": "Continuar la conversación"
            }
    
    @action(detail=False, methods=['get'], url_path='pendientes-supervisor')
    def pendientes_supervisor(self, request):
        """
        Obtiene incidencias que requieren revisión del supervisor
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden acceder a esta vista"}, status=403)
        
        # Incidencias con justificaciones pendientes de revisión
        incidencias_pendientes = IncidenciaCierre.objects.filter(
            estado='resuelta_analista'
        ).select_related('cierre', 'cierre__cliente').prefetch_related(
            'resoluciones__usuario'
        ).order_by('-fecha_ultima_accion')
        
        data = []
        for incidencia in incidencias_pendientes:
            ultima_resolucion = incidencia.resoluciones.order_by('-fecha_resolucion').first()
            data.append({
                'id': incidencia.id,
                'concepto_nombre': incidencia.concepto_nombre,
                'tipo_incidencia': incidencia.get_tipo_incidencia_display(),
                'descripcion': incidencia.descripcion[:100] + '...' if len(incidencia.descripcion) > 100 else incidencia.descripcion,
                'prioridad': incidencia.prioridad,
                'cierre': {
                    'id': incidencia.cierre.id,
                    'cliente': incidencia.cierre.cliente.nombre,
                    'periodo': incidencia.cierre.periodo
                },
                'ultima_justificacion': {
                    'fecha': ultima_resolucion.fecha_resolucion if ultima_resolucion else None,
                    'usuario': self._obtener_nombre_usuario(ultima_resolucion.usuario) if ultima_resolucion else None,
                    'comentario': ultima_resolucion.comentario[:100] + '...' if ultima_resolucion and len(ultima_resolucion.comentario) > 100 else ultima_resolucion.comentario if ultima_resolucion else None
                },
                'fecha_ultima_accion': incidencia.fecha_ultima_accion,
                'monto_esperado': incidencia.monto_esperado,
                'monto_real': incidencia.monto_real
            })
        
        return Response({
            'incidencias_pendientes': data,
            'total': len(data),
            'resumen': {
                'alta_prioridad': len([i for i in data if i['prioridad'] == 'alta']),
                'media_prioridad': len([i for i in data if i['prioridad'] == 'media']),
                'baja_prioridad': len([i for i in data if i['prioridad'] == 'baja'])
            }
        })
    
    @action(detail=False, methods=['get'], url_path='mis-pendientes')
    def mis_pendientes(self, request):
        """
        Obtiene incidencias asignadas al usuario actual o que requieren su atención
        """
        usuario = request.user
        
        # Si es supervisor, agregar las que esperan su revisión
        from django.db.models import Q
        if usuario.is_staff or usuario.is_superuser:
            todas = IncidenciaCierre.objects.filter(
                Q(asignado_a=usuario, estado__in=['pendiente', 'rechazada_supervisor']) |
                Q(estado='resuelta_analista')
            ).select_related('cierre', 'cierre__cliente').distinct().order_by('-fecha_ultima_accion')
        else:
            # Incidencias asignadas directamente al analista
            todas = IncidenciaCierre.objects.filter(
                asignado_a=usuario,
                estado__in=['pendiente', 'rechazada_supervisor']
            ).select_related('cierre', 'cierre__cliente').order_by('-fecha_ultima_accion')
        
        data = []
        for incidencia in todas:
            estado_para_usuario = self._determinar_estado_para_usuario(incidencia, usuario)
            data.append({
                'id': incidencia.id,
                'concepto_nombre': incidencia.concepto_nombre,
                'tipo_incidencia': incidencia.get_tipo_incidencia_display(),
                'descripcion': incidencia.descripcion,
                'prioridad': incidencia.prioridad,
                'estado_para_usuario': estado_para_usuario,
                'cierre': {
                    'id': incidencia.cierre.id,
                    'cliente': incidencia.cierre.cliente.nombre,
                    'periodo': incidencia.cierre.periodo
                },
                'fecha_ultima_accion': incidencia.fecha_ultima_accion,
                'total_resoluciones': incidencia.resoluciones.count()
            })
        
        return Response({
            'mis_incidencias': data,
            'total': len(data),
            'rol': 'supervisor' if (usuario.is_staff or usuario.is_superuser) else 'analista'
        })
    
    def _determinar_estado_para_usuario(self, incidencia, usuario):
        """Determina qué acción debe tomar el usuario en esta incidencia"""
        if incidencia.estado == 'pendiente' and incidencia.asignado_a == usuario:
            return "requiere_justificacion"
        elif incidencia.estado == 'rechazada_supervisor' and incidencia.asignado_a == usuario:
            return "requiere_mejora_justificacion"
        elif incidencia.estado == 'resuelta_analista' and (usuario.is_staff or usuario.is_superuser):
            return "requiere_revision_supervisor"
        elif incidencia.estado == 'aprobada_supervisor':
            return "aprobada"
        else:
            return "en_proceso"


class IncidenciaCierreViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar incidencias de cierre - Solo funciones CRUD y resolución"""
    queryset = IncidenciaCierre.objects.all()
    serializer_class = IncidenciaCierreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtros opcionales
        cierre_id = self.request.query_params.get('cierre')
        estado = self.request.query_params.get('estado')
        asignado_a = self.request.query_params.get('asignado_a')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if asignado_a:
            queryset = queryset.filter(asignado_a_id=asignado_a)
            
        return queryset.select_related('cierre', 'cierre__cliente', 'asignado_a').order_by('-fecha_detectada')
    
    @action(detail=True, methods=['patch'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado de una incidencia específica"""
        incidencia = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in ['pendiente', 'resuelta_analista', 'aprobada_supervisor', 'rechazada_supervisor']:
            return Response({"error": "Estado inválido"}, status=400)
        
        incidencia.estado = nuevo_estado
        incidencia.fecha_ultima_accion = timezone.now()
        incidencia.save(update_fields=['estado', 'fecha_ultima_accion'])
        
        return Response({"message": "Estado actualizado", "estado": nuevo_estado})
    
    @action(detail=True, methods=['patch'])
    def asignar_usuario(self, request, pk=None):
        """Asignar una incidencia a un usuario específico"""
        incidencia = self.get_object()
        usuario_id = request.data.get('usuario_id')
        
        if usuario_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                usuario = User.objects.get(id=usuario_id)
                incidencia.asignado_a = usuario
                incidencia.save(update_fields=['asignado_a'])
                return Response({"message": "Incidencia asignada correctamente"})
            except User.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=404)
        else:
            incidencia.asignado_a = None
            incidencia.save(update_fields=['asignado_a'])
            return Response({"message": "Asignación removida"})
    
    @action(detail=True, methods=['post'])
    def justificar(self, request, pk=None):
        """Justificar una incidencia como analista"""
        incidencia = self.get_object()
        justificacion = request.data.get('justificacion', '').strip()
        
        if not justificacion:
            return Response({"error": "La justificación es requerida"}, status=400)
        
        try:
            # Crear resolución de justificación
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='justificacion',
                comentario=justificacion,
            )
            
            # Cambiar estado de la incidencia
            incidencia.estado = 'resuelta_analista'
            incidencia.asignado_a = request.user
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'asignado_a', 'fecha_ultima_accion'])
            
            logger.info(f"📝 Incidencia {incidencia.id} justificada por {request.user.correo_bdo}")
            
            return Response({
                "message": "Incidencia justificada correctamente",
                "estado": incidencia.estado,
                "fecha_justificacion": incidencia.fecha_ultima_accion,
                "resolucion_id": resolucion.id
            })
            
        except Exception as e:
            logger.error(f"Error justificando incidencia {pk}: {e}")
            return Response({"error": f"Error justificando incidencia: {str(e)}"}, status=500)
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprobar una incidencia como supervisor"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        # Verificar permisos de supervisor
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden aprobar incidencias"}, status=403)
        
        try:
            # Crear resolución de aprobación
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='aprobacion',
                comentario=comentario or 'Incidencia aprobada',
            )
            
            # Cambiar estado de la incidencia
            incidencia.estado = 'aprobada_supervisor'
            incidencia.asignado_a = request.user
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'asignado_a', 'fecha_ultima_accion'])
            
            logger.info(f"✅ Incidencia {incidencia.id} aprobada por {request.user.correo_bdo}")
            
            return Response({
                "message": "Incidencia aprobada correctamente",
                "estado": incidencia.estado,
                "fecha_aprobacion": incidencia.fecha_ultima_accion,
                "resolucion_id": resolucion.id
            })
            
        except Exception as e:
            logger.error(f"Error aprobando incidencia {pk}: {e}")
            return Response({"error": f"Error aprobando incidencia: {str(e)}"}, status=500)
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechazar una incidencia como supervisor"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        if not comentario:
            return Response({"error": "El comentario es requerido para rechazar"}, status=400)
        
        # Verificar permisos de supervisor
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden rechazar incidencias"}, status=403)
        
        try:
            # Crear resolución de rechazo
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='rechazo_supervisor',
                comentario=comentario,
            )
            
            # Cambiar estado de la incidencia a rechazada
            incidencia.estado = 'rechazada_supervisor'
            incidencia.asignado_a = None  # Liberar asignación para que analista pueda volver a justificar
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'asignado_a', 'fecha_ultima_accion'])
            
            logger.info(f"❌ Incidencia {incidencia.id} rechazada por {request.user.correo_bdo}")
            
            return Response({
                "message": "Incidencia rechazada correctamente",
                "estado": incidencia.estado,
                "fecha_rechazo": incidencia.fecha_ultima_accion,
                "resolucion_id": resolucion.id,
                "motivo": comentario
            })
            
        except Exception as e:
            logger.error(f"Error rechazando incidencia {pk}: {e}")
            return Response({"error": f"Error rechazando incidencia: {str(e)}"}, status=500)
    
    # ============================================================================
    # Métodos para Operaciones a Nivel de Cierre
    # ============================================================================
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cierre_id>[^/.]+)')
    def resumen_incidencias(self, request, cierre_id=None):
        """Obtiene un resumen estadístico de incidencias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Obtener incidencias del cierre
        incidencias = IncidenciaCierre.objects.filter(cierre=cierre)
        
        # Generar resumen
        resumen = {
            'total': incidencias.count(),
            'por_prioridad': {
                'critica': incidencias.filter(prioridad='critica').count(),
                'alta': incidencias.filter(prioridad='alta').count(),
                'media': incidencias.filter(prioridad='media').count(),
                'baja': incidencias.filter(prioridad='baja').count(),
            },
            'por_estado': {
                'pendiente': incidencias.filter(estado='pendiente').count(),
                'resuelta_analista': incidencias.filter(estado='resuelta_analista').count(),
                'aprobada_supervisor': incidencias.filter(estado='aprobada_supervisor').count(),
                'rechazada_supervisor': incidencias.filter(estado='rechazada_supervisor').count(),
            },
            'impacto_monetario_total': sum(
                inc.impacto_monetario for inc in incidencias 
                if inc.impacto_monetario
            ) or 0
        }
        
        return Response(resumen)
    
    @action(detail=False, methods=['get'], url_path='estado-cierre/(?P<cierre_id>[^/.]+)')
    def estado_incidencias_cierre(self, request, cierre_id=None):
        """Obtiene el estado de incidencias de un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(pk=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        incidencias = cierre.incidencias.all()
        
        # Estadísticas por estado
        estados = {}
        for incidencia in incidencias:
            estado = incidencia.estado
            estados[estado] = estados.get(estado, 0) + 1
        
        # Estadísticas por prioridad
        prioridades = {}
        for incidencia in incidencias:
            prioridad = incidencia.prioridad
            prioridades[prioridad] = prioridades.get(prioridad, 0) + 1
        
        return Response({
            'cierre_id': cierre_id,
            'total_incidencias': incidencias.count(),
            'estados': estados,
            'prioridades': prioridades,
            'puede_finalizar': all(inc.estado == 'aprobada_supervisor' for inc in incidencias),
            'progreso': {
                'aprobadas': estados.get('aprobada_supervisor', 0),
                'pendientes': estados.get('pendiente', 0) + estados.get('resuelta_analista', 0),
                'rechazadas': estados.get('rechazada_supervisor', 0)
            }
        })
    
    @action(detail=False, methods=['post'], url_path='solicitar-recarga/(?P<cierre_id>[^/.]+)')
    def solicitar_recarga_archivos(self, request, cierre_id=None):
        """
        Permite solicitar la recarga de archivos cuando hay incidencias
        que requieren corrección en Talana
        """
        try:
            cierre = CierreNomina.objects.get(pk=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que existan incidencias rechazadas o que justifiquen la recarga
        incidencias_rechazadas = cierre.incidencias.filter(
            resoluciones__tipo_resolucion='rechazo_supervisor'
        ).distinct().count()
        
        if incidencias_rechazadas == 0:
            return Response({
                "error": "No hay incidencias rechazadas que justifiquen recargar archivos"
            }, status=400)
        
        motivo = request.data.get('motivo', '')
        if not motivo:
            return Response({"error": "Debe proporcionar un motivo para la recarga"}, status=400)
        
        # Cambiar estado del cierre para permitir recarga
        cierre.estado = 'requiere_recarga_archivos'
        if hasattr(cierre, 'observaciones_recarga'):
            cierre.observaciones_recarga = f"Solicitado por {request.user.correo_bdo}: {motivo}"
        if hasattr(cierre, 'fecha_solicitud_recarga'):
            cierre.fecha_solicitud_recarga = timezone.now()
        cierre.save()
        
        logger.info(f"🔄 Recarga de archivos solicitada para cierre {cierre_id} por {request.user.correo_bdo}: {motivo}")
        
        return Response({
            "mensaje": "Solicitud de recarga de archivos registrada",
            "cierre_id": cierre_id,
            "nuevo_estado": cierre.estado,
            "motivo": motivo,
            "incidencias_rechazadas": incidencias_rechazadas,
            "instrucciones": [
                "1. Corregir los datos en Talana según las incidencias rechazadas",
                "2. Volver a subir los archivos corregidos (Libro, Movimientos, etc.)",
                "3. El sistema re-consolidará automáticamente los datos",
                "4. Se generarán nuevas incidencias basadas en los datos actualizados"
            ]
        })
    
    @action(detail=False, methods=['post'], url_path='aprobar-masivo/(?P<cierre_id>[^/.]+)')
    def aprobar_todas_pendientes(self, request, cierre_id=None):
        """
        Acción masiva para que un supervisor marque todas las incidencias
        pendientes como aprobadas (para casos donde el analista ha explicado todo correctamente)
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({
                "error": "Solo supervisores pueden realizar aprobaciones masivas"
            }, status=403)
        
        try:
            cierre = CierreNomina.objects.get(pk=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Obtener incidencias que están esperando revisión del supervisor
        incidencias_pendientes = cierre.incidencias.filter(
            estado='resuelta_analista'
        )
        
        if not incidencias_pendientes.exists():
            return Response({
                "error": "No hay incidencias pendientes de aprobación"
            }, status=400)
        
        comentario_aprobacion = request.data.get('comentario', 'Aprobación masiva por supervisor')
        
        # Crear resolución de aprobación para cada incidencia
        resoluciones_creadas = []
        for incidencia in incidencias_pendientes:
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='aprobacion',
                comentario=comentario_aprobacion,
            )
            
            # Actualizar estado de la incidencia
            incidencia.estado = 'aprobada_supervisor'
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'fecha_ultima_accion'])
            
            resoluciones_creadas.append(resolucion)
        
        # Verificar si todas las incidencias están aprobadas
        incidencias_restantes = cierre.incidencias.exclude(estado='aprobada_supervisor').count()
        
        if incidencias_restantes == 0:
            # Todas las incidencias están resueltas
            cierre.estado = 'incidencias_resueltas'
            if hasattr(cierre, 'estado_incidencias'):
                cierre.estado_incidencias = 'resueltas'
            cierre.save()
        
        logger.info(f"✅ Aprobación masiva realizada por {request.user.correo_bdo} en cierre {cierre_id}: {len(resoluciones_creadas)} incidencias aprobadas")
        
        return Response({
            "mensaje": f"{len(resoluciones_creadas)} incidencias aprobadas exitosamente",
            "incidencias_aprobadas": len(resoluciones_creadas),
            "incidencias_restantes": incidencias_restantes,
            "cierre_completado": incidencias_restantes == 0,
            "nuevo_estado_cierre": cierre.estado
        })
    
    def totales_variacion(self, request, cierre_id=None):
        """🔎 Genera y PERSISTE incidencias de tipo suma_total SOLO para variaciones (>= ±30%).

        Diseño simplificado:
            1. Usa `libro_resumen_v2` para obtener totales actuales por concepto.
            2. Obtiene totales del cierre anterior finalizado / incidencias_resueltas.
            3. Detecta únicamente variaciones con |Δ%| >= 30 (IGNORA nuevos y eliminados).
            4. Elimina incidencias anteriores de tipo_comparacion = 'suma_total' del cierre.
            5. Inserta nuevas filas en `IncidenciaCierre` (solo VARIACION_SUMA_TOTAL).
            6. Actualiza campos de estado mínimos del cierre (`total_incidencias`, `estado_incidencias`, `estado`).

        Idempotencia básica: al ejecutar nuevamente se reemplaza el conjunto previo
        de incidencias suma_total (no afecta otros tipos).

        Request: POST (sin body necesario) | GET (modo compat: ejecuta igual)
        Response: JSON con resumen y lista de incidencias persistidas.
        """
        from nomina.views_resumen_libro import libro_resumen_v2
        from nomina.models import TipoIncidencia
        import math
        
        UMBRAL_PCT = 30.0
        
        cierre = get_object_or_404(CierreNomina, pk=cierre_id)
        cierre_anterior = _buscar_cierre_anterior(cierre)

        # Obtener datos actuales reutilizando view existente (sin duplicar lógica)
        # Invocamos directamente la función y tomamos su data
        resumen_response = libro_resumen_v2(request._request if hasattr(request, '_request') else request, cierre_id)
        if resumen_response.status_code != 200:
            return resumen_response
        resumen_data = resumen_response.data

        conceptos_actuales = {c['nombre']: c['total'] for c in resumen_data.get('conceptos', [])}

        if not cierre_anterior:
            # No hay cierre anterior -> limpiar incidencias suma_total y marcar resueltas
            IncidenciaCierre.objects.filter(cierre=cierre, tipo_comparacion='suma_total').delete()
            cierre.total_incidencias = 0
            cierre.estado_incidencias = 'resueltas'
            if cierre.estado == 'datos_consolidados':
                cierre.estado = 'incidencias_resueltas'
            cierre.save(update_fields=['total_incidencias', 'estado_incidencias', 'estado'])
            return Response({
                'cierre_actual': cierre.periodo,
                'cierre_anterior': None,
                'parametros': {'umbral_pct': UMBRAL_PCT},
                'incidencias': [],
                'mensaje': 'No existe cierre anterior finalizado para comparar. Se considera sin incidencias.'
            }, status=200)

        # Construir montos del cierre anterior (consulta directa)
        conceptos_prev = _obtener_conceptos_por_cierre(cierre_anterior.id)

        claves_actual = set(conceptos_actuales.keys())
        claves_prev = set(conceptos_prev.keys())

        # Solo consideramos conceptos presentes en ambos cierres para evaluar variación
        comunes = (set(conceptos_actuales.keys()) & set(conceptos_prev.keys()))

        incidencias = []  # para respuesta
        incidencias_bulk = []  # para persistencia

        # (Se ignoran conceptos nuevos y eliminados según requerimiento actual)

        # Variaciones significativas
        usuario_asignado = request.user  # El usuario que genera las incidencias se asigna automáticamente
        
        for nombre in comunes:
            monto_act = conceptos_actuales.get(nombre, 0.0) or 0.0
            monto_prev = conceptos_prev.get(nombre, 0.0) or 0.0
            if math.isclose(monto_prev, 0.0):
                continue  # ya cubierto como nuevo / eliminado si corresponde
            delta_abs = monto_act - monto_prev
            delta_pct = (delta_abs / monto_prev) * 100.0 if monto_prev else 0.0
            if abs(delta_pct) >= UMBRAL_PCT:
                # Obtener clasificación del concepto
                clasificacion = _obtener_clasificacion_concepto(nombre, cierre_id)
                
                incidencias.append({
                    'concepto': nombre,
                    'monto_actual': monto_act,
                    'monto_anterior': monto_prev,
                    'delta_abs': delta_abs,
                    'delta_pct': delta_pct,
                    'tipo': 'variacion',
                    'clasificacion': clasificacion
                })
                incidencias_bulk.append(IncidenciaCierre(
                    cierre=cierre,
                    tipo_incidencia=TipoIncidencia.VARIACION_SUMA_TOTAL,
                    tipo_comparacion='suma_total',
                    descripcion=f"Variación {delta_pct:.1f}% en {nombre} (Δ ${delta_abs:,.0f})",
                    concepto_afectado=nombre,
                    clasificacion_concepto=clasificacion,  # ✅ Agregado
                    asignado_a=usuario_asignado,  # ✅ Agregado
                    prioridad='alta' if abs(delta_abs) > 500000 else 'media',
                    impacto_monetario=abs(delta_abs),
                    datos_adicionales={
                        'monto_anterior': monto_prev,
                        'monto_actual': monto_act,
                        'delta_abs': delta_abs,
                        'delta_pct': delta_pct,
                        'umbral_pct': UMBRAL_PCT,
                        'tipo_concepto': clasificacion,  # También aquí para compatibilidad
                        'tipo_comparacion': 'suma_total'
                    }
                ))

        # Persistencia: limpiar anteriores tipo suma_total y crear nuevas
        IncidenciaCierre.objects.filter(cierre=cierre, tipo_comparacion='suma_total').delete()
        if incidencias_bulk:
            IncidenciaCierre.objects.bulk_create(incidencias_bulk)

        total = len(incidencias_bulk)
        # Actualizar estado del cierre (mínimo viable)
        cierre.total_incidencias = total
        if total > 0:
            cierre.estado_incidencias = 'detectadas'
            if cierre.estado == 'datos_consolidados':
                cierre.estado = 'con_incidencias'
        else:
            cierre.estado_incidencias = 'resueltas'
            if cierre.estado == 'datos_consolidados':
                cierre.estado = 'incidencias_resueltas'
        cierre.save(update_fields=['total_incidencias', 'estado_incidencias', 'estado'])

        incidencias.sort(key=lambda x: abs(x['delta_abs']), reverse=True)

        return Response({
            'cierre_actual': cierre.periodo,
            'cierre_anterior': cierre_anterior.periodo,
            'parametros': {
                'umbral_pct': UMBRAL_PCT,
                'generado_en': timezone.now().isoformat(),
                'total_conceptos_actual': len(conceptos_actuales),
                'total_conceptos_anterior': len(conceptos_prev),
            },
            'estadisticas': {
                'variaciones': len([i for i in incidencias if i['tipo'] == 'variacion']),
                'total_incidencias': total
            },
            'incidencias': incidencias
        }, status=status.HTTP_200_OK)
    
    def limpiar_incidencias(self, request, cierre_id=None):
        """
        🗑️ ENDPOINT: Limpiar incidencias de un cierre (función de debug)
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            incidencias_borradas = IncidenciaCierre.objects.filter(cierre=cierre).count()
            IncidenciaCierre.objects.filter(cierre=cierre).delete()
            
            # Resetear estado de incidencias
            cierre.estado_incidencias = 'pendiente'
            cierre.total_incidencias = 0
            cierre.save(update_fields=['estado_incidencias', 'total_incidencias'])
            
            return Response({
                "message": f"✅ {incidencias_borradas} incidencias limpiadas del cierre {cierre_id}",
                "incidencias_borradas": incidencias_borradas,
                "nuevo_estado": cierre.estado_incidencias
            }, status=200)
            
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": f"Error limpiando incidencias: {str(e)}"}, status=500)
