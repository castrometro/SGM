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
