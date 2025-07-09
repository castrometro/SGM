# Archivo temporal para funciones de clasificaciones persistentes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date

from api.models import Cliente
from ..models import (
    CuentaContable,
    CierreContabilidad,
    ClasificacionSet,
    AccountClassification,
    ClasificacionOption,
)
from ..utils.activity_logger import registrar_actividad_tarjeta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_clasificaciones_persistentes_detalladas(request, cliente_id):
    """
    Obtiene las clasificaciones persistentes con detalles completos para el modal de gestión
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Obtener todas las clasificaciones del cliente con detalles
    clasificaciones = AccountClassification.objects.filter(
        cuenta__cliente=cliente
    ).select_related(
        'cuenta', 'set_clas', 'opcion'
    ).order_by('cuenta__codigo')
    
    data = []
    for clasificacion in clasificaciones:
        data.append({
            'id': clasificacion.id,
            'cuenta_id': clasificacion.cuenta.id,
            'cuenta_codigo': clasificacion.cuenta.codigo,
            'cuenta_nombre': clasificacion.cuenta.nombre,
            'cuenta_nombre_en': clasificacion.cuenta.nombre_en,
            'set_clas_id': clasificacion.set_clas.id,
            'set_nombre': clasificacion.set_clas.nombre,
            'opcion_id': clasificacion.opcion.id,
            'opcion_valor': clasificacion.opcion.valor,
            'opcion_valor_en': clasificacion.opcion.valor_en,
            'fecha_creacion': clasificacion.fecha,  # Corrected field name
            'fecha_actualizacion': clasificacion.fecha,  # Same field as creation
        })
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_vista_clasificaciones_persistentes(request, cliente_id):
    """
    Registra que el usuario abrió el modal de clasificaciones persistentes
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    cierre_id = request.query_params.get('cierre_id')
    cierre = None
    periodo = None
    
    if cierre_id:
        try:
            # Intentar usar el cierre específico proporcionado
            cierre = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
            periodo = cierre.periodo
        except CierreContabilidad.DoesNotExist:
            pass
    
    # Si no se encontró el cierre específico, buscar cualquier cierre del cliente
    if not cierre:
        cierre = CierreContabilidad.objects.filter(cliente=cliente).order_by('-periodo').first()
        if cierre:
            periodo = cierre.periodo
        else:
            # Como último recurso, usar fecha actual
            periodo = date.today().strftime("%Y-%m")

    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo,
        tarjeta="clasificacion",
        accion="view_persistent_modal",
        descripcion="Abrió modal de clasificaciones persistentes",
        usuario=request.user,
        detalles={
            "cierre_id": cierre_id,
            "modal_type": "persistent_classifications"
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"mensaje": "Vista registrada correctamente"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clasificacion_masiva_persistente(request):
    """
    Realiza clasificación masiva de cuentas en la base de datos persistente
    """
    cuenta_ids = request.data.get('cuenta_ids', [])
    set_clas_id = request.data.get('set_clas_id')
    opcion_id = request.data.get('opcion_id')
    
    if not cuenta_ids or not set_clas_id or not opcion_id:
        return Response({
            "error": "cuenta_ids, set_clas_id y opcion_id son requeridos"
        }, status=400)
    
    try:
        set_clas = ClasificacionSet.objects.get(id=set_clas_id)
        opcion = ClasificacionOption.objects.get(id=opcion_id, set_clas=set_clas)
        cuentas = CuentaContable.objects.filter(id__in=cuenta_ids)
        
        if len(cuentas) != len(cuenta_ids):
            return Response({
                "error": "Algunas cuentas no fueron encontradas"
            }, status=400)
        
        # Verificar que todas las cuentas pertenecen al mismo cliente
        cliente = cuentas.first().cliente
        if not all(cuenta.cliente == cliente for cuenta in cuentas):
            return Response({
                "error": "Todas las cuentas deben pertenecer al mismo cliente"
            }, status=400)
        
        created_count = 0
        updated_count = 0
        
        for cuenta in cuentas:
            clasificacion, created = AccountClassification.objects.update_or_create(
                cuenta=cuenta,
                set_clas=set_clas,
                defaults={'opcion': opcion}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return Response({
            "mensaje": f"Clasificación masiva completada",
            "created": created_count,
            "updated": updated_count,
            "total": len(cuenta_ids)
        })
        
    except ClasificacionSet.DoesNotExist:
        return Response({"error": "Set de clasificación no encontrado"}, status=404)
    except ClasificacionOption.DoesNotExist:
        return Response({"error": "Opción de clasificación no encontrada"}, status=404)
    except Exception as e:
        return Response({
            "error": f"Error en clasificación masiva: {str(e)}"
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estadisticas_clasificaciones_persistentes(request, cliente_id):
    """
    Obtiene estadísticas de las clasificaciones persistentes para el cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Contar clasificaciones
    total_clasificaciones = AccountClassification.objects.filter(
        cuenta__cliente=cliente
    ).count()
    
    # Contar cuentas totales
    total_cuentas = CuentaContable.objects.filter(cliente=cliente).count()
    
    # Contar cuentas clasificadas (que tienen al menos una clasificación)
    cuentas_clasificadas = CuentaContable.objects.filter(
        cliente=cliente,
        clasificaciones__isnull=False  # Corrected relationship name
    ).distinct().count()
    
    # Cuentas sin clasificar
    cuentas_sin_clasificar = total_cuentas - cuentas_clasificadas
    
    # Contar sets disponibles
    total_sets = ClasificacionSet.objects.filter(cliente=cliente).count()
    
    return Response({
        "total_clasificaciones": total_clasificaciones,
        "total_cuentas": total_cuentas,
        "cuentas_clasificadas": cuentas_clasificadas,
        "cuentas_sin_clasificar": cuentas_sin_clasificar,
        "total_sets": total_sets,
        "porcentaje_clasificado": round((cuentas_clasificadas / total_cuentas * 100) if total_cuentas > 0 else 0, 2)
    })
