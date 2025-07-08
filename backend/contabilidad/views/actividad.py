from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import TarjetaActivityLog
from ..serializers import TarjetaActivityLogSerializer
from ..utils.activity_logger import registrar_actividad_tarjeta
from ..utils.clientes import get_client_ip
from .helpers import obtener_periodo_actividad_para_cliente
from api.models import Cliente


class TarjetaActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TarjetaActivityLog.objects.all()
    serializer_class = TarjetaActivityLogSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_actividad_crud(request):
    """
    Endpoint para registrar actividades CRUD desde el frontend
    """
    try:
        cliente_id = request.data.get("cliente_id")
        tarjeta = request.data.get("tarjeta")
        accion = request.data.get("accion")
        descripcion = request.data.get("descripcion")
        detalles = request.data.get("detalles", {})
        cierre_id = request.data.get("cierre_id")
        
        # Validaciones
        if not all([cliente_id, tarjeta, accion, descripcion]):
            return Response({
                "error": "cliente_id, tarjeta, accion y descripcion son requeridos"
            }, status=400)
        
        # Obtener cliente y período
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            if cierre_id:
                # Si se proporciona cierre_id, usarlo directamente
                from ..models import CierreContabilidad
                cierre = CierreContabilidad.objects.get(id=cierre_id)
                periodo = cierre.periodo
            else:
                # Obtener período de actividad actual del cliente
                periodo = obtener_periodo_actividad_para_cliente(cliente)
        except (Cliente.DoesNotExist, CierreContabilidad.DoesNotExist) as e:
            return Response({"error": str(e)}, status=404)
        
        # Registrar actividad
        log_entry = registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=request.user,
            detalles=detalles,
            resultado="exito",
            ip_address=get_client_ip(request)
        )
        
        if log_entry:
            return Response({
                "mensaje": "Actividad registrada exitosamente",
                "log_id": log_entry.id
            })
        else:
            return Response({
                "warning": "No se pudo registrar la actividad (cierre no encontrado)"
            }, status=200)
            
    except Exception as e:
        return Response({
            "error": f"Error interno: {str(e)}"
        }, status=500)
