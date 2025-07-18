from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones, 
    MovimientoVariacionSueldo, MovimientoVariacionContrato,
    LibroRemuneracionesUpload, MovimientosMesUpload, ArchivoAnalistaUpload, 
    ArchivoNovedadesUpload, ChecklistItem,
    AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso,
    # Modelos de novedades
    EmpleadoCierreNovedades, ConceptoRemuneracionNovedades, RegistroConceptoEmpleadoNovedades,
    # Modelos de incidencias
    IncidenciaCierre, ResolucionIncidencia,
    # Modelos de análisis y discrepancias
    AnalisisDatosCierre, IncidenciaVariacionSalarial, DiscrepanciaCierre
)


@admin.register(CierreNomina)
class CierreNominaAdmin(admin.ModelAdmin):
    list_display = (
        'cliente', 
        'periodo', 
        'estado', 
        'estado_incidencias', 
        'total_incidencias',
        'incidencias_pendientes',
        'fecha_creacion', 
        'usuario_analista'
    )
    list_filter = ('cliente', 'estado', 'estado_incidencias', 'periodo')
    search_fields = ('cliente__nombre', 'periodo')
    readonly_fields = ('fecha_creacion', 'resumen_incidencias')
    fieldsets = (
        ('Información General', {
            'fields': ('cliente', 'periodo', 'usuario_analista', 'fecha_creacion')
        }),
        ('Estados', {
            'fields': ('estado', 'estado_incidencias')
        }),
        ('Resumen de Incidencias', {
            'fields': ('resumen_incidencias',),
            'classes': ('collapse',)
        })
    )
    
    def total_incidencias(self, obj):
        """Total de incidencias del cierre"""
        return obj.incidencias.count()
    total_incidencias.short_description = 'Total Incidencias'
    
    def incidencias_pendientes(self, obj):
        """Incidencias pendientes"""
        pendientes = obj.incidencias.filter(estado='pendiente').count()
        if pendientes > 0:
            return format_html('<span style="color: #f59e0b; font-weight: bold;">{}</span>', pendientes)
        return pendientes
    incidencias_pendientes.short_description = 'Pendientes'
    
    def resumen_incidencias(self, obj):
        """Resumen detallado de incidencias para readonly"""
        incidencias = obj.incidencias.all()
        if not incidencias.exists():
            return "No hay incidencias generadas"
        
        total = incidencias.count()
        por_estado = {
            'pendiente': incidencias.filter(estado='pendiente').count(),
            'resuelta_analista': incidencias.filter(estado='resuelta_analista').count(),
            'aprobada_supervisor': incidencias.filter(estado='aprobada_supervisor').count(),
            'rechazada_supervisor': incidencias.filter(estado='rechazada_supervisor').count(),
        }
        por_prioridad = {
            'critica': incidencias.filter(prioridad='critica').count(),
            'alta': incidencias.filter(prioridad='alta').count(),
            'media': incidencias.filter(prioridad='media').count(),
            'baja': incidencias.filter(prioridad='baja').count(),
        }
        
        return f"""
        TOTAL: {total} incidencias
        
        Por Estado:
        - Pendientes: {por_estado['pendiente']}
        - Resueltas por Analista: {por_estado['resuelta_analista']}
        - Aprobadas por Supervisor: {por_estado['aprobada_supervisor']}
        - Rechazadas por Supervisor: {por_estado['rechazada_supervisor']}
        
        Por Prioridad:
        - Críticas: {por_prioridad['critica']}
        - Altas: {por_prioridad['alta']}
        - Medias: {por_prioridad['media']}
        - Bajas: {por_prioridad['baja']}
        """
    resumen_incidencias.short_description = 'Resumen de Incidencias'


@admin.register(EmpleadoCierre)
class EmpleadoCierreAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut_empresa', 'dias_trabajados', 'cierre')
    search_fields = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno')
    list_filter = ('cierre__cliente', 'cierre__periodo')


@admin.register(ConceptoRemuneracion)
class ConceptoRemuneracionAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'nombre_concepto',
        'clasificacion',
        'usuario_clasifica',
        'vigente',
    )
    list_filter = ('cliente', 'clasificacion', 'vigente')
    search_fields = ('cliente__nombre', 'nombre_concepto')


@admin.register(RegistroConceptoEmpleado)
class RegistroConceptoEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'concepto', 'nombre_concepto_original', 'monto')
    search_fields = ('empleado__rut', 'nombre_concepto_original')


# Nuevos admins para los modelos de Movimientos_Mes

@admin.register(MovimientoAltaBaja)
class MovimientoAltaBajaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'empresa_nombre', 'alta_o_baja', 'fecha_ingreso', 'fecha_retiro', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'alta_o_baja', 'empresa_nombre')
    readonly_fields = ('empleado',)
    date_hierarchy = 'fecha_ingreso'
    readonly_fields = ('empleado',)


@admin.register(MovimientoAusentismo)
class MovimientoAusentismoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'tipo', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'tipo', 'motivo')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'tipo', 'empresa_nombre')
    readonly_fields = ('empleado',)
    date_hierarchy = 'fecha_inicio_ausencia'


@admin.register(MovimientoVacaciones)
class MovimientoVacacionesAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'fecha_inicio', 'fecha_fin_vacaciones', 'cantidad_dias', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'empresa_nombre')
    readonly_fields = ('empleado',)
    date_hierarchy = 'fecha_inicio'


@admin.register(MovimientoVariacionSueldo)
class MovimientoVariacionSueldoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'sueldo_base_anterior', 'sueldo_base_actual', 'porcentaje_reajuste', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'empresa_nombre')
    readonly_fields = ('empleado', 'variacion_pesos')
    date_hierarchy = 'fecha_ingreso'


@admin.register(MovimientoVariacionContrato)
class MovimientoVariacionContratoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'tipo_contrato_anterior', 'tipo_contrato_actual', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'empresa_nombre', 'tipo_contrato_anterior', 'tipo_contrato_actual')
    readonly_fields = ('empleado',)
    date_hierarchy = 'fecha_ingreso'
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'tipo_contrato_anterior', 'tipo_contrato_actual', 'empresa_nombre')
    readonly_fields = ('empleado',)


@admin.register(LibroRemuneracionesUpload)
class LibroRemuneracionesUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'fecha_subida', 'estado')
    list_filter = ('estado',)
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')


@admin.register(MovimientosMesUpload)
class MovimientosMesUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'fecha_subida', 'estado', 'resumen_procesamiento')
    list_filter = ('estado', 'fecha_subida')
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')
    readonly_fields = ('fecha_subida', 'resumen_procesamiento_detalle')
    
    def resumen_procesamiento(self, obj):
        """Muestra un resumen del procesamiento en la lista"""
        if obj.resultados_procesamiento:
            total = sum([v for k, v in obj.resultados_procesamiento.items() 
                        if k != 'errores' and isinstance(v, int)])
            errores = len(obj.resultados_procesamiento.get('errores', []))
            if errores > 0:
                return f"{total} registros ({errores} errores)"
            return f"{total} registros"
        return "-"
    resumen_procesamiento.short_description = "Resumen"
    
    def resumen_procesamiento_detalle(self, obj):
        """Muestra detalles completos del procesamiento"""
        if not obj.resultados_procesamiento:
            return "Sin datos de procesamiento"
        
        resultados = obj.resultados_procesamiento
        detalle = []
        
        # Mostrar conteos por tipo
        if resultados.get('altas_bajas', 0) > 0:
            detalle.append(f"Altas/Bajas: {resultados['altas_bajas']}")
        if resultados.get('ausentismos', 0) > 0:
            detalle.append(f"Ausentismos: {resultados['ausentismos']}")
        if resultados.get('vacaciones', 0) > 0:
            detalle.append(f"Vacaciones: {resultados['vacaciones']}")
        if resultados.get('variaciones_sueldo', 0) > 0:
            detalle.append(f"Variaciones Sueldo: {resultados['variaciones_sueldo']}")
        if resultados.get('variaciones_contrato', 0) > 0:
            detalle.append(f"Variaciones Contrato: {resultados['variaciones_contrato']}")
        
        # Mostrar errores si los hay
        errores = resultados.get('errores', [])
        if errores:
            detalle.append(f"\nErrores ({len(errores)}):")
            for error in errores:
                detalle.append(f"- {error}")
        
        return "\n".join(detalle) if detalle else "Sin datos procesados"
    resumen_procesamiento_detalle.short_description = "Detalle del Procesamiento"


@admin.register(ArchivoAnalistaUpload)
class ArchivoAnalistaUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'tipo_archivo', 'fecha_subida', 'estado', 'analista')
    list_filter = ('tipo_archivo', 'estado')
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')


@admin.register(ArchivoNovedadesUpload)
class ArchivoNovedadesUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'fecha_subida', 'estado', 'analista')
    list_filter = ('estado',)
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'descripcion', 'estado', 'fecha_creacion', 'fecha_modificacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('descripcion', 'comentario')


# Nuevos admins para los modelos del Analista

@admin.register(AnalistaFiniquito)
class AnalistaFiniquitoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'fecha_retiro', 'motivo', 'cierre', 'archivo_origen')
    search_fields = ('rut', 'nombre', 'motivo')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'fecha_retiro', 'archivo_origen')
    readonly_fields = ('empleado', 'archivo_origen')
    date_hierarchy = 'fecha_retiro'


@admin.register(AnalistaIncidencia)
class AnalistaIncidenciaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'tipo_ausentismo', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias', 'cierre')
    search_fields = ('rut', 'nombre', 'tipo_ausentismo')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'tipo_ausentismo', 'archivo_origen')
    readonly_fields = ('empleado', 'archivo_origen')
    date_hierarchy = 'fecha_inicio_ausencia'


@admin.register(AnalistaIngreso)
class AnalistaIngresoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'fecha_ingreso', 'cierre', 'archivo_origen')
    search_fields = ('rut', 'nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'fecha_ingreso', 'archivo_origen')
    readonly_fields = ('empleado', 'archivo_origen')
    date_hierarchy = 'fecha_ingreso'


# Nuevos admins para los modelos de Novedades

@admin.register(EmpleadoCierreNovedades)
class EmpleadoCierreNovedadesAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'cierre')
    search_fields = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno')
    list_filter = ('cierre__cliente', 'cierre__periodo')
    readonly_fields = ('cierre',)


@admin.register(ConceptoRemuneracionNovedades)
class ConceptoRemuneracionNovedadesAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'nombre_concepto_novedades',
        'concepto_libro',
        'usuario_mapea',
        'activo',
        'fecha_mapeo',
    )
    list_filter = ('cliente', 'activo', 'concepto_libro__clasificacion', 'fecha_mapeo')
    search_fields = ('cliente__nombre', 'nombre_concepto_novedades', 'concepto_libro__nombre_concepto')
    readonly_fields = ('fecha_mapeo',)
    raw_id_fields = ('concepto_libro',)


@admin.register(RegistroConceptoEmpleadoNovedades)
class RegistroConceptoEmpleadoNovedadesAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'concepto', 'nombre_concepto_original', 'monto', 'fecha_registro')
    search_fields = ('empleado__rut', 'nombre_concepto_original')
    list_filter = ('concepto__concepto_libro__clasificacion', 'concepto__activo', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    date_hierarchy = 'fecha_registro'


# ========== ADMINISTRACIÓN DE INCIDENCIAS ==========

class ResolucionIncidenciaInline(admin.TabularInline):
    """Inline para mostrar resoluciones dentro de una incidencia"""
    model = ResolucionIncidencia
    extra = 0
    readonly_fields = ('fecha_resolucion',)
    fields = ('tipo_resolucion', 'usuario', 'comentario', 'valor_corregido', 'fecha_resolucion')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')


@admin.register(IncidenciaCierre)
class IncidenciaCierreAdmin(admin.ModelAdmin):
    """Administración de incidencias de cierre"""
    list_display = (
        'id',
        'cierre_info',
        'rut_empleado',
        'tipo_incidencia_display',
        'prioridad_display', 
        'estado_display',
        'asignado_a',
        'impacto_monetario',
        'fecha_detectada'
    )
    list_filter = (
        'prioridad',
        'estado', 
        'tipo_incidencia',
        'cierre__cliente',
        'cierre__periodo',
        'fecha_detectada',
        'asignado_a'
    )
    search_fields = (
        'rut_empleado',
        'descripcion',
        'concepto_afectado',
        'empleado_libro__nombre',
        'empleado_libro__apellido_paterno',
        'empleado_novedades__nombre',
        'empleado_novedades__apellido_paterno'
    )
    readonly_fields = (
        'fecha_detectada',
        'fecha_primera_resolucion',
        'cierre_info_detailed'
    )
    fieldsets = (
        ('Información General', {
            'fields': (
                'cierre',
                'cierre_info_detailed',
                'tipo_incidencia',
                'rut_empleado',
                'descripcion'
            )
        }),
        ('Clasificación', {
            'fields': (
                'prioridad',
                'estado', 
                'asignado_a',
                'concepto_afectado'
            )
        }),
        ('Valores Comparados', {
            'fields': (
                'valor_libro',
                'valor_novedades',
                'valor_movimientos',
                'valor_analista',
                'impacto_monetario'
            ),
            'classes': ('collapse',)
        }),
        ('Referencias', {
            'fields': (
                'empleado_libro',
                'empleado_novedades'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'fecha_detectada',
                'fecha_primera_resolucion'
            )
        })
    )
    inlines = [ResolucionIncidenciaInline]
    date_hierarchy = 'fecha_detectada'
    list_per_page = 50
    
    def cierre_info(self, obj):
        """Info básica del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def cierre_info_detailed(self, obj):
        """Info detallada del cierre para readonly"""
        return f"""
        Cliente: {obj.cierre.cliente.nombre}
        Período: {obj.cierre.periodo}
        Estado Cierre: {obj.cierre.get_estado_display()}
        Analista: {obj.cierre.usuario_analista or 'No asignado'}
        """
    cierre_info_detailed.short_description = 'Información del Cierre'
    
    def tipo_incidencia_display(self, obj):
        """Display mejorado del tipo de incidencia"""
        return obj.get_tipo_incidencia_display()
    tipo_incidencia_display.short_description = 'Tipo'
    
    def prioridad_display(self, obj):
        """Display con colores para prioridad"""
        colors = {
            'critica': '#dc2626',    # rojo
            'alta': '#ea580c',       # naranja
            'media': '#d97706',      # amarillo
            'baja': '#16a34a'        # verde
        }
        color = colors.get(obj.prioridad, '#6b7280')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}', color, obj.prioridad.title())
    prioridad_display.short_description = 'Prioridad'
    
    def estado_display(self, obj):
        """Display con colores para estado"""
        colors = {
            'pendiente': '#f59e0b',           # amarillo
            'resuelta_analista': '#3b82f6',   # azul
            'aprobada_supervisor': '#10b981', # verde
            'rechazada_supervisor': '#ef4444' # rojo
        }
        color = colors.get(obj.estado, '#6b7280')
        return format_html('<span style="color: {};">●</span> {}', color, obj.get_estado_display())
    estado_display.short_description = 'Estado'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente',
            'cierre__usuario_analista',
            'empleado_libro',
            'empleado_novedades',
            'asignado_a'
        )


@admin.register(ResolucionIncidencia)
class ResolucionIncidenciaAdmin(admin.ModelAdmin):
    """Administración de resoluciones de incidencias"""
    list_display = (
        'incidencia_info',
        'tipo_resolucion_display',
        'usuario',
        'comentario_resumido',
        'valor_corregido',
        'fecha_resolucion'
    )
    list_filter = (
        'tipo_resolucion',
        'incidencia__prioridad',
        'incidencia__estado',
        'incidencia__cierre__cliente',
        'fecha_resolucion',
        'usuario'
    )
    search_fields = (
        'comentario',
        'valor_corregido',
        'campo_corregido',
        'incidencia__rut_empleado',
        'incidencia__descripcion',
        'usuario__correo_bdo',
        'usuario__first_name',
        'usuario__last_name'
    )
    readonly_fields = ('fecha_resolucion',)
    fieldsets = (
        ('Información General', {
            'fields': (
                'incidencia',
                'usuario',
                'tipo_resolucion',
                'fecha_resolucion'
            )
        }),
        ('Resolución', {
            'fields': (
                'comentario',
                'valor_corregido',
                'campo_corregido',
                'adjunto'
            )
        }),
        ('Colaboración', {
            'fields': ('usuarios_mencionados',),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_resolucion'
    list_per_page = 100
    
    def incidencia_info(self, obj):
        """Info de la incidencia relacionada"""
        return f"#{obj.incidencia.id} - {obj.incidencia.rut_empleado} ({obj.incidencia.get_prioridad_display()})"
    incidencia_info.short_description = 'Incidencia'
    
    def tipo_resolucion_display(self, obj):
        """Display mejorado del tipo de resolución"""
        icons = {
            'comentario': '💬',
            'solucion': '✅',
            'correccion': '🔧',
            'rechazo': '❌'
        }
        icon = icons.get(obj.tipo_resolucion, '📝')
        return f"{icon} {obj.get_tipo_resolucion_display()}"
    tipo_resolucion_display.short_description = 'Tipo'
    
    def comentario_resumido(self, obj):
        """Comentario truncado para la lista"""
        if obj.comentario:
            return (obj.comentario[:100] + '...') if len(obj.comentario) > 100 else obj.comentario
        return '-'
    comentario_resumido.short_description = 'Comentario'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'incidencia',
            'incidencia__cierre',
            'incidencia__cierre__cliente',
            'usuario'
        ).prefetch_related('usuarios_mencionados')


# ========== ACCIONES PERSONALIZADAS ==========

@admin.action(description='Asignar incidencias seleccionadas a mí')
def asignar_incidencias_a_mi(modeladmin, request, queryset):
    """Acción para asignarse incidencias"""
    count = queryset.update(asignado_a=request.user)
    modeladmin.message_user(
        request,
        f'{count} incidencia(s) asignada(s) a {request.user.get_full_name() or request.user.correo_bdo}'
    )

@admin.action(description='Marcar como pendientes')
def marcar_como_pendientes(modeladmin, request, queryset):
    """Acción para marcar incidencias como pendientes"""
    count = queryset.update(estado='pendiente')
    modeladmin.message_user(request, f'{count} incidencia(s) marcada(s) como pendiente(s)')

@admin.action(description='Marcar como resueltas por analista')
def marcar_como_resueltas(modeladmin, request, queryset):
    """Acción para marcar incidencias como resueltas"""
    count = queryset.update(estado='resuelta_analista')
    modeladmin.message_user(request, f'{count} incidencia(s) marcada(s) como resuelta(s)')

# Agregar acciones al admin de incidencias
IncidenciaCierreAdmin.actions = [
    asignar_incidencias_a_mi,
    marcar_como_pendientes,
    marcar_como_resueltas
]


# ========== ADMINISTRACIÓN DE ANÁLISIS DE DATOS ==========

@admin.register(AnalisisDatosCierre)
class AnalisisDatosCierreAdmin(admin.ModelAdmin):
    """Administración de análisis de datos de cierre"""
    list_display = (
        'cierre_info',
        'analista_display',
        'estado_display',
        'variacion_empleados',
        'variacion_ingresos',
        'fecha_analisis',
        'fecha_completado'
    )
    list_filter = (
        'estado',
        'cierre__cliente',
        'cierre__periodo',
        'fecha_analisis',
        'analista'
    )
    search_fields = (
        'cierre__cliente__nombre',
        'cierre__periodo',
        'analista__correo_bdo',
        'analista__first_name',
        'analista__last_name'
    )
    readonly_fields = (
        'fecha_analisis',
        'fecha_completado',
        'variacion_empleados',
        'variacion_ingresos',
        'variacion_finiquitos',
        'variacion_ausentismos'
    )
    fieldsets = (
        ('Información General', {
            'fields': (
                'cierre',
                'analista',
                'tolerancia_variacion_salarial',
                'estado'
            )
        }),
        ('Datos Actuales', {
            'fields': (
                'cantidad_empleados_actual',
                'cantidad_ingresos_actual',
                'cantidad_finiquitos_actual',
                'cantidad_ausentismos_actual'
            )
        }),
        ('Datos Mes Anterior', {
            'fields': (
                'cantidad_empleados_anterior',
                'cantidad_ingresos_anterior',
                'cantidad_finiquitos_anterior',
                'cantidad_ausentismos_anterior'
            )
        }),
        ('Variaciones Calculadas', {
            'fields': (
                'variacion_empleados',
                'variacion_ingresos',
                'variacion_finiquitos',
                'variacion_ausentismos'
            ),
            'classes': ('collapse',)
        }),
        ('Ausentismos por Tipo', {
            'fields': (
                'ausentismos_por_tipo_actual',
                'ausentismos_por_tipo_anterior'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'fecha_analisis',
                'fecha_completado'
            )
        }),
        ('Notas', {
            'fields': ('notas',)
        })
    )
    date_hierarchy = 'fecha_analisis'
    list_per_page = 50
    
    def cierre_info(self, obj):
        """Info básica del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def analista_display(self, obj):
        """Mostrar analista con formato"""
        if obj.analista:
            return f"{obj.analista.get_full_name() or obj.analista.correo_bdo}"
        return "-"
    analista_display.short_description = 'Analista'
    
    def estado_display(self, obj):
        """Estado con color"""
        colors = {
            'pendiente': '#fbbf24',
            'procesando': '#3b82f6',
            'completado': '#10b981',
            'error': '#ef4444'
        }
        color = colors.get(obj.estado, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def variacion_empleados(self, obj):
        variaciones = obj.calcular_variaciones()
        return f"{variaciones['empleados']:.1f}%"
    variacion_empleados.short_description = "Variación Empleados"
    
    def variacion_ingresos(self, obj):
        variaciones = obj.calcular_variaciones()
        return f"{variaciones['ingresos']:.1f}%"
    variacion_ingresos.short_description = "Variación Ingresos"
    
    def variacion_finiquitos(self, obj):
        variaciones = obj.calcular_variaciones()
        return f"{variaciones['finiquitos']:.1f}%"
    variacion_finiquitos.short_description = "Variación Finiquitos"
    
    def variacion_ausentismos(self, obj):
        variaciones = obj.calcular_variaciones()
        return f"{variaciones['ausentismos']:.1f}%"
    variacion_ausentismos.short_description = "Variación Ausentismos"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre', 
            'cierre__cliente', 
            'analista'
        )


@admin.register(IncidenciaVariacionSalarial)
class IncidenciaVariacionSalarialAdmin(admin.ModelAdmin):
    """Administración de incidencias de variación salarial"""
    list_display = (
        'empleado_info',
        'cierre_info',
        'variacion_display',
        'tipo_variacion',
        'estado_display',
        'analista_asignado',
        'fecha_deteccion'
    )
    list_filter = (
        'estado',
        'tipo_variacion',
        'cierre__cliente',
        'cierre__periodo',
        'fecha_deteccion',
        'analista_asignado',
        'supervisor_revisor'
    )
    search_fields = (
        'rut_empleado',
        'nombre_empleado',
        'justificacion_analista',
        'comentario_supervisor',
        'cierre__cliente__nombre'
    )
    readonly_fields = (
        'fecha_deteccion',
        'fecha_justificacion',
        'fecha_resolucion_supervisor',
        'fecha_ultima_accion',
        'variacion_info_detailed'
    )
    fieldsets = (
        ('Información del Empleado', {
            'fields': (
                'rut_empleado',
                'nombre_empleado',
                'variacion_info_detailed'
            )
        }),
        ('Detalles de la Variación', {
            'fields': (
                'sueldo_base_anterior',
                'sueldo_base_actual',
                'porcentaje_variacion',
                'tipo_variacion'
            )
        }),
        ('Gestión', {
            'fields': (
                'estado',
                'analista_asignado',
                'supervisor_revisor'
            )
        }),
        ('Justificación y Comentarios', {
            'fields': (
                'justificacion_analista',
                'comentario_supervisor'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_deteccion',
                'fecha_justificacion',
                'fecha_resolucion_supervisor',
                'fecha_ultima_accion'
            )
        }),
        ('Relaciones', {
            'fields': (
                'analisis',
                'cierre'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_deteccion'
    list_per_page = 100
    
    def empleado_info(self, obj):
        """Información del empleado"""
        return f"{obj.nombre_empleado} ({obj.rut_empleado})"
    empleado_info.short_description = 'Empleado'
    
    def cierre_info(self, obj):
        """Info del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def variacion_display(self, obj):
        """Mostrar variación con formato y color"""
        porcentaje = obj.porcentaje_variacion or 0
        if porcentaje >= 30:
            color = '#ef4444'  # Rojo para variaciones altas
        elif porcentaje >= 15:
            color = '#f59e0b'  # Amarillo para variaciones medias
        else:
            color = '#10b981'  # Verde para variaciones bajas
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            porcentaje
        )
    variacion_display.short_description = 'Variación %'
    
    def estado_display(self, obj):
        """Estado con color"""
        colors = {
            'pendiente': '#f59e0b',
            'en_analisis': '#3b82f6',
            'justificado': '#8b5cf6',
            'aprobado': '#10b981',
            'rechazado': '#ef4444'
        }
        color = colors.get(obj.estado, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def variacion_info_detailed(self, obj):
        """Información detallada de la variación"""
        diferencia = obj.sueldo_base_actual - obj.sueldo_base_anterior
        return format_html(
            """
            <strong>Sueldo Anterior:</strong> ${:,.0f}<br>
            <strong>Sueldo Actual:</strong> ${:,.0f}<br>
            <strong>Diferencia:</strong> ${:,.0f}<br>
            <strong>Porcentaje de Variación:</strong> {:.1f}%<br>
            <strong>Tipo:</strong> {}
            """,
            obj.sueldo_base_anterior,
            obj.sueldo_base_actual,
            diferencia,
            obj.porcentaje_variacion,
            obj.get_tipo_variacion_display()
        )
    variacion_info_detailed.short_description = 'Detalles de la Variación'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente',
            'analista_asignado',
            'supervisor_revisor',
            'analisis'
        )


@admin.register(DiscrepanciaCierre)
class DiscrepanciaCierreAdmin(admin.ModelAdmin):
    """Administración de discrepancias de verificación de datos"""
    list_display = (
        'cierre_info',
        'tipo_discrepancia_display',
        'empleado_info',
        'descripcion_corta',
        'concepto_afectado',
        'fecha_detectada'
    )
    list_filter = (
        'tipo_discrepancia',
        'cierre__cliente',
        'cierre__periodo',
        'fecha_detectada'
    )
    search_fields = (
        'rut_empleado',
        'descripcion',
        'concepto_afectado',
        'cierre__cliente__nombre',
        'valor_libro',
        'valor_novedades'
    )
    readonly_fields = (
        'fecha_detectada',
        'detalles_formatted'
    )
    fieldsets = (
        ('Información General', {
            'fields': (
                'cierre',
                'tipo_discrepancia',
                'fecha_detectada'
            )
        }),
        ('Empleado Afectado', {
            'fields': (
                'rut_empleado',
                'empleado_libro',
                'empleado_novedades'
            )
        }),
        ('Descripción de la Discrepancia', {
            'fields': (
                'descripcion',
                'concepto_afectado',
                'detalles_formatted'
            )
        }),
        ('Valores Comparados', {
            'fields': (
                'valor_libro',
                'valor_novedades',
                'valor_movimientos',
                'valor_analista'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_detectada'
    list_per_page = 100
    
    def cierre_info(self, obj):
        """Info básica del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def tipo_discrepancia_display(self, obj):
        """Tipo de discrepancia con formato"""
        tipo_map = {
            'empleado_solo_libro': ('📚', 'Libro vs Novedades'),
            'empleado_solo_novedades': ('📝', 'Libro vs Novedades'),
            'diff_datos_personales': ('👤', 'Libro vs Novedades'),
            'diff_sueldo_base': ('💰', 'Libro vs Novedades'),
            'diff_concepto_monto': ('💲', 'Libro vs Novedades'),
            'concepto_solo_libro': ('📊', 'Libro vs Novedades'),
            'concepto_solo_novedades': ('📋', 'Libro vs Novedades'),
            'ingreso_no_reportado': ('➕', 'Movimientos vs Analista'),
            'finiquito_no_reportado': ('➖', 'Movimientos vs Analista'),
            'ausencia_no_reportada': ('🚫', 'Movimientos vs Analista'),
            'diff_fechas_ausencia': ('📅', 'Movimientos vs Analista'),
            'diff_dias_ausencia': ('🗓️', 'Movimientos vs Analista'),
            'diff_tipo_ausencia': ('🔄', 'Movimientos vs Analista')
        }
        
        icono, grupo = tipo_map.get(obj.tipo_discrepancia, ('⚠️', 'Otro'))
        tipo_texto = obj.get_tipo_discrepancia_display()
        
        return format_html(
            '<span title="{}">{} {}</span><br><small style="color: #6b7280;">{}</small>',
            tipo_texto,
            icono,
            tipo_texto,
            grupo
        )
    tipo_discrepancia_display.short_description = 'Tipo'
    
    def empleado_info(self, obj):
        """Información del empleado"""
        return obj.rut_empleado
    empleado_info.short_description = 'RUT Empleado'
    
    def descripcion_corta(self, obj):
        """Descripción truncada"""
        if len(obj.descripcion) > 100:
            return f"{obj.descripcion[:100]}..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'
    
    def detalles_formatted(self, obj):
        """Detalles formateados para lectura"""
        detalles = []
        
        if obj.valor_libro:
            detalles.append(f"Valor en Libro: {obj.valor_libro}")
        if obj.valor_novedades:
            detalles.append(f"Valor en Novedades: {obj.valor_novedades}")
        if obj.valor_movimientos:
            detalles.append(f"Valor en Movimientos: {obj.valor_movimientos}")
        if obj.valor_analista:
            detalles.append(f"Valor por Analista: {obj.valor_analista}")
            
        return format_html("<br>".join(detalles)) if detalles else "Sin valores registrados"
    detalles_formatted.short_description = 'Detalles de Valores'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente',
            'empleado_libro',
            'empleado_novedades'
        )
