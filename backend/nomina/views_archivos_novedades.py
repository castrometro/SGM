# backend/nomina/views_archivos_novedades.py

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import (
    ArchivoNovedadesUpload, CierreNomina, ConceptoRemuneracion, 
    ConceptoRemuneracionNovedades, EmpleadoCierreNovedades,
    RegistroConceptoEmpleadoNovedades
)
from .serializers import ArchivoNovedadesUploadSerializer
from .utils.clientes import get_client_ip
from .models_logging import registrar_actividad_tarjeta_nomina
from .tasks import procesar_archivo_novedades

logger = logging.getLogger(__name__)


class ArchivoNovedadesUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar archivos de novedades
    """
    queryset = ArchivoNovedadesUpload.objects.all()
    serializer_class = ArchivoNovedadesUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        """Obtiene el estado del archivo de novedades para un cierre específico"""
        archivo = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if archivo:
            return Response({
                "id": archivo.id,
                "estado": archivo.estado,
                "archivo_nombre": archivo.archivo.name.split("/")[-1] if archivo.archivo else "",
                "archivo_url": request.build_absolute_uri(archivo.archivo.url) if archivo.archivo else "",
                "fecha_subida": archivo.fecha_subida,
                "cierre_id": archivo.cierre.id,
                "cliente_id": archivo.cierre.cliente.id,
                "cliente_nombre": archivo.cierre.cliente.nombre,
            })
        else:
            return Response({
                "id": None,
                "estado": "no_subido",
                "archivo_nombre": "",
                "archivo_url": "",
                "fecha_subida": None,
                "cierre_id": None,
                "cliente_id": None,
                "cliente_nombre": "",
            })
    
    @action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)')
    def subir(self, request, cierre_id=None):
        """Sube un archivo de novedades para un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se proporcionó archivo"}, status=400)
        
        # Validar que sea un archivo Excel
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response({"error": "El archivo debe ser de tipo Excel (.xlsx o .xls)"}, status=400)
        
        # Validar nombre del archivo según formato estándar
        from .utils.validaciones import validar_nombre_archivo_novedades
        
        resultado_validacion = validar_nombre_archivo_novedades(
            nombre_archivo=archivo.name,
            rut_cliente=cierre.cliente.rut,
            periodo_cierre=cierre.periodo
        )
        
        if not resultado_validacion['es_valido']:
            errores = resultado_validacion.get('errores', [])
            return Response({
                "error": "Nombre de archivo inválido",
                "detalles": errores
            }, status=400)
        
        # Crear o actualizar el registro de novedades
        archivo_novedades, created = ArchivoNovedadesUpload.objects.get_or_create(
            cierre=cierre,
            defaults={
                'archivo': archivo,
                'analista': request.user,
                'estado': 'pendiente'
            }
        )
        
        if not created:
            # Si ya existe, LIMPIAR COMPLETAMENTE los datos del archivo anterior
            logger.info(f"Resubiendo archivo de novedades - Limpiando datos anteriores del archivo {archivo_novedades.id}")
            
            with transaction.atomic():
                # 1. Eliminar todos los registros de conceptos de empleados novedades del cierre
                empleados_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre)
                total_registros = 0
                
                for empleado in empleados_novedades:
                    count_registros = empleado.registroconceptoempleadonovedades_set.count()
                    empleado.registroconceptoempleadonovedades_set.all().delete()
                    total_registros += count_registros
                
                logger.info(f"Eliminados {total_registros} registros de conceptos novedades para resubida")
                
                # 2. Eliminar todos los empleados novedades del cierre
                count_empleados_novedades = empleados_novedades.count()
                empleados_novedades.delete()
                logger.info(f"Eliminados {count_empleados_novedades} empleados novedades para resubida")
                
                # 3. Limpiar header_json y actualizar archivo
                archivo_novedades.archivo = archivo
                archivo_novedades.analista = request.user
                archivo_novedades.estado = 'pendiente'
                archivo_novedades.header_json = None  # IMPORTANTE: Limpiar headers del archivo anterior
                archivo_novedades.save()
                
                logger.info(f"Archivo de novedades {archivo_novedades.id} limpiado y actualizado para resubida")
        
        # Disparar tarea de procesamiento con Celery
        procesar_archivo_novedades.delay(archivo_novedades.id)
        
        return Response({
            "id": archivo_novedades.id,
            "estado": archivo_novedades.estado,
            "archivo_nombre": archivo.name,
            "fecha_subida": archivo_novedades.fecha_subida,
            "mensaje": "Archivo subido correctamente y enviado a procesamiento"
        }, status=201)

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        """Reprocesa un archivo de novedades desde el inicio"""
        archivo = self.get_object()
        
        if archivo.estado == 'en_proceso':
            return Response({
                "error": "El archivo ya está siendo procesado"
            }, status=400)
        
        try:
            # Resetear estado y limpiar datos previos
            archivo.estado = 'en_proceso'
            archivo.header_json = None
            archivo.save()
            
            # Iniciar procesamiento asíncrono
            procesar_archivo_novedades.delay(archivo.id)
            
            return Response({
                "mensaje": "Reprocesamiento iniciado",
                "estado": archivo.estado
            })
            
        except Exception as e:
            archivo.estado = 'con_error'
            archivo.save()
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['get'])
    def headers(self, request, pk=None):
        """Obtiene los headers de un archivo de novedades para clasificación"""
        archivo = self.get_object()
        
        if archivo.estado not in ['clasif_pendiente', 'clasificado', 'procesado']:
            return Response({
                "error": "El archivo debe estar en estado 'clasif_pendiente', 'clasificado' o 'procesado' para obtener headers"
            }, status=400)
        
        headers_data = archivo.header_json
        if isinstance(headers_data, dict):
            headers_clasificados = headers_data.get("headers_clasificados", [])
            headers_sin_clasificar = headers_data.get("headers_sin_clasificar", [])
        else:
            headers_clasificados = []
            headers_sin_clasificar = headers_data if isinstance(headers_data, list) else []
        
        # Si el archivo está procesado, incluir los mapeos existentes
        mapeos_existentes = {}
        if archivo.estado == 'procesado':
            mapeos = ConceptoRemuneracionNovedades.objects.filter(
                cliente=archivo.cierre.cliente,
                activo=True,
                nombre_concepto_novedades__in=headers_clasificados
            ).select_related('concepto_libro')

            for mapeo in mapeos:
                if mapeo.concepto_libro:
                    mapeos_existentes[mapeo.nombre_concepto_novedades] = {
                        'concepto_libro_id': mapeo.concepto_libro.id,
                        'concepto_libro_nombre': mapeo.concepto_libro.nombre_concepto,
                        'concepto_libro_clasificacion': mapeo.concepto_libro.clasificacion,
                    }
                else:
                    mapeos_existentes[mapeo.nombre_concepto_novedades] = {
                        'concepto_libro_id': None,
                    }
        
        return Response({
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
            "mapeos_existentes": mapeos_existentes
        })

    @action(detail=True, methods=['post'])
    def clasificar_headers(self, request, pk=None):
        """Mapea headers pendientes de un archivo de novedades con conceptos del libro de remuneraciones"""
        archivo = self.get_object()
        
        if archivo.estado != 'clasif_pendiente':
            return Response({
                "error": "El archivo debe estar en estado 'clasif_pendiente' para mapear headers"
            }, status=400)
        
        mapeos = request.data.get('mapeos', [])
        if not mapeos:
            return Response({"error": "No se proporcionaron mapeos"}, status=400)
        
        try:
            # Obtener headers actuales
            headers_data = archivo.header_json
            headers_clasificados = headers_data.get("headers_clasificados", [])
            headers_sin_clasificar = headers_data.get("headers_sin_clasificar", [])
            
            # Procesar mapeos
            for mapeo in mapeos:
                header_novedades = mapeo.get('header_novedades')
                concepto_libro_id = mapeo.get('concepto_libro_id')

                if header_novedades in headers_sin_clasificar:
                    if concepto_libro_id:
                        try:
                            concepto_libro = ConceptoRemuneracion.objects.get(
                                id=concepto_libro_id,
                                cliente=archivo.cierre.cliente,
                                vigente=True
                            )
                        except ConceptoRemuneracion.DoesNotExist:
                            continue
                    else:
                        concepto_libro = None

                    # Crear o actualizar mapeo
                    mapeo_concepto, created = ConceptoRemuneracionNovedades.objects.get_or_create(
                        cliente=archivo.cierre.cliente,
                        nombre_concepto_novedades=header_novedades,
                        defaults={
                            'concepto_libro': concepto_libro,
                            'usuario_mapea': request.user,
                            'activo': True,
                        }
                    )

                    if not created:
                        mapeo_concepto.concepto_libro = concepto_libro
                        mapeo_concepto.usuario_mapea = request.user
                        mapeo_concepto.activo = True
                        mapeo_concepto.save()

                    # Mover de sin clasificar a clasificados
                    headers_sin_clasificar.remove(header_novedades)
                    headers_clasificados.append(header_novedades)
            
            # Actualizar archivo
            archivo.header_json = {
                "headers_clasificados": headers_clasificados,
                "headers_sin_clasificar": headers_sin_clasificar,
            }
            
            # Cambiar estado si ya no hay headers sin clasificar
            if not headers_sin_clasificar:
                archivo.estado = "clasificado"
            
            archivo.save()
            
            return Response({
                "mensaje": "Headers mapeados correctamente",
                "headers_clasificados": len(headers_clasificados),
                "headers_sin_clasificar": len(headers_sin_clasificar),
                "estado": archivo.estado
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def procesar_final(self, request, pk=None):
        """Procesa finalmente un archivo de novedades (actualiza empleados y guarda registros)"""
        from nomina.tasks import actualizar_empleados_desde_novedades_task, guardar_registros_novedades_task
        from celery import chain
        
        archivo = self.get_object()
        
        if archivo.estado != 'clasificado':
            return Response({
                "error": "El archivo debe estar clasificado completamente para procesamiento final"
            }, status=400)
        
        try:
            # Crear cadena de tareas finales
            workflow = chain(
                actualizar_empleados_desde_novedades_task.s({"archivo_id": archivo.id}),
                guardar_registros_novedades_task.s()
            )
            
            # Ejecutar la cadena
            workflow.apply_async()
            
            return Response({
                "mensaje": "Procesamiento final iniciado",
                "estado": archivo.estado
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def procesar_final_optimizado(self, request, pk=None):
        """🚀 Versión optimizada con Celery Chord para procesamiento paralelo"""
        from nomina.tasks import actualizar_empleados_desde_novedades_task_optimizado, guardar_registros_novedades_task_optimizado
        from nomina.models_logging import registrar_actividad_tarjeta_nomina
        from celery import chain
        
        archivo = self.get_object()
        
        if archivo.estado != 'clasificado':
            return Response({
                "error": "El archivo debe estar clasificado completamente para procesamiento optimizado"
            }, status=400)
        
        try:
            # Crear chain optimizado con chord interno
            workflow = chain(
                actualizar_empleados_desde_novedades_task_optimizado.s({"archivo_id": archivo.id}),
                guardar_registros_novedades_task_optimizado.s()
            )
            
            # Ejecutar con tracking
            result = workflow.apply_async()
            
            # Registrar inicio optimizado
            try:
                headers_clasificados = len(archivo.header_json.get('headers_clasificados', {})) if archivo.header_json else 0
                
                registrar_actividad_tarjeta_nomina(
                    cierre_id=archivo.cierre.id,
                    tarjeta="novedades", 
                    accion="procesar_final_optimizado",
                    descripcion="Iniciando procesamiento paralelo de novedades con chunks",
                    detalles={
                        "archivo_id": archivo.id,
                        "chain_id": str(result),
                        "modo": "chord_paralelo",
                        "headers_clasificados": headers_clasificados,
                        "archivo_nombre": archivo.archivo.name if archivo.archivo else "N/A"
                    },
                    resultado="procesando"
                )
            except Exception as e:
                # No fallar si no se puede registrar actividad
                logger.warning(f"⚠️ Error registrando actividad optimizada: {e}")
            
            return Response({
                "mensaje": "Procesamiento paralelo optimizado iniciado",
                "chain_id": str(result),
                "modo": "optimizado_chord",
                "estado": archivo.estado,
                "headers_clasificados": headers_clasificados,
                "optimizacion_activa": True
            })
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento optimizado: {e}")
            return Response({"error": str(e)}, status=500)

    def perform_destroy(self, instance):
        """
        Eliminar archivo de novedades y todos sus datos relacionados
        """
        logger.info(f"=== ELIMINANDO ARCHIVO DE NOVEDADES {instance.id} ===")
        
        cierre = instance.cierre
        
        # Registrar actividad antes de eliminar
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="archivos_novedades",
            accion="delete_archivo",
            descripcion=f"Archivo de novedades eliminado para resubida",
            usuario=self.request.user,
            detalles={
                "archivo_id": instance.id,
                "archivo_nombre": instance.archivo.name if instance.archivo else "N/A",
                "estado_anterior": instance.estado
            },
            ip_address=get_client_ip(self.request)
        )
        
        with transaction.atomic():
            # 1. Eliminar todos los registros de conceptos de empleados novedades del cierre
            empleados_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre)
            total_registros = 0
            
            for empleado in empleados_novedades:
                count_registros = empleado.registroconceptoempleadonovedades_set.count()
                empleado.registroconceptoempleadonovedades_set.all().delete()
                total_registros += count_registros
                logger.info(f"Eliminados {count_registros} registros de conceptos novedades para empleado {empleado.rut}")
            
            logger.info(f"Total registros de conceptos novedades eliminados: {total_registros}")
            
            # 2. Eliminar todos los empleados novedades del cierre
            count_empleados_novedades = empleados_novedades.count()
            empleados_novedades.delete()
            logger.info(f"Eliminados {count_empleados_novedades} empleados novedades del cierre {cierre.id}")
            
            # 3. Limpiar mapeos de conceptos de novedades específicos del cliente
            # (Mantenemos los mapeos globales, solo eliminamos si están huérfanos)
            mapeos_cliente = ConceptoRemuneracionNovedades.objects.filter(cliente=cierre.cliente)
            count_mapeos = mapeos_cliente.count()
            logger.info(f"Mantenemos {count_mapeos} mapeos de conceptos novedades del cliente (no se eliminan)")
            
            # 4. Eliminar el archivo de novedades
            instance.delete()
            logger.info(f"Archivo de novedades {instance.id} eliminado completamente")
        
        logger.info("=== ELIMINACIÓN DE ARCHIVO NOVEDADES COMPLETADA ===")
