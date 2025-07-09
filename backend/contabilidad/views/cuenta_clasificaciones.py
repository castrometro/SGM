from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from ..models import (
    CuentaContable,
    AccountClassification,
    ClasificacionSet,
    ClasificacionOption
)
from ..serializers import CuentaContableSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_cuenta_con_clasificaciones(request):
    """
    Crear una nueva cuenta con sus clasificaciones
    """
    try:
        data = request.data
        cliente_id = data.get('cliente')
        codigo = data.get('numero_cuenta')
        nombre = data.get('cuenta_nombre', codigo)
        clasificaciones = data.get('clasificaciones', {})
        
        with transaction.atomic():
            # Crear la cuenta
            cuenta = CuentaContable.objects.create(
                cliente_id=cliente_id,
                codigo=codigo,
                nombre=nombre
            )
            
            # Crear las clasificaciones
            for set_nombre, opcion_valor in clasificaciones.items():
                try:
                    set_cls = ClasificacionSet.objects.get(
                        cliente_id=cliente_id,
                        nombre=set_nombre
                    )
                    opcion = ClasificacionOption.objects.get(
                        set_clas=set_cls,
                        valor=opcion_valor
                    )
                    
                    AccountClassification.objects.create(
                        cuenta=cuenta,
                        set_clas=set_cls,
                        opcion=opcion
                    )
                except (ClasificacionSet.DoesNotExist, ClasificacionOption.DoesNotExist) as e:
                    print(f"Error creando clasificación {set_nombre}={opcion_valor}: {e}")
                    continue
            
            serializer = CuentaContableSerializer(cuenta)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def actualizar_cuenta_con_clasificaciones(request, cuenta_id):
    """
    Actualizar una cuenta y sus clasificaciones
    """
    try:
        cuenta = get_object_or_404(CuentaContable, id=cuenta_id)
        data = request.data
        
        with transaction.atomic():
            # Actualizar datos básicos de la cuenta
            if 'numero_cuenta' in data:
                cuenta.codigo = data['numero_cuenta']
            if 'cuenta_nombre' in data:
                cuenta.nombre = data['cuenta_nombre']
            cuenta.save()
            
            # Actualizar clasificaciones si se proveen
            if 'clasificaciones' in data:
                clasificaciones = data['clasificaciones']
                
                # Eliminar clasificaciones existentes
                AccountClassification.objects.filter(cuenta=cuenta).delete()
                
                # Crear las nuevas clasificaciones
                for set_nombre, opcion_valor in clasificaciones.items():
                    try:
                        set_cls = ClasificacionSet.objects.get(
                            cliente=cuenta.cliente,
                            nombre=set_nombre
                        )
                        opcion = ClasificacionOption.objects.get(
                            set_clas=set_cls,
                            valor=opcion_valor
                        )
                        
                        AccountClassification.objects.create(
                            cuenta=cuenta,
                            set_clas=set_cls,
                            opcion=opcion
                        )
                    except (ClasificacionSet.DoesNotExist, ClasificacionOption.DoesNotExist) as e:
                        print(f"Error actualizando clasificación {set_nombre}={opcion_valor}: {e}")
                        continue
            
            serializer = CuentaContableSerializer(cuenta)
            return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_cuenta_con_clasificaciones(request, cuenta_id):
    """
    Eliminar una cuenta y todas sus clasificaciones
    """
    try:
        cuenta = get_object_or_404(CuentaContable, id=cuenta_id)
        
        with transaction.atomic():
            # Las clasificaciones se eliminan automáticamente por CASCADE
            cuenta.delete()
            
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clasificacion_masiva_cuentas(request):
    """
    Aplicar clasificación masiva a múltiples cuentas
    """
    try:
        data = request.data
        cuenta_ids = data.get('cuenta_ids', [])
        set_clas_id = data.get('set_clas_id')
        opcion_id = data.get('opcion_id')
        
        if not cuenta_ids or not set_clas_id or not opcion_id:
            return Response(
                {'error': 'cuenta_ids, set_clas_id y opcion_id son requeridos'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            set_cls = get_object_or_404(ClasificacionSet, id=set_clas_id)
            opcion = get_object_or_404(ClasificacionOption, id=opcion_id)
            
            cuentas_actualizadas = 0
            
            for cuenta_id in cuenta_ids:
                try:
                    cuenta = CuentaContable.objects.get(id=cuenta_id)
                    
                    # Eliminar clasificación existente para este set (si existe)
                    AccountClassification.objects.filter(
                        cuenta=cuenta,
                        set_clas=set_cls
                    ).delete()
                    
                    # Crear nueva clasificación
                    AccountClassification.objects.create(
                        cuenta=cuenta,
                        set_clas=set_cls,
                        opcion=opcion
                    )
                    
                    cuentas_actualizadas += 1
                    
                except CuentaContable.DoesNotExist:
                    continue
            
            return Response({
                'message': f'Clasificación aplicada a {cuentas_actualizadas} cuentas',
                'cuentas_actualizadas': cuentas_actualizadas
            })
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
