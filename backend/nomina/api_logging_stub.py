# backend/nomina/api_logging_stub.py
"""
STUB de transición para api_logging V1
Este archivo reemplaza temporalmente las funciones del sistema V1 
para evitar errores mientras migramos al V2.
"""

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

@api_view(['GET'])
def obtener_actividad_tarjeta_stub(request, cierre_id):
    """STUB: API para obtener actividad de tarjeta"""
    logger.debug(f"STUB: obtener_actividad_tarjeta - cierre_id: {cierre_id}")
    return Response([], status=status.HTTP_200_OK)


@api_view(['POST'])
def registrar_actividad_tarjeta_stub(request):
    """STUB: API para registrar actividad"""
    logger.debug("STUB: registrar_actividad_tarjeta")
    return Response({"status": "stub"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def obtener_logs_upload_stub(request):
    """STUB: API para obtener logs de upload"""
    logger.debug("STUB: obtener_logs_upload")
    return Response([], status=status.HTTP_200_OK)


@api_view(['POST'])
def limpiar_logs_antiguos_stub(request):
    """STUB: API para limpiar logs antiguos"""
    logger.debug("STUB: limpiar_logs_antiguos")
    return Response({"status": "stub"}, status=status.HTTP_200_OK)


# Aliases para mantener compatibilidad
obtener_actividad_tarjeta = obtener_actividad_tarjeta_stub
registrar_actividad_tarjeta = registrar_actividad_tarjeta_stub
obtener_logs_upload = obtener_logs_upload_stub
limpiar_logs_antiguos = limpiar_logs_antiguos_stub