from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Industria, Area, Cliente, AsignacionClienteUsuario, Servicio, ServicioCliente, Contrato


class AnalistaSupervisadoInline(admin.TabularInline):
    """Inline para mostrar analistas supervisados en la página del supervisor"""
    model = Usuario
    fk_name = 'supervisor'
    extra = 0
    fields = ('nombre', 'apellido', 'correo_bdo', 'tipo_usuario', 'get_areas_inline')
    readonly_fields = ('get_areas_inline',)
    can_delete = False
    
    def get_areas_inline(self, obj):
        if obj:
            return ", ".join([a.nombre for a in obj.areas.all()])
        return ""
    get_areas_inline.short_description = 'Áreas'


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    list_display = (
        'correo_bdo', 'nombre', 'apellido', 'tipo_usuario',
        'get_areas', 'get_supervisor', 'get_analistas_count', 'is_staff', 'is_active'
    )
    ordering = ('tipo_usuario', 'correo_bdo')  # Ordena por tipo_usuario
    search_fields = ('correo_bdo', 'nombre', 'apellido')
    list_filter = ('tipo_usuario', 'areas', 'supervisor')  # 👈 Filtra por área, tipo de usuario y supervisor

    fieldsets = (
        (None, {'fields': ('correo_bdo', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'cargo_bdo', 'tipo_usuario', 'areas')}),
        ('Jerarquía', {'fields': ('supervisor',)}),  # 👈 Nueva sección para mostrar supervisor
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login',)}),
    )

    def get_inlines(self, request, obj):
        """Solo mostrar el inline de analistas supervisados si el usuario es supervisor"""
        if obj and obj.tipo_usuario == 'supervisor':
            return [AnalistaSupervisadoInline]
        return []

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo_bdo', 'password1', 'password2', 'nombre', 'apellido', 'cargo_bdo', 'tipo_usuario', 'supervisor', 'is_staff', 'is_superuser', 'areas'),
        }),
    )

    def get_areas(self, obj):
        return ", ".join([a.nombre for a in obj.areas.all()])
    get_areas.short_description = 'Áreas'

    def get_supervisor(self, obj):
        """Muestra el supervisor asignado"""
        if obj.supervisor:
            return f"{obj.supervisor.nombre} {obj.supervisor.apellido} ({obj.supervisor.tipo_usuario})"
        return "Sin supervisor"
    get_supervisor.short_description = 'Supervisor'

    def get_analistas_count(self, obj):
        """Muestra cuántos analistas supervisa este usuario"""
        if obj.tipo_usuario == 'supervisor':
            count = obj.analistas_supervisados.count()
            return f"{count} analista{'s' if count != 1 else ''}"
        return "-"
    get_analistas_count.short_description = 'Analistas supervisados'


@admin.register(AsignacionClienteUsuario)
class AsignacionClienteUsuarioAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'get_usuario_info', 'get_supervisor_info', 'fecha_asignacion')
    list_filter = ('usuario__tipo_usuario', 'usuario__areas', 'usuario__supervisor')
    search_fields = ('cliente__nombre', 'cliente__rut', 'usuario__nombre', 'usuario__apellido', 'usuario__correo_bdo')
    ordering = ('cliente__nombre',)

    def get_usuario_info(self, obj):
        """Muestra información completa del usuario asignado"""
        return f"{obj.usuario.nombre} {obj.usuario.apellido} ({obj.usuario.tipo_usuario})"
    get_usuario_info.short_description = 'Usuario Asignado'

    def get_supervisor_info(self, obj):
        """Muestra el supervisor del usuario asignado"""
        if obj.usuario.supervisor:
            return f"{obj.usuario.supervisor.nombre} {obj.usuario.supervisor.apellido}"
        return "Sin supervisor"
    get_supervisor_info.short_description = 'Supervisor'


admin.site.register([Industria, Area, Cliente, Servicio, ServicioCliente])



class ContratoAdmin(admin.ModelAdmin):
    filter_horizontal = ('servicios_contratados',)  # 👈 Esto te da el widget de selección dual
    list_display = ('id', 'cliente', 'fecha_inicio', 'fecha_vencimiento', 'activo')
    search_fields = ('cliente__nombre',)
    list_filter = ('activo', 'cliente')

admin.site.register(Contrato, ContratoAdmin)
