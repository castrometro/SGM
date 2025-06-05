from django.contrib import admin
from .models import (
    CierreNomina, LibroRemuneracionesUpload, MovimientosMesUpload,
    ArchivoAnalistaUpload, ArchivoNovedadesUpload, ConceptoRemuneracion,
    Novedad, IncidenciaComparacion, IncidenciaNovedad, ChecklistItem,
    EmpleadosMes, RegistroNomina
)




# Inlines para mostrar archivos/elementos ligados al cierre directamente
class LibroRemuneracionesUploadInline(admin.TabularInline):
    model = LibroRemuneracionesUpload
    extra = 0
    readonly_fields = ['archivo', 'fecha_subida', 'estado']

class MovimientosMesUploadInline(admin.TabularInline):
    model = MovimientosMesUpload
    extra = 0
    readonly_fields = ['archivo', 'fecha_subida', 'estado']

class ArchivoAnalistaUploadInline(admin.TabularInline):
    model = ArchivoAnalistaUpload
    extra = 0
    readonly_fields = ['tipo_archivo', 'archivo', 'fecha_subida', 'estado', 'analista']

class ArchivoNovedadesUploadInline(admin.TabularInline):
    model = ArchivoNovedadesUpload
    extra = 0
    readonly_fields = ['archivo', 'fecha_subida', 'estado', 'analista']

class IncidenciaComparacionInline(admin.TabularInline):
    model = IncidenciaComparacion
    extra = 0
    readonly_fields = ['tipo_incidencia', 'rut', 'detalle', 'resuelto', 'fecha_creacion', 'analista']

class IncidenciaNovedadInline(admin.TabularInline):
    model = IncidenciaNovedad
    extra = 0
    readonly_fields = ['rut', 'nombre', 'concepto', 'monto_novedad', 'monto_libro', 'tipo_incidencia', 'detalle', 'fecha_creacion', 'analista', 'resuelto']



class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ('descripcion', 'estado', 'comentario',)
    readonly_fields = ('descripcion',)  # Solo editar estado y comentario



@admin.register(CierreNomina)
class CierreNominaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'periodo', 'estado', 'fecha_creacion', 'usuario_analista', 'usuario_supervisor')
    list_filter = ('cliente', 'estado', 'periodo')
    search_fields = ('cliente__nombre', 'periodo')
    inlines = [
        LibroRemuneracionesUploadInline,
        MovimientosMesUploadInline,
        ArchivoAnalistaUploadInline,
        ArchivoNovedadesUploadInline,
        IncidenciaComparacionInline,
        IncidenciaNovedadInline,
        ChecklistItemInline,   # <<--- AGREGA ESTA LÍNEA AQUÍ
    ]
    readonly_fields = ('fecha_creacion', 'fecha_aprobacion')


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

@admin.register(ConceptoRemuneracion)
class ConceptoRemuneracionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre_concepto', 'clasificacion', 'vigente', 'fecha_creacion')
    list_filter = ('cliente', 'clasificacion', 'vigente')
    search_fields = ('cliente__nombre', 'nombre_concepto')
    readonly_fields = ('fecha_creacion',)

@admin.register(Novedad)
class NovedadAdmin(admin.ModelAdmin):
    list_display = ('archivo_upload', 'rut', 'concepto', 'monto', 'clasificacion')
    list_filter = ('clasificacion',)
    search_fields = ('rut', 'concepto')

@admin.register(IncidenciaComparacion)
class IncidenciaComparacionAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'tipo_incidencia', 'rut', 'resuelto', 'fecha_creacion', 'analista')
    list_filter = ('resuelto', 'tipo_incidencia')
    search_fields = ('cierre__cliente__nombre', 'rut')

@admin.register(IncidenciaNovedad)
class IncidenciaNovedadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'rut', 'concepto', 'monto_novedad', 'monto_libro', 'tipo_incidencia', 'resuelto', 'fecha_creacion', 'analista')
    list_filter = ('resuelto', 'tipo_incidencia')
    search_fields = ('cierre__cliente__nombre', 'rut', 'concepto')


@admin.register(EmpleadosMes)
class EmpleadosMesAdmin(admin.ModelAdmin):
    list_display = (
        'rut_trabajador',
        'nombre',
        'apellido_paterno',
        'ano',
        'mes',
        'cliente',
    )
    search_fields = ('rut_trabajador', 'nombre', 'apellido_paterno')


@admin.register(RegistroNomina)
class RegistroNominaAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'empleado')
    search_fields = (
        'empleado__rut_trabajador',
        'empleado__nombre',
        'cierre__cliente__nombre',
        'cierre__periodo',
    )
    list_filter = ('cierre__periodo', 'cierre__cliente')

