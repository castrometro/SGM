from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date

from ..models import (
    CierreContabilidad,
    MovimientoContable,
    AperturaCuenta,
    AccountClassification,
    CuentaContable,
)
from ..serializers import CierreContabilidadSerializer
from ..utils.activity_logger import registrar_actividad_tarjeta
from ..utils.mixins import ActivityLoggerMixin


class CierreContabilidadViewSet(ActivityLoggerMixin, viewsets.ModelViewSet):
    queryset = CierreContabilidad.objects.all()
    serializer_class = CierreContabilidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        periodo = self.request.query_params.get("periodo")

        if cliente:
            qs = qs.filter(cliente_id=cliente)
        if periodo:
            qs = qs.filter(periodo=periodo)

        return qs.order_by("-fecha_creacion")

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual al crear un nuevo cierre
        """
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["get"])
    def movimientos_resumen(self, request, pk=None):
        """
        Endpoint optimizado para obtener resumen de movimientos contables con paginación opcional,
        filtros avanzados y logging de actividad. Mantiene compatibilidad con API original.
        """
        cierre = self.get_object()
        
        # Validar que el cierre esté en estado permitido para ver el libro
        estados_permitidos = ['sin_incidencias', 'generando_reportes', 'finalizado']
        if cierre.estado not in estados_permitidos:
            return Response({
                'error': 'Acceso restringido',
                'message': f'El libro del cierre solo está disponible cuando el estado es: {", ".join(estados_permitidos)}. Estado actual: {cierre.estado}',
                'estado_actual': cierre.estado,
                'estados_permitidos': estados_permitidos
            }, status=403)
        
        # Parámetros de filtrado
        set_id = request.query_params.get("set_id")
        opcion_id = request.query_params.get("opcion_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        search = request.query_params.get("search")  # Búsqueda por código/nombre cuenta
        
        # Parámetros de paginación (opcional para mantener compatibilidad)
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        
        # Solo usar paginación si se piden explícitamente
        usar_paginacion = page is not None and page_size is not None
        
        if usar_paginacion:
            page = int(page)
            page_size = int(page_size)
        
        # Obtener cuentas que participan en este cierre específico
        # (cuentas con movimientos OR cuentas con saldo de apertura)
        cuentas_con_movimientos = MovimientoContable.objects.filter(
            cierre=cierre
        ).values_list('cuenta_id', flat=True).distinct()
        
        cuentas_con_apertura = AperturaCuenta.objects.filter(
            cierre=cierre
        ).values_list('cuenta_id', flat=True).distinct()
        
        # Unir ambos conjuntos de cuentas
        cuentas_del_cierre = set(cuentas_con_movimientos) | set(cuentas_con_apertura)
        
        # Filtrar solo las cuentas que participan en el cierre
        cuentas_base = CuentaContable.objects.filter(
            cliente=cierre.cliente,
            id__in=cuentas_del_cierre
        )
        
        # NO filtrar por clasificación aquí - se hará en el frontend
        # Solo aplicar filtros de búsqueda de texto
        if search:
            cuentas_base = cuentas_base.filter(
                Q(codigo__icontains=search) | 
                Q(nombre__icontains=search)
            )
        
        # Obtener movimientos para estas cuentas con filtros de fecha
        movimientos_query = MovimientoContable.objects.filter(cierre=cierre)
        if fecha_desde:
            movimientos_query = movimientos_query.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            movimientos_query = movimientos_query.filter(fecha__lte=fecha_hasta)
        
        # Calcular totales por cuenta (incluyendo cuentas sin movimientos)
        # Crear filtros dinámicos para fechas
        fecha_filters = Q(movimientocontable__cierre=cierre)
        if fecha_desde:
            fecha_filters &= Q(movimientocontable__fecha__gte=fecha_desde)
        if fecha_hasta:
            fecha_filters &= Q(movimientocontable__fecha__lte=fecha_hasta)
            
        totales_query = (
            cuentas_base.annotate(
                total_debe=Sum("movimientocontable__debe", filter=fecha_filters),
                total_haber=Sum("movimientocontable__haber", filter=fecha_filters)
            )
            .values(
                "id", 
                "codigo", 
                "nombre",
                "nombre_en",  # Incluir nombre en inglés si existe
                "total_debe",
                "total_haber"
            )
            .order_by("codigo")
        )
        
        # Obtener saldos de apertura optimizado
        aperturas = AperturaCuenta.objects.filter(cierre=cierre).values(
            "cuenta_id", "saldo_anterior"
        )
        mapa_aperturas = {a["cuenta_id"]: a["saldo_anterior"] for a in aperturas}
        
        # Convertir a lista para aplicar paginación manual si es necesario
        totales_list = list(totales_query)
        
        # Aplicar paginación manual si se solicita
        if usar_paginacion:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            totales_procesados = totales_list[start_index:end_index]
        else:
            totales_procesados = totales_list
        
        # Obtener TODAS las clasificaciones para todas las cuentas del cierre
        # para permitir filtrado en el frontend
        clasificaciones_map = {}
        if True:  # Siempre obtener clasificaciones
            clasificaciones = AccountClassification.objects.filter(
                cuenta_id__in=[t["id"] for t in totales_procesados]
            ).select_related("opcion", "set_clas")  # Cambio: 'opcion' en lugar de 'opcion_clas'
            
            # Crear un mapa con todas las clasificaciones por cuenta
            for c in clasificaciones:
                if c.cuenta_id not in clasificaciones_map:
                    clasificaciones_map[c.cuenta_id] = {}
                
                clasificaciones_map[c.cuenta_id][c.set_clas_id] = {
                    "set_nombre": c.set_clas.nombre,
                    "opcion_id": c.opcion.id if c.opcion else None,
                    "opcion_valor": c.opcion.valor if c.opcion else ""
                }
        
        # Construir datos de respuesta enriquecidos
        data = []
        for t in totales_procesados:
            cuenta_id = t["id"]  # Cambio: ahora usamos "id" directamente de la cuenta
            saldo_anterior = mapa_aperturas.get(cuenta_id, 0)
            saldo_final = saldo_anterior + (t["total_debe"] or 0) - (t["total_haber"] or 0)
            
            item = {
                "cuenta_id": cuenta_id,
                "total_debe": t["total_debe"] or 0,
                "total_haber": t["total_haber"] or 0,
                "saldo_final": saldo_final,
                "saldo_anterior": saldo_anterior,  # Siempre incluir saldo_anterior
            }
            
            # Agregar TODAS las clasificaciones disponibles para esta cuenta
            item["clasificaciones"] = clasificaciones_map.get(cuenta_id, {})
            
            # Para compatibilidad con el frontend existente, incluir la clasificación
            # del set seleccionado (si existe) en el formato original
            if set_id and str(set_id) in str(clasificaciones_map.get(cuenta_id, {})):
                for set_key, cls_data in clasificaciones_map.get(cuenta_id, {}).items():
                    if str(set_key) == str(set_id):
                        item["clasificacion"] = {
                            "opcion_valor": cls_data["opcion_valor"]
                        }
                        break
            
            # Agregar información adicional si hay paginación (API extendida)
            if usar_paginacion:
                item.update({
                    "cuenta_codigo": t["codigo"],
                    "cuenta_nombre": t["nombre"],
                    "cuenta_nombre_en": t["nombre_en"],
                })
            else:
                # Para compatibilidad con AnalisisLibro.jsx que espera 'codigo' y 'nombre'
                item.update({
                    "codigo": t["codigo"],
                    "nombre": t["nombre"],
                })
            
            data.append(item)
        
        # Registrar actividad de visualización
        try:
            self.log_activity(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tarjeta="movimientos_resumen",
                accion="view_data",
                descripcion=f"Consulta resumen movimientos - {len(data)} cuentas mostradas",
                usuario=request.user,
                detalles={
                    "cierre_id": cierre.id,
                    "filtros": {
                        "set_id": set_id,
                        "opcion_id": opcion_id,
                        "fecha_desde": fecha_desde,
                        "fecha_hasta": fecha_hasta,
                        "search": search,
                    },
                    "cuentas_mostradas": len(data),
                    "total_cuentas": len(totales_list),
                    "pagina": page if usar_paginacion else None,
                    "usar_paginacion": usar_paginacion,
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            # No fallar por error de logging
            print(f"Error registrando actividad en movimientos_resumen: {e}")
        
        # Respuesta compatible vs. paginada
        if usar_paginacion:
            # API extendida con paginación
            total_cuentas = len(totales_list)
            total_pages = (total_cuentas + page_size - 1) // page_size
            
            return Response({
                "results": data,
                "count": total_cuentas,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "metadata": {
                    "cierre_id": cierre.id,
                    "cierre_periodo": cierre.periodo,
                    "cliente_id": cierre.cliente.id,
                    "cliente_nombre": cierre.cliente.nombre,
                    "filtros_aplicados": {
                        "set_id": set_id,
                        "opcion_id": opcion_id,
                        "fecha_desde": fecha_desde,
                        "fecha_hasta": fecha_hasta,
                        "search": search,
                    }
                }
            })
        else:
            # API original (compatibilidad hacia atrás) - devuelve array directo
            return Response(data)

    @action(detail=True, methods=["get"], url_path="cuentas/(?P<cuenta_id>[^/.]+)/movimientos")
    def movimientos_cuenta(self, request, pk=None, cuenta_id=None):
        """
        Endpoint para obtener movimientos detallados de una cuenta específica
        con paginación y filtros.
        """
        cierre = self.get_object()
        
        try:
            cuenta = CuentaContable.objects.get(id=cuenta_id, cliente=cierre.cliente)
        except CuentaContable.DoesNotExist:
            return Response({"error": "Cuenta no encontrada"}, status=404)
        
        # Parámetros de filtrado
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        tipo_documento = request.query_params.get("tipo_documento")
        search = request.query_params.get("search")  # Búsqueda en descripción
        
        # Parámetros de paginación
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        
        # Query base optimizada
        movimientos = MovimientoContable.objects.filter(
            cierre=cierre, 
            cuenta=cuenta
        ).select_related(
            'tipo_documento', 'centro_costo', 'auxiliar'
        ).order_by('-fecha', '-id')
        
        # Aplicar filtros
        if fecha_desde:
            movimientos = movimientos.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(fecha__lte=fecha_hasta)
        if tipo_documento:
            movimientos = movimientos.filter(tipo_doc_codigo=tipo_documento)
        if search:
            movimientos = movimientos.filter(
                Q(descripcion__icontains=search) | 
                Q(detalle_gasto__icontains=search) |
                Q(numero_documento__icontains=search)
            )
        
        # Aplicar paginación manual
        total_movimientos = movimientos.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        movimientos_paginados = movimientos[start_index:end_index]
        
        # Construir datos de respuesta
        movimientos_data = []
        
        # Obtener saldo de apertura
        try:
            apertura = AperturaCuenta.objects.get(cierre=cierre, cuenta=cuenta)
            saldo_inicial = float(apertura.saldo_anterior)
        except AperturaCuenta.DoesNotExist:
            saldo_inicial = 0
        
        # Para calcular saldos acumulados correctamente, necesitamos todos los movimientos hasta la página actual
        # ordenados cronológicamente
        todos_movimientos_hasta_pagina = MovimientoContable.objects.filter(
            cierre=cierre, 
            cuenta=cuenta
        ).filter(
            # Aplicar mismos filtros que la consulta principal
            **({} if not fecha_desde else {'fecha__gte': fecha_desde}),
            **({} if not fecha_hasta else {'fecha__lte': fecha_hasta}),
            **({} if not tipo_documento else {'tipo_doc_codigo': tipo_documento}),
        ).order_by('fecha', 'id')
        
        if search:
            todos_movimientos_hasta_pagina = todos_movimientos_hasta_pagina.filter(
                Q(descripcion__icontains=search) | 
                Q(detalle_gasto__icontains=search) |
                Q(numero_documento__icontains=search)
            )
        
        # Calcular saldos acumulados hasta el final de la página actual
        saldo_actual = saldo_inicial
        movimientos_con_saldo = []
        
        for i, mov in enumerate(todos_movimientos_hasta_pagina):
            saldo_actual += float(mov.debe) - float(mov.haber)
            
            # Solo incluir movimientos de la página actual
            if start_index <= i < end_index:
                movimientos_con_saldo.append({
                    "id": mov.id,
                    "fecha": mov.fecha.isoformat(),
                    "tipo_documento": {
                        "codigo": mov.tipo_doc_codigo,
                        "descripcion": mov.tipo_documento.descripcion if mov.tipo_documento else ""
                    },
                    "numero_documento": mov.numero_documento,
                    "numero_comprobante": mov.numero_comprobante,
                    "numero_interno": mov.numero_interno,
                    "centro_costo": mov.centro_costo.nombre if mov.centro_costo else "",
                    "auxiliar": mov.auxiliar.nombre if mov.auxiliar else "",
                    "detalle_gasto": mov.detalle_gasto,
                    "descripcion": mov.descripcion,
                    "debe": float(mov.debe),
                    "haber": float(mov.haber),
                    "saldo": saldo_actual,  # Saldo acumulado después de este movimiento
                    "flag_incompleto": mov.flag_incompleto,
                })
        
        movimientos_data = movimientos_con_saldo
        
        # Calcular totales para esta página
        total_debe = sum(m["debe"] for m in movimientos_data)
        total_haber = sum(m["haber"] for m in movimientos_data)
        
        # Información de paginación
        total_pages = (total_movimientos + page_size - 1) // page_size
        
        response_data = {
            "codigo": cuenta.codigo,
            "nombre": cuenta.nombre,
            "nombre_en": cuenta.nombre_en,
            "saldo_inicial": saldo_inicial,
            "movimientos": movimientos_data,
            "metadata": {
                "cuenta": {
                    "id": cuenta.id,
                    "codigo": cuenta.codigo,
                    "nombre": cuenta.nombre,
                    "nombre_en": cuenta.nombre_en,
                },
                "cierre": {
                    "id": cierre.id,
                    "periodo": cierre.periodo,
                    "cliente_nombre": cierre.cliente.nombre,
                },
                "pagination": {
                    "count": total_movimientos,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
                "filtros_aplicados": {
                    "fecha_desde": fecha_desde,
                    "fecha_hasta": fecha_hasta,
                    "tipo_documento": tipo_documento,
                    "search": search,
                },
                "totales_pagina": {
                    "debe": total_debe,
                    "haber": total_haber,
                    "diferencia": total_debe - total_haber,
                }
            }
        }
        
        # Registrar actividad
        try:
            self.log_activity(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tarjeta="movimientos_cuenta",
                accion="view_data",
                descripcion=f"Consulta movimientos cuenta {cuenta.codigo} - {cuenta.nombre}",
                usuario=request.user,
                detalles={
                    "cuenta_id": cuenta.id,
                    "cuenta_codigo": cuenta.codigo,
                    "cierre_id": cierre.id,
                    "filtros": {
                        "fecha_desde": fecha_desde,
                        "fecha_hasta": fecha_hasta,
                        "tipo_documento": tipo_documento,
                        "search": search,
                    },
                    "movimientos_mostrados": len(movimientos_data),
                    "total_movimientos": total_movimientos,
                    "pagina": page,
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            print(f"Error registrando actividad en movimientos_cuenta: {e}")
        
        return Response(response_data)

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        """
        Inicia la finalización del cierre y dispara la tarea de Celery.
        """
        cierre = self.get_object()
        try:
            task_id = cierre.iniciar_finalizacion(usuario=request.user)
            return Response({"success": True, "task_id": task_id})
        except ValueError as e:
            return Response({"success": False, "error": str(e)}, status=400)
        except Exception as e:
            print(f"Error iniciando finalización del cierre: {e}")
            return Response({"success": False, "error": "Error interno del servidor"}, status=500)

    @action(detail=True, methods=["post"], url_path="reportes/generar")
    def generar_reportes(self, request, pk=None):
        """
        Genera o regenera reportes financieros específicos para el cierre.
        
        Body params:
        - tipo_reporte: 'esf', 'eri', 'ecp' (opcional, si no se especifica genera todos)
        - regenerar: true/false (opcional, default false)
        """
        cierre = self.get_object()
        
        # Validar que el cierre esté en estado permitido
        estados_permitidos = ['sin_incidencias', 'generando_reportes', 'finalizado']
        if cierre.estado not in estados_permitidos:
            return Response({
                'error': 'Estado no permitido',
                'message': f'Los reportes solo se pueden generar cuando el estado es: {", ".join(estados_permitidos)}',
                'estado_actual': cierre.estado
            }, status=403)
        
        # Obtener parámetros
        tipo_reporte = request.data.get('tipo_reporte')
        regenerar = request.data.get('regenerar', False)
        
        tipos_disponibles = ['esf', 'eri', 'ecp']
        tipos_a_generar = [tipo_reporte] if tipo_reporte in tipos_disponibles else tipos_disponibles
        
        resultados = []
        
        for tipo in tipos_a_generar:
            try:
                if tipo == 'esf':
                    # Importar y ejecutar la tarea de ESF
                    from ..tasks_reportes import generar_estado_situacion_financiera
                    
                    # Ejecutar la tarea (puede ser async o sync dependiendo de Celery)
                    try:
                        task = generar_estado_situacion_financiera.delay(
                            cierre_id=cierre.id,
                            usuario_id=request.user.id,
                            regenerar=regenerar
                        )
                        task_id = task.id if hasattr(task, 'id') else None
                    except Exception as celery_error:
                        # Fallback a ejecución síncrona
                        resultado = generar_estado_situacion_financiera(
                            cierre_id=cierre.id,
                            usuario_id=request.user.id,
                            regenerar=regenerar
                        )
                        task_id = None
                    
                    resultados.append({
                        'tipo': 'esf',
                        'nombre': 'Estado de Situación Financiera',
                        'task_id': task_id,
                        'estado': 'iniciado' if task_id else 'completado',
                        'regenerar': regenerar
                    })
                    
                elif tipo == 'eri':
                    # TODO: Implementar Estado de Resultado Integral
                    resultados.append({
                        'tipo': 'eri',
                        'nombre': 'Estado de Resultado Integral',
                        'estado': 'no_implementado',
                        'mensaje': 'Próximamente disponible'
                    })
                    
                elif tipo == 'ecp':
                    # TODO: Implementar Estado de Cambios en el Patrimonio
                    resultados.append({
                        'tipo': 'ecp',
                        'nombre': 'Estado de Cambios en el Patrimonio',
                        'estado': 'no_implementado',
                        'mensaje': 'Próximamente disponible'
                    })
                    
            except Exception as e:
                resultados.append({
                    'tipo': tipo,
                    'estado': 'error',
                    'error': str(e)
                })
        
        # Registrar actividad
        try:
            self.log_activity(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tarjeta="reportes",
                accion="manual_generate",
                descripcion=f"Generación manual de reportes: {', '.join(tipos_a_generar)}",
                usuario=request.user,
                detalles={
                    "cierre_id": cierre.id,
                    "tipos_solicitados": tipos_a_generar,
                    "regenerar": regenerar,
                    "resultados": resultados
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            print(f"Error registrando actividad en generar_reportes: {e}")
        
        return Response({
            'success': True,
            'message': f'Generación iniciada para {len(tipos_a_generar)} tipo(s) de reporte',
            'resultados': resultados,
            'cierre_id': cierre.id,
            'regenerar': regenerar
        })

    @action(detail=True, methods=["get"], url_path="reportes")
    def consultar_reportes(self, request, pk=None):
        """
        Consulta el estado y datos de los reportes financieros del cierre.
        
        Query params:
        - tipo: 'esf', 'eri', 'ecp' (opcional, si no se especifica devuelve todos)
        - incluir_datos: true/false (opcional, default false - si incluir los datos JSON)
        """
        cierre = self.get_object()
        
        # Validar acceso a reportes
        estados_permitidos = ['sin_incidencias', 'generando_reportes', 'finalizado']
        if cierre.estado not in estados_permitidos:
            return Response({
                'error': 'Acceso restringido',
                'message': f'Los reportes solo están disponibles cuando el estado es: {", ".join(estados_permitidos)}',
                'estado_actual': cierre.estado
            }, status=403)
        
        # Obtener parámetros
        tipo_filtro = request.query_params.get('tipo')
        incluir_datos = request.query_params.get('incluir_datos', 'false').lower() == 'true'
        
        # Importar modelo dentro de la función para evitar problemas de importación circular
        from ..models import ReporteFinanciero
        
        # Construir query
        reportes_query = ReporteFinanciero.objects.filter(cierre=cierre)
        if tipo_filtro:
            reportes_query = reportes_query.filter(tipo_reporte=tipo_filtro)
        
        reportes = reportes_query.order_by('tipo_reporte', '-fecha_actualizacion')
        
        # Serializar reportes
        reportes_data = []
        for reporte in reportes:
            datos_reporte = {
                'id': reporte.id,
                'tipo_reporte': reporte.tipo_reporte,
                'tipo_reporte_display': reporte.get_tipo_reporte_display(),
                'estado': reporte.estado,
                'fecha_generacion': reporte.fecha_generacion.isoformat(),
                'fecha_actualizacion': reporte.fecha_actualizacion.isoformat(),
                'usuario_generador': {
                    'id': reporte.usuario_generador.id,
                    'username': reporte.usuario_generador.username
                } if reporte.usuario_generador else None,
                'es_valido': reporte.es_valido,
                'metadata': reporte.metadata,
                'error_mensaje': reporte.error_mensaje if reporte.estado == 'error' else None
            }
            
            # Incluir datos si se solicita y está disponible
            if incluir_datos and reporte.datos_reporte:
                datos_reporte['datos_reporte'] = reporte.datos_reporte
            elif reporte.datos_reporte:
                # Solo incluir un resumen de los datos
                datos_reporte['datos_disponibles'] = True
                if isinstance(reporte.datos_reporte, dict):
                    datos_reporte['resumen_datos'] = {
                        'claves': list(reporte.datos_reporte.keys()),
                        'tamaño_aproximado': len(str(reporte.datos_reporte))
                    }
            else:
                datos_reporte['datos_disponibles'] = False
            
            reportes_data.append(datos_reporte)
        
        # Registrar actividad
        try:
            self.log_activity(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                tarjeta="reportes",
                accion="view_data",
                descripcion=f"Consulta de reportes financieros - {len(reportes_data)} reportes",
                usuario=request.user,
                detalles={
                    "cierre_id": cierre.id,
                    "tipo_filtro": tipo_filtro,
                    "incluir_datos": incluir_datos,
                    "reportes_encontrados": len(reportes_data)
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            print(f"Error registrando actividad en consultar_reportes: {e}")
        
        return Response({
            'cierre_id': cierre.id,
            'cierre_periodo': cierre.periodo,
            'cliente_nombre': cierre.cliente.nombre,
            'estado_cierre': cierre.estado,
            'reportes': reportes_data,
            'total_reportes': len(reportes_data),
            'tipos_disponibles': ['esf', 'eri', 'ecp'],
            'metadata': {
                'incluir_datos': incluir_datos,
                'tipo_filtro': tipo_filtro,
                'fecha_consulta': timezone.now().isoformat()
            }
        })

    @action(detail=True, methods=["delete"], url_path="reportes/(?P<reporte_id>[^/.]+)")
    def eliminar_reporte(self, request, pk=None, reporte_id=None):
        """
        Elimina un reporte financiero específico (para regeneración o limpieza).
        """
        cierre = self.get_object()
        
        # Validar permisos (solo en estado sin_incidencias o generando_reportes)
        if cierre.estado not in ['sin_incidencias', 'generando_reportes']:
            return Response({
                'error': 'Operación no permitida',
                'message': 'Solo se pueden eliminar reportes en estado sin_incidencias o generando_reportes'
            }, status=403)
        
        try:
            from ..models import ReporteFinanciero
            reporte = ReporteFinanciero.objects.get(
                id=reporte_id,
                cierre=cierre
            )
            
            tipo_reporte = reporte.tipo_reporte
            tipo_display = reporte.get_tipo_reporte_display()
            
            reporte.delete()
            
            # Registrar actividad
            try:
                self.log_activity(
                    cliente_id=cierre.cliente.id,
                    periodo=cierre.periodo,
                    tarjeta="reportes",
                    accion="manual_delete",
                    descripcion=f"Eliminación manual de reporte: {tipo_display}",
                    usuario=request.user,
                    detalles={
                        "cierre_id": cierre.id,
                        "reporte_id": int(reporte_id),
                        "tipo_reporte": tipo_reporte,
                        "tipo_display": tipo_display
                    },
                    resultado="exito",
                    ip_address=request.META.get("REMOTE_ADDR"),
                )
            except Exception as e:
                print(f"Error registrando actividad en eliminar_reporte: {e}")
            
            return Response({
                'success': True,
                'message': f'Reporte {tipo_display} eliminado exitosamente',
                'reporte_eliminado': {
                    'id': int(reporte_id),
                    'tipo': tipo_reporte,
                    'tipo_display': tipo_display
                }
            })
            
        except ReporteFinanciero.DoesNotExist:
            return Response({
                'error': 'Reporte no encontrado',
                'message': f'No existe un reporte con ID {reporte_id} para este cierre'
            }, status=404)
        except Exception as e:
            return Response({
                'error': 'Error interno',
                'message': f'Error eliminando reporte: {str(e)}'
            }, status=500)
