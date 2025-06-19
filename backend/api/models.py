from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models

# —————————————————————————————————————————————————————
#           Custom User & Manager
# —————————————————————————————————————————————————————

class UsuarioManager(BaseUserManager):
    def create_user(self, correo_bdo, password=None, **extra_fields):
        if not correo_bdo:
            raise ValueError('El correo_bdo debe ser proporcionado')
        user = self.model(correo_bdo=self.normalize_email(correo_bdo), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo_bdo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'gerente')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        return self.create_user(correo_bdo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ('analista',   'Analista'),
        ('senior',     'Senior'),
        ('supervisor','Supervisor'),
        ('gerente',    'Gerente'),
    ]

    nombre         = models.CharField(max_length=50)
    apellido       = models.CharField(max_length=50)
    correo_bdo     = models.EmailField(unique=True)
    tipo_usuario   = models.CharField(max_length=20, choices=ROLES, default='analista')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cargo_bdo      = models.CharField(max_length=50)

    # Un usuario puede pertenecer a varias áreas de BDO (Contabilidad, Nómina, etc.)
    areas          = models.ManyToManyField('Area', related_name='usuarios', blank=True)
    
    # Relación supervisor-analista dentro de la misma área
    supervisor     = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='analistas_supervisados',
        help_text="El supervisor asignado a este analista (debe ser de la misma área)"
    )

    is_staff       = models.BooleanField(default=False)
    is_superuser   = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)

    objects        = UsuarioManager()

    USERNAME_FIELD  = 'correo_bdo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    def clean(self):
        """Validar que el supervisor sea del mismo área que el analista"""
        from django.core.exceptions import ValidationError
        
        if self.supervisor:
            # Verificar que el supervisor sea realmente un supervisor
            if self.supervisor.tipo_usuario != 'supervisor':
                raise ValidationError('El usuario asignado como supervisor debe tener tipo_usuario "supervisor"')
            
            # Verificar que ambos estén en la misma área (al menos una área en común)
            if self.pk:  # Solo si el usuario ya existe (tiene pk)
                supervisor_areas = set(self.supervisor.areas.all())
                analista_areas = set(self.areas.all())
                
                if not supervisor_areas.intersection(analista_areas):
                    raise ValidationError('El supervisor y el analista deben pertenecer al menos a una área en común')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_analistas_supervisados(self):
        """Obtiene todos los analistas que supervisa este usuario"""
        if self.tipo_usuario != 'supervisor':
            return Usuario.objects.none()
        return self.analistas_supervisados.all()
    
    def get_clientes_de_analistas_supervisados(self):
        """Obtiene todos los clientes asignados a los analistas supervisados"""
        if self.tipo_usuario != 'supervisor':
            return []
        
        analistas = self.get_analistas_supervisados()
        clientes = []
        for analista in analistas:
            # Obtener clientes asignados a cada analista
            asignaciones = analista.asignaciones.all()
            clientes.extend([asignacion.cliente for asignacion in asignaciones])
        return clientes
    
    def puede_supervisar_a(self, analista):
        """Verifica si este supervisor puede supervisar al analista dado"""
        if self.tipo_usuario != 'supervisor':
            return False
        
        # Verificar que tengan al menos un área en común
        supervisor_areas = set(self.areas.all())
        analista_areas = set(analista.areas.all())
        
        return bool(supervisor_areas.intersection(analista_areas))

    def __str__(self):
        return self.correo_bdo


# —————————————————————————————————————————————————————
#                      Catalogos
# —————————————————————————————————————————————————————

class Industria(models.Model):
    id_industria = models.BigAutoField(primary_key=True)
    nombre       = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Area(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# —————————————————————————————————————————————————————
#                    Clientes & Asignaciones
# —————————————————————————————————————————————————————

class Cliente(models.Model):
    id             = models.BigAutoField(primary_key=True)
    nombre         = models.CharField(max_length=100)
    rut            = models.CharField(max_length=12, unique=True)
    bilingue       = models.BooleanField(default=False, help_text="¿Este cliente requiere informes bilingües?")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    industria      = models.ForeignKey(
        Industria,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clientes'
    )

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class AsignacionClienteUsuario(models.Model):
    cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='asignaciones')
    usuario          = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='asignaciones')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Un cliente solo puede estar asignado a un analista
        unique_together = ('cliente', 'usuario')
        # TODO: Para enforcement estricto de 1 cliente = 1 analista únicamente,
        # cambiar a: constraints = [models.UniqueConstraint(fields=['cliente'], name='unique_cliente_assignment')]

    @classmethod
    def get_clientes_por_supervisor(cls, supervisor):
        """Obtiene todas las asignaciones de clientes para analistas supervisados por este supervisor"""
        if supervisor.tipo_usuario != 'supervisor':
            return cls.objects.none()
        
        analistas_supervisados = supervisor.get_analistas_supervisados()
        return cls.objects.filter(usuario__in=analistas_supervisados)

    def __str__(self):
        return f"{self.usuario.correo_bdo} ↔ {self.cliente.nombre}"


# —————————————————————————————————————————————————————
#                   Servicios y Contratos
# —————————————————————————————————————————————————————

class Servicio(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='servicios',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


class ServicioCliente(models.Model):
    id       = models.BigAutoField(primary_key=True)
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='precios_cliente'
    )
    cliente  = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='servicios_contratados'
    )
    valor    = models.DecimalField(max_digits=10, decimal_places=2)
    moneda   = models.CharField(
        max_length=10,
        choices=[('UF','UF'), ('USD','USD'), ('CLP','CLP')],
        default='CLP'
    )

    class Meta:
        unique_together = ('servicio', 'cliente')

    def __str__(self):
        return f"{self.cliente.nombre} – {self.servicio.nombre}: {self.moneda} {self.valor}"


class Contrato(models.Model):
    id                    = models.BigAutoField(primary_key=True)
    cliente               = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='contratos'
    )
    servicios_contratados = models.ManyToManyField(
        ServicioCliente,
        related_name='contratos'
    )
    fecha_inicio          = models.DateField(auto_now_add=True)
    fecha_vencimiento     = models.DateField()
    activo                = models.BooleanField(default=True)

    def __str__(self):
        return f"Contrato {self.id} – {self.cliente.nombre}"
