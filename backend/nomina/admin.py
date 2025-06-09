from django.contrib import admin
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoIngreso, MovimientoFiniquito, MovimientoAusentismo,
    LibroRemuneracionesUpload, MovimientosMesUpload, ArchivoAnalistaUpload, ArchivoNovedadesUpload,
    ChecklistItem
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


@admin.register(MovimientoIngreso)
class MovimientoIngresoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'fecha_ingreso', 'cierre', 'empleado')
    search_fields = ('rut', 'nombre')
    list_filter = ('cierre__cliente', 'cierre__periodo')


@admin.register(MovimientoFiniquito)
class MovimientoFiniquitoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'fecha_finiquito', 'motivo', 'cierre', 'empleado')
    search_fields = ('rut', 'nombre', 'motivo')
    list_filter = ('cierre__cliente', 'cierre__periodo')


@admin.register(MovimientoAusentismo)
class MovimientoAusentismoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'tipo_ausentismo', 'fecha_inicio', 'fecha_fin', 'dias', 'cierre', 'empleado')
    search_fields = ('rut', 'nombre', 'tipo_ausentismo')
    list_filter = ('cierre__cliente', 'tipo_ausentismo')


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
