from django.db import models
from api.models import Cliente
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

# Importar modelos de logging
from .models_logging import UploadLogNomina, TarjetaActivityLogNomina

User = get_user_model()

# Actualizar las clasificaciones según la migración 0012
CLASIFICACION_CHOICES = [
    ('haberes_imponibles', 'Haberes Imponibles'),
    ('haberes_no_imponibles', 'Haberes No Imponibles'),
    ('horas_extras', 'Horas Extras'),
    ('descuentos_legales', 'Descuentos Legales'),
    ('otros_descuentos', 'Otros Descuentos'),
    ('aportes_patronales', 'Aportes Patronales'),
    ('informacion_adicional', 'Información Adicional (No Monto)'),
    ('impuestos', 'Impuestos'),
]

def libro_remuneraciones_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/libro/{now}_{filename}"

def movimientos_mes_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/mov_mes/{now}_{filename}"

def analista_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/{instance.tipo_archivo}/{now}_{filename}"

def novedades_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/novedades/{now}_{filename}"


class CierreNomina(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=7)  # Ej: "2025-06"
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('datos_consolidados', 'Datos Consolidados'),
            ('reportes_generados', 'Reportes Generados'),
            ('validacion_senior', 'Validación Senior'),
            ('completado', 'Completado'),
            ('analisis_generado', 'Análisis Generado'),
            ('incidencias_abiertas', 'Incidencias Abiertas'),
            ('sin_incidencias', 'Sin Incidencias'),
        ],
        default='pendiente'
    )
    usuario_analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_analista')
    
    # NUEVOS CAMPOS PARA INCIDENCIAS
    estado_incidencias = models.CharField(
        max_length=50,
        choices=[
            ('analisis_pendiente', 'Análisis de Incidencias Pendiente'),
            ('incidencias_generadas', 'Incidencias Detectadas'),
            ('archivos_consolidados', 'Archivos Consolidados'),
            ('analisis_generado', 'Análisis Generado'),
            ('incidencias_abiertas', 'Incidencias Abiertas'),
            ('sin_incidencias', 'Sin Incidencias'),
            ('cerrado', 'Cerrado'),
        ],
        default='analisis_pendiente'
    )
    fecha_ultima_revision = models.DateTimeField(null=True, blank=True)
    revisiones_realizadas = models.PositiveIntegerField(default=0)
    supervisor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_supervisor')

    class Meta:
        unique_together = ('cliente', 'periodo')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo}"
    
    def actualizar_estado_automatico(self):
        """
        Actualiza el estado del cierre basado en el estado de los archivos
        y las incidencias pendientes automáticamente.
        """
        from django.utils import timezone
        
        # Si ya está completado, no cambiar
        if self.estado == 'completado':
            return self.estado
            
        # Verificar el estado de todos los archivos necesarios
        archivos_listos = self._verificar_archivos_listos()
        
        if not archivos_listos['todos_listos']:
            # Aún no están todos los archivos procesados
            if self.estado != 'en_proceso':
                self.estado = 'en_proceso'
                self.save(update_fields=['estado'])
            return self.estado
        
        # Todos los archivos están listos, cambiar a "datos_consolidados"
        if self.estado != 'datos_consolidados':
            self.estado = 'datos_consolidados'
            self.estado_incidencias = 'analisis_pendiente'
            self.save(update_fields=['estado', 'estado_incidencias'])
        
        return self.estado
    
    def _verificar_archivos_listos(self):
        """
        Verifica que todos los archivos necesarios estén en estado 'procesado'
        """
        resultado = {
            'todos_listos': False,
            'detalles': {},
            'archivos_faltantes': []
        }
        
        # 1. Verificar Libro de Remuneraciones (OBLIGATORIO)
        libro = self.libros_remuneraciones.first()
        if not libro or libro.estado != 'procesado':
            resultado['detalles']['libro_remuneraciones'] = {
                'estado': libro.estado if libro else 'no_subido',
                'requerido': True,
                'listo': False
            }
            resultado['archivos_faltantes'].append('Libro de Remuneraciones')
        else:
            resultado['detalles']['libro_remuneraciones'] = {
                'estado': 'procesado',
                'requerido': True,
                'listo': True
            }
        
        # 2. Verificar Movimientos del Mes (OBLIGATORIO)
        movimientos = self.movimientos_mes.first()
        if not movimientos or movimientos.estado != 'procesado':
            resultado['detalles']['movimientos_mes'] = {
                'estado': movimientos.estado if movimientos else 'no_subido',
                'requerido': True,
                'listo': False
            }
            resultado['archivos_faltantes'].append('Movimientos del Mes')
        else:
            resultado['detalles']['movimientos_mes'] = {
                'estado': 'procesado',
                'requerido': True,
                'listo': True
            }
        
        # 3. Verificar Archivos del Analista (AL MENOS UNO DEBE ESTAR PROCESADO)
        archivos_analista = self.archivos_analista.filter(estado='procesado')
        if archivos_analista.count() == 0:
            resultado['detalles']['archivos_analista'] = {
                'estado': 'ninguno_procesado',
                'requerido': True,
                'listo': False
            }
            resultado['archivos_faltantes'].append('Al menos un Archivo del Analista')
        else:
            resultado['detalles']['archivos_analista'] = {
                'estado': f'{archivos_analista.count()}_procesados',
                'requerido': True,
                'listo': True
            }
        
        # 4. Verificar Novedades (OPCIONAL - puede estar procesado o no subido)
        novedades = self.archivos_novedades.first()
        if novedades:
            if novedades.estado == 'procesado':
                resultado['detalles']['novedades'] = {
                    'estado': 'procesado',
                    'requerido': False,
                    'listo': True
                }
            else:
                # Si hay archivo de novedades pero no está procesado, debe procesarse
                resultado['detalles']['novedades'] = {
                    'estado': novedades.estado,
                    'requerido': False,
                    'listo': False
                }
                resultado['archivos_faltantes'].append('Novedades (pendiente de procesar)')
        else:
            # No hay archivo de novedades, está OK
            resultado['detalles']['novedades'] = {
                'estado': 'no_subido',
                'requerido': False,
                'listo': True
            }
        
        # Determinar si todos los archivos requeridos están listos
        archivos_requeridos_listos = (
            resultado['detalles']['libro_remuneraciones']['listo'] and
            resultado['detalles']['movimientos_mes']['listo'] and
            resultado['detalles']['archivos_analista']['listo']
        )
        
        # Si hay novedades subidas, también deben estar procesadas
        novedades_ok = resultado['detalles']['novedades']['listo']
        
        resultado['todos_listos'] = archivos_requeridos_listos and novedades_ok
        
        return resultado


class EmpleadoCierre(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='empleados')
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)
    rut_empresa = models.CharField(max_length=20)
    dias_trabajados = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("cierre", "rut")

    def __str__(self):
        return f"{self.rut} - {self.nombre} {self.apellido_paterno}"


class ConceptoRemuneracion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre_concepto = models.CharField(max_length=120)
    clasificacion = models.CharField(max_length=30, choices=CLASIFICACION_CHOICES)
    hashtags = models.JSONField(default=list, blank=True)
    usuario_clasifica = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conceptos_clasificados",
    )
    vigente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.nombre_concepto}"


class RegistroConceptoEmpleado(models.Model):
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoRemuneracion, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_concepto_original = models.CharField(max_length=200)
    monto = models.CharField(max_length=255, blank=True, null=True)  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empleado', 'nombre_concepto_original')

    def __str__(self):
        return f"{self.empleado} - {self.nombre_concepto_original}: {self.monto}"
    
    @property
    def monto_numerico(self):
        """Convierte el monto a número para cálculos, retorna 0 si no es posible"""
        try:
            return float(self.monto) if self.monto else 0
        except (ValueError, TypeError):
            return 0
    
    @property
    def es_numerico(self):
        """Verifica si el monto puede convertirse a número"""
        try:
            float(self.monto) if self.monto else 0
            return True
        except (ValueError, TypeError):
            return False


# Modelos para Movimientos_Mes completos

class MovimientoAltaBaja(models.Model):
    """Modelo para Altas y Bajas (b.1)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    fecha_retiro = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=80)
    dias_trabajados = models.IntegerField()
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)
    alta_o_baja = models.CharField(max_length=20)  # "ALTA" o "BAJA"
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - {self.alta_o_baja}"


class MovimientoAusentismo(models.Model):
    """Modelo completo para Ausentismos (b.2)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_inicio_ausencia = models.DateField()
    fecha_fin_ausencia = models.DateField()
    dias = models.IntegerField()
    tipo = models.CharField(max_length=80)
    motivo = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - {self.tipo}"


class MovimientoVacaciones(models.Model):
    """Modelo para Vacaciones (b.3)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin_vacaciones = models.DateField()
    fecha_retorno = models.DateField()
    cantidad_dias = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Vacaciones"


class MovimientoVariacionSueldo(models.Model):
    """Modelo para Variaciones Sueldo Base (b.4)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=80)
    sueldo_base_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_base_actual = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_reajuste = models.DecimalField(max_digits=5, decimal_places=2)
    variacion_pesos = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Variación Sueldo"


class MovimientoVariacionContrato(models.Model):
    """Modelo para Variaciones Tipo Contrato (b.5)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField(null=True, blank=True)
    tipo_contrato_anterior = models.CharField(max_length=80)
    tipo_contrato_actual = models.CharField(max_length=80)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Cambio Contrato"


class LibroRemuneracionesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='libros_remuneraciones')
    archivo = models.FileField(upload_to=libro_remuneraciones_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=60, choices=[
        ('pendiente', 'Pendiente'),
        ('analizando_hdrs', 'Analizando Headers'),
        ('hdrs_analizados', 'Headers Analizados'),
        ('clasif_en_proceso', 'Clasificación en Proceso'),
        ('clasif_pendiente', 'Clasificación Pendiente'),
        ('clasificado', 'Clasificado'),
        ('con_error', 'Con Error')
    ], default='pendiente')
    header_json = models.JSONField(default=list)
    upload_log = models.ForeignKey(
        'UploadLogNomina', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Referencia al log del upload que generó este archivo"
    )


class MovimientosMesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='movimientos_mes')
    archivo = models.FileField(upload_to=movimientos_mes_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error'),
        ('con_errores_parciales', 'Con Errores Parciales')
    ], default='pendiente')
    resultados_procesamiento = models.JSONField(default=dict, blank=True)
    upload_log = models.ForeignKey(
        'UploadLogNomina', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Referencia al log del upload que generó este archivo"
    )


class ArchivoAnalistaUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_analista')
    tipo_archivo = models.CharField(max_length=20, choices=[
        ('ingresos', 'Ingresos'),
        ('finiquitos', 'Finiquitos'),
        ('incidencias', 'Incidencias')
    ])
    archivo = models.FileField(upload_to=analista_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')
    upload_log = models.ForeignKey(
        'UploadLogNomina', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Referencia al log del upload que generó este archivo"
    )


class ArchivoNovedadesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_novedades')
    archivo = models.FileField(upload_to=novedades_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=60, choices=[
        ('pendiente', 'Pendiente'),
        ('analizando_hdrs', 'Analizando Headers'),
        ('hdrs_analizados', 'Headers Analizados'),
        ('clasif_en_proceso', 'Clasificación en Proceso'),
        ('clasif_pendiente', 'Clasificación Pendiente'),
        ('clasificado', 'Clasificado'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')
    header_json = models.JSONField(default=list)
    upload_log = models.ForeignKey(
        'UploadLogNomina', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Referencia al log del upload que generó este archivo"
    )


class ChecklistItem(models.Model):
    CHECK_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('no_realizado', 'No Realizado'),
    ]

    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='checklist')
    descripcion = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=CHECK_CHOICES, default='pendiente')
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cierre} - {self.descripcion} - {self.estado}"


# Modelos específicos para Novedades

class EmpleadoCierreNovedades(models.Model):
    """Modelo específico para empleados en el procesamiento de novedades"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='empleados_novedades')
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("cierre", "rut")

    def __str__(self):
        return f"Novedades - {self.rut} - {self.nombre} {self.apellido_paterno}"


class ConceptoRemuneracionNovedades(models.Model):
    """Mapeo entre headers de novedades y conceptos del libro de remuneraciones"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Header tal como aparece en el archivo de novedades
    nombre_concepto_novedades = models.CharField(max_length=120)
    
    # Mapeo directo al concepto del libro de remuneraciones
    concepto_libro = models.ForeignKey(
        ConceptoRemuneracion, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Concepto del libro de remuneraciones al que mapea este header de novedades"
    )
    
    # Metadatos del mapeo
    usuario_mapea = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mapeos_novedades_creados",
    )
    activo = models.BooleanField(default=True)
    fecha_mapeo = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto_novedades')

    def __str__(self):
        nombre = self.concepto_libro.nombre_concepto if self.concepto_libro else "Sin asignación"
        return f"{self.cliente.nombre}: {self.nombre_concepto_novedades} → {nombre}"
    
    # Propiedades que delegan al concepto del libro
    @property
    def clasificacion(self):
        return self.concepto_libro.clasificacion if self.concepto_libro else None
    
    @property
    def hashtags(self):
        return self.concepto_libro.hashtags if self.concepto_libro else []
    
    @property
    def nombre_concepto(self):
        """Compatibilidad con código existente"""
        return self.nombre_concepto_novedades
    
    @property
    def vigente(self):
        """Compatibilidad con código existente"""
        return self.activo and (self.concepto_libro.vigente if self.concepto_libro else False)


class RegistroConceptoEmpleadoNovedades(models.Model):
    """Modelo específico para registros de conceptos de empleados en novedades"""
    empleado = models.ForeignKey(EmpleadoCierreNovedades, on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoRemuneracionNovedades, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_concepto_original = models.CharField(max_length=200)
    monto = models.CharField(max_length=255, blank=True, null=True)  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empleado', 'nombre_concepto_original')

    def __str__(self):
        return f"Novedades - {self.empleado} - {self.nombre_concepto_original}: {self.monto}"
    
    @property
    def monto_numerico(self):
        """Convierte el monto a número para cálculos, retorna 0 si no es posible"""
        try:
            return float(self.monto) if self.monto else 0
        except (ValueError, TypeError):
            return 0
    
    @property
    def es_numerico(self):
        """Verifica si el monto puede convertirse a número"""
        try:
            float(self.monto) if self.monto else 0
            return True
        except (ValueError, TypeError):
            return False
    
    @property
    def concepto_libro_equivalente(self):
        """Retorna el concepto del libro de remuneraciones equivalente"""
        return self.concepto.concepto_libro if self.concepto else None


# Modelos para datos del Analista

class AnalistaFiniquito(models.Model):
    """Datos de Finiquitos subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_retiro = models.DateField()
    motivo = models.CharField(max_length=200)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - Finiquito"


class AnalistaIncidencia(models.Model):
    """Datos de Incidencias subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_inicio_ausencia = models.DateField()
    fecha_fin_ausencia = models.DateField()
    dias = models.IntegerField()
    tipo_ausentismo = models.CharField(max_length=80)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - {self.tipo_ausentismo}"


class AnalistaIngreso(models.Model):
    """Datos de Ingresos subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_ingreso = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - Ingreso"


# ===== SISTEMA DE INCIDENCIAS COLABORATIVO =====

class EstadoCierreIncidencias(models.TextChoices):
    ANALISIS_PENDIENTE = 'analisis_pendiente', 'Análisis de Incidencias Pendiente'
    INCIDENCIAS_GENERADAS = 'incidencias_generadas', 'Incidencias Detectadas'
    RESOLUCION_ANALISTA = 'resolucion_analista', 'En Resolución por Analista'
    REVISION_SUPERVISOR = 'revision_supervisor', 'En Revisión por Supervisor'
    DEVUELTO_ANALISTA = 'devuelto_analista', 'Devuelto al Analista'
    APROBADO = 'aprobado', 'Incidencias Aprobadas'
    CIERRE_COMPLETADO = 'cierre_completado', 'Cierre Completado'

class TipoIncidencia(models.TextChoices):
    # Grupo 1: Libro vs Novedades
    EMPLEADO_SOLO_LIBRO = 'empleado_solo_libro', 'Empleado solo en Libro'
    EMPLEADO_SOLO_NOVEDADES = 'empleado_solo_novedades', 'Empleado solo en Novedades'
    DIFERENCIA_DATOS_PERSONALES = 'diff_datos_personales', 'Diferencia en Datos Personales'
    DIFERENCIA_SUELDO_BASE = 'diff_sueldo_base', 'Diferencia en Sueldo Base'
    DIFERENCIA_CONCEPTO_MONTO = 'diff_concepto_monto', 'Diferencia en Monto por Concepto'
    CONCEPTO_SOLO_LIBRO = 'concepto_solo_libro', 'Concepto solo en Libro'
    CONCEPTO_SOLO_NOVEDADES = 'concepto_solo_novedades', 'Concepto solo en Novedades'
    
    # Grupo 2: MovimientosMes vs Analista
    INGRESO_NO_REPORTADO = 'ingreso_no_reportado', 'Ingreso no reportado por Analista'
    FINIQUITO_NO_REPORTADO = 'finiquito_no_reportado', 'Finiquito no reportado por Analista'
    AUSENCIA_NO_REPORTADA = 'ausencia_no_reportada', 'Ausencia no reportada por Analista'
    DIFERENCIA_FECHAS_AUSENCIA = 'diff_fechas_ausencia', 'Diferencia en Fechas de Ausencia'
    DIFERENCIA_DIAS_AUSENCIA = 'diff_dias_ausencia', 'Diferencia en Días de Ausencia'
    DIFERENCIA_TIPO_AUSENCIA = 'diff_tipo_ausencia', 'Diferencia en Tipo de Ausencia'

class EstadoIncidencia(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de Resolución'
    RESUELTA_ANALISTA = 'resuelta_analista', 'Resuelta por Analista'
    APROBADA_SUPERVISOR = 'aprobada_supervisor', 'Aprobada por Supervisor'
    RECHAZADA_SUPERVISOR = 'rechazada_supervisor', 'Rechazada por Supervisor'
    RE_RESUELTA = 're_resuelta', 'Re-resuelta por Analista'

def resolucion_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"resoluciones/{instance.incidencia.cierre.cliente.id}/{instance.incidencia.cierre.periodo}/{now}_{filename}"

class IncidenciaCierre(models.Model):
    """Incidencias detectadas en la comparación de archivos de un cierre"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='incidencias')
    tipo_incidencia = models.CharField(max_length=50, choices=TipoIncidencia.choices)
    
    # Empleado afectado
    empleado_libro = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    empleado_novedades = models.ForeignKey('EmpleadoCierreNovedades', on_delete=models.CASCADE, null=True, blank=True)
    rut_empleado = models.CharField(max_length=20)
    
    # Detalles de la incidencia
    descripcion = models.TextField()
    valor_libro = models.CharField(max_length=500, null=True, blank=True)
    valor_novedades = models.CharField(max_length=500, null=True, blank=True)
    valor_movimientos = models.CharField(max_length=500, null=True, blank=True)
    valor_analista = models.CharField(max_length=500, null=True, blank=True)
    
    # Contexto adicional
    concepto_afectado = models.CharField(max_length=200, null=True, blank=True)
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    
    # NUEVOS CAMPOS PARA RESOLUCIÓN COLABORATIVA
    estado = models.CharField(max_length=20, choices=EstadoIncidencia.choices, default='pendiente')
    prioridad = models.CharField(max_length=10, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ], default='media')
    
    # Impacto monetario calculado
    impacto_monetario = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Usuario asignado para resolución
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_asignadas')
    
    # Fechas de seguimiento
    fecha_primera_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_ultima_accion = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'tipo_incidencia']),
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['rut_empleado', 'cierre']),
            models.Index(fields=['estado', 'prioridad']),
            models.Index(fields=['asignado_a', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_incidencia_display()} - {self.rut_empleado} - {self.cierre}"

    def calcular_impacto_monetario(self):
        """Calcula el impacto monetario de la incidencia"""
        try:
            if self.tipo_incidencia == TipoIncidencia.DIFERENCIA_CONCEPTO_MONTO:
                if self.valor_libro and self.valor_novedades:
                    # Limpiar y convertir valores
                    monto_libro = float(str(self.valor_libro).replace(',', '').replace('$', '').strip())
                    monto_novedades = float(str(self.valor_novedades).replace(',', '').replace('$', '').strip())
                    return abs(monto_libro - monto_novedades)
            elif self.tipo_incidencia == TipoIncidencia.DIFERENCIA_SUELDO_BASE:
                if self.valor_libro and self.valor_novedades:
                    sueldo_libro = float(str(self.valor_libro).replace(',', '').replace('$', '').strip())
                    sueldo_novedades = float(str(self.valor_novedades).replace(',', '').replace('$', '').strip())
                    return abs(sueldo_libro - sueldo_novedades)
        except (ValueError, TypeError):
            pass
        return 0

    def save(self, *args, **kwargs):
        # Calcular impacto monetario automáticamente
        if not self.impacto_monetario:
            self.impacto_monetario = self.calcular_impacto_monetario()
        super().save(*args, **kwargs)

class ResolucionIncidencia(models.Model):
    """Historial de resoluciones de una incidencia (conversación)"""
    incidencia = models.ForeignKey(IncidenciaCierre, on_delete=models.CASCADE, related_name='resoluciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_resolucion = models.CharField(max_length=20, choices=[
        ('justificacion', 'Justificación'),
        ('correccion', 'Corrección'),
        ('aprobacion', 'Aprobación'),
        ('rechazo', 'Rechazo'),
        ('consulta', 'Consulta'),
        ('solicitud_cambio', 'Solicitud de Cambio'),
    ])
    
    # Contenido de la resolución
    comentario = models.TextField()
    adjunto = models.FileField(upload_to=resolucion_upload_to, null=True, blank=True)
    
    # Metadatos
    fecha_resolucion = models.DateTimeField(auto_now_add=True)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    
    # Para correcciones de datos
    valor_corregido = models.CharField(max_length=500, null=True, blank=True)
    campo_corregido = models.CharField(max_length=100, null=True, blank=True)
    
    # Referencias a usuarios mencionados
    usuarios_mencionados = models.ManyToManyField(User, related_name='resoluciones_mencionado', blank=True)
    
    class Meta:
        ordering = ['-fecha_resolucion']
    
    def __str__(self):
        return f"{self.get_tipo_resolucion_display()} por {self.usuario.correo_bdo} - {self.incidencia}"


# ======== MODELOS PARA ANÁLISIS DE DATOS ========

class AnalisisDatosCierre(models.Model):
    """Análisis estadístico de datos del cierre actual vs mes anterior"""
    cierre = models.OneToOneField(CierreNomina, on_delete=models.CASCADE, related_name='analisis_datos')
    
    # Datos del cierre actual
    cantidad_empleados_actual = models.IntegerField(default=0)
    cantidad_ingresos_actual = models.IntegerField(default=0)
    cantidad_finiquitos_actual = models.IntegerField(default=0)
    cantidad_ausentismos_actual = models.IntegerField(default=0)
    
    # Datos del mes anterior (para comparación)
    cantidad_empleados_anterior = models.IntegerField(default=0)
    cantidad_ingresos_anterior = models.IntegerField(default=0)
    cantidad_finiquitos_anterior = models.IntegerField(default=0)
    cantidad_ausentismos_anterior = models.IntegerField(default=0)
    
    # Ausentismos por tipo (JSON con conteos)
    ausentismos_por_tipo_actual = models.JSONField(default=dict)
    ausentismos_por_tipo_anterior = models.JSONField(default=dict)
    
    # Configuración de tolerancia usada
    tolerancia_variacion_salarial = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    
    # Estado del análisis
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ], default='pendiente')
    
    # Fechas
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Usuario que inició el análisis
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Notas adicionales
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Análisis de Datos del Cierre"
        verbose_name_plural = "Análisis de Datos de Cierres"
        ordering = ['-fecha_analisis']
    
    def __str__(self):
        return f"Análisis {self.cierre.periodo} - {self.cierre.cliente.nombre}"
    
    def calcular_variaciones(self):
        """Calcula las variaciones porcentuales entre mes actual y anterior"""
        return {
            'empleados': self._calcular_variacion_porcentual(self.cantidad_empleados_actual, self.cantidad_empleados_anterior),
            'ingresos': self._calcular_variacion_porcentual(self.cantidad_ingresos_actual, self.cantidad_ingresos_anterior),
            'finiquitos': self._calcular_variacion_porcentual(self.cantidad_finiquitos_actual, self.cantidad_finiquitos_anterior),
            'ausentismos': self._calcular_variacion_porcentual(self.cantidad_ausentismos_actual, self.cantidad_ausentismos_anterior),
        }
    
    def _calcular_variacion_porcentual(self, actual, anterior):
        """Calcula variación porcentual entre dos valores"""
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        return ((actual - anterior) / anterior) * 100


class IncidenciaVariacionSalarial(models.Model):
    """Incidencias específicas de variaciones salariales significativas"""
    analisis = models.ForeignKey(AnalisisDatosCierre, on_delete=models.CASCADE, related_name='incidencias_variacion')
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    
    # Datos del empleado
    rut_empleado = models.CharField(max_length=12)
    nombre_empleado = models.CharField(max_length=200)
    
    # Datos salariales
    sueldo_base_actual = models.DecimalField(max_digits=15, decimal_places=2)
    sueldo_base_anterior = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje_variacion = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Tipo de variación
    tipo_variacion = models.CharField(max_length=20, choices=[
        ('aumento', 'Aumento'),
        ('disminucion', 'Disminución'),
    ])
    
    # Estado de resolución
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_analisis', 'En Análisis'),
        ('justificado', 'Justificado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ], default='pendiente')
    
    # Usuarios involucrados
    analista_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_variacion_asignadas')
    supervisor_revisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_variacion_supervisadas')
    
    # Justificación del analista
    justificacion_analista = models.TextField(blank=True)
    fecha_justificacion = models.DateTimeField(null=True, blank=True)
    
    # Resolución del supervisor
    comentario_supervisor = models.TextField(blank=True)
    fecha_resolucion_supervisor = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_accion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Incidencia de Variación Salarial"
        verbose_name_plural = "Incidencias de Variación Salarial"
        ordering = ['-fecha_deteccion']
        indexes = [
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['analista_asignado', 'estado']),
            models.Index(fields=['supervisor_revisor', 'estado']),
            models.Index(fields=['rut_empleado', 'cierre']),
        ]
    
    def __str__(self):
        return f"Variación salarial {self.rut_empleado} - {self.porcentaje_variacion}%"
    
    def puede_justificar(self, usuario):
        """Verifica si el usuario puede justificar la incidencia"""
        return (self.analista_asignado == usuario or 
                usuario.has_perm('nomina.change_incidenciavariacionsalarial')) and \
               self.estado in ['pendiente', 'rechazado']
    
    def puede_resolver(self, usuario):
        """Verifica si el usuario puede resolver la incidencia"""
        return usuario.has_perm('nomina.approve_incidenciavariacionsalarial') and \
               self.estado == 'en_analisis'
    
    def marcar_como_justificada(self, usuario, justificacion):
        """Marca la incidencia como justificada por el analista"""
        if self.puede_justificar(usuario):
            self.estado = 'en_analisis'
            self.justificacion_analista = justificacion
            self.fecha_justificacion = timezone.now()
            self.save()
            return True
        return False
    
    def aprobar(self, supervisor, comentario=""):
        """Aprueba la incidencia"""
        if self.puede_resolver(supervisor):
            self.estado = 'aprobado'
            self.supervisor_revisor = supervisor
            self.comentario_supervisor = comentario
            self.fecha_resolucion_supervisor = timezone.now()
            self.save()
            return True
        return False
    
    def rechazar(self, supervisor, comentario):
        """Rechaza la incidencia"""
        if self.puede_resolver(supervisor):
            self.estado = 'rechazado'
            self.supervisor_revisor = supervisor
            self.comentario_supervisor = comentario
            self.fecha_resolucion_supervisor = timezone.now()
            self.save()
            return True
        return False
