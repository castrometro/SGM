from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Industria, Area, Cliente, AsignacionClienteUsuario, Servicio, ServicioCliente, Contrato

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    list_display = (
        'correo_bdo', 'nombre', 'apellido', 'tipo_usuario',
        'get_areas', 'is_staff', 'is_active'
    )
    ordering = ('tipo_usuario', 'correo_bdo')  # Ordena por tipo_usuario
    search_fields = ('correo_bdo', 'nombre', 'apellido')
    list_filter = ('tipo_usuario', 'areas')  # 👈 Filtra por área y tipo de usuario

    fieldsets = (
        (None, {'fields': ('correo_bdo', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'cargo_bdo', 'tipo_usuario', 'areas')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo_bdo', 'password1', 'password2', 'nombre', 'apellido', 'cargo_bdo', 'tipo_usuario', 'is_staff', 'is_superuser', 'areas'),
        }),
    )

    def get_areas(self, obj):
        return ", ".join([a.nombre for a in obj.areas.all()])
    get_areas.short_description = 'Áreas'


admin.site.register([Industria, Area, Cliente, AsignacionClienteUsuario, Servicio, ServicioCliente])



class ContratoAdmin(admin.ModelAdmin):
    filter_horizontal = ('servicios_contratados',)  # 👈 Esto te da el widget de selección dual
    list_display = ('id', 'cliente', 'fecha_inicio', 'fecha_vencimiento', 'activo')
    search_fields = ('cliente__nombre',)
    list_filter = ('activo', 'cliente')

admin.site.register(Contrato, ContratoAdmin)
