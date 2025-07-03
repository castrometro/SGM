from django.db.models import Sum, Q
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
        
        # Query base optimizada con select_related para evitar N+1 queries
        movimientos = MovimientoContable.objects.filter(cierre=cierre).select_related(
            'cuenta', 'tipo_documento', 'centro_costo', 'auxiliar'
        )
        
        # Filtrado por clasificación
        cuentas_filtradas = None
        if set_id and opcion_id:
            cuentas_filtradas = AccountClassification.objects.filter(
                set_clas_id=set_id, opcion_id=opcion_id
            ).values_list("cuenta_id", flat=True)
            movimientos = movimientos.filter(cuenta_id__in=cuentas_filtradas)
        
        # Filtrado por fechas
        if fecha_desde:
            movimientos = movimientos.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(fecha__lte=fecha_hasta)
        
        # Filtrado por búsqueda en código/nombre de cuenta
        if search:
            movimientos = movimientos.filter(
                Q(cuenta__codigo__icontains=search) | 
                Q(cuenta__nombre__icontains=search)
            )
        
        # Calcular totales por cuenta con información adicional
        totales_query = (
            movimientos.values(
                "cuenta_id", 
                "cuenta__codigo", 
                "cuenta__nombre",
                "cuenta__nombre_en"  # Incluir nombre en inglés si existe
            )
            .annotate(
                total_debe=Sum("debe"), 
                total_haber=Sum("haber")
            )
            .order_by("cuenta__codigo")
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
        
        # Construir datos de respuesta enriquecidos
        data = []
        for t in totales_procesados:
            cuenta_id = t["cuenta_id"]
            saldo_anterior = mapa_aperturas.get(cuenta_id, 0)
            saldo_final = saldo_anterior + (t["total_debe"] or 0) - (t["total_haber"] or 0)
            
            item = {
                "cuenta_id": cuenta_id,
                "total_debe": t["total_debe"] or 0,
                "total_haber": t["total_haber"] or 0,
                "saldo_final": saldo_final,
                "saldo_anterior": saldo_anterior,  # Siempre incluir saldo_anterior
            }
            
            # Agregar información adicional si hay paginación (API extendida)
            if usar_paginacion:
                item.update({
                    "cuenta_codigo": t["cuenta__codigo"],
                    "cuenta_nombre": t["cuenta__nombre"],
                    "cuenta_nombre_en": t["cuenta__nombre_en"],
                })
            else:
                # Para compatibilidad con AnalisisLibro.jsx que espera 'codigo' y 'nombre'
                item.update({
                    "codigo": t["cuenta__codigo"],
                    "nombre": t["cuenta__nombre"],
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
