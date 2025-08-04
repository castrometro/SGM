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
        max_length=40,
        choices=[
            ('pendiente', 'Pendiente'),
            ('archivos_completos', 'Archivos Completos'),
            ('verificacion_datos', 'Verificación de Datos'),
            ('verificado_sin_discrepancias', 'Verificado Sin Discrepancias'),
            ('datos_consolidados', 'Datos Consolidados'),
            ('con_discrepancias', 'Con Discrepancias'),
            ('con_incidencias', 'Con Incidencias'),
            ('incidencias_resueltas', 'Incidencias Resueltas'),
            ('requiere_recarga_archivos', 'Requiere Recarga de Archivos'),
            ('validacion_final', 'Validación Final'),
            ('generando_informe', 'Generando Informe'),  # NUEVO ESTADO PARA TASKS
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
            # Aún no están todos los archivos procesados - mantener en pendiente
            if self.estado != 'pendiente':
                self.estado = 'pendiente'
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
    
    def finalizar_cierre(self, usuario, usar_tasks=None):
        """
        🎯 FINALIZA EL CIERRE Y GENERA EL INFORME COMPREHENSIVO
        
        Modo híbrido que soporta:
        - Sincrónico (original): Para cierres pequeños, respuesta inmediata
        - Asíncrono (nuevo): Para cierres grandes, con progress tracking
        
        Args:
            usuario: Usuario que finaliza el cierre
            usar_tasks: None (auto), True (forzar async), False (forzar sync)
        
        Returns:
            dict: Resultado con 'task_id' si es async o 'datos_cierre' si es sync
        """
        from django.utils import timezone
        from .models_informe import InformeNomina
        
        # Verificar que se puede finalizar
        puede, razon = self.puede_finalizar()
        if not puede:
            raise ValueError(f"No se puede finalizar el cierre: {razon}")
        
        # Decidir modo de ejecución
        if usar_tasks is None:
            # Auto-detectar basado en tamaño del cierre
            total_empleados = self.empleados.count()
            usar_tasks = total_empleados > 200  # Threshold configurable
        
        if usar_tasks:
            # =================== MODO ASÍNCRONO ===================
            return self._finalizar_con_task(usuario)
        else:
            # =================== MODO SINCRÓNICO (ORIGINAL) ===================
            return self._finalizar_sincronico(usuario)
    
    def _finalizar_con_task(self, usuario):
        """🚀 Finalización asíncrona usando Celery tasks"""
        from .tasks_informes import generar_informe_nomina_completo
        
        try:
            # Cambiar estado a generando_informe
            self.estado = 'generando_informe'
            self.save(update_fields=['estado'])
            
            # Disparar task de Celery
            task = generar_informe_nomina_completo.delay(
                cierre_id=self.id,
                usuario_id=usuario.id,
                modo='completo'
            )
            
            print(f"🚀 Task iniciado para {self.cliente.nombre} - {self.periodo}")
            print(f"📋 Task ID: {task.id}")
            
            return {
                'success': True,
                'modo': 'asincrono',
                'task_id': task.id,
                'mensaje': 'Proceso de finalización iniciado. Use el task_id para consultar progreso.',
                'cierre_id': self.id
            }
            
        except Exception as e:
            # Revertir estado si falla el task
            self.estado = 'incidencias_resueltas'
            self.save(update_fields=['estado'])
            raise Exception(f"Error iniciando task de finalización: {str(e)}")
    
    def _finalizar_sincronico(self, usuario):
        """⚡ Finalización sincrónica (método original)"""
        from django.utils import timezone
        from .models_informe import InformeNomina
        
        try:
            # Actualizar estado y metadatos
            self.estado = 'finalizado'
            self.fecha_finalizacion = timezone.now()
            self.usuario_finalizacion = usuario
            self.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
            
            # Generar informe comprehensivo
            print(f"🎯 Generando informe para cierre {self.cliente.nombre} - {self.periodo}")
            informe = InformeNomina.generar_informe_completo(self)
            
            # 🚀 ENVIAR AUTOMÁTICAMENTE A REDIS
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
            print(f"📊 Informe generado con {informe.get_kpi_principal('dotacion_calculada')} empleados")
            print(f"💰 Costo empresa total: ${informe.get_kpi_principal('costo_empresa_total'):,.0f}")
            
            return {
                'success': True,
                'modo': 'sincrono',
                'informe_id': informe.id,
                'mensaje': 'Cierre finalizado e informe generado exitosamente',
                'datos_cierre': informe.datos_cierre
            }
            
        except Exception as e:
            # Revertir estado si hay error
            self.estado = 'incidencias_resueltas'
            self.fecha_finalizacion = None
            self.usuario_finalizacion = None
            self.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
            
            raise Exception(f"Error al finalizar cierre: {str(e)}")
    
    def iniciar_finalizacion_asincrona(self, usuario):
        """
        🚀 Inicia finalización asíncrona (método público específico)
        Similar a contabilidad pero para nómina
        """
        return self._finalizar_con_task(usuario)
    
    @property
    def tiene_informe(self):
        """Verifica si el cierre tiene informe generado"""
        try:
            return hasattr(self, 'informe_nomina') and self.informe_nomina is not None
        except:
            return False
    
    def get_task_activo(self):
        """
        🔍 Busca si hay un task activo de finalización para este cierre
        Útil para evitar múltiples finalizaciones simultáneas
        """
        if self.estado != 'generando_informe':
            return None
        
        try:
            # Aquí podrías implementar lógica para buscar tasks activos en Celery
            # Por simplicidad, asumimos que si está en 'generando_informe' hay un task activo
            return {
                'estado': 'RUNNING',
                'descripcion': 'Generando informe de nómina...'
            }
        except:
            return None


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
    # Tipos base para comparación entre períodos consolidados
    VARIACION_CONCEPTO = 'variacion_concepto', 'Variación de Concepto (>30%)'
    CONCEPTO_NUEVO = 'concepto_nuevo', 'Concepto Nuevo'
    CONCEPTO_PERDIDO = 'concepto_perdido', 'Concepto Perdido'
    EMPLEADO_DEBERIA_INGRESAR = 'empleado_deberia_ingresar', 'Empleado que Debería Ingresar'
    EMPLEADO_NO_DEBERIA_ESTAR = 'empleado_no_deberia_estar', 'Empleado que No Debería Estar'
    AUSENTISMO_CONTINUO = 'ausentismo_continuo', 'Ausentismo Continuo'
    
    # NUEVOS TIPOS ESPECÍFICOS DEL SISTEMA DUAL
    # Comparación Individual (elemento a elemento)
    VARIACION_CONCEPTO_INDIVIDUAL = 'variacion_concepto_individual', 'Variación Individual en Concepto'
    CONCEPTO_NUEVO_EMPLEADO = 'concepto_nuevo_empleado', 'Concepto Nuevo para Empleado'
    CONCEPTO_ELIMINADO_EMPLEADO = 'concepto_eliminado_empleado', 'Concepto Eliminado de Empleado'
    EMPLEADO_NUEVO = 'empleado_nuevo', 'Empleado Nuevo sin Período Anterior'
    
    # Comparación Agregada (suma total)
    VARIACION_SUMA_TOTAL = 'variacion_suma_total', 'Variación en Suma Total de Concepto'
    CONCEPTO_NUEVO_PERIODO = 'concepto_nuevo_periodo', 'Concepto Nuevo en Período'
    CONCEPTO_ELIMINADO_PERIODO = 'concepto_eliminado_periodo', 'Concepto Eliminado del Período'
    
    # Validaciones de Reglas de Negocio
    REGLA_NEGOCIO_VIOLADA = 'regla_negocio_violada', 'Violación de Regla de Negocio'
    CALCULO_INCORRECTO = 'calculo_incorrecto', 'Error en Cálculo'

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
    """
    Incidencias detectadas en la comparación de archivos de un cierre
    VERSIÓN 2.0: Sistema Dual con soporte para comparación individual y suma total
    """
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='incidencias')
    tipo_incidencia = models.CharField(max_length=50, choices=TipoIncidencia.choices)
    
    # NUEVO: Tipo de comparación que generó la incidencia
    TIPO_COMPARACION_CHOICES = [
        ('individual', 'Comparación Individual (Elemento a Elemento)'),
        ('suma_total', 'Comparación Suma Total (Agregada)'),
        ('regla_negocio', 'Validación Regla de Negocio'),
        ('legacy', 'Sistema Legacy (Compatibilidad)'),
    ]
    tipo_comparacion = models.CharField(
        max_length=20, 
        choices=TIPO_COMPARACION_CHOICES, 
        default='legacy',
        help_text="Tipo de análisis que detectó esta incidencia"
    )
    
    # Empleado afectado (campos existentes para compatibilidad)
    empleado_libro = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    empleado_novedades = models.ForeignKey('EmpleadoCierreNovedades', on_delete=models.CASCADE, null=True, blank=True)
    rut_empleado = models.CharField(max_length=20, db_index=True)
    
    # NUEVO: Información del empleado para sistema consolidado
    empleado_nombre = models.CharField(max_length=200, null=True, blank=True, help_text="Nombre del empleado (desde consolidación)")
    
    # Detalles de la incidencia
    descripcion = models.TextField()
    valor_libro = models.CharField(max_length=500, null=True, blank=True)
    valor_novedades = models.CharField(max_length=500, null=True, blank=True)
    valor_movimientos = models.CharField(max_length=500, null=True, blank=True)
    valor_analista = models.CharField(max_length=500, null=True, blank=True)
    
    # Contexto adicional
    concepto_afectado = models.CharField(max_length=200, null=True, blank=True)
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    
    # NUEVO: Datos adicionales específicos del sistema dual
    datos_adicionales = models.JSONField(
        default=dict, 
        help_text="Datos específicos según tipo de incidencia y comparación"
    )
    
    # CAMPOS PARA RESOLUCIÓN COLABORATIVA
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
    
    # NUEVO: Resolución específica del sistema dual
    resuelto_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidencias_resueltas')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    comentario_resolucion = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'tipo_incidencia']),
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['rut_empleado', 'cierre']),
            models.Index(fields=['estado', 'prioridad']),
            models.Index(fields=['asignado_a', 'estado']),
            # NUEVOS ÍNDICES para sistema dual
            models.Index(fields=['cierre', 'tipo_comparacion']),
            models.Index(fields=['tipo_comparacion', 'estado']),
            models.Index(fields=['prioridad', 'fecha_detectada']),
        ]
        ordering = ['-fecha_detectada', '-impacto_monetario']
    
    def __str__(self):
        tipo_comp = f"[{self.get_tipo_comparacion_display()}]" if self.tipo_comparacion != 'legacy' else ""
        empleado_info = self.empleado_nombre or self.rut_empleado
        return f"{tipo_comp} {self.get_tipo_incidencia_display()} - {empleado_info}"

    def calcular_impacto_monetario(self):
        """
        Calcula el impacto monetario de la incidencia
        ACTUALIZADO: Soporte para sistema dual con datos_adicionales
        """
        try:
            # SISTEMA DUAL: Usar datos_adicionales si están disponibles
            if self.datos_adicionales and self.tipo_comparacion in ['individual', 'suma_total']:
                if 'variacion_absoluta' in self.datos_adicionales:
                    return abs(float(self.datos_adicionales['variacion_absoluta']))
                elif 'monto_actual' in self.datos_adicionales:
                    monto_actual = float(self.datos_adicionales['monto_actual'])
                    monto_anterior = float(self.datos_adicionales.get('monto_anterior', 0))
                    return abs(monto_actual - monto_anterior)
                elif 'suma_actual' in self.datos_adicionales:
                    suma_actual = float(self.datos_adicionales['suma_actual'])
                    suma_anterior = float(self.datos_adicionales.get('suma_anterior', 0))
                    return abs(suma_actual - suma_anterior)
            
            # SISTEMA LEGACY: Lógica original para compatibilidad
            if self.tipo_incidencia == TipoIncidencia.VARIACION_CONCEPTO:
                if self.valor_libro and self.valor_novedades:
                    # Limpiar y convertir valores
                    monto_actual = float(str(self.valor_libro).replace(',', '').replace('$', '').strip())
                    monto_anterior = float(str(self.valor_novedades).replace(',', '').replace('$', '').strip())
                    return abs(monto_actual - monto_anterior)
            elif self.tipo_incidencia in [TipoIncidencia.CONCEPTO_NUEVO, TipoIncidencia.CONCEPTO_PERDIDO]:
                if self.valor_libro:
                    monto = float(str(self.valor_libro).replace(',', '').replace('$', '').strip())
                    return abs(monto)
            elif self.tipo_incidencia in [TipoIncidencia.EMPLEADO_DEBERIA_INGRESAR, TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR]:
                # Para movimientos de personal, el impacto podría ser el líquido a pagar
                if self.valor_libro:
                    liquido = float(str(self.valor_libro).replace(',', '').replace('$', '').strip())
                    return abs(liquido)
        except (ValueError, TypeError, KeyError):
            pass
        return 0
    
    def get_contexto_comparacion(self):
        """
        Retorna información contextual específica del tipo de comparación
        """
        if self.tipo_comparacion == 'individual':
            return {
                'tipo': 'Análisis Individual',
                'descripcion': 'Comparación elemento a elemento por empleado',
                'alcance': 'Solo conceptos seleccionados',
                'precision': 'Alta granularidad'
            }
        elif self.tipo_comparacion == 'suma_total':
            return {
                'tipo': 'Análisis Agregado',
                'descripcion': 'Comparación de sumas totales por concepto',
                'alcance': 'Todos los conceptos',
                'precision': 'Tendencias generales'
            }
        elif self.tipo_comparacion == 'regla_negocio':
            return {
                'tipo': 'Validación de Reglas',
                'descripcion': 'Verificación de reglas de negocio',
                'alcance': 'Validaciones específicas',
                'precision': 'Cumplimiento normativo'
            }
        else:
            return {
                'tipo': 'Sistema Legacy',
                'descripcion': 'Detección tradicional',
                'alcance': 'Comparación general',
                'precision': 'Estándar'
            }
    
    def es_incidencia_critica(self):
        """Determina si la incidencia es crítica basada en múltiples factores"""
        return (
            self.prioridad == 'critica' or
            (self.impacto_monetario and self.impacto_monetario >= 10000000) or  # 10M+
            self.tipo_incidencia in [
                TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,
                TipoIncidencia.CONCEPTO_PERDIDO
            ]
        )
    
    def get_variacion_porcentual(self):
        """Obtiene la variación porcentual si está disponible"""
        if (self.datos_adicionales and 
            'variacion_porcentual' in self.datos_adicionales):
            return self.datos_adicionales['variacion_porcentual']
        return None

    def save(self, *args, **kwargs):
        # Calcular impacto monetario automáticamente
        if not self.impacto_monetario:
            self.impacto_monetario = self.calcular_impacto_monetario()
        super().save(*args, **kwargs)

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
    
    # Totales consolidados finales
    total_haberes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_descuentos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    liquido_pagar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
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
            models.Index(fields=['liquido_pagar']),
        ]
        ordering = ['nombre_empleado']
    
    def __str__(self):
        return f"{self.nombre_empleado} - {self.cierre.periodo} - ${self.liquido_pagar:,.0f}"


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
    """
    🔄 MOVIMIENTOS DE PERSONAL DETECTADOS
    
    Cambios de personal entre periodos (incorporaciones, finiquitos, ausencias).
    Responde: "¿Quién entró, salió o faltó este mes?"
    """
    nomina_consolidada = models.ForeignKey(NominaConsolidada, on_delete=models.CASCADE, related_name='movimientos')
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('ingreso', 'Nueva Incorporación'),
        ('finiquito', 'Finiquito'),
        ('ausentismo', 'Ausencia Periodo'),
        ('reincorporacion', 'Reincorporación después de Ausencia'),
        ('cambio_datos', 'Cambio de Datos Personales'),
    ]
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    
    # Detalles del movimiento
    motivo = models.CharField(max_length=300, null=True, blank=True)
    dias_ausencia = models.IntegerField(null=True, blank=True, help_text="Días de ausencia si aplica")
    fecha_movimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    
    # Metadatos
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    detectado_por_sistema = models.CharField(max_length=100, default='consolidacion_automatica')
    
    class Meta:
        verbose_name = "Movimiento de Personal"
        verbose_name_plural = "Movimientos de Personal"
        indexes = [
            models.Index(fields=['nomina_consolidada', 'tipo_movimiento']),
            models.Index(fields=['fecha_movimiento']),
        ]
        ordering = ['-fecha_deteccion']
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.nomina_consolidada.nombre_empleado}"

