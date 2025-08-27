# backend/payroll/models/models_staging.py
# Modelos de staging con estructura EAV para el procesamiento de archivos de payroll

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
import re

from .models_fase_1 import ArchivoSubido


class ListaEmpleados_stg(models.Model):
    """
    Entidad 1: Lista de empleados extraídos de los archivos Excel.
    Almacena únicamente la información básica de identificación del empleado.
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='lista_empleados'
    )
    
    # Datos básicos del empleado (estructura fija)
    rut_trabajador = models.CharField(max_length=12)  # RUT limpio: 12345678-9
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True)
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField()
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Lista de Empleados Staging"
        verbose_name_plural = "Listas de Empleados Staging"
        unique_together = ['archivo_subido', 'rut_trabajador']
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut_trabajador']),
            models.Index(fields=['fila_excel']),
        ]
    
    def __str__(self):
        return f"{self.rut_trabajador} - {self.nombre} {self.apellido_paterno}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        nombres = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)


class ItemsRemuneraciones_stg(models.Model):
    """
    Entidad 2: Headers/Conceptos de remuneración extraídos del Excel.
    Representa las columnas del Excel (Sueldo Base, Gratificación, Descuentos, etc.)
    """
    
    TIPOS_CONCEPTO = [
        ('haber', 'Haber'),
        ('descuento', 'Descuento'),
        ('informativo', 'Informativo'),
        ('total', 'Total'),
    ]
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='items_remuneraciones'
    )
    
    # Identificación en el Excel
    codigo_columna = models.CharField(max_length=10)  # "A", "B", "C", etc.
    nombre_concepto = models.CharField(max_length=200)  # Como viene del header
    nombre_normalizado = models.CharField(max_length=200, blank=True)  # Procesado
    
    # Clasificación del concepto
    tipo_concepto = models.CharField(max_length=15, choices=TIPOS_CONCEPTO, blank=True, null=True)
    
    # Orden y ubicación en el Excel
    orden = models.IntegerField()
    fila_header = models.IntegerField(default=1)
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Items de Remuneraciones Staging"
        verbose_name_plural = "Items de Remuneraciones Staging"
        unique_together = ['archivo_subido', 'codigo_columna']
        ordering = ['orden']
        indexes = [
            models.Index(fields=['archivo_subido', 'tipo_concepto']),
            models.Index(fields=['orden']),
            models.Index(fields=['codigo_columna']),
        ]
    
    def __str__(self):
        return f"[{self.codigo_columna}] {self.nombre_concepto}"


class ValorItemEmpleado_stg(models.Model):
    """
    Entidad 3: Valores de la matriz Empleado x Concepto.
    Almacena todos los valores que NO son información básica del empleado.
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='valores_items_empleados'
    )
    
    # Relaciones con las otras entidades
    empleado = models.ForeignKey(
        ListaEmpleados_stg,
        on_delete=models.CASCADE,
        related_name='valores_remuneracion'
    )
    item_remuneracion = models.ForeignKey(
        ItemsRemuneraciones_stg,
        on_delete=models.CASCADE,
        related_name='valores_empleados'
    )
    
    # Valor como viene del Excel
    valor_original = models.CharField(max_length=200)  # Valor tal como viene del Excel
    
    # Valor procesado
    valor_numerico = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    valor_texto = models.CharField(max_length=200, blank=True)  # Para valores no numéricos
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField()
    columna_excel = models.CharField(max_length=10)
    
    # Indicadores básicos
    es_numerico = models.BooleanField(default=False)
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Valor Item Empleado Staging"
        verbose_name_plural = "Valores Items Empleados Staging"
        unique_together = ['empleado', 'item_remuneracion']
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['empleado', 'item_remuneracion']),
            models.Index(fields=['fila_excel', 'columna_excel']),
            models.Index(fields=['es_numerico']),
        ]
    
    def __str__(self):
        return f"{self.empleado.rut_trabajador} - {self.item_remuneracion.nombre_concepto}: {self.valor_original}"


# Funciones de utilidad
def limpiar_staging_por_archivo(archivo_subido):
    """
    Limpia todos los datos staging de un archivo específico
    """
    ListaEmpleados_stg.objects.filter(archivo_subido=archivo_subido).delete()
    ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo_subido).delete()
    ValorItemEmpleado_stg.objects.filter(archivo_subido=archivo_subido).delete()


def obtener_resumen_staging(archivo_subido):
    """
    Obtiene un resumen del estado del staging para un archivo
    """
    empleados = ListaEmpleados_stg.objects.filter(archivo_subido=archivo_subido)
    items = ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo_subido)
    valores = ValorItemEmpleado_stg.objects.filter(archivo_subido=archivo_subido)
    
    return {
        'empleados': {
            'total': empleados.count(),
        },
        'items': {
            'total': items.count(),
            'haberes': items.filter(tipo_concepto='haber').count(),
            'descuentos': items.filter(tipo_concepto='descuento').count(),
            'informativos': items.filter(tipo_concepto='informativo').count(),
            'totales': items.filter(tipo_concepto='total').count(),
        },
        'valores': {
            'total': valores.count(),
            'numericos': valores.filter(es_numerico=True).count(),
            'texto': valores.filter(es_numerico=False).count(),
        }
    }


# =============================================================================
# MODELOS STAGING PARA MOVIMIENTOS DEL MES
# =============================================================================

class Ausencias_stg(models.Model):
    """
    Staging para ausencias de empleados extraídas de archivos Excel.
    Estructura: Nombre, Rut, Empresa, Cargo, Centro de Costo, Sucursal, 
                Fecha Inicio Ausencia, Fecha Fin Ausencia, Dias, Tipo de Ausentismo, Motivo, Observaciones
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='ausencias_staging'
    )
    
    # Datos del Excel (estructura exacta)
    nombre = models.CharField(max_length=200)  # Columna: Nombre
    rut = models.CharField(max_length=12)  # Columna: Rut
    empresa = models.CharField(max_length=100, blank=True)  # Columna: Empresa
    cargo = models.CharField(max_length=100, blank=True)  # Columna: Cargo
    centro_de_costo = models.CharField(max_length=100, blank=True)  # Columna: Centro de Costo
    sucursal = models.CharField(max_length=100, blank=True)  # Columna: Sucursal
    fecha_inicio_ausencia = models.DateField(null=True, blank=True)  # Columna: Fecha Inicio Ausencia
    fecha_fin_ausencia = models.DateField(null=True, blank=True)  # Columna: Fecha Fin Ausencia
    dias = models.IntegerField(null=True, blank=True)  # Columna: Dias
    tipo_de_ausentismo = models.CharField(max_length=100, blank=True)  # Columna: Tipo de Ausentismo
    motivo = models.CharField(max_length=200, blank=True)  # Columna: Motivo
    observaciones = models.TextField(blank=True)  # Columna: Observaciones
    
    # Datos raw del Excel (para debugging)
    fecha_inicio_ausencia_raw = models.CharField(max_length=50, blank=True)  # Texto original
    fecha_fin_ausencia_raw = models.CharField(max_length=50, blank=True)  # Texto original
    dias_raw = models.CharField(max_length=50, blank=True)  # Texto original
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField()
    
    # Validaciones y errores
    tiene_errores = models.BooleanField(default=False)
    errores_detectados = models.JSONField(default=list, blank=True)
    observaciones_procesamiento = models.TextField(blank=True)  # Para distinguir de observaciones del Excel
    
    # Metadatos
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ausencia Staging"
        verbose_name_plural = "Ausencias Staging"
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut']),
            models.Index(fields=['fecha_inicio_ausencia']),
            models.Index(fields=['tipo_de_ausentismo']),
            models.Index(fields=['empresa']),
            models.Index(fields=['centro_de_costo']),
            models.Index(fields=['fila_excel']),
        ]
    
    def __str__(self):
        return f"Ausencia {self.rut} - {self.tipo_de_ausentismo} (Fila {self.fila_excel})"


class AltasBajas_stg(models.Model):
    """
    Staging para altas y bajas de empleados extraídas de archivos Excel.
    Estructura: Nombre, Rut, Empresa, Cargo, Centro de Costo, Sucursal, 
                Fecha Ingreso, Fecha Retiro, Tipo Contrato, Dias Trabajados, Sueldo Base, Alta / Baja, Motivo
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='altas_bajas_staging'
    )
    
    # Datos del Excel (estructura exacta)
    nombre = models.CharField(max_length=200)  # Columna: Nombre
    rut = models.CharField(max_length=12)  # Columna: Rut
    empresa = models.CharField(max_length=100, blank=True)  # Columna: Empresa
    cargo = models.CharField(max_length=100, blank=True)  # Columna: Cargo
    centro_de_costo = models.CharField(max_length=100, blank=True)  # Columna: Centro de Costo
    sucursal = models.CharField(max_length=100, blank=True)  # Columna: Sucursal
    fecha_ingreso = models.DateField(null=True, blank=True)  # Columna: Fecha Ingreso
    fecha_retiro = models.DateField(null=True, blank=True)  # Columna: Fecha Retiro
    tipo_contrato = models.CharField(max_length=100, blank=True)  # Columna: Tipo Contrato
    dias_trabajados = models.IntegerField(null=True, blank=True)  # Columna: Dias Trabajados
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Columna: Sueldo Base
    alta_baja = models.CharField(max_length=20, blank=True)  # Columna: Alta / Baja
    motivo = models.CharField(max_length=200, blank=True)  # Columna: Motivo
    
    # Datos raw del Excel (para debugging)
    fecha_ingreso_raw = models.CharField(max_length=50, blank=True)  # Texto original
    fecha_retiro_raw = models.CharField(max_length=50, blank=True)  # Texto original
    dias_trabajados_raw = models.CharField(max_length=50, blank=True)  # Texto original
    sueldo_base_raw = models.CharField(max_length=50, blank=True)  # Texto original
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField()
    
    # Validaciones y errores
    tiene_errores = models.BooleanField(default=False)
    errores_detectados = models.JSONField(default=list, blank=True)
    observaciones_procesamiento = models.TextField(blank=True)
    
    # Metadatos
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Alta/Baja Staging"
        verbose_name_plural = "Altas/Bajas Staging"
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['fecha_retiro']),
            models.Index(fields=['alta_baja']),
            models.Index(fields=['empresa']),
            models.Index(fields=['centro_de_costo']),
            models.Index(fields=['fila_excel']),
        ]
    
    def __str__(self):
        return f"{self.alta_baja} {self.rut} - {self.cargo} (Fila {self.fila_excel})"
    
    @property
    def es_alta(self):
        """Determina si es un alta (ingreso)"""
        return self.alta_baja and 'alta' in self.alta_baja.lower()
    
    @property
    def es_baja(self):
        """Determina si es una baja (finiquito)"""
        return self.alta_baja and 'baja' in self.alta_baja.lower()


# ==============================================
# MODELOS STAGING PARA ARCHIVOS DEL ANALISTA
# ==============================================

class Finiquitos_analista_stg(models.Model):
    """
    Staging para el archivo de Finiquitos del Analista.
    Estructura: Rut, Nombre, Fecha Retiro, Motivo
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='finiquitos_analista'
    )
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField(help_text="Número de fila en el Excel")
    
    # Datos del empleado
    rut = models.CharField(max_length=12, help_text="RUT del empleado")
    nombre = models.CharField(max_length=200, help_text="Nombre completo del empleado")
    
    # Datos del finiquito
    fecha_retiro = models.DateField(null=True, blank=True, help_text="Fecha de retiro")
    motivo = models.CharField(max_length=500, blank=True, help_text="Motivo del finiquito")
    
    # Metadatos
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Finiquito Analista Staging"
        verbose_name_plural = "Finiquitos Analista Staging"
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut']),
            models.Index(fields=['fecha_retiro']),
        ]
    
    def __str__(self):
        return f"Finiquito {self.rut} - {self.nombre} ({self.fecha_retiro})"


class Ausentismos_analista_stg(models.Model):
    """
    Staging para el archivo de Ausentismos del Analista.
    Estructura: Rut, Nombre, Fecha Inicio Ausencia, Fecha Fin Ausencia, Dias, Tipo de Ausentismo
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='ausentismos_analista'
    )
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField(help_text="Número de fila en el Excel")
    
    # Datos del empleado
    rut = models.CharField(max_length=12, help_text="RUT del empleado")
    nombre = models.CharField(max_length=200, help_text="Nombre completo del empleado")
    
    # Datos de la ausencia
    fecha_inicio_ausencia = models.DateField(null=True, blank=True, help_text="Fecha de inicio de la ausencia")
    fecha_fin_ausencia = models.DateField(null=True, blank=True, help_text="Fecha de fin de la ausencia")
    dias = models.IntegerField(null=True, blank=True, help_text="Cantidad de días de ausencia")
    tipo_ausentismo = models.CharField(max_length=200, blank=True, help_text="Tipo de ausentismo")
    
    # Metadatos
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ausentismo Analista Staging"
        verbose_name_plural = "Ausentismos Analista Staging"
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut']),
            models.Index(fields=['fecha_inicio_ausencia']),
            models.Index(fields=['tipo_ausentismo']),
        ]
    
    def __str__(self):
        return f"Ausencia {self.rut} - {self.nombre} ({self.fecha_inicio_ausencia})"
    
    @property
    def duracion_calculada(self):
        """Calcula la duración en días si ambas fechas están disponibles"""
        if self.fecha_inicio_ausencia and self.fecha_fin_ausencia:
            return (self.fecha_fin_ausencia - self.fecha_inicio_ausencia).days + 1
        return self.dias


class Ingresos_analista_stg(models.Model):
    """
    Staging para el archivo de Ingresos del Analista.
    Estructura: Rut, Nombre, Fecha Ingreso
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='ingresos_analista'
    )
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField(help_text="Número de fila en el Excel")
    
    # Datos del empleado
    rut = models.CharField(max_length=12, help_text="RUT del empleado")
    nombre = models.CharField(max_length=200, help_text="Nombre completo del empleado")
    
    # Datos del ingreso
    fecha_ingreso = models.DateField(null=True, blank=True, help_text="Fecha de ingreso")
    
    # Metadatos
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ingreso Analista Staging"
        verbose_name_plural = "Ingresos Analista Staging"
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut']),
            models.Index(fields=['fecha_ingreso']),
        ]
    
    def __str__(self):
        return f"Ingreso {self.rut} - {self.nombre} ({self.fecha_ingreso})"


# =============================================================================
# MODELOS STAGING PARA NOVEDADES DEL ANALISTA
# =============================================================================

class Empleados_Novedades_stg(models.Model):
    """
    Entidad 1: Lista de empleados extraídos de archivos de novedades del analista.
    Almacena únicamente la información básica de identificación del empleado.
    Formato: RUT | Nombre | Apellido Paterno | Apellido Materno
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='empleados_novedades'
    )
    
    # Datos básicos del empleado (estructura fija)
    rut_trabajador = models.CharField(max_length=12, help_text="RUT limpio: 12345678-9")
    nombre = models.CharField(max_length=100, help_text="Nombre del empleado")
    apellido_paterno = models.CharField(max_length=100, help_text="Apellido paterno")
    apellido_materno = models.CharField(max_length=100, blank=True, help_text="Apellido materno")
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField(help_text="Número de fila en el Excel")
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Empleado Novedades Staging"
        verbose_name_plural = "Empleados Novedades Staging"
        unique_together = ['archivo_subido', 'rut_trabajador']
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['rut_trabajador']),
            models.Index(fields=['fila_excel']),
        ]
    
    def __str__(self):
        return f"{self.rut_trabajador} - {self.nombre} {self.apellido_paterno}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado"""
        nombres = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)


class Items_Novedades_stg(models.Model):
    """
    Entidad 2: Headers/Conceptos de novedades extraídos del Excel del analista.
    Representa las columnas del Excel después de los datos básicos del empleado.
    """
    
    TIPOS_CONCEPTO = [
        ('haber', 'Haber'),
        ('descuento', 'Descuento'),
        ('informativo', 'Informativo'),
        ('total', 'Total'),
        ('novedad', 'Novedad'),
    ]
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='items_novedades'
    )
    
    # Identificación en el Excel
    codigo_columna = models.CharField(max_length=10, help_text="Letra de columna: A, B, C, etc.")
    nombre_concepto = models.CharField(max_length=200, help_text="Como viene del header")
    nombre_normalizado = models.CharField(max_length=200, blank=True, help_text="Nombre procesado")
    
    # Clasificación del concepto
    tipo_concepto = models.CharField(max_length=15, choices=TIPOS_CONCEPTO, blank=True, null=True)
    
    # Orden y ubicación en el Excel
    orden = models.IntegerField(help_text="Orden de aparición en el Excel")
    fila_header = models.IntegerField(default=1, help_text="Fila donde está el header")
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Item Novedades Staging"
        verbose_name_plural = "Items Novedades Staging"
        unique_together = ['archivo_subido', 'codigo_columna']
        ordering = ['orden']
        indexes = [
            models.Index(fields=['archivo_subido', 'tipo_concepto']),
            models.Index(fields=['orden']),
            models.Index(fields=['codigo_columna']),
        ]
    
    def __str__(self):
        return f"[{self.codigo_columna}] {self.nombre_concepto}"


class Valores_item_empleado_analista_stg(models.Model):
    """
    Entidad 3: Valores de la matriz Empleado x Concepto para novedades del analista.
    Almacena todos los valores que NO son información básica del empleado.
    """
    
    # Relación con el archivo origen
    archivo_subido = models.ForeignKey(
        ArchivoSubido, 
        on_delete=models.CASCADE,
        related_name='valores_novedades_analista'
    )
    
    # Relaciones con las otras entidades
    empleado = models.ForeignKey(
        Empleados_Novedades_stg,
        on_delete=models.CASCADE,
        related_name='valores_novedades'
    )
    item_novedad = models.ForeignKey(
        Items_Novedades_stg,
        on_delete=models.CASCADE,
        related_name='valores_empleados'
    )
    
    # Valor como viene del Excel
    valor_original = models.CharField(max_length=200, help_text="Valor tal como viene del Excel")
    
    # Valor procesado
    valor_numerico = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Valor numérico convertido"
    )
    valor_texto = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Para valores no numéricos"
    )
    
    # Trazabilidad en el Excel
    fila_excel = models.IntegerField(help_text="Número de fila en el Excel")
    columna_excel = models.CharField(max_length=10, help_text="Letra de columna")
    
    # Indicadores básicos
    es_numerico = models.BooleanField(default=False)
    
    # Metadatos adicionales
    observaciones = models.TextField(blank=True)
    
    # Fechas
    fecha_extraccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Valor Item Empleado Analista Staging"
        verbose_name_plural = "Valores Items Empleados Analista Staging"
        unique_together = ['empleado', 'item_novedad']
        indexes = [
            models.Index(fields=['archivo_subido']),
            models.Index(fields=['empleado', 'item_novedad']),
            models.Index(fields=['fila_excel', 'columna_excel']),
            models.Index(fields=['es_numerico']),
        ]
    
    def __str__(self):
        return f"{self.empleado.rut_trabajador} - {self.item_novedad.nombre_concepto}: {self.valor_original}"


# Funciones de utilidad para novedades del analista
def limpiar_novedades_analista_por_archivo(archivo_subido):
    """
    Limpia todos los datos staging de novedades del analista de un archivo específico
    """
    Empleados_Novedades_stg.objects.filter(archivo_subido=archivo_subido).delete()
    Items_Novedades_stg.objects.filter(archivo_subido=archivo_subido).delete()
    Valores_item_empleado_analista_stg.objects.filter(archivo_subido=archivo_subido).delete()


def obtener_resumen_novedades_analista(archivo_subido):
    """
    Obtiene un resumen del estado del staging para un archivo de novedades del analista
    """
    empleados = Empleados_Novedades_stg.objects.filter(archivo_subido=archivo_subido)
    items = Items_Novedades_stg.objects.filter(archivo_subido=archivo_subido)
    valores = Valores_item_empleado_analista_stg.objects.filter(archivo_subido=archivo_subido)
    
    return {
        'empleados': {
            'total': empleados.count(),
        },
        'items': {
            'total': items.count(),
            'haberes': items.filter(tipo_concepto='haber').count(),
            'descuentos': items.filter(tipo_concepto='descuento').count(),
            'informativos': items.filter(tipo_concepto='informativo').count(),
            'novedades': items.filter(tipo_concepto='novedad').count(),
        },
        'valores': {
            'total': valores.count(),
            'numericos': valores.filter(es_numerico=True).count(),
            'texto': valores.filter(es_numerico=False).count(),
        }
    }
