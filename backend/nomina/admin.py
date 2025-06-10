from django.contrib import admin
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones, 
    MovimientoVariacionSueldo, MovimientoVariacionContrato,
    LibroRemuneracionesUpload, MovimientosMesUpload, ArchivoAnalistaUpload, 
    ArchivoNovedadesUpload, ChecklistItem
)


@admin.register(CierreNomina)
class CierreNominaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'periodo', 'estado', 'fecha_creacion', 'usuario_analista')
    list_filter = ('cliente', 'estado', 'periodo')
    search_fields = ('cliente__nombre', 'periodo')
    readonly_fields = ('fecha_creacion',)


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


@admin.register(MovimientoAusentismo)
class MovimientoAusentismoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'tipo', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'tipo', 'motivo')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'tipo', 'empresa_nombre')
    readonly_fields = ('empleado',)


@admin.register(MovimientoVacaciones)
class MovimientoVacacionesAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'fecha_inicio', 'fecha_fin_vacaciones', 'cantidad_dias', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'empresa_nombre')
    readonly_fields = ('empleado',)


@admin.register(MovimientoVariacionSueldo)
class MovimientoVariacionSueldoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'sueldo_base_anterior', 'sueldo_base_actual', 'porcentaje_reajuste', 'cierre')
    search_fields = ('rut', 'nombres_apellidos', 'empresa_nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo', 'empresa_nombre')
    readonly_fields = ('empleado', 'variacion_pesos')


@admin.register(MovimientoVariacionContrato)
class MovimientoVariacionContratoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres_apellidos', 'tipo_contrato_anterior', 'tipo_contrato_actual', 'cierre')
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
    list_display = ('cierre', 'fecha_subida', 'estado')
    list_filter = ('estado',)
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')


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
