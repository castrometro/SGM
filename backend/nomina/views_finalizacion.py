from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import CierreNomina


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finalizar_cierre_view(request, pk: int):
    """
    Endpoint explícito para finalizar un cierre y generar el informe con Celery chord.
    Equivale al action 'finalizar_cierre' del CierreNominaViewSet.
    """
    try:
        cierre = CierreNomina.objects.get(id=pk)
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user or not request.user.is_authenticated:
        return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

    if cierre.estado != 'incidencias_resueltas':
        return Response({
            "error": "Estado incorrecto",
            "message": f"El cierre debe estar en 'incidencias_resueltas' para ser finalizado. Estado actual: {cierre.estado}",
            "estado_actual": cierre.estado,
            "estados_permitidos": ["incidencias_resueltas"],
            "estado_incidencias": getattr(cierre, 'estado_incidencias', 'no_definido'),
            "total_incidencias": getattr(cierre, 'total_incidencias', 0)
        }, status=status.HTTP_400_BAD_REQUEST)

    if not cierre.nomina_consolidada.exists():
        return Response({
            'error': 'No hay datos consolidados para este cierre. Ejecute consolidación antes de finalizar.'
        }, status=status.HTTP_409_CONFLICT)

    try:
        from celery import chord
        from .tasks import (
            build_informe_libro,
            build_informe_movimientos,
            unir_y_guardar_informe,
            enviar_informe_redis_task,
            finalizar_cierre_post_informe,
        )

        tasks = [
            build_informe_libro.s(cierre.id),
            build_informe_movimientos.s(cierre.id),
        ]
        callback_guardar = unir_y_guardar_informe.s(cierre.id)
        callback_en_redis = enviar_informe_redis_task.s(cierre.id)
        callback_final = finalizar_cierre_post_informe.s(cierre.id, getattr(request.user, 'id', None))

        result = chord(tasks)(callback_guardar | callback_en_redis | callback_final)

        return Response({
            'success': True,
            'message': 'Finalización iniciada. Generando informe y cerrando.',
            'cierre_id': cierre.id,
            'task_id': getattr(result, 'id', None)
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({
            "error": "Error interno",
            "message": f"Error al iniciar finalización: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
