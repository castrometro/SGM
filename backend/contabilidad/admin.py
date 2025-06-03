from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    TipoDocumento, CuentaContable, CierreContabilidad, LibroMayorUpload,
    AperturaCuenta, MovimientoContable, ClasificacionSet,
    ClasificacionOption, AccountClassification, Incidencia, CentroCosto,
    Auxiliar
)

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'codigo', 'descripcion')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('cliente',)

@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'codigo', 'nombre','nombre_en')
    search_fields = ('codigo', 'nombre')
    list_filter = ('cliente',)

@admin.register(CierreContabilidad)
class CierreContabilidadAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'periodo', 'estado', 'usuario', 'fecha_creacion')
    list_filter = ('estado', 'cliente')
    search_fields = ('periodo',)

@admin.register(LibroMayorUpload)
class LibroMayorUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'fecha_subida', 'procesado')
    list_filter = ('procesado',)

@admin.register(AperturaCuenta)
class AperturaCuentaAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'cuenta', 'saldo_anterior')

@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'cuenta', 'fecha', 'debe', 'haber')
    list_filter = ('fecha', 'cuenta')
    search_fields = ('descripcion',)

@admin.register(ClasificacionSet)
class ClasificacionSetAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre')

@admin.register(ClasificacionOption)
class ClasificacionOptionAdmin(admin.ModelAdmin):
    list_display = ('set_clas', 'valor')

@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'set_clas', 'opcion', 'asignado_por', 'fecha')

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'tipo', 'resuelta', 'fecha_creacion')
    list_filter = ('resuelta', 'tipo')
    search_fields = ('descripcion', 'respuesta')

@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre')
    list_filter = ('cliente',)

@admin.register(Auxiliar)
class AuxiliarAdmin(admin.ModelAdmin):
    list_display = ('rut_auxiliar', 'nombre', 'fecha_creacion')
