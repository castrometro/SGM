from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
import json
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
    AnalisisDatosCierre, IncidenciaVariacionSalarial, DiscrepanciaCierre,
    HistorialVerificacionCierre, DiscrepanciaHistorial,  # ✅ NUEVOS MODELOS
    # Modelos consolidados (están en models.py)
    NominaConsolidada, HeaderValorEmpleado, ConceptoConsolidado, MovimientoPersonal
)

# Importar modelo de informes
from .models_informe import InformeNomina

# Importar modelos de logging
from .models_logging import UploadLogNomina, TarjetaActivityLogNomina

# (Import ya realizado arriba)


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

    @admin.action(description='⬇️ Descargar informe JSON (v2 si es posible)')
    def descargar_informe_json(self, request, queryset):
        """Descarga el informe del cierre como JSON (intenta v2; si no, v1)."""
        if queryset.count() != 1:
            self.message_user(request, 'Selecciona exactamente un cierre para descargar el informe.', level=messages.WARNING)
            return None
        cierre = queryset.first()

        try:
            # Intentar usar informe existente; si no, generar v2
            informe = InformeNomina.objects.filter(cierre=cierre).first()
            if not informe or not informe.datos_cierre:
                self.message_user(request, 'No existe informe JSON para este cierre.', level=messages.WARNING)
                return None

            data = informe.datos_cierre or {}
            filename = f"informe_nomina_{cierre.cliente.id}_{cierre.periodo}.json"

            payload = json.dumps(data, ensure_ascii=False, indent=2)
            response = HttpResponse(payload, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            self.message_user(request, f'Error al generar/descargar informe: {e}', level=messages.ERROR)
            return None


# ========== ACCIONES PERSONALIZADAS PARA CIERRE NOMINA ==========

@admin.action(description='Actualizar consolidación (eliminar y regenerar)')
def actualizar_consolidacion_cierre(modeladmin, request, queryset):
    """Acción para eliminar consolidación actual y regenerar"""
    from django.db import transaction
    from .utils.ConsolidarInformacion import consolidar_cierre_completo
    
    actualizado_count = 0
    error_count = 0
    errores = []
    
    for cierre in queryset:
        try:
            with transaction.atomic():
                # 1. Eliminar consolidación existente
                nominas_eliminadas = cierre.nomina_consolidada.count()
                cierre.nomina_consolidada.all().delete()
                
                # 2. Limpiar otros datos consolidados
                # Si hay otros modelos relacionados, eliminarlos también
                
                # 3. Resetear estado de consolidación
                cierre.estado_consolidacion = 'pendiente'
                cierre.fecha_consolidacion = None
                cierre.save(update_fields=['estado_consolidacion', 'fecha_consolidacion'])
                
                # 4. Ejecutar nueva consolidación
                resultado = consolidar_cierre_completo(cierre.id, request.user)
                
                if resultado.get('exitoso', False):
                    actualizado_count += 1
                    estadisticas = resultado.get('estadisticas', {})
                    nominas_procesadas = estadisticas.get('nominas_consolidadas', 0)
                    
                    # Mensaje de éxito
                    mensaje = f"Consolidación actualizada: {nominas_eliminadas} registros eliminados, {nominas_procesadas} nuevos registros generados"
                    modeladmin.message_user(
                        request,
                        f"✅ {cierre.cliente.nombre} - {cierre.periodo}: {mensaje}",
                        level=modeladmin.message_user.SUCCESS
                    )
                else:
                    error_count += 1
                    error_msg = resultado.get('error', 'Error desconocido')
                    errores.append(f"{cierre.cliente.nombre} - {cierre.periodo}: {error_msg}")
                    
        except Exception as e:
            error_count += 1
            errores.append(f"{cierre.cliente.nombre} - {cierre.periodo}: Error inesperado - {str(e)}")
    
    # Mensaje resumen
    if actualizado_count > 0:
        modeladmin.message_user(
            request,
            f"🔄 {actualizado_count} consolidación(es) actualizada(s) exitosamente.",
            level=modeladmin.message_user.SUCCESS
        )
    
    if error_count > 0:
        modeladmin.message_user(
            request,
            f"❌ {error_count} error(es) durante actualización: {'; '.join(errores[:3])}{'...' if len(errores) > 3 else ''}",
            level=modeladmin.message_user.ERROR
        )

@admin.action(description='Generar consolidación inicial')
def generar_consolidacion_inicial(modeladmin, request, queryset):
    """Acción para generar consolidación en cierres que no la tienen"""
    from django.db import transaction
    from .utils.ConsolidarInformacion import consolidar_cierre_completo
    
    generado_count = 0
    error_count = 0
    ya_existia_count = 0
    errores = []
    
    for cierre in queryset:
        try:
            # Verificar si ya tiene consolidación
            if cierre.nomina_consolidada.exists():
                ya_existia_count += 1
                continue
                
            with transaction.atomic():
                # Asegurar estado correcto antes de consolidar
                cierre.estado_consolidacion = 'pendiente'
                cierre.save(update_fields=['estado_consolidacion'])
                
                resultado = consolidar_cierre_completo(cierre.id, request.user)
                
                if resultado.get('exitoso', False):
                    generado_count += 1
                    estadisticas = resultado.get('estadisticas', {})
                    nominas_procesadas = estadisticas.get('nominas_consolidadas', 0)
                    
                    modeladmin.message_user(
                        request,
                        f"✅ {cierre.cliente.nombre} - {cierre.periodo}: {nominas_procesadas} nóminas consolidadas generadas",
                        level=modeladmin.message_user.SUCCESS
                    )
                else:
                    error_count += 1
                    error_msg = resultado.get('error', 'Error desconocido')
                    errores.append(f"{cierre.cliente.nombre} - {cierre.periodo}: {error_msg}")
                    
        except Exception as e:
            error_count += 1
            errores.append(f"{cierre.cliente.nombre} - {cierre.periodo}: Error inesperado - {str(e)}")
    
    # Mensaje resumen
    if generado_count > 0:
        modeladmin.message_user(
            request,
            f"🆕 {generado_count} consolidación(es) inicial(es) generada(s) exitosamente.",
            level=modeladmin.message_user.SUCCESS
        )
    
    if ya_existia_count > 0:
        modeladmin.message_user(
            request,
            f"ℹ️ {ya_existia_count} cierre(s) ya tenía(n) consolidación existente.",
            level=modeladmin.message_user.INFO
        )
    
    if error_count > 0:
        modeladmin.message_user(
            request,
            f"❌ {error_count} error(es) durante generación: {'; '.join(errores[:3])}{'...' if len(errores) > 3 else ''}",
            level=modeladmin.message_user.ERROR
        )

# Asignar acciones al admin de CierreNomina
CierreNominaAdmin.actions = [
    actualizar_consolidacion_cierre,
    generar_consolidacion_inicial,
    'descargar_informe_json'
]


## Eliminado: registro duplicado de InformeNominaAdmin (se usa el de abajo)


@admin.register(EmpleadoCierre)
class EmpleadoCierreAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut_empresa', 'dias_trabajados', 'cierre_info', 'cierre_id_display')
    search_fields = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'cierre__id')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'cierre__estado')
    readonly_fields = ('cierre_id_display', 'cierre_info')
    
    def cierre_id_display(self, obj):
        """Muestra el ID del cierre de forma clara"""
        return f"ID: {obj.cierre.id}"
    cierre_id_display.short_description = "Cierre ID"
    
    def cierre_info(self, obj):
        """Muestra información completa del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo} (ID: {obj.cierre.id})"
    cierre_info.short_description = "Información del Cierre"


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
    list_display = ('empleado', 'concepto', 'nombre_concepto_original', 'monto', 'fecha_registro')
    search_fields = ('empleado__rut', 'nombre_concepto_original', 'empleado__nombre', 'empleado__apellido_paterno')
    list_filter = (
        'empleado__cierre__cliente', 
        'empleado__cierre__periodo', 
        'fecha_registro',
        'concepto__clasificacion'
    )
    
    # ✅ CONFIGURACIÓN PARA MANEJAR MUCHOS REGISTROS
    list_per_page = 50  # Mostrar solo 50 registros por página
    list_max_show_all = 100  # Máximo 100 registros en "mostrar todos"
    show_full_result_count = False  # No contar todos los registros (mejora performance)
    
    # ✅ ORDENAMIENTO POR DEFECTO (MÁS RECIENTES PRIMERO)
    ordering = ['-fecha_registro']
    
    # ✅ CAMPOS DE SOLO LECTURA PARA PROTEGER DATOS
    readonly_fields = ('fecha_registro',)
    
    # ✅ ACCIONES PERSONALIZADAS PARA ELIMINACIÓN MASIVA
    actions = ['eliminar_por_cierre', 'eliminar_registros_seleccionados', 'info_estadisticas']
    
    def eliminar_por_cierre(self, request, queryset):
        """Eliminar todos los registros de conceptos por cierre de nómina"""
        cierres_afectados = set()
        total_eliminados = 0
        
        # Obtener cierres únicos
        for registro in queryset:
            cierres_afectados.add(registro.empleado.cierre)
        
        # Confirmar eliminación
        if len(cierres_afectados) > 0:
            for cierre in cierres_afectados:
                count = RegistroConceptoEmpleado.objects.filter(empleado__cierre=cierre).count()
                total_eliminados += count
                RegistroConceptoEmpleado.objects.filter(empleado__cierre=cierre).delete()
            
            self.message_user(
                request, 
                f"✅ Eliminados {total_eliminados} registros de conceptos de {len(cierres_afectados)} cierre(s) de nómina."
            )
        
    eliminar_por_cierre.short_description = "🗑️ Eliminar TODOS los conceptos del cierre seleccionado"
    
    def eliminar_registros_seleccionados(self, request, queryset):
        """Eliminar solo los registros seleccionados (más seguro)"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"✅ Eliminados {count} registros de conceptos seleccionados.")
    
    eliminar_registros_seleccionados.short_description = "🗑️ Eliminar solo registros seleccionados"
    
    def info_estadisticas(self, request, queryset):
        """Mostrar estadísticas de los registros seleccionados"""
        total = queryset.count()
        cierres = queryset.values('empleado__cierre').distinct().count()
        empleados = queryset.values('empleado').distinct().count()
        
        self.message_user(
            request, 
            f"📊 Estadísticas: {total} registros, {empleados} empleados, {cierres} cierres diferentes."
        )
    
    info_estadisticas.short_description = "📊 Ver estadísticas de selección"
    
    # ✅ FILTROS PERSONALIZADOS PARA NAVEGACIÓN EFICIENTE
    def get_queryset(self, request):
        """Optimizar queryset para mejor performance"""
        return super().get_queryset(request).select_related(
            'empleado', 'empleado__cierre', 'empleado__cierre__cliente', 'concepto'
        )
    
    # ✅ FIELDSETS PARA ORGANIZAR FORMULARIO
    fieldsets = (
        ('Información Principal', {
            'fields': ('empleado', 'concepto', 'nombre_concepto_original')
        }),
        ('Datos Financieros', {
            'fields': ('monto',)
        }),
        ('Información de Sistema', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )


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
    list_display = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'cierre_info', 'cierre_id_display')
    search_fields = ('rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'cierre__id')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'cierre__estado')
    readonly_fields = ('cierre', 'cierre_id_display', 'cierre_info')
    
    def cierre_id_display(self, obj):
        """Muestra el ID del cierre de forma clara"""
        return f"ID: {obj.cierre.id}"
    cierre_id_display.short_description = "Cierre ID"
    
    def cierre_info(self, obj):
        """Muestra información completa del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo} (ID: {obj.cierre.id})"
    cierre_info.short_description = "Información del Cierre"


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
    list_display = ('empleado_info', 'cierre_id_display', 'concepto', 'nombre_concepto_original', 'monto', 'fecha_registro')
    search_fields = ('empleado__rut', 'empleado__nombre', 'nombre_concepto_original', 'empleado__cierre__id')
    list_filter = ('concepto__concepto_libro__clasificacion', 'concepto__activo', 'fecha_registro', 'empleado__cierre__cliente')
    readonly_fields = ('fecha_registro', 'empleado_info', 'cierre_id_display')
    date_hierarchy = 'fecha_registro'
    
    def empleado_info(self, obj):
        """Información del empleado con RUT"""
        return f"{obj.empleado.nombre} {obj.empleado.apellido_paterno} ({obj.empleado.rut})"
    empleado_info.short_description = "Empleado"
    
    def cierre_id_display(self, obj):
        """Muestra el ID del cierre desde el empleado"""
        return f"ID: {obj.empleado.cierre.id}"
    cierre_id_display.short_description = "Cierre ID"


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
    """Administración de resoluciones de incidencias - Arquitectura simplificada"""
    list_display = (
        'incidencia_info',
        'tipo_resolucion_display',
        'usuario',
        'comentario_resumido',
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
                'adjunto'
            )
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
            'justificacion': '💬',
            'consulta': '❓',
            'rechazo': '❌',
            'aprobacion': '✅'
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
        )


# ========== ACCIONES PERSONALIZADAS ==========

@admin.action(description='Asignar incidencias seleccionadas a mí')
def asignar_incidencias_a_mi(modeladmin, request, queryset):
    """Acción para asignarse incidencias"""
    count = queryset.update(asignado_a=request.user)
    nombre_completo = f'{request.user.nombre} {request.user.apellido}'.strip() if hasattr(request.user, 'nombre') else request.user.correo_bdo
    modeladmin.message_user(
        request,
        f'{count} incidencia(s) asignada(s) a {nombre_completo or request.user.correo_bdo}'
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
            nombre_completo = f'{obj.analista.nombre} {obj.analista.apellido}'.strip() if hasattr(obj.analista, 'nombre') else obj.analista.correo_bdo
            return nombre_completo or obj.analista.correo_bdo
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


# ========== ADMINISTRACIÓN DE MODELOS CONSOLIDADOS ==========

class HeaderValorEmpleadoInline(admin.TabularInline):
    """Inline para mostrar headers-valores dentro de una nómina consolidada"""
    model = HeaderValorEmpleado
    extra = 0
    readonly_fields = ('nombre_header', 'concepto_remuneracion', 'valor_original', 'valor_numerico', 'es_numerico')
    fields = ('nombre_header', 'concepto_remuneracion', 'valor_original', 'valor_numerico', 'es_numerico')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class ConceptoConsolidadoInline(admin.TabularInline):
    """Inline para mostrar conceptos dentro de una nómina consolidada"""
    model = ConceptoConsolidado
    extra = 0
    readonly_fields = ('codigo_concepto', 'nombre_concepto', 'tipo_concepto', 'monto_total', 'cantidad', 'fecha_consolidacion')
    fields = ('codigo_concepto', 'nombre_concepto', 'tipo_concepto', 'monto_total', 'cantidad')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class MovimientoPersonalInline(admin.TabularInline):
    """Inline para mostrar movimientos de personal dentro de una nómina consolidada (schema normalizado)"""
    model = MovimientoPersonal
    extra = 0
    readonly_fields = ('categoria', 'subtipo', 'fecha_inicio', 'fecha_fin', 'dias_evento', 'dias_en_periodo', 'fecha_deteccion')
    fields = ('categoria', 'subtipo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'dias_evento', 'dias_en_periodo', 'multi_mes', 'observaciones')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NominaConsolidada)
class NominaConsolidadaAdmin(admin.ModelAdmin):
    """Administración de nóminas consolidadas"""
    list_display = (
        'cierre_info',
        'nombre_empleado',
        'rut_empleado',
        'estado_empleado_display',
        'haberes_imponibles_formatted',
        'haberes_no_imponibles_formatted',
        'dctos_legales_formatted',
        'otros_dctos_formatted',
        'impuestos_formatted',
        'horas_extras_cantidad',
        'aportes_patronales_formatted',
        'dias_trabajados',
    )
    list_filter = (
        'cierre',
        'cierre__cliente',
        'estado_empleado',
        'cierre__periodo',
    )
    search_fields = (
        'nombre_empleado',
        'rut_empleado',
        'cargo',
        'centro_costo',
        'cierre__cliente__nombre'
    )
    readonly_fields = (
        'fecha_consolidacion',
        'fuente_datos_formatted',
        'resumen_empleado'
    )
    fieldsets = (
        ('Información del Empleado', {
            'fields': (
                'cierre',
                'rut_empleado',
                'nombre_empleado',
                'cargo',
                'centro_costo',
                'estado_empleado'
            )
        }),
        ('Totales Consolidados', {
            'fields': (
                'haberes_imponibles',
                'haberes_no_imponibles',
                'dctos_legales',
                'otros_dctos',
                'impuestos',
                'horas_extras_cantidad',
                'aportes_patronales',
                'dias_trabajados',
                'dias_ausencia'
            )
        }),
        ('Metadatos de Consolidación', {
            'fields': (
                'fecha_consolidacion',
                'fuente_datos_formatted',
                'resumen_empleado'
            ),
            'classes': ('collapse',)
        })
    )
    inlines = [HeaderValorEmpleadoInline, ConceptoConsolidadoInline, MovimientoPersonalInline]
    date_hierarchy = 'fecha_consolidacion'
    list_per_page = 50
    
    def cierre_info(self, obj):
        """Info básica del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def estado_empleado_display(self, obj):
        """Display con colores para estado del empleado"""
        colors = {
            'activo': '#10b981',              # verde
            'nueva_incorporacion': '#3b82f6', # azul
            'finiquito': '#ef4444',           # rojo
            'ausente_total': '#f59e0b',       # amarillo
            'ausente_parcial': '#f97316'      # naranja
        }
        color = colors.get(obj.estado_empleado, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_estado_empleado_display()
        )
    estado_empleado_display.short_description = 'Estado'

    # ------------------ Formateadores de totales por categoría ------------------
    def haberes_imponibles_formatted(self, obj):
        try:
            return f"${obj.haberes_imponibles:,.0f}"
        except Exception:
            return "0"
    haberes_imponibles_formatted.short_description = 'Haberes Imponibles'

    def haberes_no_imponibles_formatted(self, obj):
        try:
            return f"${obj.haberes_no_imponibles:,.0f}"
        except Exception:
            return "0"
    haberes_no_imponibles_formatted.short_description = 'Haberes No Imponibles'

    def dctos_legales_formatted(self, obj):
        try:
            return f"${obj.dctos_legales:,.0f}"
        except Exception:
            return "0"
    dctos_legales_formatted.short_description = 'Descuentos Legales'

    def otros_dctos_formatted(self, obj):
        try:
            return f"${obj.otros_dctos:,.0f}"
        except Exception:
            return "0"
    otros_dctos_formatted.short_description = 'Otros Descuentos'

    def impuestos_formatted(self, obj):
        try:
            return f"${obj.impuestos:,.0f}"
        except Exception:
            return "0"
    impuestos_formatted.short_description = 'Impuestos'

    def aportes_patronales_formatted(self, obj):
        try:
            return f"${obj.aportes_patronales:,.0f}"
        except Exception:
            return "0"
    aportes_patronales_formatted.short_description = 'Aportes Patronales'
    
    
    def fuente_datos_formatted(self, obj):
        """Mostrar fuentes de datos formateadas"""
        if not obj.fuente_datos:
            return "Sin información de fuentes"
        
        fuentes = []
        for fuente, presente in obj.fuente_datos.items():
            if presente:
                fuentes.append(f"✅ {fuente}")
            else:
                fuentes.append(f"❌ {fuente}")
        
        return format_html("<br>".join(fuentes))
    fuente_datos_formatted.short_description = 'Fuentes de Datos'
    
    def resumen_empleado(self, obj):
        """Resumen ejecutivo del empleado"""
        conceptos_count = obj.conceptos.count()
        movimientos_count = obj.movimientos.count()
        
        return f"""
        RESUMEN EMPLEADO:
        - Total Conceptos: {conceptos_count}
        - Movimientos de Personal: {movimientos_count}
        - Días Trabajados: {obj.dias_trabajados or 'N/D'}
        - Días de Ausencia: {obj.dias_ausencia}
        - Estado: {obj.get_estado_empleado_display()}
        - Líquido Final: ${obj.liquido_pagar:,.0f}
        """
    resumen_empleado.short_description = 'Resumen del Empleado'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente'
        ).prefetch_related('conceptos', 'movimientos')


@admin.register(HeaderValorEmpleado)
class HeaderValorEmpleadoAdmin(admin.ModelAdmin):
    """Administración de headers-valores por empleado"""
    list_display = (
        'nombre_header',
        'empleado_info',
        'concepto_display',
        'valor_display',
        'es_numerico',
        'fuente_archivo',
        'fecha_consolidacion'
    )
    list_filter = (
        'es_numerico',
        'fuente_archivo',
        'concepto_remuneracion__clasificacion',
        'nomina_consolidada__cierre__cliente',
        'nomina_consolidada__cierre__periodo',
        'fecha_consolidacion'
    )
    search_fields = (
        'nombre_header',
        'nomina_consolidada__nombre_empleado',
        'nomina_consolidada__rut_empleado',
        'valor_original',
        'concepto_remuneracion__nombre_concepto'
    )
    readonly_fields = (
        'fecha_consolidacion',
        'coordenadas_excel',
        'resumen_header_valor'
    )
    fieldsets = (
        ('Información del Header', {
            'fields': (
                'nomina_consolidada',
                'nombre_header',
                'concepto_remuneracion'
            )
        }),
        ('Valores', {
            'fields': (
                'valor_original',
                'valor_numerico',
                'es_numerico'
            )
        }),
        ('Origen del Dato', {
            'fields': (
                'fuente_archivo',
                'columna_excel',
                'fila_excel',
                'coordenadas_excel'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'fecha_consolidacion',
                'resumen_header_valor'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_consolidacion'
    list_per_page = 100
    
    def empleado_info(self, obj):
        """Info del empleado"""
        return f"{obj.nomina_consolidada.nombre_empleado} ({obj.nomina_consolidada.rut_empleado})"
    empleado_info.short_description = 'Empleado'
    
    def concepto_display(self, obj):
        """Display del concepto si existe"""
        if obj.concepto_remuneracion:
            return f"{obj.concepto_remuneracion.nombre_concepto} ({obj.concepto_remuneracion.get_clasificacion_display()})"
        return "Sin clasificar"
    concepto_display.short_description = 'Concepto'
    
    def valor_display(self, obj):
        """Display inteligente del valor"""
        if obj.es_numerico and obj.valor_numerico is not None:
            return f"${obj.valor_numerico:,.2f}"
        return obj.valor_original or "Sin valor"
    valor_display.short_description = 'Valor'
    
    def coordenadas_excel(self, obj):
        """Coordenadas Excel si están disponibles"""
        if obj.columna_excel and obj.fila_excel:
            return f"{obj.columna_excel}{obj.fila_excel}"
        return "No disponible"
    coordenadas_excel.short_description = 'Coordenadas Excel'
    
    def resumen_header_valor(self, obj):
        """Resumen completo del header-valor"""
        return f"""
        RESUMEN HEADER-VALOR:
        
        👤 EMPLEADO:
        - Nombre: {obj.nomina_consolidada.nombre_empleado}
        - RUT: {obj.nomina_consolidada.rut_empleado}
        - Cierre: {obj.nomina_consolidada.cierre.cliente.nombre} - {obj.nomina_consolidada.cierre.periodo}
        
        📊 HEADER:
        - Nombre: {obj.nombre_header}
        - Clasificación: {obj.concepto_remuneracion.get_clasificacion_display() if obj.concepto_remuneracion else 'Sin clasificar'}
        - Fuente: {obj.fuente_archivo}
        
        💰 VALOR:
        - Original: {obj.valor_original}
        - Numérico: {f'${obj.valor_numerico:,.2f}' if obj.valor_numerico else 'N/A'}
        - Es Numérico: {'Sí' if obj.es_numerico else 'No'}
        
        📍 ORIGEN:
        - Coordenadas Excel: {f'{obj.columna_excel}{obj.fila_excel}' if obj.columna_excel and obj.fila_excel else 'No disponible'}
        - Fecha Consolidación: {obj.fecha_consolidacion.strftime('%d/%m/%Y %H:%M')}
        """
    resumen_header_valor.short_description = 'Resumen Completo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'nomina_consolidada',
            'nomina_consolidada__cierre',
            'nomina_consolidada__cierre__cliente',
            'concepto_remuneracion'
        )


@admin.register(ConceptoConsolidado)
class ConceptoConsolidadoAdmin(admin.ModelAdmin):
    """Administración de conceptos consolidados"""
    list_display = (
        'nombre_concepto',
        'codigo_concepto',
        'empleado_info',
        'tipo_concepto_display',
        'monto_total_formatted',
        'cantidad',
        'fuente_archivo_display',
        'fecha_consolidacion'
    )
    list_filter = (
        'tipo_concepto',
        'nomina_consolidada__cierre__cliente',
        'nomina_consolidada__cierre__periodo',
        'es_numerico',
        'fuente_archivo',
        'fecha_consolidacion'
    )
    search_fields = (
        'nombre_concepto',
        'codigo_concepto',
        'nomina_consolidada__nombre_empleado',
        'nomina_consolidada__rut_empleado',
        'nomina_consolidada__cierre__cliente__nombre'
    )
    readonly_fields = (
        'fecha_consolidacion',
        'estadisticas_detalladas'
    )
    fieldsets = (
        ('Información del Concepto', {
            'fields': (
                'nomina_consolidada',
                'codigo_concepto',
                'nombre_concepto',
                'tipo_concepto'
            )
        }),
        ('Valores', {
            'fields': (
                'monto_total',
                'cantidad',
                'es_numerico',
                'fuente_archivo'
            )
        }),
        ('Metadatos', {
            'fields': (
                'fecha_consolidacion',
                'estadisticas_detalladas'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_consolidacion'
    list_per_page = 100
    
    def empleado_info(self, obj):
        """Info del empleado asociado"""
        return f"{obj.nomina_consolidada.nombre_empleado} ({obj.nomina_consolidada.rut_empleado})"
    empleado_info.short_description = 'Empleado'
    
    def tipo_concepto_display(self, obj):
        """Display con colores para tipo de concepto"""
        if not obj.tipo_concepto:
            return format_html('<span style="color: #6b7280;">Sin clasificar</span>')
        
        colors = {
            'haber_imponible': '#10b981',        # verde
            'haber_no_imponible': '#3b82f6',     # azul
            'descuento_legal': '#ef4444',        # rojo
            'otro_descuento': '#f59e0b',         # amarillo
            'aporte_patronal': '#8b5cf6',        # morado
            'informativo': '#6b7280'             # gris
        }
        color = colors.get(obj.tipo_concepto, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_tipo_concepto_display()
        )
    tipo_concepto_display.short_description = 'Tipo'
    
    def monto_total_formatted(self, obj):
        """Formato de moneda para monto total"""
        if not obj.es_numerico:
            return '-'
        color = '#ef4444' if obj.monto_total < 0 else '#10b981'
        formatted_amount = f"${obj.monto_total:,.0f}"
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            formatted_amount
        )
    monto_total_formatted.short_description = 'Monto'
    
    def fuente_archivo_display(self, obj):
        """Display con color para fuente"""
        colors = {
            'libro': '#3b82f6',              # azul
            'movimientos': '#f59e0b',        # amarillo  
            'novedades': '#10b981',          # verde
            'analista': '#8b5cf6',           # morado
            'consolidacion': '#6b7280'       # gris
        }
        color = colors.get(obj.fuente_archivo, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.fuente_archivo.title()
        )
    fuente_archivo_display.short_description = 'Fuente'
    
    def estadisticas_detalladas(self, obj):
        """Estadísticas detalladas del concepto"""
        return f"""
        ESTADÍSTICAS DEL CONCEPTO:
        
        👤 EMPLEADO:
        - Nombre: {obj.nomina_consolidada.nombre_empleado}
        - RUT: {obj.nomina_consolidada.rut_empleado}
        - Estado: {obj.nomina_consolidada.get_estado_empleado_display()}
        
        💰 CONCEPTO:
        - Código: {obj.codigo_concepto or 'Sin código'}
        - Nombre: {obj.nombre_concepto}
        - Tipo: {obj.get_tipo_concepto_display() if obj.tipo_concepto else 'Sin clasificar'}
        - Es Numérico: {'Sí' if obj.es_numerico else 'No'}
        
        🔢 VALORES:
        - Monto: {'${:,.2f}'.format(obj.monto_total) if obj.es_numerico else 'N/A'}
        - Cantidad: {obj.cantidad}
        - Fuente: {obj.fuente_archivo.title()}
        
        📊 CONTEXTO:
        - Cierre: {obj.nomina_consolidada.cierre.cliente.nombre} - {obj.nomina_consolidada.cierre.periodo}
        - Fecha Consolidación: {obj.fecha_consolidacion.strftime('%d/%m/%Y %H:%M')}
        """
    estadisticas_detalladas.short_description = 'Estadísticas Detalladas'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'nomina_consolidada',
            'nomina_consolidada__cierre',
            'nomina_consolidada__cierre__cliente'
        )


@admin.register(MovimientoPersonal)
class MovimientoPersonalAdmin(admin.ModelAdmin):
    """Administración de movimientos de personal"""
    class SinJustificarFilter(admin.SimpleListFilter):
        title = 'Ausencia sin justificar'
        parameter_name = 'sin_justificar'

        def lookups(self, request, model_admin):
            return (
                ('1', 'Solo sin justificar'),
            )

        def queryset(self, request, queryset):
            if self.value() == '1':
                return queryset.filter(subtipo__iexact='sin_justificar')
            return queryset

    list_display = (
            'empleado_info','cierre_info','categoria_display','subtipo','subtipo_badge',
            'descripcion_corta','fecha_rango','dias_evento','dias_en_periodo','multi_mes_badge','fecha_deteccion'
    )
    list_filter = (
            'categoria','subtipo',SinJustificarFilter,'nomina_consolidada__cierre__cliente',
            'nomina_consolidada__cierre__periodo','multi_mes','fecha_deteccion','fecha_inicio','fecha_fin','detectado_por_sistema'
    )
    search_fields = (
        'nomina_consolidada__nombre_empleado','nomina_consolidada__rut_empleado','descripcion','observaciones','subtipo','nomina_consolidada__cierre__cliente__nombre'
    )
    readonly_fields = ('fecha_deteccion','detectado_por_sistema','resumen_movimiento')
    fieldsets = (
            ('Empleado y Cierre', {'fields': ('nomina_consolidada',)}),
            ('Clasificación', {'fields': ('categoria','subtipo')}),
            ('Fechas y Duraciones', {'fields': ('fecha_inicio','fecha_fin','dias_evento','dias_en_periodo','multi_mes')}),
            ('Detalle', {'fields': ('descripcion','observaciones')}),
            ('Hashes y Fuente', {'fields': ('hash_evento','hash_registro_periodo','detalle_fuente')}),
            ('Metadatos de Detección', {'fields': ('fecha_deteccion','detectado_por_sistema','resumen_movimiento'), 'classes': ('collapse',)})
    )
    date_hierarchy = 'fecha_deteccion'
    list_per_page = 100
    
    def empleado_info(self, obj):
        """Info del empleado"""
        return f"{obj.nomina_consolidada.nombre_empleado} ({obj.nomina_consolidada.rut_empleado})"
    empleado_info.short_description = 'Empleado'
    
    def cierre_info(self, obj):
        """Info básica del cierre"""
        return f"{obj.nomina_consolidada.cierre.cliente.nombre} - {obj.nomina_consolidada.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def categoria_display(self, obj):
        colors = {
            'ingreso': '#10b981',
            'finiquito': '#ef4444',
            'ausencia': '#f59e0b',
            'reincorporacion': '#3b82f6',
            'cambio_datos': '#8b5cf6',
            'cambio_contrato': '#8b5cf6',
            'cambio_sueldo': '#8b5cf6'
        }
        label = obj.categoria or '-'
        color = colors.get(label, '#6b7280')
        return format_html('<span style="color:{};font-weight:bold;">●</span> {}', color, label or '-')
    categoria_display.short_description = 'Categoría'

    def descripcion_corta(self, obj):
        txt = obj.descripcion or ''
        return (txt[:40] + '...') if len(txt) > 43 else txt or '-'
    descripcion_corta.short_description = 'Descripción'

    def fecha_rango(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            if obj.fecha_inicio == obj.fecha_fin:
                return obj.fecha_inicio.strftime('%d/%m/%Y')
            return f"{obj.fecha_inicio.strftime('%d/%m/%Y')} → {obj.fecha_fin.strftime('%d/%m/%Y')}"
        return '-'
    fecha_rango.short_description = 'Rango'

    def multi_mes_badge(self, obj):
        if obj.multi_mes:
            return format_html('<span style="background:#334155;color:#fbbf24;padding:2px 6px;border-radius:10px;font-size:11px;">Multi-mes</span>')
        return ''
    multi_mes_badge.short_description = 'Multi'

    def subtipo_badge(self, obj):
        if (obj.subtipo or '').lower() == 'sin_justificar':
            return format_html('<span style="background:#991b1b;color:#fff;padding:2px 6px;border-radius:10px;font-size:11px;">Sin justificar</span>')
        return ''
    subtipo_badge.short_description = '⚠️'
    
    # Retiramos motivo_corto (reemplazado por descripcion_corta)
    
    def resumen_movimiento(self, obj):
        """Resumen detallado del movimiento"""
        return f"""
        RESUMEN MOVIMIENTO:
        
        👤 EMPLEADO:
        - Nombre: {obj.nomina_consolidada.nombre_empleado}
        - RUT: {obj.nomina_consolidada.rut_empleado}
        - Estado: {obj.nomina_consolidada.get_estado_empleado_display()}
        
    🔄 MOVIMIENTO:
    - Categoría: {obj.categoria or '-'}
    - Subtipo: {obj.subtipo or '-'}
    - Rango: {self.fecha_rango(obj)}
    - Días Evento: {obj.dias_evento or '-'} / En período: {obj.dias_en_periodo or '-'}
        
        📊 CONTEXTO:
        - Cierre: {obj.nomina_consolidada.cierre.cliente.nombre} - {obj.nomina_consolidada.cierre.periodo}
        - Detectado por: {obj.detectado_por_sistema}
        - Fecha Detección: {obj.fecha_deteccion.strftime('%d/%m/%Y %H:%M')}
        
        📝 OBSERVACIONES:
        {obj.observaciones or 'Sin observaciones'}
        """
    resumen_movimiento.short_description = 'Resumen del Movimiento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'nomina_consolidada',
            'nomina_consolidada__cierre',
            'nomina_consolidada__cierre__cliente'
        )


# ========== ACCIONES PERSONALIZADAS PARA MODELOS CONSOLIDADOS ==========

@admin.action(description='Recalcular estadísticas de conceptos consolidados')
def recalcular_estadisticas_conceptos(modeladmin, request, queryset):
    """Acción para recalcular estadísticas de conceptos consolidados"""
    count = 0
    for concepto in queryset:
        # Aquí se implementaría la lógica de recálculo
        # concepto.recalcular_estadisticas()
        count += 1
    
    modeladmin.message_user(
        request,
        f'Estadísticas recalculadas para {count} concepto(s) consolidado(s)'
    )

@admin.action(description='Exportar datos consolidados a Excel')
def exportar_consolidados_excel(modeladmin, request, queryset):
    """Acción para exportar datos consolidados a Excel"""
    # Aquí se implementaría la lógica de exportación
    modeladmin.message_user(
        request,
        f'Exportación iniciada para {queryset.count()} registro(s). Se notificará cuando esté listo.'
    )

# Agregar acciones personalizadas
NominaConsolidadaAdmin.actions = [exportar_consolidados_excel]
HeaderValorEmpleadoAdmin.actions = [exportar_consolidados_excel]
ConceptoConsolidadoAdmin.actions = [recalcular_estadisticas_conceptos, exportar_consolidados_excel]
MovimientoPersonalAdmin.actions = [exportar_consolidados_excel]


# ========== ADMINISTRACIÓN DE MODELOS DE LOGGING ==========

@admin.register(UploadLogNomina)
class UploadLogNominaAdmin(admin.ModelAdmin):
    """Administración de logs de uploads de nómina"""
    list_display = (
        'archivo_nombre_corto',
        'tipo_display',
        'cierre_info',
        'estado_display',
        'fecha_subida',
        'usuario_display'
    )
    list_filter = (
        'tipo_upload',
        'estado',
        'cierre__cliente',
        'cierre__periodo',
        'fecha_subida',
        'usuario'
    )
    search_fields = (
        'nombre_archivo_original',
        'cierre__cliente__nombre',
        'cierre__periodo',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__correo_bdo'
    )
    readonly_fields = (
        'fecha_subida',
        'tiempo_procesamiento',
        'headers_detectados_formatted',
        'resumen_formatted'
    )
    fieldsets = (
        ('Información del Archivo', {
            'fields': (
                'tipo_upload',
                'nombre_archivo_original',
                'cierre',
                'usuario'
            )
        }),
        ('Estado de Procesamiento', {
            'fields': (
                'estado',
                'fecha_subida',
                'tiempo_procesamiento'
            )
        }),
        ('Headers Detectados', {
            'fields': (
                'headers_detectados_formatted',
            ),
            'classes': ('collapse',)
        }),
        ('Resultados', {
            'fields': (
                'resumen_formatted',
                'errores'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'fecha_subida'
    list_per_page = 50
    
    def archivo_nombre_corto(self, obj):
        """Nombre del archivo truncado"""
        if obj.nombre_archivo_original:
            nombre = obj.nombre_archivo_original
            if len(nombre) > 30:
                return f"{nombre[:15]}...{nombre[-10:]}"
            return nombre
        return "Sin archivo"
    archivo_nombre_corto.short_description = 'Archivo'
    
    def tipo_display(self, obj):
        """Display con iconos para tipo"""
        icons = {
            'libro_remuneraciones': '📚',
            'movimientos_mes': '🔄',
            'novedades': '📋',
            'movimientos_ingresos': '🟢',
            'movimientos_finiquitos': '🔴',
            'movimientos_incidencias': '⚠️',
            'archivos_analista': '👤'
        }
        icon = icons.get(obj.tipo_upload, '📄')
        return f"{icon} {obj.get_tipo_upload_display()}"
    tipo_display.short_description = 'Tipo'
    
    def cierre_info(self, obj):
        """Info del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def estado_display(self, obj):
        """Estado con colores"""
        colors = {
            'subido': '#6b7280',           # gris
            'procesando': '#f59e0b',       # amarillo
            'analizando_hdrs': '#3b82f6',  # azul
            'hdrs_analizados': '#8b5cf6',  # morado
            'clasif_en_proceso': '#f97316', # naranja
            'clasificado': '#10b981',      # verde
            'procesado': '#059669',        # verde oscuro
            'error': '#ef4444',            # rojo
            'cancelado': '#6b7280'         # gris oscuro
        }
        color = colors.get(obj.estado, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'
    
    def usuario_display(self, obj):
        """Info del usuario"""
        if obj.usuario:
            nombre_completo = f"{obj.usuario.nombre} {obj.usuario.apellido}".strip()
            return nombre_completo if nombre_completo else obj.usuario.correo_bdo
        return "Sin asignar"
    usuario_display.short_description = 'Usuario'
    
    def headers_detectados_formatted(self, obj):
        """Headers detectados formateados"""
        if obj.headers_detectados:
            headers = obj.headers_detectados
            if isinstance(headers, list):
                return format_html("<br>".join([f"• {header}" for header in headers[:10]]))
            elif isinstance(headers, dict):
                return f"Headers: {len(headers)} detectados"
        return "Sin headers detectados"
    headers_detectados_formatted.short_description = 'Headers Detectados'
    
    def resumen_formatted(self, obj):
        """Resumen formateado"""
        if obj.resumen:
            # Convertir dict a string seguro evitando problemas de formateo
            import json
            resumen_str = json.dumps(obj.resumen, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', resumen_str)
        return "Sin resumen"
    resumen_formatted.short_description = 'Resumen'
    
    def tiempo_procesamiento_display(self, obj):
        """Tiempo de procesamiento calculado"""
        if obj.tiempo_procesamiento:
            total_seconds = obj.tiempo_procesamiento.total_seconds()
            if total_seconds < 60:
                return f"{total_seconds:.1f}s"
            elif total_seconds < 3600:
                return f"{total_seconds/60:.1f}m"
            else:
                return f"{total_seconds/3600:.1f}h"
        return "Sin calcular"
    tiempo_procesamiento_display.short_description = 'Tiempo Procesamiento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente',
            'usuario'
        )


@admin.register(TarjetaActivityLogNomina)
class TarjetaActivityLogNominaAdmin(admin.ModelAdmin):
    """Administración de logs de actividad de tarjetas"""
    list_display = (
        'timestamp',
        'tarjeta_display',
        'accion_display',
        'usuario_info',
        'cierre_info',
        'resultado_display'
    )
    list_filter = (
        'tarjeta',
        'accion',
        'usuario',
        'cierre__cliente',
        'cierre__periodo',
        'timestamp'
    )
    search_fields = (
        'tarjeta',
        'accion',
        'descripcion',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__correo_bdo',
        'cierre__cliente__nombre'
    )
    readonly_fields = (
        'timestamp',
        'metadata_formatted'
    )
    fieldsets = (
        ('Información de la Actividad', {
            'fields': (
                'tarjeta',
                'accion',
                'usuario',
                'cierre',
                'timestamp'
            )
        }),
        ('Detalles', {
            'fields': (
                'descripcion',
                'metadata_formatted'
            )
        })
    )
    date_hierarchy = 'timestamp'
    list_per_page = 100
    
    def tarjeta_display(self, obj):
        """Display de tarjeta con iconos"""
        icons = {
            'verificador_datos': '🔍',
            'archivos_analista': '👤',
            'consolidacion': '📊',
            'incidencias': '⚠️',
            'entrega': '📤'
        }
        icon = icons.get(obj.tarjeta, '📋')
        return f"{icon} {obj.tarjeta.replace('_', ' ').title()}"
    tarjeta_display.short_description = 'Tarjeta'
    
    def accion_display(self, obj):
        """Display de acción con colores"""
        colors = {
            'abrir': '#3b82f6',      # azul
            'procesar': '#f59e0b',   # amarillo
            'completar': '#10b981',  # verde
            'error': '#ef4444',      # rojo
            'cancelar': '#6b7280'    # gris
        }
        color = colors.get(obj.accion, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.accion.title()
        )
    accion_display.short_description = 'Acción'
    
    def usuario_info(self, obj):
        """Info del usuario"""
        if obj.usuario:
            nombre_completo = f"{obj.usuario.nombre} {obj.usuario.apellido}".strip()
            return nombre_completo if nombre_completo else obj.usuario.correo_bdo
        return "Sistema"
    usuario_info.short_description = 'Usuario'
    
    def cierre_info(self, obj):
        """Info del cierre"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def resultado_display(self, obj):
        """Display del resultado con colores"""
        colors = {
            'exito': '#10b981',      # verde
            'error': '#ef4444',      # rojo
            'warning': '#f59e0b'     # amarillo
        }
        color = colors.get(obj.resultado, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_resultado_display()
        )
    resultado_display.short_description = 'Resultado'
    
    def metadata_formatted(self, obj):
        """Metadata formateada"""
        if obj.detalles:
            import json
            try:
                formatted = json.dumps(obj.detalles, indent=2, ensure_ascii=False)
                return format_html(f"<pre>{formatted}</pre>")
            except:
                return str(obj.detalles)
        return "Sin detalles"
    metadata_formatted.short_description = 'Detalles'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'usuario',
            'cierre',
            'cierre__cliente'
        )


# ================================
# ADMINISTRACIÓN DE INFORMES
# ================================

@admin.register(InformeNomina)
class InformeNominaAdmin(admin.ModelAdmin):
    """Administración de informes de nómina generados automáticamente"""
    
    list_display = (
        'cierre_info',
        'periodo_display',
        'cliente_display', 
        'fecha_generacion',
        'kpis_principales_display',
        'tiempo_calculo',
        'version_calculo',
        'estado_redis_display'
    )
    
    list_filter = (
        'fecha_generacion',
        'version_calculo',
        'cierre__cliente',
        'cierre__estado'
    )
    
    search_fields = (
        'cierre__cliente__nombre',
        'cierre__periodo'
    )
    
    readonly_fields = (
        'cierre',
        'fecha_generacion',
        'tiempo_calculo',
        'datos_cierre_display',
        'estado_redis_display'
    )
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'cierre',
                'fecha_generacion',
                'version_calculo',
                'tiempo_calculo',
                'estado_redis_display'
            )
        }),
        ('Datos del Cierre', {
            'fields': ('datos_cierre_display',),
            'classes': ('collapse',)
        })
    )
    
    @admin.action(description='⬇️ Descargar JSON del informe (v2 si es posible)')
    def descargar_json(self, request, queryset):
        if queryset.count() != 1:
            from django.contrib import messages
            self.message_user(request, 'Selecciona exactamente un informe.', level=messages.WARNING)
            return None
        informe = queryset.first()
        try:
            data = informe.datos_cierre or {}
            if not data:
                self.message_user(request, 'El informe no tiene datos JSON para descargar.', level=messages.WARNING)
                return None
            filename = f"informe_nomina_{informe.cierre.cliente.id}_{informe.cierre.periodo}.json"
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            response = HttpResponse(payload, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            from django.contrib import messages
            self.message_user(request, f'Error al descargar informe: {e}', level=messages.ERROR)
            return None

    actions = ['enviar_a_redis_action', 'descargar_json']
    date_hierarchy = 'fecha_generacion'
    list_per_page = 50
    
    def has_add_permission(self, request):
        """No permitir crear informes manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar informes"""
        return request.user.is_superuser
    
    def cierre_info(self, obj):
        """Info del cierre asociado"""
        return format_html(
            '<strong>{}</strong><br/>'
            '<small>Estado: <span style="color: {};">{}</span></small>',
            str(obj.cierre),
            '#10b981' if obj.cierre.estado == 'finalizado' else '#f59e0b',
            obj.cierre.get_estado_display()
        )
    cierre_info.short_description = 'Cierre'
    
    def periodo_display(self, obj):
        """Período del cierre"""
        return obj.cierre.periodo
    periodo_display.short_description = 'Período'
    
    def cliente_display(self, obj):
        """Cliente del cierre"""
        return obj.cierre.cliente.nombre
    cliente_display.short_description = 'Cliente'
    
    def kpis_principales_display(self, obj):
        """KPIs principales en formato compacto"""
        try:
            metricas = obj.datos_cierre.get('metricas_basicas', {})
            return format_html(
                '<strong>Dotación:</strong> {}<br/>'
                '<strong>Costo Empresa:</strong> ${:,.0f}<br/>'
                '<strong>Descuentos Legales:</strong> ${:,.0f}<br/>'
                '<strong>Rotación:</strong> {}%',
                metricas.get('dotacion_total', 0),
                metricas.get('costo_empresa_total', 0),
                metricas.get('descuentos_legales_total', 0),
                metricas.get('rotacion_porcentaje', 0)
            )
        except:
            return "Error al mostrar métricas"
    kpis_principales_display.short_description = 'Métricas Principales'
    
    def estado_redis_display(self, obj):
        """Estado del informe en Redis"""
        try:
            from .cache_redis import get_cache_system_nomina
            cache_system = get_cache_system_nomina()
            
            # Verificar si existe en Redis
            datos_redis = cache_system.get_informe_nomina(
                obj.cierre.cliente.id, 
                obj.cierre.periodo
            )
            
            if datos_redis:
                cached_at = datos_redis.get('_metadata', {}).get('cached_at', 'N/A')
                return format_html(
                    '<span style="color: #10b981;">✅ En Redis</span><br/>'
                    '<small>Actualizado: {}</small>',
                    cached_at[:16] if cached_at != 'N/A' else 'N/A'
                )
            else:
                return format_html(
                    '<span style="color: #ef4444;">❌ No en Redis</span><br/>'
                    '<small><a href="#" onclick="document.querySelector(\'select[name=action]\').value=\'enviar_a_redis_action\'; document.querySelector(\'input[name=_selected_action][value={}]\').checked=true; document.querySelector(\'button[name=index]\').click(); return false;">Enviar a Redis</a></small>',
                    obj.id
                )
        except Exception as e:
            return format_html(
                '<span style="color: #f59e0b;">⚠️ Error verificando</span><br/>'
                '<small>{}</small>',
                str(e)[:50]
            )
    estado_redis_display.short_description = 'Estado Redis'
    
    def datos_cierre_display(self, obj):
        """Datos del cierre formateados"""
        try:
            import json
            formatted = json.dumps(obj.datos_cierre, indent=2, ensure_ascii=False)
            return format_html(f"<pre style='max-height: 400px; overflow-y: auto;'>{formatted}</pre>")
        except:
            return str(obj.datos_cierre)
    datos_cierre_display.short_description = 'Datos del Cierre (JSON)'
    
    def enviar_a_redis_action(self, request, queryset):
        """Acción para encolar el envío de informes seleccionados a Redis (TTL infinito)."""
        from django.contrib import messages
        from .tasks import enviar_informe_redis_task

        encolados = 0
        for informe in queryset:
            try:
                # Encolar con TTL infinito (None) usando la task
                enviar_informe_redis_task.delay(prev_result=None, cierre_id=informe.cierre.id, ttl_hours=None)
                encolados += 1
            except Exception as e:
                messages.error(
                    request,
                    f"❌ No se pudo encolar envío a Redis para {informe.cierre.cliente.nombre} - {informe.cierre.periodo}: {e}"
                )

        if encolados:
            messages.success(
                request,
                f"🚀 {encolados} envío(s) a Redis encolado(s). Se procesarán en segundo plano."
            )
    
    enviar_a_redis_action.short_description = "🚀 Enviar a Redis (DB 2)"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente'
        )


# =============================================================================
# ✅ ADMINS PARA AUDITORÍA DE VERIFICACIONES
# =============================================================================

@admin.register(HistorialVerificacionCierre)
class HistorialVerificacionCierreAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'numero_intento', 'total_discrepancias_encontradas')
    list_filter = ('numero_intento',)
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')


@admin.register(DiscrepanciaHistorial)  
class DiscrepanciaHistorialAdmin(admin.ModelAdmin):
    list_display = ('historial_verificacion', 'tipo_discrepancia', 'rut_empleado')
    list_filter = ('tipo_discrepancia',)
    search_fields = ('rut_empleado', 'nombre_empleado')
