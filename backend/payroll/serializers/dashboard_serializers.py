# ============================================================================
#                           DASHBOARD SERIALIZERS
# ============================================================================
# Serializers para dashboard y estadísticas del sistema payroll

try:
    from rest_framework import serializers
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    from ..models import CierrePayroll, Empleados_Cierre, Incidencias_Cierre, Logs_Actividad
    
    
    class DashboardStatsSerializer(serializers.Serializer):
        """
        Serializer para estadísticas principales del dashboard
        """
        # Estadísticas generales
        total_cierres = serializers.IntegerField()
        cierres_mes = serializers.IntegerField()
        cierres_pendientes = serializers.IntegerField()
        cierres_procesando = serializers.IntegerField()
        cierres_completados = serializers.IntegerField()
        
        # Estadísticas de empleados
        total_empleados = serializers.IntegerField()
        empleados_procesados_hoy = serializers.IntegerField()
        
        # Estadísticas de incidencias
        incidencias_abiertas = serializers.IntegerField()
        incidencias_criticas = serializers.IntegerField()
        
        # Estadísticas de actividad
        operaciones_hoy = serializers.IntegerField()
        errores_hoy = serializers.IntegerField()
        
        # Fechas de referencia
        fecha_actualizacion = serializers.DateTimeField()
        
        @classmethod
        def get_dashboard_stats(cls):
            """Método para obtener todas las estadísticas del dashboard"""
            now = timezone.now()
            hoy = now.replace(hour=0, minute=0, second=0, microsecond=0)
            mes_actual = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            return {
                # Cierres
                'total_cierres': CierrePayroll.objects.count(),
                'cierres_mes': CierrePayroll.objects.filter(fecha_creacion__gte=mes_actual).count(),
                'cierres_pendientes': CierrePayroll.objects.filter(estado='pendiente').count(),
                'cierres_procesando': CierrePayroll.objects.filter(estado='procesando').count(),
                'cierres_completados': CierrePayroll.objects.filter(estado='completado').count(),
                
                # Empleados
                'total_empleados': Empleados_Cierre.objects.count(),
                'empleados_procesados_hoy': Empleados_Cierre.objects.filter(
                    fecha_procesamiento__gte=hoy
                ).count(),
                
                # Incidencias
                'incidencias_abiertas': Incidencias_Cierre.objects.filter(estado='abierta').count(),
                'incidencias_criticas': Incidencias_Cierre.objects.filter(
                    estado='abierta', 
                    prioridad='critica'
                ).count(),
                
                # Actividad
                'operaciones_hoy': Logs_Actividad.objects.filter(timestamp__gte=hoy).count(),
                'errores_hoy': Logs_Actividad.objects.filter(
                    timestamp__gte=hoy,
                    resultado='error'
                ).count(),
                
                'fecha_actualizacion': now,
            }
    
    
    class ResumenCierreSerializer(serializers.Serializer):
        """
        Serializer para resumen detallado de un cierre
        """
        cierre_id = serializers.IntegerField()
        cliente_nombre = serializers.CharField()
        periodo = serializers.CharField()
        estado = serializers.CharField()
        estado_display = serializers.CharField()
        
        # Estadísticas de empleados
        empleados_total = serializers.IntegerField()
        empleados_procesados = serializers.IntegerField()
        empleados_pendientes = serializers.IntegerField()
        empleados_con_errores = serializers.IntegerField()
        total_liquido = serializers.DecimalField(max_digits=15, decimal_places=2)
        
        # Estadísticas de items
        items_total = serializers.IntegerField()
        items_haberes = serializers.IntegerField()
        items_descuentos = serializers.IntegerField()
        items_variables = serializers.IntegerField()
        
        # Estadísticas de incidencias
        incidencias_total = serializers.IntegerField()
        incidencias_abiertas = serializers.IntegerField()
        incidencias_resueltas = serializers.IntegerField()
        incidencias_criticas = serializers.IntegerField()
        
        # Progreso y tiempo
        progreso_porcentaje = serializers.FloatField()
        tiempo_procesamiento = serializers.DictField()
        
        @classmethod
        def get_resumen_cierre(cls, cierre):
            """Método para obtener resumen completo de un cierre"""
            empleados = cierre.empleados_cierre.all()
            items = cierre.item_cierre.all()
            incidencias = cierre.incidencias_cierre.all()
            
            # Calcular tiempo de procesamiento
            tiempo_procesamiento = None
            if cierre.fecha_inicio_procesamiento and cierre.fecha_fin_procesamiento:
                delta = cierre.fecha_fin_procesamiento - cierre.fecha_inicio_procesamiento
                tiempo_procesamiento = {
                    'total_seconds': delta.total_seconds(),
                    'horas': delta.total_seconds() / 3600,
                    'formatted': str(delta)
                }
            
            return {
                'cierre_id': cierre.id,
                'cliente_nombre': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': cierre.estado,
                'estado_display': cierre.get_estado_display(),
                
                # Empleados
                'empleados_total': empleados.count(),
                'empleados_procesados': empleados.filter(estado_procesamiento='procesado').count(),
                'empleados_pendientes': empleados.filter(estado_procesamiento='pendiente').count(),
                'empleados_con_errores': empleados.filter(estado_procesamiento='error').count(),
                'total_liquido': empleados.aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0,
                
                # Items
                'items_total': items.count(),
                'items_haberes': items.filter(tipo_item='haberes').count(),
                'items_descuentos': items.filter(tipo_item='descuentos').count(),
                'items_variables': items.filter(es_variable=True).count(),
                
                # Incidencias
                'incidencias_total': incidencias.count(),
                'incidencias_abiertas': incidencias.filter(estado='abierta').count(),
                'incidencias_resueltas': incidencias.filter(estado='resuelta').count(),
                'incidencias_criticas': incidencias.filter(prioridad='critica').count(),
                
                # Progreso
                'progreso_porcentaje': cierre.get_progreso_porcentaje() if hasattr(cierre, 'get_progreso_porcentaje') else 0,
                'tiempo_procesamiento': tiempo_procesamiento,
            }
    
    
    class EstadisticasSerializer(serializers.Serializer):
        """
        Serializer para estadísticas avanzadas del sistema
        """
        periodo_analisis = serializers.CharField()
        fecha_desde = serializers.DateTimeField()
        fecha_hasta = serializers.DateTimeField()
        
        # Estadísticas por periodo
        cierres_por_mes = serializers.ListField()
        empleados_por_mes = serializers.ListField()
        
        # Estadísticas por cliente
        cierres_por_cliente = serializers.ListField()
        
        # Rendimiento
        tiempo_promedio_procesamiento = serializers.FloatField()
        tasa_exito = serializers.FloatField()
        
        # Tendencias
        tendencia_cierres = serializers.CharField()
        tendencia_empleados = serializers.CharField()
        
        @classmethod
        def get_estadisticas(cls, periodo_meses=6):
            """Método para obtener estadísticas del sistema"""
            now = timezone.now()
            fecha_desde = now - timedelta(days=30 * periodo_meses)
            
            cierres = CierrePayroll.objects.filter(fecha_creacion__gte=fecha_desde)
            
            # Estadísticas por mes
            cierres_por_mes = list(cierres.extra(
                select={'mes': "DATE_FORMAT(fecha_creacion, '%%Y-%%m')"}
            ).values('mes').annotate(
                total_cierres=Count('id'),
                total_empleados=Count('empleados_cierre')
            ).order_by('mes'))
            
            # Estadísticas por cliente
            cierres_por_cliente = list(cierres.values(
                'cliente__nombre'
            ).annotate(
                total_cierres=Count('id'),
                promedio_empleados=Avg('empleados_cierre__count')
            ).order_by('-total_cierres')[:10])
            
            # Tiempo promedio de procesamiento
            cierres_completados = cierres.filter(
                estado='completado',
                fecha_inicio_procesamiento__isnull=False,
                fecha_fin_procesamiento__isnull=False
            )
            
            tiempo_promedio = 0
            if cierres_completados.exists():
                tiempos = []
                for cierre in cierres_completados:
                    delta = cierre.fecha_fin_procesamiento - cierre.fecha_inicio_procesamiento
                    tiempos.append(delta.total_seconds() / 3600)  # En horas
                tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
            
            # Tasa de éxito
            total = cierres.count()
            exitosos = cierres.filter(estado='completado').count()
            tasa_exito = (exitosos / total * 100) if total > 0 else 0
            
            return {
                'periodo_analisis': f'{periodo_meses} meses',
                'fecha_desde': fecha_desde,
                'fecha_hasta': now,
                'cierres_por_mes': cierres_por_mes,
                'empleados_por_mes': [],  # Se puede implementar después
                'cierres_por_cliente': cierres_por_cliente,
                'tiempo_promedio_procesamiento': tiempo_promedio,
                'tasa_exito': tasa_exito,
                'tendencia_cierres': 'estable',  # Se puede calcular tendencia
                'tendencia_empleados': 'estable',
            }
    
    
    class ActividadTiempoRealSerializer(serializers.Serializer):
        """
        Serializer para actividad en tiempo real
        """
        eventos = serializers.ListField()
        total_eventos = serializers.IntegerField()
        periodo_minutos = serializers.IntegerField()
        ultima_actualizacion = serializers.DateTimeField()
        
        @classmethod
        def get_actividad_tiempo_real(cls, minutos=30):
            """Método para obtener actividad reciente"""
            desde = timezone.now() - timedelta(minutes=minutos)
            
            logs = Logs_Actividad.objects.filter(
                timestamp__gte=desde
            ).select_related('cierre_payroll__cliente', 'usuario').order_by('-timestamp')[:20]
            
            eventos = []
            for log in logs:
                eventos.append({
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'usuario': log.usuario.username,
                    'accion': log.get_accion_display(),
                    'resultado': log.resultado,
                    'cierre': f"{log.cierre_payroll.cliente.nombre} - {log.cierre_payroll.periodo}" if log.cierre_payroll else 'Sistema',
                    'descripcion_corta': log.descripcion[:50] + '...' if len(log.descripcion) > 50 else log.descripcion
                })
            
            return {
                'eventos': eventos,
                'total_eventos': len(eventos),
                'periodo_minutos': minutos,
                'ultima_actualizacion': timezone.now(),
            }

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class DashboardStatsSerializer:
        pass
    
    class ResumenCierreSerializer:
        pass
    
    class EstadisticasSerializer:
        pass
    
    class ActividadTiempoRealSerializer:
        pass
