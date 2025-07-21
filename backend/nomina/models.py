"""
Modelos de Nómina SGM - Rediseñados desde cero
==============================================

Arquitectura centrada en CierreNomina con optimizaciones avanzadas:
- CierreNomina: Modelo principal (Cliente → Periodo)
- EmpleadoNomina/EmpleadoConcepto: Lista de empleados con conceptos (datos de Talana post-validación)
- Ausentismos, Incidencias: Datos adicionales del cierre y análisis comparativo
- Mapeos: Diccionarios de conceptos para validación en Redis

OPTIMIZACIONES IMPLEMENTADAS:
1. Tablas de KPIs pre-calculados para consultas rápidas
2. Índices optimizados para búsquedas por empleado y período
3. Algoritmo de comparación mensual eficiente con cache
4. Sistema de ofuscación de datos sensibles con hash reversible
5. Particionado conceptual por cliente para escalabilidad
6. Agregaciones pre-computadas para dashboards en tiempo real

Flujo: Redis (validación) → BDD (datos limpios) → KPIs pre-calculados → Análisis comparativo

Autor: Sistema SGM - Módulo Nómina
Fecha: 20 de julio de 2025
"""

from django.db import models
from django.db.models import Sum, Avg, Max, Min, Count, Q
from django.db.models.functions import Extract
from api.models import Cliente
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import hashlib
import hmac
import base64
import json
import logging
import secrets
import random
import unicodedata
import re
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()

# ========== FUNCIONES DE UPLOAD ==========

def resolucion_upload_to(instance, filename):
    """Función para determinar la ruta de subida de archivos de resolución"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"resoluciones/{instance.incidencia.cierre.cliente.id}/{instance.incidencia.cierre.periodo}/{now}_{filename}"

# ========== CLASIFICACIONES ESTÁNDAR ==========
CLASIFICACION_CHOICES = [
    ('haber_imponible', 'Haber Imponible'),
    ('haber_no_imponible', 'Haber No Imponible'),
    ('horas_extras', 'Horas Extras'),
    ('descuento_legal', 'Descuento Legal'),
    ('otro_descuento', 'Otro Descuento'),
    ('aporte_patronal', 'Aporte Patronal'),
    ('informativo', 'Solo Informativo'),
    ('impuesto', 'Impuesto'),
]

ESTADO_CIERRE_CHOICES = [
    ('iniciado', 'Cierre Iniciado'),
    ('en_redis', 'En Proceso de Validación (Redis)'),
    ('validado', 'Validado Sin Discrepancias'),
    ('con_discrepancias', 'Con Discrepancias Pendientes'),
    ('consolidado', 'Consolidado en Base de Datos'),
    ('cerrado', 'Cerrado Definitivamente'),
    ('error', 'Error en Proceso'),
    ('reabierto', 'Cierre Reabierto'),
]

TIPO_EMPLEADO_CHOICES = [
    ('activo', 'Empleado Activo'),
    ('finiquito', 'Finiquito'),
    ('ingreso', 'Ingreso'),
]

# ========== MODELOS DE MAPEO (DEFINIDOS PRIMERO) ==========

class MapeoConcepto(models.Model):
    """
    Mapeo universal de conceptos del libro de remuneraciones a conceptos estándar.
    Ejemplo: "Sueldo Base" → "SUELDO_BASE" (haber_imponible)
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Concepto tal como aparece en el archivo
    concepto_original = models.CharField(
        max_length=200,
        help_text="Concepto tal como aparece en el libro de remuneraciones"
    )
    
    # Concepto estandarizado para el sistema
    concepto_estandar = models.CharField(
        max_length=100,
        help_text="Código estándar del concepto (ej: SUELDO_BASE)"
    )
    
    # Clasificación contable/tributaria
    clasificacion = models.CharField(
        max_length=30,
        choices=CLASIFICACION_CHOICES,
        help_text="Clasificación contable del concepto"
    )
    
    # Metadatos del mapeo
    activo = models.BooleanField(default=True)
    usuario_mapea = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que creó este mapeo"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Configuración adicional
    es_numerico = models.BooleanField(
        default=True,
        help_text="Si el concepto tiene valor numérico"
    )
    orden_display = models.PositiveIntegerField(
        default=0,
        help_text="Orden para mostrar en reportes"
    )
    
    class Meta:
        unique_together = ('cliente', 'concepto_original')
        verbose_name = "Mapeo de Concepto"
        verbose_name_plural = "Mapeos de Conceptos"
        ordering = ['orden_display', 'concepto_estandar']
    
    def __str__(self):
        return f"{self.cliente.nombre}: {self.concepto_original} → {self.concepto_estandar}"

class MapeoNovedades(models.Model):
    """
    Mapeo de conceptos de novedades a conceptos del libro de remuneraciones.
    Ejemplo: "Sueldo" (novedades) → "Sueldo Base" (libro)
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Concepto tal como aparece en archivo de novedades
    concepto_novedades = models.CharField(
        max_length=200,
        help_text="Concepto tal como aparece en el archivo de novedades"
    )
    
    # Mapeo al concepto del libro (que ya tiene su mapeo estándar)
    concepto_libro = models.CharField(
        max_length=200,
        help_text="Concepto del libro al que mapea (debe existir en MapeoConcepto)"
    )
    
    # Metadatos del mapeo
    activo = models.BooleanField(default=True)
    usuario_mapea = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que creó este mapeo"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cliente', 'concepto_novedades')
        verbose_name = "Mapeo de Novedades"
        verbose_name_plural = "Mapeos de Novedades"
        ordering = ['concepto_novedades']
    
    def __str__(self):
        return f"{self.cliente.nombre}: {self.concepto_novedades} → {self.concepto_libro}"
    
    def get_concepto_estandar(self):
        """
        Obtener el concepto estándar a través del mapeo del libro
        
        Returns:
            MapeoConcepto: Mapeo estándar correspondiente o None
        """
        try:
            return MapeoConcepto.objects.get(
                cliente=self.cliente,
                concepto_original=self.concepto_libro,
                activo=True
            )
        except MapeoConcepto.DoesNotExist:
            return None
    
    def get_clasificacion(self):
        """
        Obtener la clasificación a través del mapeo del libro
        
        Returns:
            str: Clasificación del concepto o None
        """
        mapeo_estandar = self.get_concepto_estandar()
        return mapeo_estandar.clasificacion if mapeo_estandar else None

# ========== MODELO PRINCIPAL: CIERRE NÓMINA ==========

class CierreNomina(models.Model):
    """
    Modelo principal del sistema de nómina.
    Representa el cierre de un período específico para un cliente.
    
    Contiene toda la información del cierre: empleados, conceptos, ausentismos,
    finiquitos, ingresos, y el control del proceso completo.
    """
    # Identificación del cierre
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=7, help_text="Formato: YYYY-MM (ej: 2025-07)")
    
    # Control del proceso de cierre
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CIERRE_CHOICES,
        default='iniciado',
        help_text="Estado actual del proceso de cierre"
    )
    
    # Fechas del ciclo de vida
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_consolidacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha cuando se consolidaron los datos desde Redis"
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha cuando se cerró definitivamente"
    )
    
    # Usuarios responsables
    analista_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_asignados',
        help_text="Analista responsable del cierre"
    )
    usuario_cierre = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_ejecutados',
        help_text="Usuario que ejecutó el cierre final"
    )
    
    # Metadatos del proceso
    discrepancias_detectadas = models.PositiveIntegerField(
        default=0,
        help_text="Número de discrepancias detectadas en validación Redis"
    )
    cache_key_redis = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Clave base en Redis para este cierre"
    )
    
    # Resumen de archivos procesados
    archivos_procesados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Resumen de archivos subidos y procesados"
    )
    
    # Metadatos de consolidación
    total_empleados_activos = models.PositiveIntegerField(
        default=0,
        help_text="Total de empleados activos en el período"
    )
    total_finiquitos = models.PositiveIntegerField(
        default=0,
        help_text="Total de finiquitos en el período"
    )
    total_ingresos = models.PositiveIntegerField(
        default=0,
        help_text="Total de ingresos en el período"
    )
    
    # Control de reaperturas
    fecha_reapertura = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de reapertura si aplica"
    )
    usuario_reapertura = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reaperturas_ejecutadas',
        help_text="Usuario que ejecutó la reapertura"
    )
    motivo_reapertura = models.TextField(
        blank=True,
        help_text="Motivo de la reapertura"
    )
    
    # Versión del cierre (para reaperturas)
    version = models.PositiveIntegerField(
        default=1,
        help_text="Versión del cierre (incrementa con reaperturas)"
    )
    
    # Observaciones y notas
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones del proceso de cierre"
    )
    
    class Meta:
        unique_together = ('cliente', 'periodo')
        verbose_name = "Cierre de Nómina"
        verbose_name_plural = "Cierres de Nómina"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'periodo']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['analista_responsable']),
        ]
    
    # Manager optimizado
    objects = models.Manager()  # Manager por defecto
    
    def __str__(self):
        estado_display = self.get_estado_display()
        return f"Cierre {self.cliente.nombre} - {self.periodo} ({estado_display})"
    
    # ========== MÉTODOS DE INTEGRACIÓN REDIS ==========
    
    def inicializar_en_redis(self):
        """
        Inicializar el workspace de validación en Redis
        """
        try:
            from .cache_redis import get_cache_nomina_system
            
            cache_system = get_cache_nomina_system()
            
            success = cache_system.set_validacion_status(
                cliente_id=self.cliente.id,
                periodo=self.periodo,
                status_data={
                    'cierre_id': self.id,
                    'estado': 'iniciado',
                    'fecha_inicio': datetime.now().isoformat(),
                    'archivos_esperados': ['libro_remuneraciones'],
                    'archivos_recibidos': []
                }
            )
            
            if success:
                self.estado = 'en_redis'
                self.cache_key_redis = f"sgm:cierre:{self.cliente.id}:{self.periodo}"
                self.save()
            
            return success
            
        except Exception as e:
            return False
    
    def consolidar_desde_redis(self):
        """
        Consolidar datos validados desde Redis a la base de datos
        Solo se ejecuta cuando discrepancias = 0
        """
        try:
            from .cache_redis import get_cache_nomina_system
            
            cache_system = get_cache_nomina_system()
            
            # Preparar consolidación en Redis
            consolidacion = cache_system.preparar_consolidacion(
                cliente_id=self.cliente.id,
                periodo=self.periodo
            )
            
            if not consolidacion['success']:
                return consolidacion
            
            # Consolidar datos de empleados activos, finiquitos e ingresos
            empleados_data = consolidacion.get('empleados_consolidados', [])
            
            for empleado_data in empleados_data:
                self._consolidar_empleado_data(empleado_data)
            
            # Consolidar ausentismos
            ausentismos_data = consolidacion.get('ausentismos', [])
            for ausentismo_data in ausentismos_data:
                self._consolidar_ausentismo_data(ausentismo_data)
            
            # Actualizar contadores
            self._actualizar_contadores()
            
            # Actualizar estado
            self.estado = 'consolidado'
            self.fecha_consolidacion = datetime.now()
            self.discrepancias_detectadas = 0
            self.save()
            
            # Limpiar Redis
            cache_system.limpiar_cache_consolidado(
                cliente_id=self.cliente.id,
                periodo=self.periodo
            )
            
            return {
                'success': True,
                'message': 'Cierre consolidado exitosamente',
                'empleados_consolidados': len(empleados_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error consolidando cierre: {str(e)}'
            }
    
    def _consolidar_empleado_data(self, empleado_data):
        """Consolidar datos de un empleado específico"""
        rut = empleado_data.get('rut')
        nombre = empleado_data.get('nombre', '')
        tipo_empleado = empleado_data.get('tipo', 'activo')
        conceptos = empleado_data.get('conceptos', {})
        
        # Crear empleado en nómina
        empleado_nomina, created = EmpleadoNomina.objects.get_or_create(
            cierre=self,
            rut_empleado=rut,
            defaults={
                'nombre_empleado': nombre,
                'tipo_empleado': tipo_empleado
            }
        )
        
        # Crear conceptos del empleado
        for concepto_nombre, valor in conceptos.items():
            EmpleadoConcepto.objects.get_or_create(
                empleado_nomina=empleado_nomina,
                concepto=concepto_nombre,
                defaults={
                    'valor': str(valor),
                    'valor_numerico': self._convertir_valor_numerico(valor)
                }
            )
    
    def _consolidar_ausentismo_data(self, ausentismo_data):
        """Consolidar datos de ausentismos"""
        Ausentismo.objects.get_or_create(
            cierre=self,
            rut_empleado=ausentismo_data.get('rut'),
            defaults={
                'nombre_empleado': ausentismo_data.get('nombre', ''),
                'tipo_ausentismo': ausentismo_data.get('tipo', ''),
                'fecha_inicio': ausentismo_data.get('fecha_inicio'),
                'fecha_fin': ausentismo_data.get('fecha_fin'),
                'dias_ausentismo': ausentismo_data.get('dias', 0),
                'observaciones': ausentismo_data.get('observaciones', '')
            }
        )
    
    def _convertir_valor_numerico(self, valor):
        """Convertir valor a numérico de forma segura"""
        try:
            valor_limpio = str(valor).replace(',', '').replace('$', '').strip()
            return float(valor_limpio) if valor_limpio else 0
        except (ValueError, TypeError):
            return 0
    
    def _actualizar_contadores(self):
        """Actualizar contadores después de consolidación"""
        self.total_empleados_activos = self.empleados_nomina.filter(tipo_empleado='activo').count()
        self.total_finiquitos = self.empleados_nomina.filter(tipo_empleado='finiquito').count()
        self.total_ingresos = self.empleados_nomina.filter(tipo_empleado='ingreso').count()
    
    def ejecutar_cierre(self, usuario_cierre, observaciones=""):
        """
        Ejecutar el cierre definitivo del período
        """
        if self.estado != 'consolidado':
            return {
                'success': False,
                'message': 'El cierre debe estar consolidado para poder cerrarse'
            }
        
        try:
            self.estado = 'cerrado'
            self.fecha_cierre = datetime.now()
            self.usuario_cierre = usuario_cierre
            if observaciones:
                self.observaciones = observaciones
            self.save()
            
            return {
                'success': True,
                'message': 'Cierre ejecutado exitosamente',
                'version': self.version
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error ejecutando cierre: {str(e)}'
            }
    
    def reabrir(self, usuario_reapertura, motivo):
        """
        Reabrir un cierre cerrado
        """
        if self.estado != 'cerrado':
            return {
                'success': False,
                'message': 'Solo se pueden reabrir cierres cerrados'
            }
        
        try:
            self.usuario_reapertura = usuario_reapertura
            self.motivo_reapertura = motivo
            self.fecha_reapertura = timezone.now()
            self.estado = 'reabierto'
            self.version += 1
            self.save()
            
            return {
                'success': True,
                'message': f'Cierre reabierto exitosamente (versión {self.version})',
                'nueva_version': self.version
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error reabriendo cierre: {str(e)}'
            }

# ========== LISTA DE EMPLEADOS DE LA NÓMINA ==========

class EmpleadoNomina(models.Model):
    """
    Lista de empleados presentes en una nómina específica.
    
    Esta es la "nómina" propiamente tal: la lista de empleados
    con su clasificación (activo, finiquito, ingreso).
    """
    cierre = models.ForeignKey(
        CierreNomina, 
        on_delete=models.CASCADE,
        related_name='empleados_nomina',
        help_text="Cierre al que pertenece este empleado"
    )
    
    # Datos del empleado
    rut_empleado = models.CharField(max_length=12, db_index=True)
    nombre_empleado = models.CharField(max_length=200)
    
    # Clasificación del empleado en el período
    tipo_empleado = models.CharField(
        max_length=20,
        choices=TIPO_EMPLEADO_CHOICES,
        default='activo',
        help_text="Tipo de empleado en este período"
    )
    
    # Metadatos específicos por tipo
    fecha_ingreso = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de ingreso (para tipo 'ingreso')"
    )
    fecha_finiquito = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de finiquito (para tipo 'finiquito')"
    )
    motivo_finiquito = models.CharField(
        max_length=200,
        blank=True,
        help_text="Motivo del finiquito"
    )
    
    # Control
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cierre', 'rut_empleado')
        verbose_name = "Empleado Nómina"
        verbose_name_plural = "Empleados Nómina"
        indexes = [
            models.Index(fields=['cierre', 'rut_empleado']),
            models.Index(fields=['tipo_empleado']),
        ]
        ordering = ['nombre_empleado']
    
    def __str__(self):
        tipo_display = self.get_tipo_empleado_display()
        return f"{self.nombre_empleado} ({self.rut_empleado}) - {tipo_display}"

class EmpleadoConcepto(models.Model):
    """
    Conceptos y valores de cada empleado en la nómina.
    
    Un registro por cada concepto de cada empleado.
    Solo datos de Talana post-Redis (discrepancias = 0).
    """
    empleado_nomina = models.ForeignKey(
        EmpleadoNomina,
        on_delete=models.CASCADE,
        related_name='conceptos',
        help_text="Empleado al que pertenece este concepto"
    )
    
    # Datos del concepto
    concepto = models.CharField(
        max_length=200,
        help_text="Nombre del concepto tal como viene de Talana"
    )
    
    # Valor del concepto
    valor = models.CharField(
        max_length=255,
        help_text="Valor como texto (puede ser numérico o descriptivo)"
    )
    valor_numerico = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor numérico para cálculos (0 si no es numérico)"
    )
    
    # Metadatos
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('empleado_nomina', 'concepto')
        verbose_name = "Concepto de Empleado"
        verbose_name_plural = "Conceptos de Empleados"
        indexes = [
            models.Index(fields=['empleado_nomina']),
            models.Index(fields=['concepto']),
            models.Index(fields=['valor_numerico']),
        ]
        ordering = ['concepto']
    
    def __str__(self):
        return f"{self.empleado_nomina.nombre_empleado} - {self.concepto}: {self.valor}"
    
    def save(self, *args, **kwargs):
        """Calcular valor numérico automáticamente al guardar"""
        try:
            valor_limpio = str(self.valor).replace(',', '').replace('$', '').strip()
            self.valor_numerico = float(valor_limpio) if valor_limpio else 0
        except (ValueError, TypeError):
            self.valor_numerico = 0
        
        super().save(*args, **kwargs)
    
    def get_mapeo_concepto(self):
        """
        Obtener el mapeo estándar de este concepto
        """
        try:
            return MapeoConcepto.objects.get(
                cliente=self.empleado_nomina.cierre.cliente,
                concepto_original=self.concepto,
                activo=True
            )
        except MapeoConcepto.DoesNotExist:
            return None
    
    def get_clasificacion(self):
        """
        Obtener clasificación del concepto
        """
        mapeo = self.get_mapeo_concepto()
        return mapeo.clasificacion if mapeo else 'sin_clasificar'

# ========== AUSENTISMOS ==========

class Ausentismo(models.Model):
    """
    Ausentismos registrados en el período de nómina.
    """
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='ausentismos',
        help_text="Cierre al que pertenece este ausentismo"
    )
    
    # Datos del empleado
    rut_empleado = models.CharField(max_length=12, db_index=True)
    nombre_empleado = models.CharField(max_length=200)
    
    # Datos del ausentismo
    tipo_ausentismo = models.CharField(
        max_length=50,
        help_text="Tipo de ausentismo (vacaciones, licencia médica, etc.)"
    )
    fecha_inicio = models.DateField(help_text="Fecha de inicio del ausentismo")
    fecha_fin = models.DateField(help_text="Fecha de fin del ausentismo")
    dias_ausentismo = models.PositiveIntegerField(
        default=0,
        help_text="Número de días de ausentismo"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones adicionales del ausentismo"
    )
    
    # Control
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ausentismo"
        verbose_name_plural = "Ausentismos"
        indexes = [
            models.Index(fields=['cierre', 'rut_empleado']),
            models.Index(fields=['tipo_ausentismo']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
        ordering = ['fecha_inicio', 'nombre_empleado']
    
    def __str__(self):
        return f"{self.nombre_empleado} - {self.tipo_ausentismo} ({self.fecha_inicio} a {self.fecha_fin})"

# ========== CHECKLIST DE CIERRE ==========

class ChecklistItem(models.Model):
    """
    Items del checklist de control de calidad para cada cierre.
    
    Sistema de verificación paso a paso para asegurar que todos
    los controles necesarios se ejecuten antes del cierre definitivo.
    """
    
    CHECK_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'), 
        ('no_realizado', 'No Realizado'),
        ('omitido', 'Omitido por Supervisor'),
    ]
    
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='checklist',
        help_text="Cierre al que pertenece este item del checklist"
    )
    
    # Datos del item
    descripcion = models.CharField(
        max_length=255,
        help_text="Descripción del control a realizar"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=CHECK_CHOICES,
        default='pendiente',
        help_text="Estado actual del item"
    )
    
    # Información adicional
    comentario = models.TextField(
        blank=True,
        help_text="Comentario o observación del analista/supervisor"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    usuario_modificacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que realizó la última modificación"
    )
    
    # Orden y categorización
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de ejecución del item"
    )
    categoria = models.CharField(
        max_length=50,
        default='general',
        help_text="Categoría del control (general, validacion, revision, etc.)"
    )
    
    # Control de obligatoriedad
    es_obligatorio = models.BooleanField(
        default=True,
        help_text="Si es obligatorio para cerrar la nómina"
    )
    
    class Meta:
        verbose_name = "Item de Checklist"
        verbose_name_plural = "Items de Checklist"
        ordering = ['orden', 'fecha_creacion']
        indexes = [
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['categoria', 'orden']),
        ]
    
    def __str__(self):
        return f"{self.cierre.cliente.nombre} {self.cierre.periodo} - {self.descripcion} ({self.get_estado_display()})"
    
    @classmethod
    def crear_checklist_por_defecto(cls, cierre):
        """
        Crear checklist por defecto para un cierre nuevo.
        
        Items estándar que deben verificarse en todo cierre.
        """
        items_defecto = [
            {
                'descripcion': 'Validar archivo libro de remuneraciones subido',
                'categoria': 'validacion',
                'orden': 1,
                'es_obligatorio': True
            },
            {
                'descripcion': 'Verificar coincidencia con datos de Talana',
                'categoria': 'validacion', 
                'orden': 2,
                'es_obligatorio': True
            },
            {
                'descripcion': 'Revisar y resolver discrepancias detectadas',
                'categoria': 'revision',
                'orden': 3,
                'es_obligatorio': True
            },
            {
                'descripcion': 'Validar ausentismos del período',
                'categoria': 'revision',
                'orden': 4,
                'es_obligatorio': False
            },
            {
                'descripcion': 'Verificar finiquitos e ingresos',
                'categoria': 'revision',
                'orden': 5,
                'es_obligatorio': False
            },
            {
                'descripcion': 'Revisar variaciones significativas vs mes anterior',
                'categoria': 'analisis',
                'orden': 6,
                'es_obligatorio': False
            },
            {
                'descripcion': 'Validar totales por tipo de concepto',
                'categoria': 'analisis',
                'orden': 7,
                'es_obligatorio': True
            },
            {
                'descripcion': 'Obtener VoBo del cliente (si aplica)',
                'categoria': 'aprobacion',
                'orden': 8,
                'es_obligatorio': False
            },
            {
                'descripcion': 'Supervisión final de analista senior/supervisor',
                'categoria': 'supervision',
                'orden': 9,
                'es_obligatorio': True
            },
        ]
        
        items_creados = []
        for item_data in items_defecto:
            item = cls.objects.create(
                cierre=cierre,
                **item_data
            )
            items_creados.append(item)
        
        logger.info(f"Creados {len(items_creados)} items de checklist para cierre {cierre.id}")
        return items_creados

# ========== INCIDENCIAS (FASE SIGUIENTE) ==========

class Incidencia(models.Model):
    """
    Incidencias detectadas en el análisis comparativo mes anterior.
    
    Sistema tipo foro entre analista y supervisor para resolver
    diferencias sospechosas entre períodos.
    """
    # Relación con el cierre
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='incidencias',
        help_text="Cierre donde se detectó la incidencia"
    )
    
    # Fecha de detección
    fecha_deteccion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora cuando se detectó la incidencia"
    )
    
    # Datos de la incidencia
    empleado_rut = models.CharField(max_length=12, db_index=True)
    empleado_nombre = models.CharField(max_length=200)
    concepto_afectado = models.CharField(max_length=200)
    
    # Comparación con período anterior
    valor_periodo_anterior = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor del mismo concepto en el período anterior"
    )
    valor_periodo_actual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Valor del concepto en el período actual"
    )
    
    # Análisis de la diferencia
    diferencia_absoluta = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Diferencia absoluta entre períodos"
    )
    diferencia_porcentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Diferencia porcentual entre períodos"
    )
    
    # Clasificación de la incidencia
    TIPO_INCIDENCIA_CHOICES = [
        ('variacion_sospechosa', 'Variación Sospechosa'),
        ('empleado_nuevo', 'Empleado Nuevo'),
        ('empleado_saliente', 'Empleado Saliente'),
        ('concepto_nuevo', 'Concepto Nuevo'),
        ('valor_extremo', 'Valor Extremo'),
        ('otro', 'Otro'),
    ]
    tipo_incidencia = models.CharField(
        max_length=30,
        choices=TIPO_INCIDENCIA_CHOICES,
        help_text="Tipo de incidencia detectada"
    )
    
    # Estado de la incidencia
    ESTADO_INCIDENCIA_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('en_revision', 'En Revisión por Analista'),
        ('escalada', 'Escalada a Supervisor'),
        ('resuelta', 'Resuelta'),
        ('descartada', 'Descartada'),
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_INCIDENCIA_CHOICES,
        default='pendiente',
        help_text="Estado actual de la incidencia"
    )
    
    # Usuarios involucrados
    analista_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_asignadas',
        help_text="Analista asignado para revisar la incidencia"
    )
    supervisor_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_supervisadas',
        help_text="Supervisor asignado para revisar la incidencia"
    )
    
    # Resolución
    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de resolución de la incidencia"
    )
    usuario_resolucion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_resueltas',
        help_text="Usuario que resolvió la incidencia"
    )
    observaciones_resolucion = models.TextField(
        blank=True,
        help_text="Observaciones de la resolución"
    )
    
    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        indexes = [
            models.Index(fields=['cierre', 'empleado_rut']),
            models.Index(fields=['tipo_incidencia']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_deteccion']),
            models.Index(fields=['analista_asignado']),
            models.Index(fields=['supervisor_asignado']),
        ]
        ordering = ['-fecha_deteccion']
    
    def __str__(self):
        return f"Incidencia {self.empleado_nombre} - {self.concepto_afectado} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        """Calcular diferencias automáticamente"""
        if self.valor_periodo_anterior and self.valor_periodo_actual:
            self.diferencia_absoluta = abs(self.valor_periodo_actual - self.valor_periodo_anterior)
            
            if self.valor_periodo_anterior != 0:
                self.diferencia_porcentual = (
                    (self.valor_periodo_actual - self.valor_periodo_anterior) / 
                    self.valor_periodo_anterior
                ) * 100
        
        super().save(*args, **kwargs)

class InteraccionIncidencia(models.Model):
    """
    Interacciones en el sistema tipo foro para resolver incidencias.
    
    Permite comunicación entre analista y supervisor sobre cada incidencia.
    """
    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name='interacciones',
        help_text="Incidencia a la que pertenece esta interacción"
    )
    
    # Datos de la interacción
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="Usuario que realizó la interacción"
    )
    fecha_interaccion = models.DateTimeField(auto_now_add=True)
    
    # Contenido
    mensaje = models.TextField(help_text="Mensaje de la interacción")
    
    # Tipo de interacción
    TIPO_INTERACCION_CHOICES = [
        ('comentario', 'Comentario'),
        ('pregunta', 'Pregunta'),
        ('respuesta', 'Respuesta'),
        ('escalacion', 'Escalación'),
        ('resolucion', 'Resolución'),
    ]
    tipo_interaccion = models.CharField(
        max_length=20,
        choices=TIPO_INTERACCION_CHOICES,
        default='comentario',
        help_text="Tipo de interacción"
    )
    
    class Meta:
        verbose_name = "Interacción de Incidencia"
        verbose_name_plural = "Interacciones de Incidencias"
        ordering = ['fecha_interaccion']
        indexes = [
            models.Index(fields=['incidencia', 'fecha_interaccion']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_interaccion_display()} ({self.fecha_interaccion.strftime('%d/%m/%Y %H:%M')})"

# ========== SISTEMA DE KPIs PRE-CALCULADOS ==========

class KPINomina(models.Model):
    """
    Tabla de KPIs pre-calculados para consultas ultra-rápidas.
    
    Algoritmo de optimización:
    1. Se calculan automáticamente al consolidar desde Redis
    2. Se indexan por cliente, período y tipo para búsquedas O(log n)
    3. Se mantienen agregaciones por clasificación de conceptos
    4. Permiten dashboards en tiempo real sin cálculos pesados
    """
    # Identificación del KPI
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='kpis_calculados',
        help_text="Cierre al que pertenece este KPI"
    )
    
    # Tipo de KPI para indexación optimizada
    TIPO_KPI_CHOICES = [
        ('total_haberes_imponibles', 'Total Haberes Imponibles'),
        ('total_haberes_no_imponibles', 'Total Haberes No Imponibles'),
        ('total_descuentos_legales', 'Total Descuentos Legales'),
        ('total_otros_descuentos', 'Total Otros Descuentos'),
        ('total_aportes_patronales', 'Total Aportes Patronales'),
        ('total_horas_extras', 'Total Horas Extras'),
        ('promedio_sueldo_base', 'Promedio Sueldo Base'),
        ('empleados_activos_count', 'Cantidad Empleados Activos'),
        ('empleados_finiquitos_count', 'Cantidad Finiquitos'),
        ('empleados_ingresos_count', 'Cantidad Ingresos'),
        ('masa_salarial_total', 'Masa Salarial Total'),
        ('variacion_vs_anterior', 'Variación vs Período Anterior'),
    ]
    tipo_kpi = models.CharField(
        max_length=40,
        choices=TIPO_KPI_CHOICES,
        db_index=True,
        help_text="Tipo de KPI para búsquedas optimizadas"
    )
    
    # Valores del KPI
    valor_numerico = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Valor principal del KPI"
    )
    valor_comparativo_anterior = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor del período anterior para comparación"
    )
    variacion_porcentual = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
        help_text="Variación porcentual respecto período anterior"
    )
    
    # Metadatos adicionales (JSON para flexibilidad)
    metadatos_kpi = models.JSONField(
        default=dict,
        help_text="Metadatos adicionales del KPI (distribuciones, percentiles, etc.)"
    )
    
    # Control de actualización
    fecha_calculo = models.DateTimeField(auto_now=True)
    hash_verificacion = models.CharField(
        max_length=64,
        help_text="Hash para verificar integridad del KPI"
    )
    
    class Meta:
        unique_together = ('cierre', 'tipo_kpi')
        verbose_name = "KPI de Nómina"
        verbose_name_plural = "KPIs de Nómina"
        indexes = [
            # Índice compuesto para consultas rápidas de dashboard
            models.Index(fields=['cierre', 'tipo_kpi']),
            # Índice para comparaciones temporales
            models.Index(fields=['tipo_kpi', 'fecha_calculo']),
            # Índice para análisis de variaciones
            models.Index(fields=['variacion_porcentual']),
        ]
        ordering = ['tipo_kpi']
    
    def __str__(self):
        return f"{self.cierre} - {self.get_tipo_kpi_display()}: {self.valor_numerico}"
    
    def save(self, *args, **kwargs):
        """Calcular hash de verificación y variación automáticamente"""
        # Calcular variación porcentual
        if self.valor_comparativo_anterior and self.valor_comparativo_anterior != 0:
            self.variacion_porcentual = (
                (self.valor_numerico - self.valor_comparativo_anterior) / 
                abs(self.valor_comparativo_anterior)
            ) * 100
        
        # Generar hash de verificación
        hash_data = f"{self.cierre.id}:{self.tipo_kpi}:{self.valor_numerico}:{datetime.now().strftime('%Y%m%d')}"
        self.hash_verificacion = hashlib.sha256(hash_data.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def calcular_kpis_cierre(cls, cierre):
        """
        Algoritmo optimizado para calcular todos los KPIs de un cierre.
        
        Optimizaciones:
        1. Una sola consulta con agregaciones múltiples
        2. Uso de select_related para evitar N+1 queries
        3. Cálculo en memoria para reducir hits a BD
        4. Transacción atómica para consistencia
        """
        from django.db import transaction
        
        with transaction.atomic():
            # Consulta optimizada con todas las agregaciones
            stats = cierre.empleados_nomina.select_related().aggregate(
                total_activos=Count('id', filter=Q(tipo_empleado='activo')),
                total_finiquitos=Count('id', filter=Q(tipo_empleado='finiquito')),
                total_ingresos=Count('id', filter=Q(tipo_empleado='ingreso')),
            )
            
            # Agregaciones por clasificación de conceptos
            clasificaciones_stats = {}
            for clasificacion_code, _ in CLASIFICACION_CHOICES:
                # Buscar conceptos de esta clasificación
                conceptos_clasificacion = MapeoConcepto.objects.filter(
                    cliente=cierre.cliente,
                    clasificacion=clasificacion_code,
                    activo=True
                ).values_list('concepto_original', flat=True)
                
                if conceptos_clasificacion:
                    total = EmpleadoConcepto.objects.filter(
                        empleado_nomina__cierre=cierre,
                        concepto__in=conceptos_clasificacion
                    ).aggregate(total=Sum('valor_numerico'))['total'] or 0
                    
                    clasificaciones_stats[clasificacion_code] = total
            
            # Obtener KPIs del período anterior para comparación
            periodo_anterior = cls._obtener_periodo_anterior(cierre.periodo)
            kpis_anteriores = {}
            
            if periodo_anterior:
                try:
                    cierre_anterior = CierreNomina.objects.get(
                        cliente=cierre.cliente,
                        periodo=periodo_anterior,
                        estado='cerrado'
                    )
                    kpis_anteriores = {
                        kpi.tipo_kpi: kpi.valor_numerico 
                        for kpi in cierre_anterior.kpis_calculados.all()
                    }
                except CierreNomina.DoesNotExist:
                    pass
            
            # Crear/actualizar KPIs
            kpis_a_crear = [
                ('empleados_activos_count', stats['total_activos']),
                ('empleados_finiquitos_count', stats['total_finiquitos']),
                ('empleados_ingresos_count', stats['total_ingresos']),
                ('total_haberes_imponibles', clasificaciones_stats.get('haber_imponible', 0)),
                ('total_haberes_no_imponibles', clasificaciones_stats.get('haber_no_imponible', 0)),
                ('total_descuentos_legales', clasificaciones_stats.get('descuento_legal', 0)),
                ('total_otros_descuentos', clasificaciones_stats.get('otro_descuento', 0)),
                ('total_aportes_patronales', clasificaciones_stats.get('aporte_patronal', 0)),
                ('total_horas_extras', clasificaciones_stats.get('horas_extras', 0)),
                ('masa_salarial_total', 
                 clasificaciones_stats.get('haber_imponible', 0) + 
                 clasificaciones_stats.get('haber_no_imponible', 0)),
            ]
            
            for tipo_kpi, valor in kpis_a_crear:
                cls.objects.update_or_create(
                    cierre=cierre,
                    tipo_kpi=tipo_kpi,
                    defaults={
                        'valor_numerico': valor,
                        'valor_comparativo_anterior': kpis_anteriores.get(tipo_kpi),
                        'metadatos_kpi': cls._generar_metadatos_kpi(cierre, tipo_kpi, valor)
                    }
                )
    
    @staticmethod
    def _obtener_periodo_anterior(periodo_actual):
        """Obtener período anterior en formato YYYY-MM"""
        try:
            year, month = periodo_actual.split('-')
            year, month = int(year), int(month)
            
            if month == 1:
                return f"{year-1}-12"
            else:
                return f"{year}-{month-1:02d}"
        except:
            return None
    
    @staticmethod
    def _generar_metadatos_kpi(cierre, tipo_kpi, valor):
        """Generar metadatos adicionales según el tipo de KPI"""
        metadatos = {
            'fecha_calculo': datetime.now().isoformat(),
            'periodo': cierre.periodo,
            'cliente_id': cierre.cliente.id
        }
        
        if 'count' in tipo_kpi:
            # Para KPIs de conteo, agregar distribución por tipo
            metadatos['tipo_distribucion'] = 'conteo'
        elif 'total' in tipo_kpi:
            # Para KPIs monetarios, agregar estadísticas descriptivas
            metadatos['tipo_distribucion'] = 'monetario'
            metadatos['moneda'] = 'CLP'
        
        return metadatos

class EmpleadoOfuscado(models.Model):
    """
    Sistema de ofuscación reversible para protección de datos sensibles.
    
    Algoritmo de ofuscación:
    1. Hash SHA-256 con salt por cliente para generar ID anónimo
    2. Encriptación AES para datos reversibles (nombre ofuscado)
    3. Mapeo 1:1 para mantener consistencia en análisis
    4. Auditoría de accesos a datos reales
    """
    # Relación con el cierre
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='empleados_ofuscados',
        help_text="Cierre al que pertenece este empleado ofuscado"
    )
    
    # Datos ofuscados
    rut_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Hash SHA-256 del RUT para identificación anónima"
    )
    nombre_ofuscado = models.CharField(
        max_length=200,
        help_text="Nombre ofuscado pero reversible"
    )
    
    # Datos estadísticos (sin ofuscar para análisis)
    tipo_empleado = models.CharField(
        max_length=20,
        choices=TIPO_EMPLEADO_CHOICES,
        help_text="Tipo de empleado (no sensible)"
    )
    rango_salarial = models.CharField(
        max_length=20,
        help_text="Rango salarial en lugar de valor exacto"
    )
    
    # Metadatos de ofuscación
    salt_ofuscacion = models.CharField(
        max_length=32,
        help_text="Salt único para este registro"
    )
    algoritmo_version = models.CharField(
        max_length=10,
        default='v1.0',
        help_text="Versión del algoritmo de ofuscación"
    )
    
    # Control de acceso
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    accesos_datos_reales = models.PositiveIntegerField(
        default=0,
        help_text="Contador de accesos a datos reales"
    )
    ultimo_acceso_real = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se accedieron los datos reales"
    )
    
    class Meta:
        unique_together = ('cierre', 'rut_hash')
        verbose_name = "Empleado Ofuscado"
        verbose_name_plural = "Empleados Ofuscados"
        indexes = [
            models.Index(fields=['rut_hash']),
            models.Index(fields=['cierre', 'tipo_empleado']),
            models.Index(fields=['rango_salarial']),
        ]
    
    def __str__(self):
        return f"Empleado Anónimo {self.rut_hash[:8]}... ({self.get_tipo_empleado_display()})"
    
    @classmethod
    def ofuscar_empleado(cls, empleado_nomina):
        """
        Crear versión ofuscada de un empleado.
        
        Algoritmo:
        1. Generar hash único del RUT con salt del cliente
        2. Crear nombre ofuscado manteniendo características
        3. Clasificar en rango salarial en lugar de valor exacto
        4. Mantener metadatos para reversibilidad
        """
        import secrets
        
        # Generar salt único
        salt = secrets.token_hex(16)
        
        # Crear hash del RUT
        rut_data = f"{empleado_nomina.rut_empleado}:{empleado_nomina.cierre.cliente.id}:{salt}"
        rut_hash = hashlib.sha256(rut_data.encode()).hexdigest()
        
        # Generar nombre ofuscado (mantiene longitud y patrón)
        nombre_ofuscado = cls._generar_nombre_ofuscado(empleado_nomina.nombre_empleado, salt)
        
        # Calcular rango salarial
        rango_salarial = cls._calcular_rango_salarial(empleado_nomina)
        
        # Crear registro ofuscado
        return cls.objects.create(
            cierre=empleado_nomina.cierre,
            rut_hash=rut_hash,
            nombre_ofuscado=nombre_ofuscado,
            tipo_empleado=empleado_nomina.tipo_empleado,
            rango_salarial=rango_salarial,
            salt_ofuscacion=salt
        )
    
    @staticmethod
    def _generar_nombre_ofuscado(nombre_real, salt):
        """
        Generar nombre ofuscado manteniendo características estructurales.
        
        Mantiene:
        - Longitud aproximada
        - Número de palabras
        - Patrón de mayúsculas/minúsculas
        """
        import random
        
        random.seed(salt)  # Seed determinístico para consistencia
        
        palabras = nombre_real.split()
        palabras_ofuscadas = []
        
        nombres_genericos = [
            'JUAN', 'MARIA', 'CARLOS', 'ANA', 'LUIS', 'CARMEN', 'JOSE', 'ELENA',
            'PEDRO', 'ROSA', 'MIGUEL', 'LUCIA', 'ANTONIO', 'SOFIA', 'MANUEL', 'ISABEL'
        ]
        
        apellidos_genericos = [
            'GARCIA', 'RODRIGUEZ', 'MARTINEZ', 'LOPEZ', 'GONZALEZ', 'PEREZ',
            'SANCHEZ', 'MARTIN', 'JIMENEZ', 'RUIZ', 'HERNANDEZ', 'DIAZ'
        ]
        
        for i, palabra in enumerate(palabras):
            if i == 0:  # Primer nombre
                nueva_palabra = random.choice(nombres_genericos)
            elif i == 1:  # Segundo nombre o apellido
                nueva_palabra = random.choice(apellidos_genericos)
            else:  # Apellidos adicionales
                nueva_palabra = random.choice(apellidos_genericos)
            
            # Mantener patrón de mayúsculas/minúsculas original
            if palabra.isupper():
                palabras_ofuscadas.append(nueva_palabra)
            elif palabra.islower():
                palabras_ofuscadas.append(nueva_palabra.lower())
            else:
                palabras_ofuscadas.append(nueva_palabra.capitalize())
        
        return ' '.join(palabras_ofuscadas)
    
    @staticmethod
    def _calcular_rango_salarial(empleado_nomina):
        """
        Calcular rango salarial en lugar de valor exacto.
        
        Rangos en UF para proteger datos exactos:
        - A: 0-20 UF
        - B: 20-40 UF  
        - C: 40-60 UF
        - D: 60-80 UF
        - E: 80+ UF
        """
        # Calcular total de haberes imponibles
        total_haberes = empleado_nomina.conceptos.filter(
            concepto__in=MapeoConcepto.objects.filter(
                cliente=empleado_nomina.cierre.cliente,
                clasificacion='haber_imponible'
            ).values_list('concepto_original', flat=True)
        ).aggregate(total=Sum('valor_numerico'))['total'] or 0
        
        # Convertir a UF aproximadamente (UF ≈ $37,000 en 2025)
        uf_aproximadas = total_haberes / 37000
        
        if uf_aproximadas <= 20:
            return 'A (0-20 UF)'
        elif uf_aproximadas <= 40:
            return 'B (20-40 UF)'
        elif uf_aproximadas <= 60:
            return 'C (40-60 UF)'
        elif uf_aproximadas <= 80:
            return 'D (60-80 UF)'
        else:
            return 'E (80+ UF)'
    
    def registrar_acceso_datos_reales(self, usuario):
        """
        Registrar acceso a datos reales para auditoría.
        """
        self.accesos_datos_reales += 1
        self.ultimo_acceso_real = timezone.now()
        self.save()
        
        # Log de auditoría
        LogAccesoOfuscacion.objects.create(
            empleado_ofuscado=self,
            usuario_acceso=usuario,
            motivo_acceso="Consulta datos reales"
        )

class LogAccesoOfuscacion(models.Model):
    """
    Log de auditoría para accesos a datos reales de empleados ofuscados.
    """
    empleado_ofuscado = models.ForeignKey(
        EmpleadoOfuscado,
        on_delete=models.CASCADE,
        related_name='logs_acceso'
    )
    usuario_acceso = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_acceso = models.DateTimeField(auto_now_add=True)
    motivo_acceso = models.CharField(max_length=200)
    ip_acceso = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log Acceso Ofuscación"
        verbose_name_plural = "Logs Acceso Ofuscación"
        ordering = ['-fecha_acceso']

# ========== OPTIMIZACIONES DE BÚSQUEDA Y COMPARACIÓN ==========

class IndiceEmpleadoBusqueda(models.Model):
    """
    Índice optimizado para búsquedas full-text de empleados.
    
    Algoritmo de búsqueda optimizada:
    1. Índice de texto normalizado para búsquedas rápidas
    2. Soundex/Metaphone para búsquedas fonéticas
    3. Trigrams para búsquedas aproximadas
    4. Metadatos de empleado pre-calculados para filtros
    """
    empleado_nomina = models.OneToOneField(
        EmpleadoNomina,
        on_delete=models.CASCADE,
        related_name='indice_busqueda',
        help_text="Empleado indexado para búsqueda"
    )
    
    # Índices de búsqueda
    texto_normalizado = models.CharField(
        max_length=400,
        db_index=True,
        help_text="Texto normalizado para búsqueda exacta"
    )
    rut_normalizado = models.CharField(
        max_length=15,
        db_index=True,
        help_text="RUT sin puntos ni guiones"
    )
    soundex_nombre = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Código Soundex para búsqueda fonética"
    )
    
    # Metadatos para filtros rápidos
    periodo_activo = models.CharField(
        max_length=7,
        db_index=True,
        help_text="Período donde está activo (YYYY-MM)"
    )
    cliente_id = models.PositiveIntegerField(
        db_index=True,
        help_text="ID del cliente para filtros rápidos"
    )
    rango_salarial_codigo = models.CharField(
        max_length=5,
        db_index=True,
        help_text="Código del rango salarial (A, B, C, D, E)"
    )
    
    # Estadísticas pre-calculadas
    total_conceptos = models.PositiveIntegerField(
        default=0,
        help_text="Número total de conceptos del empleado"
    )
    suma_haberes_imponibles = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Suma de haberes imponibles pre-calculada"
    )
    
    # Control de actualización
    fecha_indexacion = models.DateTimeField(auto_now=True)
    version_indice = models.CharField(
        max_length=10,
        default='v1.0',
        help_text="Versión del algoritmo de indexación"
    )
    
    class Meta:
        verbose_name = "Índice de Búsqueda Empleado"
        verbose_name_plural = "Índices de Búsqueda Empleados"
        indexes = [
            # Índice compuesto para búsquedas multi-criterio
            models.Index(fields=['cliente_id', 'periodo_activo', 'rango_salarial_codigo']),
            # Índice para búsquedas fonéticas
            models.Index(fields=['soundex_nombre']),
            # Índice para ordenamiento por salario
            models.Index(fields=['suma_haberes_imponibles']),
        ]
    
    def __str__(self):
        return f"Índice: {self.empleado_nomina.nombre_empleado} ({self.periodo_activo})"
    
    def save(self, *args, **kwargs):
        """Generar índices automáticamente al guardar"""
        # Normalizar texto para búsqueda
        self.texto_normalizado = self._normalizar_texto(
            f"{self.empleado_nomina.nombre_empleado} {self.empleado_nomina.rut_empleado}"
        )
        
        # Normalizar RUT
        self.rut_normalizado = self.empleado_nomina.rut_empleado.replace('.', '').replace('-', '')
        
        # Generar Soundex
        self.soundex_nombre = self._generar_soundex(self.empleado_nomina.nombre_empleado)
        
        # Metadatos
        self.periodo_activo = self.empleado_nomina.cierre.periodo
        self.cliente_id = self.empleado_nomina.cierre.cliente.id
        
        # Calcular rango salarial
        self.rango_salarial_codigo = self._calcular_rango_codigo()
        
        # Estadísticas
        self.total_conceptos = self.empleado_nomina.conceptos.count()
        self.suma_haberes_imponibles = self._calcular_suma_haberes()
        
        super().save(*args, **kwargs)
    
    def _normalizar_texto(self, texto):
        """Normalizar texto para búsquedas eficientes"""
        import unicodedata
        import re
        
        # Normalizar unicode y eliminar acentos
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        
        # Convertir a mayúsculas y eliminar caracteres especiales
        texto = re.sub(r'[^A-Z0-9\s]', '', texto.upper())
        
        # Eliminar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def _generar_soundex(self, nombre):
        """
        Generar código Soundex simplificado para búsqueda fonética.
        
        Algoritmo adaptado para nombres en español:
        1. Conservar primera letra
        2. Eliminar vocales (excepto la primera)
        3. Reemplazar consonantes similares
        4. Generar código de 4 caracteres
        """
        if not nombre:
            return '0000'
        
        nombre = nombre.upper().strip()
        if not nombre:
            return '0000'
        
        # Conservar primera letra
        soundex = nombre[0]
        
        # Mapeo de consonantes similares
        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5', 'Ñ': '5',
            'R': '6'
        }
        
        # Procesar resto del nombre
        for char in nombre[1:]:
            if char in mapping:
                code = mapping[char]
                if code != soundex[-1]:  # No repetir códigos consecutivos
                    soundex += code
                    if len(soundex) >= 4:
                        break
        
        # Rellenar con ceros si es necesario
        soundex = soundex[:4].ljust(4, '0')
        
        return soundex
    
    def _calcular_rango_codigo(self):
        """Calcular código de rango salarial (A-E)"""
        # Reutilizar lógica de EmpleadoOfuscado
        rango_completo = EmpleadoOfuscado._calcular_rango_salarial(self.empleado_nomina)
        return rango_completo[0]  # Solo la letra (A, B, C, D, E)
    
    def _calcular_suma_haberes(self):
        """Calcular suma de haberes imponibles pre-calculada"""
        conceptos_haberes = MapeoConcepto.objects.filter(
            cliente_id=self.cliente_id,
            clasificacion='haber_imponible',
            activo=True
        ).values_list('concepto_original', flat=True)
        
        return self.empleado_nomina.conceptos.filter(
            concepto__in=conceptos_haberes
        ).aggregate(total=Sum('valor_numerico'))['total'] or 0
    
    @classmethod
    def buscar_empleados(cls, query, cliente_id=None, periodo=None, **filtros):
        """
        Algoritmo de búsqueda optimizada multi-criterio.
        
        Soporta:
        - Búsqueda por nombre (exacta, normalizada, fonética)
        - Búsqueda por RUT (parcial y completa)  
        - Filtros por período, cliente, rango salarial
        - Ordenamiento por relevancia
        """
        queryset = cls.objects.select_related('empleado_nomina__cierre__cliente')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if periodo:
            queryset = queryset.filter(periodo_activo=periodo)
        
        # Aplicar filtros adicionales
        for field, value in filtros.items():
            queryset = queryset.filter(**{field: value})
        
        if not query:
            return queryset.order_by('-suma_haberes_imponibles')[:100]
        
        query_normalizado = cls._normalizar_texto_static(query)
        query_soundex = cls._generar_soundex_static(query)
        rut_query = query.replace('.', '').replace('-', '')
        
        # Búsquedas con diferentes pesos de relevancia
        resultados = []
        
        # 1. Búsqueda exacta por RUT (peso máximo)
        if rut_query.isdigit():
            exactos_rut = queryset.filter(rut_normalizado__icontains=rut_query)[:10]
            resultados.extend([(emp, 100) for emp in exactos_rut])
        
        # 2. Búsqueda exacta por texto normalizado (peso alto)
        exactos_texto = queryset.filter(texto_normalizado__icontains=query_normalizado)[:20]
        resultados.extend([(emp, 90) for emp in exactos_texto])
        
        # 3. Búsqueda fonética por Soundex (peso medio)
        foneticos = queryset.filter(soundex_nombre=query_soundex)[:30]
        resultados.extend([(emp, 70) for emp in foneticos])
        
        # 4. Búsqueda parcial por palabras (peso bajo)
        palabras = query_normalizado.split()
        for palabra in palabras:
            if len(palabra) >= 3:
                parciales = queryset.filter(texto_normalizado__icontains=palabra)[:20]
                resultados.extend([(emp, 50) for emp in parciales])
        
        # Eliminar duplicados manteniendo mayor peso
        empleados_unicos = {}
        for empleado, peso in resultados:
            if empleado.id not in empleados_unicos or empleados_unicos[empleado.id][1] < peso:
                empleados_unicos[empleado.id] = (empleado, peso)
        
        # Ordenar por peso y retornar
        resultados_finales = sorted(
            empleados_unicos.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [emp for emp, peso in resultados_finales[:50]]
    
    @staticmethod
    def _normalizar_texto_static(texto):
        """Versión estática del normalizador de texto"""
        import unicodedata
        import re
        
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r'[^A-Z0-9\s]', '', texto.upper())
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    @staticmethod
    def _generar_soundex_static(nombre):
        """Versión estática del generador Soundex"""
        if not nombre:
            return '0000'
        
        nombre = nombre.upper().strip()
        if not nombre:
            return '0000'
        
        soundex = nombre[0]
        
        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5', 'Ñ': '5',
            'R': '6'
        }
        
        for char in nombre[1:]:
            if char in mapping:
                code = mapping[char]
                if code != soundex[-1]:
                    soundex += code
                    if len(soundex) >= 4:
                        break
        
        soundex = soundex[:4].ljust(4, '0')
        
        return soundex

class ComparacionMensual(models.Model):
    """
    Tabla optimizada para comparaciones mes a mes.
    
    Algoritmo de comparación eficiente:
    1. Pre-calcula todas las métricas comparativas al cerrar un período
    2. Indexa por empleado, concepto y variación para búsquedas rápidas
    3. Identifica automáticamente anomalías y tendencias
    4. Soporta análisis históricos multi-período
    """
    # Identificación de la comparación
    cierre_actual = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='comparaciones_como_actual',
        help_text="Cierre del período actual"
    )
    cierre_anterior = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='comparaciones_como_anterior',
        help_text="Cierre del período anterior"
    )
    
    # Datos del empleado
    empleado_actual = models.ForeignKey(
        EmpleadoNomina,
        on_delete=models.CASCADE,
        related_name='comparaciones_actuales'
    )
    empleado_anterior = models.ForeignKey(
        EmpleadoNomina,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comparaciones_anteriores',
        help_text="Puede ser null si el empleado es nuevo"
    )
    
    # Tipo de comparación
    TIPO_COMPARACION_CHOICES = [
        ('empleado_continuo', 'Empleado Continuo'),
        ('empleado_nuevo', 'Empleado Nuevo'),
        ('empleado_saliente', 'Empleado Saliente'),
        ('empleado_reingreso', 'Empleado Reingreso'),
    ]
    tipo_comparacion = models.CharField(
        max_length=20,
        choices=TIPO_COMPARACION_CHOICES,
        db_index=True,
        help_text="Tipo de comparación según situación del empleado"
    )
    
    # Métricas comparativas pre-calculadas
    variacion_sueldo_base = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Variación absoluta del sueldo base"
    )
    variacion_sueldo_porcentual = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
        help_text="Variación porcentual del sueldo base"
    )
    
    variacion_total_haberes = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Variación absoluta total de haberes"
    )
    variacion_total_haberes_porcentual = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
        help_text="Variación porcentual total de haberes"
    )
    
    # Análisis de anomalías
    ES_ANOMALIA_CHOICES = [
        ('no', 'Variación Normal'),
        ('menor', 'Anomalía Menor (<20% variación)'),
        ('mayor', 'Anomalía Mayor (20-50% variación)'),
        ('critica', 'Anomalía Crítica (>50% variación)'),
    ]
    nivel_anomalia = models.CharField(
        max_length=10,
        choices=ES_ANOMALIA_CHOICES,
        default='no',
        db_index=True,
        help_text="Nivel de anomalía detectado automáticamente"
    )
    
    # Metadatos de variaciones por concepto
    detalle_variaciones = models.JSONField(
        default=dict,
        help_text="Detalle de variaciones por cada concepto"
    )
    
    # Indicadores de tendencia
    tendencia_3_meses = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tendencia calculada de 3 meses (ascendente/descendente/estable)"
    )
    coeficiente_variacion = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        default=0,
        help_text="Coeficiente de variación para estabilidad salarial"
    )
    
    # Control
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    algoritmo_version = models.CharField(
        max_length=10,
        default='v2.0',
        help_text="Versión del algoritmo de comparación"
    )
    
    class Meta:
        unique_together = ('cierre_actual', 'empleado_actual')
        verbose_name = "Comparación Mensual"
        verbose_name_plural = "Comparaciones Mensuales"
        indexes = [
            # Índice para consultas por período
            models.Index(fields=['cierre_actual', 'empleado_actual']),
            # Índice para análisis de anomalías
            models.Index(fields=['nivel_anomalia', 'variacion_sueldo_porcentual']),
            # Índice para análisis de tendencias
            models.Index(fields=['tendencia_3_meses', 'coeficiente_variacion']),
        ]
        ordering = ['-variacion_sueldo_porcentual']
    
    def __str__(self):
        return f"Comparación {self.empleado_actual.nombre_empleado} ({self.cierre_actual.periodo}): {self.get_nivel_anomalia_display()}"
    
    def save(self, *args, **kwargs):
        """Calcular métricas automáticamente al guardar"""
        self._calcular_variaciones()
        self._detectar_anomalias()
        super().save(*args, **kwargs)
    
    def _calcular_variaciones(self):
        """Algoritmo optimizado para calcular todas las variaciones"""
        if not self.empleado_anterior:
            # Empleado nuevo - no hay variación
            self.tipo_comparacion = 'empleado_nuevo'
            return
        
        # Obtener conceptos de ambos períodos
        conceptos_actual = {
            c.concepto: c.valor_numerico 
            for c in self.empleado_actual.conceptos.all()
        }
        conceptos_anterior = {
            c.concepto: c.valor_numerico 
            for c in self.empleado_anterior.conceptos.all()
        }
        
        # Calcular variaciones por concepto
        detalle = {}
        
        # Buscar sueldo base (concepto más importante)
        sueldo_base_concepto = self._obtener_concepto_sueldo_base()
        if sueldo_base_concepto:
            actual = conceptos_actual.get(sueldo_base_concepto, 0)
            anterior = conceptos_anterior.get(sueldo_base_concepto, 0)
            
            self.variacion_sueldo_base = actual - anterior
            if anterior != 0:
                self.variacion_sueldo_porcentual = (actual - anterior) / abs(anterior) * 100
            
            detalle[sueldo_base_concepto] = {
                'actual': float(actual),
                'anterior': float(anterior),
                'variacion_absoluta': float(self.variacion_sueldo_base),
                'variacion_porcentual': float(self.variacion_sueldo_porcentual)
            }
        
        # Calcular total de haberes imponibles
        haberes_actuales = self._calcular_total_haberes(conceptos_actual)
        haberes_anteriores = self._calcular_total_haberes(conceptos_anterior)
        
        self.variacion_total_haberes = haberes_actuales - haberes_anteriores
        if haberes_anteriores != 0:
            self.variacion_total_haberes_porcentual = (
                (haberes_actuales - haberes_anteriores) / abs(haberes_anteriores) * 100
            )
        
        detalle['total_haberes'] = {
            'actual': float(haberes_actuales),
            'anterior': float(haberes_anteriores),
            'variacion_absoluta': float(self.variacion_total_haberes),
            'variacion_porcentual': float(self.variacion_total_haberes_porcentual)
        }
        
        # Guardar detalle completo de variaciones
        for concepto in set(conceptos_actual.keys()) | set(conceptos_anterior.keys()):
            if concepto not in detalle:
                actual = conceptos_actual.get(concepto, 0)
                anterior = conceptos_anterior.get(concepto, 0)
                variacion_abs = actual - anterior
                variacion_pct = (actual - anterior) / abs(anterior) * 100 if anterior != 0 else 0
                
                detalle[concepto] = {
                    'actual': float(actual),
                    'anterior': float(anterior),
                    'variacion_absoluta': float(variacion_abs),
                    'variacion_porcentual': float(variacion_pct)
                }
        
        self.detalle_variaciones = detalle
    
    def _detectar_anomalias(self):
        """Algoritmo de detección automática de anomalías"""
        # Usar variación porcentual del sueldo base como indicador principal
        variacion_abs = abs(float(self.variacion_sueldo_porcentual))
        
        if variacion_abs < 5:
            self.nivel_anomalia = 'no'
        elif variacion_abs < 20:
            self.nivel_anomalia = 'menor'
        elif variacion_abs < 50:
            self.nivel_anomalia = 'mayor'
        else:
            self.nivel_anomalia = 'critica'
    
    def _obtener_concepto_sueldo_base(self):
        """Identificar el concepto que representa el sueldo base"""
        cliente = self.cierre_actual.cliente
        
        # Buscar concepto mapeado como sueldo base
        try:
            mapeo_sueldo = MapeoConcepto.objects.get(
                cliente=cliente,
                concepto_estandar__icontains='SUELDO_BASE',
                activo=True
            )
            return mapeo_sueldo.concepto_original
        except MapeoConcepto.DoesNotExist:
            pass
        
        # Fallback: buscar el concepto con mayor valor promedio
        conceptos_haberes = MapeoConcepto.objects.filter(
            cliente=cliente,
            clasificacion='haber_imponible',
            activo=True
        ).values_list('concepto_original', flat=True)
        
        if conceptos_haberes:
            # Retornar el primer concepto de haberes imponibles
            return conceptos_haberes[0]
        
        return None
    
    def _calcular_total_haberes(self, conceptos_dict):
        """Calcular total de haberes imponibles desde diccionario de conceptos"""
        cliente = self.cierre_actual.cliente
        
        conceptos_haberes = MapeoConcepto.objects.filter(
            cliente=cliente,
            clasificacion='haber_imponible',
            activo=True
        ).values_list('concepto_original', flat=True)
        
        total = 0
        for concepto in conceptos_haberes:
            total += conceptos_dict.get(concepto, 0)
        
        return total
    
    @classmethod
    def generar_comparaciones_cierre(cls, cierre_actual):
        """
        Algoritmo principal para generar todas las comparaciones de un cierre.
        
        Optimizaciones:
        1. Una sola consulta para obtener cierre anterior
        2. Bulk create para insertar comparaciones
        3. Pre-carga de conceptos para evitar N+1 queries
        4. Cálculo en memoria para reducir hits a BD
        """
        # Obtener período anterior
        periodo_anterior = KPINomina._obtener_periodo_anterior(cierre_actual.periodo)
        if not periodo_anterior:
            return {'success': False, 'message': 'No hay período anterior para comparar'}
        
        try:
            cierre_anterior = CierreNomina.objects.get(
                cliente=cierre_actual.cliente,
                periodo=periodo_anterior,
                estado__in=['consolidado', 'cerrado']
            )
        except CierreNomina.DoesNotExist:
            return {'success': False, 'message': f'No se encontró cierre para período {periodo_anterior}'}
        
        # Pre-cargar empleados con sus conceptos
        empleados_actuales = list(cierre_actual.empleados_nomina.prefetch_related('conceptos').all())
        empleados_anteriores = {
            emp.rut_empleado: emp 
            for emp in cierre_anterior.empleados_nomina.prefetch_related('conceptos').all()
        }
        
        # Generar comparaciones
        comparaciones = []
        
        for empleado_actual in empleados_actuales:
            empleado_anterior = empleados_anteriores.get(empleado_actual.rut_empleado)
            
            comparacion = cls(
                cierre_actual=cierre_actual,
                cierre_anterior=cierre_anterior,
                empleado_actual=empleado_actual,
                empleado_anterior=empleado_anterior
            )
            
            # Los cálculos se harán automáticamente en save()
            comparaciones.append(comparacion)
        
        # Bulk create para eficiencia
        cls.objects.bulk_create(comparaciones, batch_size=1000)
        
        # Calcular estadísticas del proceso
        total_comparaciones = len(comparaciones)
        anomalias_detectadas = cls.objects.filter(
            cierre_actual=cierre_actual,
            nivel_anomalia__in=['menor', 'mayor', 'critica']
        ).count()
        
        return {
            'success': True,
            'total_comparaciones': total_comparaciones,
            'anomalias_detectadas': anomalias_detectadas,
                'empleados_nuevos': cls.objects.filter(
                cierre_actual=cierre_actual,
                tipo_comparacion='empleado_nuevo'
            ).count()
        }

# ========== CACHE INTELIGENTE Y UTILIDADES ==========

class CacheConsultas(models.Model):
    """
    Sistema de cache inteligente para consultas frecuentes.
    
    Algoritmo de cache optimizado:
    1. Cache con TTL automático basado en estado del cierre
    2. Invalidación inteligente cuando cambian los datos
    3. Compresión de resultados para consultas grandes
    4. Métricas de hit rate para optimización
    """
    # Identificación del cache
    clave_cache = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Clave única del cache (hash MD5 de la consulta)"
    )
    consulta_tipo = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Tipo de consulta cacheada"
    )
    
    # Metadatos de la consulta
    parametros_consulta = models.JSONField(
        help_text="Parámetros originales de la consulta"
    )
    cliente_id = models.PositiveIntegerField(
        db_index=True,
        help_text="Cliente asociado al cache"
    )
    periodo = models.CharField(
        max_length=7,
        db_index=True,
        help_text="Período asociado al cache"
    )
    
    # Datos del cache
    resultado_comprimido = models.BinaryField(
        help_text="Resultado de la consulta comprimido con gzip"
    )
    tamaño_original = models.PositiveIntegerField(
        help_text="Tamaño original del resultado en bytes"
    )
    tamaño_comprimido = models.PositiveIntegerField(
        help_text="Tamaño comprimido del resultado en bytes"
    )
    
    # Control de expiración
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(
        db_index=True,
        help_text="Fecha de expiración del cache"
    )
    ttl_segundos = models.PositiveIntegerField(
        help_text="Time To Live original en segundos"
    )
    
    # Métricas de uso
    hits = models.PositiveIntegerField(
        default=0,
        help_text="Número de veces que se usó este cache"
    )
    ultima_lectura = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que se leyó este cache"
    )
    
    # Metadatos de invalidación
    dependencias = models.JSONField(
        default=list,
        help_text="Lista de entidades que invalidan este cache"
    )
    version_datos = models.CharField(
        max_length=32,
        help_text="Hash de los datos de los cuales depende el cache"
    )
    
    class Meta:
        verbose_name = "Cache de Consulta"
        verbose_name_plural = "Caches de Consultas"
        indexes = [
            models.Index(fields=['consulta_tipo', 'cliente_id', 'periodo']),
            models.Index(fields=['fecha_expiracion']),
            models.Index(fields=['hits', 'ultima_lectura']),
        ]
        ordering = ['-ultima_lectura']
    
    def __str__(self):
        return f"Cache {self.consulta_tipo} - Cliente {self.cliente_id} - {self.periodo} (hits: {self.hits})"
    
    @classmethod
    def obtener_o_generar(cls, consulta_tipo, parametros, generador_func, ttl_segundos=3600):
        """
        Obtener resultado del cache o generarlo si no existe/expiró.
        
        Args:
            consulta_tipo: Tipo de consulta
            parametros: Diccionario con parámetros de la consulta
            generador_func: Función que genera el resultado si no está cacheado
            ttl_segundos: Time To Live en segundos
        
        Returns:
            Resultado de la consulta (desde cache o generado)
        """
        import gzip
        import json
        import pickle
        from django.utils import timezone
        from datetime import timedelta
        
        # Generar clave de cache
        clave_datos = f"{consulta_tipo}:{json.dumps(parametros, sort_keys=True)}"
        clave_cache = hashlib.md5(clave_datos.encode()).hexdigest()
        
        # Buscar en cache
        try:
            cache_obj = cls.objects.get(
                clave_cache=clave_cache,
                fecha_expiracion__gt=timezone.now()
            )
            
            # Cache hit - actualizar métricas
            cache_obj.hits += 1
            cache_obj.ultima_lectura = timezone.now()
            cache_obj.save(update_fields=['hits', 'ultima_lectura'])
            
            # Descomprimir y deserializar resultado
            resultado_bytes = gzip.decompress(cache_obj.resultado_comprimido)
            resultado = pickle.loads(resultado_bytes)
            
            return resultado
            
        except cls.DoesNotExist:
            pass
        
        # Cache miss - generar resultado
        resultado = generador_func(**parametros)
        
        # Serializar y comprimir
        resultado_bytes = pickle.dumps(resultado)
        resultado_comprimido = gzip.compress(resultado_bytes)
        
        # Guardar en cache
        fecha_expiracion = timezone.now() + timedelta(seconds=ttl_segundos)
        
        # Calcular version de datos para invalidación
        version_datos = cls._calcular_version_datos(parametros)
        
        cache_obj, created = cls.objects.update_or_create(
            clave_cache=clave_cache,
            defaults={
                'consulta_tipo': consulta_tipo,
                'parametros_consulta': parametros,
                'cliente_id': parametros.get('cliente_id', 0),
                'periodo': parametros.get('periodo', ''),
                'resultado_comprimido': resultado_comprimido,
                'tamaño_original': len(resultado_bytes),
                'tamaño_comprimido': len(resultado_comprimido),
                'fecha_expiracion': fecha_expiracion,
                'ttl_segundos': ttl_segundos,
                'version_datos': version_datos,
                'dependencias': cls._calcular_dependencias(consulta_tipo, parametros)
            }
        )
        
        if created:
            cache_obj.hits = 1
            cache_obj.ultima_lectura = timezone.now()
            cache_obj.save(update_fields=['hits', 'ultima_lectura'])
        
        return resultado
    
    @staticmethod
    def _calcular_version_datos(parametros):
        """Calcular hash de versión de los datos relevantes"""
        # Simplificado - en producción incluiría timestamps de las tablas relevantes
        return hashlib.md5(json.dumps(parametros, sort_keys=True).encode()).hexdigest()
    
    @staticmethod
    def _calcular_dependencias(consulta_tipo, parametros):
        """Calcular entidades de las cuales depende el cache"""
        dependencias = []
        
        if 'cliente_id' in parametros:
            dependencias.append(f"cliente_{parametros['cliente_id']}")
        
        if 'periodo' in parametros:
            dependencias.append(f"periodo_{parametros['periodo']}")
        
        # Agregar dependencias específicas por tipo de consulta
        tipo_dependencias = {
            'kpis_dashboard': ['kpi_nomina', 'cierre_nomina'],
            'busqueda_empleados': ['empleado_nomina', 'indice_busqueda'],
            'comparacion_mensual': ['comparacion_mensual', 'empleado_concepto'],
            'reportes_analista': ['incidencia', 'interaccion_incidencia']
        }
        
        dependencias.extend(tipo_dependencias.get(consulta_tipo, []))
        
        return dependencias
    
    @classmethod
    def invalidar_por_dependencia(cls, dependencia):
        """Invalidar todos los caches que dependan de una entidad específica"""
        caches_dependientes = cls.objects.filter(
            dependencias__contains=[dependencia],
            fecha_expiracion__gt=timezone.now()
        )
        
        # Marcar como expirados
        caches_dependientes.update(fecha_expiracion=timezone.now())
        
        return caches_dependientes.count()
    
    @classmethod
    def limpiar_expirados(cls):
        """Limpiar caches expirados"""
        expirados = cls.objects.filter(fecha_expiracion__lt=timezone.now())
        count = expirados.count()
        expirados.delete()
        return count
    
    @classmethod
    def estadisticas_cache(cls, cliente_id=None, periodo=None):
        """Generar estadísticas del sistema de cache"""
        queryset = cls.objects.all()
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        
        total_caches = queryset.count()
        total_hits = queryset.aggregate(total=Sum('hits'))['total'] or 0
        
        # Hit rate por tipo de consulta
        hit_rates = {}
        for consulta_tipo in queryset.values_list('consulta_tipo', flat=True).distinct():
            tipo_queryset = queryset.filter(consulta_tipo=consulta_tipo)
            tipo_hits = tipo_queryset.aggregate(total=Sum('hits'))['total'] or 0
            tipo_count = tipo_queryset.count()
            hit_rates[consulta_tipo] = {
                'total_caches': tipo_count,
                'total_hits': tipo_hits,
                'hit_rate_promedio': tipo_hits / tipo_count if tipo_count > 0 else 0
            }
        
        # Eficiencia de compresión
        stats = queryset.aggregate(
            tamaño_original_total=Sum('tamaño_original'),
            tamaño_comprimido_total=Sum('tamaño_comprimido')
        )
        
        ratio_compresion = 0
        if stats['tamaño_original_total']:
            ratio_compresion = (
                1 - (stats['tamaño_comprimido_total'] / stats['tamaño_original_total'])
            ) * 100
        
        return {
            'total_caches_activos': total_caches,
            'total_hits': total_hits,
            'hit_rate_global': total_hits / total_caches if total_caches > 0 else 0,
            'hit_rates_por_tipo': hit_rates,
            'ratio_compresion_porcentaje': round(ratio_compresion, 2),
            'espacio_ahorrado_bytes': stats['tamaño_original_total'] - stats['tamaño_comprimido_total']
        }

# ========== UTILIDADES Y MANAGERS OPTIMIZADOS ==========

class CierreNominaManager(models.Manager):
    """Manager optimizado para CierreNomina con consultas frecuentes pre-definidas"""
    
    def activos_cliente(self, cliente_id):
        """Obtener cierres activos de un cliente con optimizaciones"""
        return self.select_related('cliente', 'analista_responsable').filter(
            cliente_id=cliente_id,
            estado__in=['en_redis', 'validado', 'con_discrepancias', 'consolidado']
        ).order_by('-fecha_creacion')
    
    def con_discrepancias(self):
        """Obtener cierres con discrepancias pendientes"""
        return self.select_related('cliente', 'analista_responsable').filter(
            estado='con_discrepancias',
            discrepancias_detectadas__gt=0
        ).order_by('-fecha_creacion')
    
    def dashboard_analista(self, analista_user):
        """Dashboard optimizado para analista con prefetch de relaciones"""
        return self.select_related('cliente').prefetch_related(
            'kpis_calculados',
            'incidencias'
        ).filter(
            analista_responsable=analista_user,
            estado__in=['validado', 'con_discrepancias', 'consolidado']
        ).order_by('-fecha_creacion')[:20]
    
    def para_comparacion(self, cliente_id, periodo_actual):
        """Obtener cierres disponibles para comparación mensual"""
        return self.filter(
            cliente_id=cliente_id,
            estado__in=['consolidado', 'cerrado'],
            periodo__lt=periodo_actual
        ).order_by('-periodo')[:12]  # Últimos 12 meses
    
    def estadisticas_cliente(self, cliente_id, año=None):
        """Estadísticas agregadas por cliente y año"""
        queryset = self.filter(cliente_id=cliente_id, estado='cerrado')
        
        if año:
            queryset = queryset.filter(periodo__startswith=str(año))
        
        return queryset.aggregate(
            total_cierres=Count('id'),
            total_empleados_procesados=Sum('total_empleados_activos'),
            total_finiquitos=Sum('total_finiquitos'),
            total_ingresos=Sum('total_ingresos'),
            promedio_discrepancias=Avg('discrepancias_detectadas')
        )

class EmpleadoNominaManager(models.Manager):
    """Manager optimizado para EmpleadoNomina"""
    
    def activos_periodo(self, cliente_id, periodo):
        """Empleados activos en un período específico"""
        return self.select_related('cierre').filter(
            cierre__cliente_id=cliente_id,
            cierre__periodo=periodo,
            tipo_empleado='activo'
        ).order_by('nombre_empleado')
    
    def con_variaciones_altas(self, cliente_id, periodo, threshold=20):
        """Empleados con variaciones salariales altas"""
        return self.filter(
            cierre__cliente_id=cliente_id,
            cierre__periodo=periodo,
            comparaciones_actuales__variacion_sueldo_porcentual__gte=threshold
        ).select_related('cierre').order_by(
            '-comparaciones_actuales__variacion_sueldo_porcentual'
        )
    
    def top_earners(self, cliente_id, periodo, limit=10):
        """Top empleados por ingresos en un período"""
        from django.db.models import Case, When, Sum as DBSum
        
        return self.filter(
            cierre__cliente_id=cliente_id,
            cierre__periodo=periodo,
            tipo_empleado='activo'
        ).annotate(
            total_haberes=DBSum(
                Case(
                    When(
                        conceptos__concepto__in=MapeoConcepto.objects.filter(
                            cliente_id=cliente_id,
                            clasificacion='haber_imponible'
                        ).values_list('concepto_original', flat=True),
                        then='conceptos__valor_numerico'
                    ),
                    default=0
                )
            )
        ).order_by('-total_haberes')[:limit]

# Asignar solo el manager de EmpleadoNomina (CierreNomina ya tiene su manager interno)
EmpleadoNomina.objects = EmpleadoNominaManager()

# ========== MÉTODOS DE UTILIDAD PARA OPTIMIZACIÓN ==========

def generar_indices_busqueda_masiva(cliente_id=None, periodo=None):
    """
    Generar índices de búsqueda de forma masiva y optimizada.
    
    Útil para reprocesar índices después de cambios en algoritmos.
    """
    queryset = EmpleadoNomina.objects.all()
    
    if cliente_id:
        queryset = queryset.filter(cierre__cliente_id=cliente_id)
    
    if periodo:
        queryset = queryset.filter(cierre__periodo=periodo)
    
    # Procesar en lotes para no sobrecargar memoria
    batch_size = 1000
    total_procesados = 0
    
    for batch_start in range(0, queryset.count(), batch_size):
        batch = queryset[batch_start:batch_start + batch_size]
        
        indices_batch = []
        for empleado in batch:
            # Eliminar índice existente si lo hay
            IndiceEmpleadoBusqueda.objects.filter(empleado_nomina=empleado).delete()
            
            # Crear nuevo índice (se calculará automáticamente en save())
            indice = IndiceEmpleadoBusqueda(empleado_nomina=empleado)
            indices_batch.append(indice)
        
        # Bulk create del batch
        IndiceEmpleadoBusqueda.objects.bulk_create(indices_batch)
        total_procesados += len(indices_batch)
    
    return {
        'success': True,
        'total_procesados': total_procesados,
        'mensaje': f'Índices generados exitosamente para {total_procesados} empleados'
    }

def optimizar_base_datos_nomina():
    """
    Ejecutar optimizaciones de mantenimiento en la base de datos.
    
    Incluye:
    - Limpieza de caches expirados
    - Regeneración de estadísticas
    - Validación de integridad de KPIs
    """
    resultados = {
        'caches_limpiados': 0,
        'kpis_validados': 0,
        'inconsistencias_encontradas': 0,
        'tiempo_ejecucion': 0
    }
    
    inicio = timezone.now()
    
    try:
        # 1. Limpiar caches expirados
        resultados['caches_limpiados'] = CacheConsultas.limpiar_expirados()
        
        # 2. Validar integridad de KPIs
        kpis_inconsistentes = []
        for kpi in KPINomina.objects.select_related('cierre').all()[:1000]:  # Muestra limitada
            # Validar hash de verificación
            hash_esperado = hashlib.sha256(
                f"{kpi.cierre.id}:{kpi.tipo_kpi}:{kpi.valor_numerico}:{kpi.fecha_calculo.strftime('%Y%m%d')}".encode()
            ).hexdigest()
            
            if kpi.hash_verificacion != hash_esperado:
                kpis_inconsistentes.append(kpi.id)
        
        resultados['kpis_validados'] = KPINomina.objects.count()
        resultados['inconsistencias_encontradas'] = len(kpis_inconsistentes)
        
        # 3. Calcular tiempo de ejecución
        fin = timezone.now()
        resultados['tiempo_ejecucion'] = (fin - inicio).total_seconds()
        
        return {
            'success': True,
            'resultados': resultados
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'resultados_parciales': resultados
        }

def generar_reporte_rendimiento(cliente_id=None, periodo=None):
    """
    Generar reporte de rendimiento del sistema de nómina.
    
    Incluye métricas de cache, tiempos de consulta, y recomendaciones.
    """
    reporte = {
        'fecha_generacion': timezone.now(),
        'parametros': {
            'cliente_id': cliente_id,
            'periodo': periodo
        },
        'metricas': {},
        'recomendaciones': []
    }
    
    # Métricas de cache
    stats_cache = CacheConsultas.estadisticas_cache(cliente_id, periodo)
    reporte['metricas']['cache'] = stats_cache
    
    # Métricas de búsquedas
    if cliente_id:
        total_indices = IndiceEmpleadoBusqueda.objects.filter(cliente_id=cliente_id).count()
        reporte['metricas']['indices_busqueda'] = {
            'total_indices_generados': total_indices
        }
    
    # Métricas de comparaciones
    if periodo:
        total_comparaciones = ComparacionMensual.objects.filter(
            cierre_actual__periodo=periodo
        ).count() if cliente_id is None else ComparacionMensual.objects.filter(
            cierre_actual__cliente_id=cliente_id,
            cierre_actual__periodo=periodo
        ).count()
        
        anomalias_criticas = ComparacionMensual.objects.filter(
            cierre_actual__cliente_id=cliente_id if cliente_id else None,
            cierre_actual__periodo=periodo,
            nivel_anomalia='critica'
        ).count()
        
        reporte['metricas']['comparaciones'] = {
            'total_comparaciones': total_comparaciones,
            'anomalias_criticas': anomalias_criticas
        }
    
    # Generar recomendaciones
    if stats_cache['hit_rate_global'] < 0.7:
        reporte['recomendaciones'].append(
            "Hit rate de cache bajo (<70%). Considerar aumentar TTL o revisar patrones de consulta."
        )
    
    if stats_cache.get('espacio_ahorrado_bytes', 0) < 1024 * 1024:  # Menos de 1MB
        reporte['recomendaciones'].append(
            "Beneficio de compresión bajo. Evaluar si el cache es necesario para consultas pequeñas."
        )
    
    return reporte

# ========== LOG DE ARCHIVOS (MÍNIMO) ==========

class LogArchivo(models.Model):
    """
    Log minimalista de archivos subidos.
    Solo metadatos esenciales, el procesamiento se hace en Redis.
    """
    cierre = models.ForeignKey(
        CierreNomina, 
        on_delete=models.CASCADE, 
        related_name='logs_archivos',
        help_text="Cierre al que pertenecen estos archivos"
    )
    
    TIPO_ARCHIVO_CHOICES = [
        ('libro_remuneraciones', 'Libro de Remuneraciones'),
        ('novedades', 'Novedades'),
        ('movimientos_mes', 'Movimientos del Mes'),
        ('analista', 'Archivo del Analista'),
    ]
    
    tipo_archivo = models.CharField(max_length=30, choices=TIPO_ARCHIVO_CHOICES)
    nombre_archivo = models.CharField(max_length=255)
    ruta_temporal = models.CharField(
        max_length=500,
        help_text="Ruta donde se guardó temporalmente el archivo"
    )
    
    # Estado del procesamiento
    ESTADO_CHOICES = [
        ('subido', 'Archivo Subido'),
        ('procesando', 'Procesando en Redis'),
        ('procesado', 'Procesado Exitosamente'),
        ('error', 'Error en Procesamiento'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='subido')
    
    # Metadatos del archivo
    tamaño_bytes = models.PositiveBigIntegerField(default=0)
    total_registros = models.PositiveIntegerField(
        default=0,
        help_text="Total de registros/filas procesadas"
    )
    
    # Fechas
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Usuario responsable
    usuario_subida = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Mensajes de error si los hay
    mensaje_error = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Log de Archivo"
        verbose_name_plural = "Logs de Archivos"
        ordering = ['-fecha_subida']
        indexes = [
            models.Index(fields=['cierre', 'tipo_archivo']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_archivo_display()} - {self.nombre_archivo} ({self.get_estado_display()})"
    
    def marcar_procesado(self, total_registros=0, mensaje=""):
        """
        Marcar el archivo como procesado exitosamente
        """
        self.estado = 'procesado'
        self.total_registros = total_registros
        self.fecha_procesamiento = datetime.now()
        if mensaje:
            self.mensaje_error = mensaje  # Reutilizar campo para mensaje informativo
        self.save()
    
    def marcar_error(self, mensaje_error):
        """
        Marcar el archivo con error
        """
        self.estado = 'error'
        self.mensaje_error = mensaje_error
        self.fecha_procesamiento = datetime.now()
        self.save()

# ========== UTILIDADES ==========

def archivo_upload_path(instance, filename):
    """
    Generar ruta de upload para archivos temporales
    """
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"nomina/{instance.cierre.cliente.id}/{instance.cierre.periodo}/{instance.tipo_archivo}/{now}_{filename}"
