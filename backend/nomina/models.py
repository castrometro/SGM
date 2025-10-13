from django.db import models
from api.models import Cliente
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from django.conf import settings
import unicodedata
import hashlib

# Importar modelos de logging - USANDO STUBS DE TRANSICIÓN
from .models_logging_stub import UploadLogNomina, TarjetaActivityLogNomina

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
        max_length=40,
        choices=[
            ('pendiente', 'Pendiente'),
            ('cargando_archivos', 'Cargando Archivos'),
            ('archivos_completos', 'Archivos Completos'),
            ('verificacion_datos', 'Verificación de Datos'),
            ('verificado_sin_discrepancias', 'Verificado Sin Discrepancias'),
            ('datos_consolidados', 'Datos Consolidados'),
            ('con_discrepancias', 'Con Discrepancias'),
            ('con_incidencias', 'Con Incidencias'),
            ('incidencias_resueltas', 'Incidencias Resueltas'),
            ('recarga_solicitud_pendiente', 'Recarga Solicitada (Pendiente de Aprobación)'),
            ('requiere_recarga_archivos', 'Requiere Recarga de Archivos'),
            ('validacion_final', 'Validación Final'),
            ('finalizado', 'Finalizado'),
        ],
        default='pendiente'
    )
    usuario_analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_analista')
    
    # CAMPOS PARA SEGUIMIENTO DE INCIDENCIAS
    estado_incidencias = models.CharField(
        max_length=30,
        choices=[
            ('pendiente', 'Pendiente'),
            ('detectadas', 'Detectadas'),
            ('en_revision', 'En Revisión'),
            ('resueltas', 'Resueltas'),
        ],
        default='pendiente'
    )
    total_incidencias = models.PositiveIntegerField(default=0, help_text="Total de incidencias detectadas")
    fecha_ultima_revision = models.DateTimeField(null=True, blank=True)
    revisiones_realizadas = models.PositiveIntegerField(default=0)
    supervisor_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_supervisor')

    # === CAMPOS PARA MANEJO DE RECARGA DE ARCHIVOS ===
    observaciones_recarga = models.TextField(null=True, blank=True, help_text="Motivo para solicitar recarga de archivos")
    fecha_solicitud_recarga = models.DateTimeField(null=True, blank=True, help_text="Fecha cuando se solicitó la recarga")
    fecha_aprobacion_recarga = models.DateTimeField(null=True, blank=True, help_text="Fecha cuando el supervisor aprobó la recarga")
    version_datos = models.PositiveIntegerField(default=1, help_text="Versión de los datos consolidados (incrementa con cada recarga)")

    # === CAMPOS PARA CONSOLIDACIÓN ===
    estado_consolidacion = models.CharField(
        max_length=30,
        choices=[
            ('pendiente', 'Pendiente de Consolidar'),
            ('consolidando', 'Consolidando Información'),
            ('consolidado', 'Información Consolidada'),
            ('error_consolidacion', 'Error en Consolidación'),
        ],
        default='pendiente'
    )
    fecha_consolidacion = models.DateTimeField(null=True, blank=True)
    puede_consolidar = models.BooleanField(default=False, help_text="¿Tiene 0 discrepancias y puede consolidarse?")

    # === CAMPOS PARA FINALIZACIÓN ===
    fecha_finalizacion = models.DateTimeField(null=True, blank=True, help_text="Fecha cuando se finalizó el cierre")
    usuario_finalizacion = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cierres_finalizados',
        help_text="Usuario que finalizó el cierre"
    )

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
        
        # Si ya está finalizado, no cambiar
        if self.estado == 'finalizado':
            return self.estado
            
        # Verificar el estado de todos los archivos necesarios
        archivos_listos = self._verificar_archivos_listos()
        
        if not archivos_listos['todos_listos']:
            # Aún no están todos los archivos procesados
            if self.estado == 'pendiente':
                self.estado = 'cargando_archivos'
                self.save(update_fields=['estado'])
            elif self.estado != 'cargando_archivos':
                # Mantener en cargando_archivos mientras se procesan
                self.estado = 'cargando_archivos'
                self.save(update_fields=['estado'])
            return self.estado
        
        # Todos los archivos están listos, cambiar a "archivos_completos"
        if self.estado != 'archivos_completos':
            self.estado = 'archivos_completos'
            self.estado_incidencias = 'pendiente'
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

    def puede_generar_incidencias(self):
        """
        Verifica si el cierre está listo para generar incidencias consolidadas
        """
        # Debe estar consolidado
        if self.estado_consolidacion != 'consolidado':
            return False
        
        # No debe tener incidencias ya generadas
        if self.estado_incidencias in ['incidencias_generadas', 'incidencias_resueltas']:
            return False
        
        return True
    
    def puede_finalizar(self):
        """
        Verifica si el cierre puede ser finalizado
        """
        # Debe estar en estado 'incidencias_resueltas' o 'validacion_final'
        if self.estado not in ['incidencias_resueltas', 'validacion_final']:
            return False, "El cierre debe estar con incidencias resueltas o en validación final"
        
        # Verificar que no haya incidencias pendientes críticas
        if hasattr(self, 'incidencias'):
            incidencias_criticas = self.incidencias.filter(
                prioridad='critica',
                estado__in=['pendiente', 'en_revision']
            ).count()
            
            if incidencias_criticas > 0:
                return False, f"Hay {incidencias_criticas} incidencias críticas pendientes"
        
        return True, "El cierre puede ser finalizado"
    
    def finalizar_cierre(self, usuario):
        """
        🎯 FINALIZA EL CIERRE Y GENERA EL INFORME COMPREHENSIVO
        
        Esta función:
        1. Verifica que se puede finalizar
        2. Cambia el estado a 'finalizado'
    3. (Opcional) Enviar el informe a Redis si ya existe
        4. Registra metadatos de finalización
        """
        from django.utils import timezone
        from .models_informe import InformeNomina
        
        # Verificar que se puede finalizar
        puede, razon = self.puede_finalizar()
        if not puede:
            raise ValueError(f"No se puede finalizar el cierre: {razon}")
        
        try:
            # Actualizar estado y metadatos
            self.estado = 'finalizado'
            self.fecha_finalizacion = timezone.now()
            self.usuario_finalizacion = usuario
            self.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
            
            # 🚀 ENVIAR A REDIS si existe informe relacionado
            informe = getattr(self, 'informe', None)
            if informe:
                print(f"🚀 Enviando informe a Redis...")
                try:
                    resultado_redis = informe.enviar_a_redis(ttl_hours=24)
                    if resultado_redis['success']:
                        print(f"✅ Informe enviado a Redis: {resultado_redis['clave_redis']}")
                        print(f"📏 Tamaño en Redis: {resultado_redis['size_kb']:.1f} KB")
                    else:
                        print(f"⚠️ Error enviando a Redis: {resultado_redis['error']}")
                except Exception as e:
                    print(f"⚠️ Error al enviar a Redis: {e}")

            print(f"✅ Cierre finalizado exitosamente")
            
            return {
                'success': True,
                'informe_id': getattr(informe, 'id', None),
                'mensaje': 'Cierre finalizado',
                'datos_cierre': getattr(informe, 'datos_cierre', {})
            }
            
        except Exception as e:
            # Revertir estado si hay error
            self.estado = 'incidencias_resueltas'
            self.fecha_finalizacion = None
            self.usuario_finalizacion = None
            self.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
            
            raise Exception(f"Error al finalizar cierre: {str(e)}")
    
    @property
    def tiene_informe(self):
        """Verifica si el cierre tiene informe generado"""
        return hasattr(self, 'informe') and self.informe is not None


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
        """Convierte el monto a número (peso) redondeado a entero con HALF_UP para comparaciones."""
        try:
            from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
            if self.monto is None or self.monto == "":
                return 0
            d = Decimal(str(self.monto))
            d0 = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return float(d0)
        except (InvalidOperation, ValueError, TypeError):
            try:
                val = float(self.monto)
                return float(int(val + 0.5)) if val >= 0 else float(int(val - 0.5))
            except Exception:
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
        ('procesando', 'Procesando'),
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
        """Convierte el monto a número para cálculos, redondeando a entero (peso) con HALF_UP.
        Esto alinea los montos de Novedades con los del Libro, evitando discrepancias por decimales.
        """
        try:
            from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
            if self.monto is None or self.monto == "":
                return 0
            d = Decimal(str(self.monto))
            d0 = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return float(d0)
        except (InvalidOperation, ValueError, TypeError):
            # Fallback: intentar como float y redondear con round estándar
            try:
                val = float(self.monto)
                return float(int(val + 0.5)) if val >= 0 else float(int(val - 0.5))
            except Exception:
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
    """Tipos de incidencia simplificados - solo totales por concepto"""
    # Únicamente variaciones de conceptos (agregados) - SISTEMA SIMPLIFICADO
    VARIACION_SUMA_TOTAL = 'variacion_suma_total', 'Variación en Suma Total de Concepto (≥30%)'
    CONCEPTO_NUEVO_PERIODO = 'concepto_nuevo_periodo', 'Concepto Nuevo en Período'
    CONCEPTO_ELIMINADO_PERIODO = 'concepto_eliminado_periodo', 'Concepto Eliminado del Período'

class EstadoIncidencia(models.TextChoices):
    """Estados de resolución simplificados manteniendo flujo colaborativo"""
    PENDIENTE = 'pendiente', 'Pendiente de Análisis'
    RESUELTA_ANALISTA = 'resuelta_analista', 'Justificada por Analista'
    APROBADA_SUPERVISOR = 'aprobada_supervisor', 'Aprobada por Supervisor'
    RECHAZADA_SUPERVISOR = 'rechazada_supervisor', 'Rechazada por Supervisor'

def resolucion_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"resoluciones/{instance.incidencia.cierre.cliente.id}/{instance.incidencia.cierre.periodo}/{now}_{filename}"

class IncidenciaCierre(models.Model):
    """
    🎯 INCIDENCIAS SIMPLIFICADAS - SOLO TOTALES POR CONCEPTO
    
    Sistema simplificado enfocado únicamente en variaciones de totales por concepto
    entre períodos, sin manejo de empleados individuales.
    Mantiene flujo colaborativo analista-supervisor.
    """
    # === RELACIÓN BÁSICA ===
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='incidencias')
    tipo_incidencia = models.CharField(max_length=50, choices=TipoIncidencia.choices)
    
    # === TIPO DE COMPARACIÓN SIMPLIFICADO ===
    TIPO_COMPARACION_CHOICES = [
        ('suma_total', 'Comparación Suma Total (Agregada)'),
        ('legacy', 'Sistema Legacy (Compatibilidad)'),
    ]
    tipo_comparacion = models.CharField(
        max_length=20, 
        choices=TIPO_COMPARACION_CHOICES, 
        default='suma_total',
        help_text="Tipo de análisis que detectó esta incidencia"
    )
    
    # === CONCEPTO AFECTADO (SIN EMPLEADOS) ===
    concepto_afectado = models.CharField(
        max_length=200, 
        db_index=True,
        help_text="Nombre del concepto que presenta la incidencia"
    )
    
    clasificacion_concepto = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="Clasificación del concepto (haberes_imponibles, descuentos_legales, etc.)"
    )
    
    # === DESCRIPCIÓN Y DETALLES ===
    descripcion = models.TextField(help_text="Descripción automática de la incidencia")
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    
    # === DATOS DE VARIACIÓN ===
    datos_adicionales = models.JSONField(
        default=dict, 
        help_text="Datos de variación: monto_actual, monto_anterior, delta_abs, delta_pct, etc."
    )
    
    # === RESOLUCIÓN COLABORATIVA (MANTENIDO) ===
    estado = models.CharField(max_length=40, choices=EstadoIncidencia.choices, default='pendiente')
    prioridad = models.CharField(max_length=10, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ], default='media')
    
    # Impacto monetario calculado
    impacto_monetario = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # === FLUJO COLABORATIVO ANALISTA-SUPERVISOR ===
    # Usuario asignado para resolución
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_asignadas')
    
    # Fechas de seguimiento
    fecha_primera_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_ultima_accion = models.DateTimeField(auto_now=True)
    
    # Resolución por analista
    resuelto_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_resueltas')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    comentario_resolucion = models.TextField(blank=True, help_text="Justificación del analista")
    
    # Resolución por supervisor
    supervisor_revisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_supervisadas')
    comentario_supervisor = models.TextField(blank=True, help_text="Comentario del supervisor (aprobación/rechazo)")
    fecha_resolucion_final = models.DateTimeField(null=True, blank=True)

    # === TRAZABILIDAD Y VERSIONES ===
    version_detectada_primera = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Primera versión de datos (cierre.version_datos) donde apareció la incidencia"
    )
    version_detectada_ultima = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Última versión de datos donde fue recalculada/detectada"
    )
    
    hash_deteccion = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Hash único para evitar duplicados en re-detecciones"
    )
    
    class Meta:
        constraints = [
            # Evitar duplicados por concepto en el mismo cierre
            models.UniqueConstraint(
                fields=['cierre', 'concepto_afectado', 'tipo_incidencia'],
                name='unique_incidencia_por_concepto_cierre'
            ),
        ]
        
        indexes = [
            models.Index(fields=['cierre', 'tipo_incidencia']),
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['concepto_afectado']),
            models.Index(fields=['estado', 'prioridad']),
            models.Index(fields=['asignado_a', 'estado']),
            models.Index(fields=['cierre', 'tipo_comparacion']),
            models.Index(fields=['prioridad', 'fecha_detectada']),
            models.Index(fields=['hash_deteccion']),
        ]
        ordering = ['-fecha_detectada', '-impacto_monetario']
    
    def __str__(self):
        delta_abs = self.get_delta_absoluto()
        signo = '+' if (delta_abs is not None and delta_abs >= 0) else ''
        delta_pct = self.get_delta_porcentual()
        if delta_pct is not None and delta_abs is not None:
            try:
                return f"{self.concepto_afectado}: {signo}{float(delta_pct):.1f}% (${float(delta_abs):,.0f})"
            except Exception:
                pass
        return f"{self.get_tipo_incidencia_display()} - {self.concepto_afectado}"

    def save(self, *args, **kwargs):
        """Auto-cálculo de campos derivados antes de guardar"""
        
        # Calcular impacto monetario automáticamente
        if not self.impacto_monetario:
            self.impacto_monetario = abs(self.get_delta_absoluto() or 0)
        
        # Calcular prioridad automáticamente si no está definida
        if not self.prioridad or self.prioridad == 'media':
            self.prioridad = self.calcular_prioridad_automatica()
        
        # Generar hash de detección para evitar duplicados
        if not self.hash_deteccion:
            self.hash_deteccion = self.generar_hash_deteccion()
        
        super().save(*args, **kwargs)

    def calcular_impacto_monetario(self):
        """
        Calcula el impacto monetario de la incidencia (valor absoluto del delta)
        """
        delta_abs = self.get_delta_absoluto()
        return abs(delta_abs) if delta_abs is not None else 0
    
    def get_delta_absoluto(self):
        """Obtiene el delta absoluto desde datos_adicionales"""
        if 'delta_abs' in self.datos_adicionales:
            return float(self.datos_adicionales['delta_abs'])
        elif 'monto_actual' in self.datos_adicionales and 'monto_anterior' in self.datos_adicionales:
            return float(self.datos_adicionales['monto_actual']) - float(self.datos_adicionales['monto_anterior'])
        return None
    
    def get_delta_porcentual(self):
        """Obtiene el delta porcentual desde datos_adicionales"""
        if 'delta_pct' in self.datos_adicionales:
            return float(self.datos_adicionales['delta_pct'])
        elif 'variacion_porcentual' in self.datos_adicionales:
            return float(self.datos_adicionales['variacion_porcentual'])
        return None
    
    def get_monto_actual(self):
        """Obtiene el monto actual desde datos_adicionales"""
        if 'monto_actual' in self.datos_adicionales:
            return float(self.datos_adicionales['monto_actual'])
        return None
    
    def get_monto_anterior(self):
        """Obtiene el monto anterior desde datos_adicionales"""
        if 'monto_anterior' in self.datos_adicionales:
            return float(self.datos_adicionales['monto_anterior'])
        return None

    def calcular_prioridad_automatica(self):
        """Calcula prioridad basada en impacto monetario y porcentaje"""
        delta_abs = abs(self.get_delta_absoluto() or 0)
        delta_pct = abs(self.get_delta_porcentual() or 0)
        
        # Criterios de prioridad
        if delta_abs >= 1000000 or delta_pct >= 100:  # $1M+ o 100%+
            return 'critica'
        elif delta_abs >= 500000 or delta_pct >= 75:   # $500K+ o 75%+
            return 'alta'
        elif delta_abs >= 100000 or delta_pct >= 50:   # $100K+ o 50%+
            return 'media'
        else:
            return 'baja'
    
    def generar_hash_deteccion(self):
        """Genera hash único para esta detección específica"""
        import hashlib
        
        contenido = f"{self.cierre.id}|{self.concepto_afectado}|{self.tipo_incidencia}|{self.get_monto_actual()}|{self.get_monto_anterior()}"
        return hashlib.sha256(contenido.encode()).hexdigest()[:32]
    
    # === MÉTODOS PARA FLUJO COLABORATIVO ===
    def puede_justificar(self, usuario):
        """Verifica si un usuario puede justificar esta incidencia"""
        return (
            self.estado == 'pendiente' and
            (not self.asignado_a or self.asignado_a == usuario) and
            hasattr(usuario, 'tipo_usuario') and usuario.tipo_usuario in ['analista', 'gerente']
        )
    
    def puede_aprobar_rechazar(self, usuario):
        """Verifica si un usuario puede aprobar/rechazar esta incidencia"""
        return (
            self.estado == 'resuelta_analista' and
            hasattr(usuario, 'tipo_usuario') and usuario.tipo_usuario in ['supervisor', 'gerente']
        )
    
    def justificar(self, usuario, justificacion):
        """Marca la incidencia como justificada por el analista"""
        from django.utils import timezone
        
        if not self.puede_justificar(usuario):
            raise ValueError("Usuario no puede justificar esta incidencia")
        
        self.estado = 'resuelta_analista'
        self.asignado_a = usuario
        self.resuelto_por = usuario
        self.comentario_resolucion = justificacion
        self.fecha_resolucion = timezone.now()
        self.save(update_fields=['estado', 'asignado_a', 'resuelto_por', 'comentario_resolucion', 'fecha_resolucion'])
    
    def aprobar(self, supervisor, comentario=""):
        """Aprueba la incidencia"""
        from django.utils import timezone
        
        if not self.puede_aprobar_rechazar(supervisor):
            raise ValueError("Usuario no puede aprobar esta incidencia")
        
        self.estado = 'aprobada_supervisor'
        self.supervisor_revisor = supervisor
        self.comentario_supervisor = comentario
        self.fecha_resolucion_final = timezone.now()
        self.save(update_fields=['estado', 'supervisor_revisor', 'comentario_supervisor', 'fecha_resolucion_final'])
    
    def rechazar(self, supervisor, comentario):
        """Rechaza la incidencia (vuelve a pendiente)"""
        from django.utils import timezone
        
        if not self.puede_aprobar_rechazar(supervisor):
            raise ValueError("Usuario no puede rechazar esta incidencia")
        
        self.estado = 'rechazada_supervisor'
        self.supervisor_revisor = supervisor
        self.comentario_supervisor = comentario
        self.fecha_resolucion_final = timezone.now()
        self.save(update_fields=['estado', 'supervisor_revisor', 'comentario_supervisor', 'fecha_resolucion_final'])
    
    # === PROPIEDADES DE COMPATIBILIDAD ===
    @property
    def es_variacion_positiva(self):
        """True si es un aumento, False si es disminución"""
        delta = self.get_delta_absoluto()
        return delta > 0 if delta is not None else False
    
    @property
    def es_incidencia_critica(self):
        """True si la incidencia es de prioridad crítica"""
        return self.prioridad == 'critica'


class ResolucionIncidencia(models.Model):
    """Historial de resoluciones de una incidencia (conversación simplificada)"""
    incidencia = models.ForeignKey(IncidenciaCierre, on_delete=models.CASCADE, related_name='resoluciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # ÚNICO CAMPO DE ESTADO - Más claro y directo
    tipo_resolucion = models.CharField(max_length=30, choices=[
        ('justificacion', 'Justificación del Analista'),
        ('consulta', 'Consulta del Supervisor'), 
        ('rechazo', 'Rechazo del Supervisor'),
        ('aprobacion', 'Aprobación del Supervisor'),
    ])
    
    # Contenido esencial
    comentario = models.TextField()
    adjunto = models.FileField(upload_to=resolucion_upload_to, null=True, blank=True)
    fecha_resolucion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_resolucion']
    
    def __str__(self):
        return f"{self.get_tipo_resolucion_display()} por {self.usuario.correo_bdo} - {self.incidencia}"
    
    def es_accion_supervisor(self):
        """Determina si esta resolución fue hecha por un supervisor"""
        return self.tipo_resolucion.endswith('_supervisor')
    
    def permite_siguiente_accion(self, usuario_rol):
        """
        Determina qué acciones puede hacer el usuario actual según el estado de la conversación
        """
        if usuario_rol == 'analista':
            # Los analistas pueden actuar si la última acción fue del supervisor o es el inicio
            ultima_resolucion = self.incidencia.resoluciones.order_by('-fecha_resolucion').first()
            if not ultima_resolucion:
                return ['justificacion_analista', 'correccion_analista', 'consulta_analista']
            elif ultima_resolucion.es_accion_supervisor():
                return ['justificacion_analista', 'correccion_analista', 'consulta_analista']
            else:
                return []  # Ya actuó, debe esperar respuesta del supervisor
        
        elif usuario_rol == 'supervisor':
            # Los supervisores pueden actuar si la última acción fue del analista
            ultima_resolucion = self.incidencia.resoluciones.order_by('-fecha_resolucion').first()
            if ultima_resolucion and ultima_resolucion.es_accion_analista():
                return ['aprobacion_supervisor', 'rechazo_supervisor', 'solicitud_cambio_supervisor']
            else:
                return []  # Debe esperar que el analista actúe primero
        
        return []


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


# ===== SISTEMA DE VERIFICACIÓN DE DATOS (DISCREPANCIAS) =====

class TipoDiscrepancia(models.TextChoices):
    """Tipos de discrepancias para verificación de datos simplificada"""
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

class DiscrepanciaCierre(models.Model):
    """
    Discrepancias detectadas en la verificación de datos de un cierre.
    Sistema puramente informativo - solo registra las diferencias encontradas.
    """
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='discrepancias')
    tipo_discrepancia = models.CharField(max_length=50, choices=TipoDiscrepancia.choices)
    
    # ✅ NUEVO: Relación con historial de verificaciones
    historial_verificacion = models.ForeignKey(
        'HistorialVerificacionCierre',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Verificación en la que se detectó esta discrepancia"
    )
    
    # Empleado afectado
    empleado_libro = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    empleado_novedades = models.ForeignKey('EmpleadoCierreNovedades', on_delete=models.CASCADE, null=True, blank=True)
    rut_empleado = models.CharField(max_length=20)
    
    # Detalles de la discrepancia
    descripcion = models.TextField()
    valor_libro = models.CharField(max_length=500, null=True, blank=True)
    valor_novedades = models.CharField(max_length=500, null=True, blank=True)
    valor_movimientos = models.CharField(max_length=500, null=True, blank=True)
    valor_analista = models.CharField(max_length=500, null=True, blank=True)
    
    # Contexto adicional
    concepto_afectado = models.CharField(max_length=200, null=True, blank=True)
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Discrepancia de Verificación"
        verbose_name_plural = "Discrepancias de Verificación"
        indexes = [
            models.Index(fields=['cierre', 'tipo_discrepancia']),
            models.Index(fields=['rut_empleado', 'cierre']),
            models.Index(fields=['fecha_detectada']),
        ]
        ordering = ['-fecha_detectada']
    
    def __str__(self):
        return f"Discrepancia: {self.get_tipo_discrepancia_display()} - {self.rut_empleado} - {self.cierre}"


class HistorialVerificacionCierre(models.Model):
    """
    🔍 HISTORIAL DE VERIFICACIONES DE DATOS
    
    Registra cada ejecución de "Verificar Datos" realizada por el analista,
    permitiendo auditar cuántas iteraciones fueron necesarias para llegar a 0 discrepancias.
    """
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='historial_verificaciones')
    
    # Información de la ejecución
    numero_intento = models.PositiveIntegerField(help_text="Número de intento de verificación (1, 2, 3...)")
    usuario_ejecutor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Usuario que ejecutó la verificación"
    )
    
    # Timestamps
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    tiempo_ejecucion = models.PositiveIntegerField(null=True, blank=True, help_text="Duración en segundos")
    
    # Resultados de la verificación
    total_discrepancias_encontradas = models.PositiveIntegerField(default=0)
    discrepancias_libro_vs_novedades = models.PositiveIntegerField(default=0)
    discrepancias_movimientos_vs_analista = models.PositiveIntegerField(default=0)
    
    # Estado y contexto
    ESTADO_CHOICES = [
        ('iniciado', 'Verificación Iniciada'),
        ('procesando', 'Procesando Verificación'),
        ('completado', 'Verificación Completada'),
        ('error', 'Error en Verificación'),
        ('cancelado', 'Verificación Cancelada'),
    ]
    estado_verificacion = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='iniciado')
    
    # Detalles de ejecución
    task_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID de la tarea Celery")
    observaciones = models.TextField(null=True, blank=True, help_text="Notas del analista sobre esta verificación")
    error_mensaje = models.TextField(null=True, blank=True, help_text="Mensaje de error si falló")
    
    # Metadatos para análisis
    archivos_analizados = models.JSONField(
        default=dict,
        help_text="Información sobre archivos analizados en esta verificación"
    )
    estadisticas_procesamiento = models.JSONField(
        default=dict,
        help_text="Estadísticas detalladas del procesamiento"
    )
    
    class Meta:
        verbose_name = "Historial de Verificación"
        verbose_name_plural = "Historiales de Verificación"
        unique_together = ('cierre', 'numero_intento')
        indexes = [
            models.Index(fields=['cierre', 'numero_intento']),
            models.Index(fields=['fecha_ejecucion']),
            models.Index(fields=['estado_verificacion']),
            models.Index(fields=['total_discrepancias_encontradas']),
        ]
        ordering = ['-numero_intento', '-fecha_ejecucion']
    
    def __str__(self):
        return f"Verificación #{self.numero_intento} - {self.cierre} - {self.total_discrepancias_encontradas} discrepancias"
    
    def marcar_completado(self):
        """Marca la verificación como completada y calcula duración"""
        from django.utils import timezone
        self.fecha_finalizacion = timezone.now()
        if self.fecha_ejecucion:
            duracion = self.fecha_finalizacion - self.fecha_ejecucion
            self.tiempo_ejecucion = int(duracion.total_seconds())
        self.estado_verificacion = 'completado'
        self.save(update_fields=['fecha_finalizacion', 'tiempo_ejecucion', 'estado_verificacion'])
    
    def marcar_error(self, mensaje_error):
        """Marca la verificación como fallida"""
        from django.utils import timezone
        self.fecha_finalizacion = timezone.now()
        if self.fecha_ejecucion:
            duracion = self.fecha_finalizacion - self.fecha_ejecucion
            self.tiempo_ejecucion = int(duracion.total_seconds())
        self.estado_verificacion = 'error'
        self.error_mensaje = mensaje_error
        self.save(update_fields=['fecha_finalizacion', 'tiempo_ejecucion', 'estado_verificacion', 'error_mensaje'])


class DiscrepanciaHistorial(models.Model):
    """
    � DISCREPANCIAS ESPECÍFICAS POR VERIFICACIÓN
    
    Almacena una copia de cada discrepancia detectada en una verificación específica,
    permitiendo ver la evolución entre intentos.
    """
    historial_verificacion = models.ForeignKey(
        HistorialVerificacionCierre, 
        on_delete=models.CASCADE, 
        related_name='discrepancias_detectadas'
    )
    
    # Información de la discrepancia
    tipo_discrepancia = models.CharField(max_length=50)
    rut_empleado = models.CharField(max_length=20, db_index=True)
    nombre_empleado = models.CharField(max_length=200)
    concepto = models.CharField(max_length=200, null=True, blank=True)
    
    # Valores comparados
    valor_esperado = models.CharField(max_length=500, null=True, blank=True)
    valor_encontrado = models.CharField(max_length=500, null=True, blank=True)
    diferencia = models.CharField(max_length=500, null=True, blank=True)
    
    # Detalles
    descripcion_detallada = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Metadatos
    orden_deteccion = models.PositiveIntegerField(help_text="Orden en que se detectó esta discrepancia")
    solucionada_en_siguiente = models.BooleanField(
        default=False, 
        help_text="¿Esta discrepancia fue solucionada en la siguiente verificación?"
    )
    
    class Meta:
        verbose_name = "Discrepancia en Historial"
        verbose_name_plural = "Discrepancias en Historial"
        indexes = [
            models.Index(fields=['historial_verificacion', 'orden_deteccion']),
            models.Index(fields=['rut_empleado']),
            models.Index(fields=['fecha_creacion']),
        ]
        ordering = ['-fecha_creacion', 'orden_deteccion']
    
    def __str__(self):
        return f"Verificación #{self.historial_verificacion.numero_intento} - {self.tipo_discrepancia} - {self.rut_empleado}"


# ==========================================
# MODELOS CONSOLIDADOS
# ==========================================

class NominaConsolidada(models.Model):
    """
    📋 NÓMINA CONSOLIDADA FINAL
    
    Un registro por empleado por cierre con toda su información consolidada.
    Responde: "Dame todos los empleados activos de este cierre con sus totales"
    """
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='nomina_consolidada')
    
    # Información del empleado
    rut_empleado = models.CharField(max_length=20, db_index=True)
    nombre_empleado = models.CharField(max_length=200)
    cargo = models.CharField(max_length=200, null=True, blank=True)
    centro_costo = models.CharField(max_length=200, null=True, blank=True)
    
    # Estado del empleado en este periodo
    ESTADO_CHOICES = [
        ('activo', 'Empleado Activo'),
        ('nueva_incorporacion', 'Nueva Incorporación'),
        ('finiquito', 'Finiquito'),
        ('ausente_total', 'Ausente Periodo Completo'),
        ('ausente_parcial', 'Ausente Parcial'),
    ]
    estado_empleado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    
    # Totales consolidados por categoría (nuevo esquema)
    haberes_imponibles = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    haberes_no_imponibles = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    dctos_legales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    otros_dctos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    horas_extras_cantidad = models.DecimalField(max_digits=10, decimal_places=4, default=0, help_text='Cantidad de horas extra')
    aportes_patronales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Días trabajados/ausencias
    dias_trabajados = models.IntegerField(null=True, blank=True)
    dias_ausencia = models.IntegerField(default=0)
    
    # Metadatos de consolidación
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    fuente_datos = models.JSONField(default=dict, help_text="Fuentes de datos usadas para consolidar")
    
    class Meta:
        verbose_name = "Nómina Consolidada"
        verbose_name_plural = "Nóminas Consolidadas"
        unique_together = ['cierre', 'rut_empleado']
        indexes = [
            models.Index(fields=['cierre', 'estado_empleado']),
            models.Index(fields=['rut_empleado']),
        ]
        ordering = ['nombre_empleado']
    
    def __str__(self):
        try:
            liquido = ((self.haberes_imponibles or 0) + (self.haberes_no_imponibles or 0)) - ((self.dctos_legales or 0) + (self.otros_dctos or 0) + (self.impuestos or 0))
            return f"{self.nombre_empleado} - {self.cierre.periodo} - ${liquido:,.0f}"
        except Exception:
            return f"{self.nombre_empleado} - {self.cierre.periodo}"


class HeaderValorEmpleado(models.Model):
    """
    📊 HEADER-VALOR POR EMPLEADO (CONSOLIDACIÓN BÁSICA)
    
    Mapeo directo 1:1 de cada celda del libro de remuneraciones.
    Un registro por cada intersección Empleado x Header del Excel.
    Base fundamental para reportes y análisis posteriores.
    """
    nomina_consolidada = models.ForeignKey(NominaConsolidada, on_delete=models.CASCADE, related_name='header_valores')
    
    # Header del libro
    nombre_header = models.CharField(max_length=200, db_index=True)
    
    # Clasificación del header (si existe)
    concepto_remuneracion = models.ForeignKey(
        ConceptoRemuneracion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Clasificación del header si está disponible"
    )
    
    # Valor original del Excel
    valor_original = models.CharField(max_length=500, help_text="Valor tal como viene del Excel")
    valor_numerico = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    es_numerico = models.BooleanField(default=False)
    
    # Metadatos de origen
    columna_excel = models.CharField(max_length=10, null=True, blank=True, help_text="Ej: 'D', 'AE'")
    fila_excel = models.IntegerField(null=True, blank=True)
    fuente_archivo = models.CharField(max_length=50, default='libro_remuneraciones')
    
    # Fechas
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Header-Valor por Empleado"
        verbose_name_plural = "Headers-Valores por Empleado"
        unique_together = ['nomina_consolidada', 'nombre_header']
        indexes = [
            models.Index(fields=['nomina_consolidada', 'nombre_header']),
            models.Index(fields=['nombre_header']),
            models.Index(fields=['valor_numerico']),
            models.Index(fields=['es_numerico']),
        ]
        ordering = ['nombre_header']
    
    def __str__(self):
        valor_display = f"${self.valor_numerico:,.2f}" if self.es_numerico and self.valor_numerico else self.valor_original
        return f"{self.nomina_consolidada.nombre_empleado} - {self.nombre_header}: {valor_display}"


class ConceptoConsolidado(models.Model):
    """
    💰 CONCEPTOS CONSOLIDADOS POR CIERRE
    
    Resumen de cada concepto con estadísticas consolidadas.
    Responde: "¿Cuántos empleados tienen este concepto y cuál es el total?"
    """
    nomina_consolidada = models.ForeignKey(NominaConsolidada, on_delete=models.CASCADE, related_name='conceptos')
    
    # Información del concepto
    codigo_concepto = models.CharField(max_length=20, db_index=True, null=True, blank=True)
    nombre_concepto = models.CharField(max_length=200)
    
    TIPO_CONCEPTO_CHOICES = [
        ('haber_imponible', 'Haber Imponible'),
        ('haber_no_imponible', 'Haber No Imponible'),
        ('descuento_legal', 'Descuento Legal'),
        ('otro_descuento', 'Otro Descuento'),
        ('aporte_patronal', 'Aporte Patronal'),
        ('impuesto', 'Impuesto'),
        ('informativo', 'Solo Informativo'),
    ]
    tipo_concepto = models.CharField(max_length=20, choices=TIPO_CONCEPTO_CHOICES, null=True, blank=True)
    
    # Valor del concepto para este empleado
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cantidad = models.DecimalField(max_digits=10, decimal_places=4, default=1, help_text="Cantidad/Horas si aplica")
    es_numerico = models.BooleanField(default=True, help_text="Si el concepto tiene valor numérico")
    
    # Fuente del dato
    fuente_archivo = models.CharField(max_length=50, default='consolidacion', help_text="libro/movimientos/novedades/analista")
    
    # Metadatos
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Concepto Consolidado"
        verbose_name_plural = "Conceptos Consolidados"
        unique_together = ['nomina_consolidada', 'nombre_concepto']
        indexes = [
            models.Index(fields=['nomina_consolidada', 'tipo_concepto']),
            models.Index(fields=['nombre_concepto']),
            models.Index(fields=['monto_total']),
        ]
        ordering = ['-monto_total', 'nombre_concepto']
    
    def __str__(self):
        return f"{self.nombre_concepto} - {self.nomina_consolidada.nombre_empleado} - ${self.monto_total:,.0f}"


class MovimientoPersonal(models.Model):
    """Modelo normalizado de movimientos de personal.

    Eliminada compatibilidad legacy: ya no existen campos tipo_movimiento/motivo/dias_ausencia/fecha_movimiento.
    Usar siempre: categoria + subtipo + fechas (inicio/fin) + días calculados.
    """
    nomina_consolidada = models.ForeignKey(NominaConsolidada, on_delete=models.CASCADE, related_name='movimientos')
    descripcion = models.CharField(max_length=300, null=True, blank=True, help_text="Descripción textual directa del origen / motivo humano")
    observaciones = models.TextField(null=True, blank=True)

    # Normalización nueva para ausencias / eventos
    categoria = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Clasificación general: ingreso | finiquito | ausencia | reincorporacion | cambio_datos"
    )
    subtipo = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="Subtipo de la ausencia o detalle del evento (vacaciones, licencia_medica, sin_justificar, etc.)"
    )
    fecha_inicio = models.DateField(null=True, blank=True, help_text="Inicio real del evento (ausencia, vacaciones, etc.)")
    fecha_fin = models.DateField(null=True, blank=True, help_text="Fin real del evento")
    dias_evento = models.IntegerField(null=True, blank=True, help_text="Duración total del evento (fin - inicio + 1)")
    dias_en_periodo = models.IntegerField(null=True, blank=True, help_text="Días del evento imputables al periodo del cierre")
    multi_mes = models.BooleanField(default=False, help_text="El evento cruza límites de mes")
    hash_evento = models.CharField(max_length=64, null=True, blank=True, db_index=True, help_text="Hash global del evento (rango completo)")
    hash_registro_periodo = models.CharField(max_length=80, null=True, blank=True, db_index=True, help_text="Hash del evento ligado al periodo (hash_evento + periodo)")
    detalle_fuente = models.JSONField(null=True, blank=True, help_text="Snapshot opcional de campos origen para auditoría")
    
    # Metadatos
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    detectado_por_sistema = models.CharField(max_length=100, default='consolidacion_automatica')
    
    class Meta:
        verbose_name = "Movimiento de Personal"
        verbose_name_plural = "Movimientos de Personal"
        indexes = [
            models.Index(fields=['nomina_consolidada', 'categoria']),
            models.Index(fields=['categoria', 'subtipo']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['hash_evento']),
        ]
        ordering = ['-fecha_deteccion']

    def __str__(self):
        base = self.categoria or 'mov'
        if self.subtipo:
            base += f"/{self.subtipo}"
        return f"{base} - {self.nomina_consolidada.nombre_empleado}"


# ============================================================================
# ACTIVITY LOGGING V2 - Sistema unificado de actividad
# ============================================================================

class ActivityEvent(models.Model):
    """
    Modelo unificado para registrar todas las actividades del sistema V2.
    Reemplaza TarjetaActivityLogNomina y UploadLogNomina.
    """
    
    # Identificación básica
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    
    # Contexto de la actividad
    event_type = models.CharField(max_length=50, db_index=True, help_text="Tipo de evento: upload, process, view, etc.")
    resource_type = models.CharField(max_length=50, db_index=True, help_text="Tipo de recurso: nomina, contabilidad, etc.")
    resource_id = models.CharField(max_length=100, blank=True, help_text="ID del recurso específico")
    
    # Detalles del evento
    action = models.CharField(max_length=100, help_text="Acción específica realizada")
    details = models.JSONField(default=dict, blank=True, help_text="Detalles adicionales del evento")
    
    # Metadatos de sesión
    session_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="ID de sesión para agrupar eventos relacionados")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'nomina_activity_event'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['cliente', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['session_id']),
        ]
        ordering = ['-timestamp']
        
    def __str__(self):
        user_display = getattr(self.user, 'username', None) or getattr(self.user, 'email', str(self.user))
        return f"{self.event_type}.{self.action} - {user_display} @ {self.timestamp.strftime('%H:%M:%S')}"
    
    @staticmethod
    def log(user, cliente, event_type, action, resource_type='general', resource_id='', details=None, session_id='', request=None):
        """
        Método estático para registrar eventos de actividad.
        
        Args:
            user: Usuario que realiza la acción
            cliente: Cliente relacionado
            event_type: Tipo de evento (upload, process, view, etc.)
            action: Acción específica
            resource_type: Tipo de recurso (nomina, contabilidad, etc.)
            resource_id: ID específico del recurso
            details: Diccionario con detalles adicionales
            session_id: ID de sesión para agrupar eventos
            request: Request HTTP para extraer IP y user agent
        
        Returns:
            ActivityEvent: El evento creado
        """
        if details is None:
            details = {}
            
        # Extraer información del request si está disponible
        ip_address = None
        user_agent = ''
        if request:
            # Obtener IP real considerando proxies
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar tamaño
        
        return ActivityEvent.objects.create(
            user=user,
            cliente=cliente,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def cleanup_old_events(cls, days=90):
        """
        Limpia eventos antiguos para mantener el rendimiento.
        
        Args:
            days: Días de antigüedad para eliminar (default: 90)
        
        Returns:
            int: Número de eventos eliminados
        """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        count, _ = cls.objects.filter(timestamp__lt=cutoff_date).delete()
        return count
    
    def get_related_events(self, time_window_minutes=5):
        """
        Obtiene eventos relacionados en una ventana de tiempo.
        
        Args:
            time_window_minutes: Ventana de tiempo en minutos
            
        Returns:
            QuerySet: Eventos relacionados
        """
        from datetime import timedelta
        start_time = self.timestamp - timedelta(minutes=time_window_minutes)
        end_time = self.timestamp + timedelta(minutes=time_window_minutes)
        
        return ActivityEvent.objects.filter(
            user=self.user,
            cliente=self.cliente,
            timestamp__range=(start_time, end_time)
        ).exclude(pk=self.pk)

