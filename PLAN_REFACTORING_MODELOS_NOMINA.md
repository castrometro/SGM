# 🔧 Plan de Refactoring: Modelos de Nómina

## Índice
1. [Diagnóstico Actual](#diagnóstico-actual)
2. [Objetivos del Refactoring](#objetivos-del-refactoring)
3. [Arquitectura Propuesta](#arquitectura-propuesta)
4. [Plan de Ejecución](#plan-de-ejecución)
5. [Ejemplos de Implementación](#ejemplos-de-implementación)
6. [Estrategia de Migración](#estrategia-de-migración)
7. [Métricas de Éxito](#métricas-de-éxito)

---

## Diagnóstico Actual

### 🚨 Problemas Identificados

#### 1. **Archivo Monolítico**
- `models.py` con 1330+ líneas
- 32 modelos mezclados sin separación lógica
- Difícil navegación y mantenimiento

#### 2. **Duplicación de Código**
```python
# Patrón repetido en múltiples modelos:
class MovimientoAltaBaja(models.Model):
    cierre = models.ForeignKey(CierreNomina, ...)
    empleado = models.ForeignKey(EmpleadoCierre, ...)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)

class MovimientoAusentismo(models.Model):
    # Los mismos campos básicos se repiten...
    cierre = models.ForeignKey(CierreNomina, ...)
    empleado = models.ForeignKey(EmpleadoCierre, ...)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    # etc...
```

#### 3. **Inconsistencias de Diseño**
- Algunos modelos usan `upload_to` functions, otros no
- Patrones diferentes para campos similares
- Estados definidos de manera inconsistente

#### 4. **Relaciones Subóptimas**
- Falta de `related_name` consistentes
- Índices no optimizados para consultas comunes
- Campos desnormalizados innecesariamente

#### 5. **Falta de Abstracción**
- No hay modelos base para funcionalidades comunes
- Lógica de negocio mezclada con definición de modelos
- Validaciones inconsistentes

---

## Objetivos del Refactoring

### 🎯 Metas Principales

1. **Modularidad**: Separar modelos por dominio funcional
2. **DRY (Don't Repeat Yourself)**: Eliminar duplicación de código
3. **Consistencia**: Estandarizar patrones y convenciones
4. **Performance**: Optimizar consultas y índices
5. **Mantenibilidad**: Código más limpio y documentado
6. **Escalabilidad**: Estructura preparada para crecimiento

### 📊 Métricas Objetivo
- Reducir líneas de código en 30%
- Eliminar 80% de duplicación
- Mejorar tiempo de consultas en 25%
- Aumentar cobertura de tests a 90%

---

## Arquitectura Propuesta

### 📁 Nueva Estructura de Archivos

```
nomina/
├── models/
│   ├── __init__.py              # Importaciones centralizadas
│   ├── base.py                  # Modelos base y mixins
│   ├── core.py                  # CierreNomina, EmpleadoCierre
│   ├── conceptos.py             # ConceptoRemuneracion y relacionados
│   ├── archivos.py              # Modelos de upload de archivos
│   ├── movimientos.py           # Movimientos de personal
│   ├── incidencias.py           # Sistema de incidencias
│   ├── verificacion.py          # Sistema de discrepancias
│   ├── analisis.py              # Análisis de datos
│   ├── consolidacion.py         # Modelos consolidados
│   └── logging.py               # Logging y auditoría
├── managers.py                  # Custom managers
├── querysets.py                 # Custom querysets
├── validators.py                # Validadores personalizados
└── enums.py                     # Constantes y enums
```

### 🧩 Modelos Base Propuestos

#### 1. **BaseTimeStampedModel**
```python
# models/base.py
from django.db import models
from django.utils import timezone

class BaseTimeStampedModel(models.Model):
    """Modelo base con timestamps automáticos"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

#### 2. **BaseCierreRelatedModel**
```python
class BaseCierreRelatedModel(BaseTimeStampedModel):
    """Modelo base para entidades relacionadas con cierre"""
    cierre = models.ForeignKey(
        'CierreNomina', 
        on_delete=models.CASCADE,
        related_name='%(class)ss'  # Auto-genera related_name
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['cierre', 'created_at']),
        ]
```

#### 3. **BaseEmpleadoMovimientoModel**
```python
class BaseEmpleadoMovimientoModel(BaseCierreRelatedModel):
    """Modelo base para movimientos de empleados"""
    empleado = models.ForeignKey(
        'EmpleadoCierre', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
    )
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, db_index=True)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['cierre', 'rut']),
            models.Index(fields=['rut']),
        ]
    
    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos}"
```

#### 4. **BaseUploadModel**
```python
class BaseUploadModel(BaseCierreRelatedModel):
    """Modelo base para uploads de archivos"""
    archivo = models.FileField(upload_to='uploads/nomina/%Y/%m/')
    estado = models.CharField(max_length=30, choices=EstadosUpload.choices)
    upload_log = models.ForeignKey(
        'UploadLogNomina',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        abstract = True
        
    def get_estado_display_color(self):
        """Retorna color CSS basado en el estado"""
        color_map = {
            'pendiente': 'warning',
            'procesado': 'success',
            'con_error': 'danger',
        }
        return color_map.get(self.estado, 'secondary')
```

### 🔧 Managers y QuerySets Personalizados

#### 1. **CierreNominaQuerySet**
```python
# querysets.py
from django.db import models

class CierreNominaQuerySet(models.QuerySet):
    def activos(self):
        return self.exclude(estado='finalizado')
    
    def por_cliente(self, cliente_id):
        return self.filter(cliente_id=cliente_id)
    
    def con_incidencias_pendientes(self):
        return self.filter(
            estado_incidencias__in=['detectadas', 'en_revision']
        )
    
    def listos_para_consolidar(self):
        return self.filter(
            estado='verificado_sin_discrepancias',
            puede_consolidar=True
        )

class CierreNominaManager(models.Manager):
    def get_queryset(self):
        return CierreNominaQuerySet(self.model, using=self._db)
    
    def activos(self):
        return self.get_queryset().activos()
    
    def por_cliente(self, cliente_id):
        return self.get_queryset().por_cliente(cliente_id)
```

#### 2. **EmpleadoCierreQuerySet**
```python
class EmpleadoCierreQuerySet(models.QuerySet):
    def con_registros_conceptos(self):
        return self.prefetch_related('registroconceptoempleado_set')
    
    def por_rut(self, rut):
        return self.filter(rut=rut)
    
    def activos_en_periodo(self, cierre_id):
        return self.filter(
            cierre_id=cierre_id
        ).exclude(
            # Empleados con finiquito en el periodo
            cierre__analistafiniquito__rut=models.F('rut')
        )
```

### 📋 Enums y Constantes

```python
# enums.py
from django.db import models

class EstadosCierre(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    CARGANDO_ARCHIVOS = 'cargando_archivos', 'Cargando Archivos'
    ARCHIVOS_COMPLETOS = 'archivos_completos', 'Archivos Completos'
    VERIFICACION_DATOS = 'verificacion_datos', 'Verificación de Datos'
    CON_DISCREPANCIAS = 'con_discrepancias', 'Con Discrepancias'
    VERIFICADO_SIN_DISCREPANCIAS = 'verificado_sin_discrepancias', 'Verificado Sin Discrepancias'
    DATOS_CONSOLIDADOS = 'datos_consolidados', 'Datos Consolidados'
    CON_INCIDENCIAS = 'con_incidencias', 'Con Incidencias'
    INCIDENCIAS_RESUELTAS = 'incidencias_resueltas', 'Incidencias Resueltas'
    VALIDACION_FINAL = 'validacion_final', 'Validación Final'
    FINALIZADO = 'finalizado', 'Finalizado'
    REQUIERE_RECARGA_ARCHIVOS = 'requiere_recarga_archivos', 'Requiere Recarga de Archivos'

class EstadosUpload(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    PROCESANDO = 'procesando', 'Procesando'
    ANALIZANDO_HDRS = 'analizando_hdrs', 'Analizando Headers'
    HDRS_ANALIZADOS = 'hdrs_analizados', 'Headers Analizados'
    CLASIF_EN_PROCESO = 'clasif_en_proceso', 'Clasificación en Proceso'
    CLASIF_PENDIENTE = 'clasif_pendiente', 'Clasificación Pendiente'
    CLASIFICADO = 'clasificado', 'Clasificado'
    PROCESADO = 'procesado', 'Procesado'
    CON_ERROR = 'con_error', 'Con Error'
    CON_ERRORES_PARCIALES = 'con_errores_parciales', 'Con Errores Parciales'

class ClasificacionConcepto(models.TextChoices):
    HABERES_IMPONIBLES = 'haberes_imponibles', 'Haberes Imponibles'
    HABERES_NO_IMPONIBLES = 'haberes_no_imponibles', 'Haberes No Imponibles'
    HORAS_EXTRAS = 'horas_extras', 'Horas Extras'
    DESCUENTOS_LEGALES = 'descuentos_legales', 'Descuentos Legales'
    OTROS_DESCUENTOS = 'otros_descuentos', 'Otros Descuentos'
    APORTES_PATRONALES = 'aportes_patronales', 'Aportes Patronales'
    INFORMACION_ADICIONAL = 'informacion_adicional', 'Información Adicional (No Monto)'
    IMPUESTOS = 'impuestos', 'Impuestos'
```

---

## Plan de Ejecución

### 📅 Fase 1: Preparación y Análisis (Semana 1-2)

#### Objetivos:
- Crear estructura de archivos
- Implementar modelos base
- Preparar herramientas de migración

#### Tareas:
1. **Crear nueva estructura de carpetas**
   ```bash
   mkdir nomina/models
   touch nomina/models/__init__.py
   touch nomina/models/base.py
   # etc...
   ```

2. **Implementar modelos base abstractos**
   - `BaseTimeStampedModel`
   - `BaseCierreRelatedModel`
   - `BaseEmpleadoMovimientoModel`
   - `BaseUploadModel`

3. **Crear managers y querysets básicos**
   - `CierreNominaManager`
   - `EmpleadoCierreManager`

4. **Definir enums y constantes**
   - Migrar choices a TextChoices
   - Centralizar constantes

#### Entregables:
- [ ] Estructura de carpetas creada
- [ ] Modelos base implementados
- [ ] Enums definidos
- [ ] Tests básicos para modelos base

---

### 📅 Fase 2: Migración Modular (Semana 3-6)

#### Objetivos:
- Migrar modelos por módulos
- Mantener funcionalidad existente
- Aplicar nuevos patrones

#### Tareas por Módulo:

##### **Módulo 1: Core (Semana 3)**
```python
# models/core.py
from .base import BaseCierreRelatedModel, BaseTimeStampedModel
from .enums import EstadosCierre

class CierreNomina(BaseTimeStampedModel):
    # Migrar y mejorar modelo actual
    estado = models.CharField(max_length=40, choices=EstadosCierre.choices)
    
    # Aplicar manager personalizado
    objects = CierreNominaManager()
    
    # Mejorar métodos existentes
    def puede_consolidar(self):
        return (
            self.estado == EstadosCierre.VERIFICADO_SIN_DISCREPANCIAS and
            self.discrepancias.count() == 0
        )
```

##### **Módulo 2: Archivos (Semana 3-4)**
```python
# models/archivos.py
from .base import BaseUploadModel

class LibroRemuneracionesUpload(BaseUploadModel):
    # Heredar campos comunes de BaseUploadModel
    header_json = models.JSONField(default=list)
    
    class Meta:
        verbose_name = "Libro de Remuneraciones"
        verbose_name_plural = "Libros de Remuneraciones"
    
    def save(self, *args, **kwargs):
        if not self.archivo.name:
            raise ValidationError("Archivo requerido")
        super().save(*args, **kwargs)
```

##### **Módulo 3: Movimientos (Semana 4-5)**
```python
# models/movimientos.py
from .base import BaseEmpleadoMovimientoModel

class MovimientoAltaBaja(BaseEmpleadoMovimientoModel):
    # Solo campos específicos, heredar los comunes
    fecha_ingreso = models.DateField()
    fecha_retiro = models.DateField(null=True, blank=True)
    alta_o_baja = models.CharField(
        max_length=20,
        choices=[('ALTA', 'Alta'), ('BAJA', 'Baja')]
    )
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = "Movimiento Alta/Baja"
        verbose_name_plural = "Movimientos Altas/Bajas"
```

#### Estrategia de Migración por Módulo:
1. **Crear nuevo modelo en módulo**
2. **Mantener modelo antiguo temporalmente**
3. **Crear migración de datos**
4. **Actualizar imports gradualmente**
5. **Eliminar modelo antiguo**

---

### 📅 Fase 3: Optimización (Semana 7-8)

#### Objetivos:
- Optimizar rendimiento
- Mejorar consultas
- Limpiar código legacy

#### Tareas:

##### **Optimización de Consultas**
```python
# Antes
empleados = EmpleadoCierre.objects.filter(cierre=cierre)
for empleado in empleados:
    registros = empleado.registroconceptoempleado_set.all()  # N+1 query problem

# Después
empleados = EmpleadoCierre.objects.filter(cierre=cierre)\
    .prefetch_related('registroconceptoempleado_set__concepto')
```

##### **Índices Optimizados**
```python
class Meta:
    indexes = [
        models.Index(fields=['cierre', 'estado']),
        models.Index(fields=['cliente', 'periodo']),
        models.Index(fields=['estado', 'fecha_creacion']),
        # Índices compuestos para consultas comunes
        models.Index(fields=['cliente', 'estado', 'periodo']),
    ]
```

##### **Validadores Personalizados**
```python
# validators.py
from django.core.exceptions import ValidationError
import re

def validate_rut_format(value):
    """Valida formato de RUT chileno"""
    pattern = r'^\d{7,8}-[0-9K]$'
    if not re.match(pattern, value):
        raise ValidationError('Formato de RUT inválido')

def validate_periodo_format(value):
    """Valida formato YYYY-MM"""
    pattern = r'^\d{4}-(0[1-9]|1[0-2])$'
    if not re.match(pattern, value):
        raise ValidationError('Formato de período inválido (YYYY-MM)')
```

---

### 📅 Fase 4: Testing y Documentación (Semana 9-10)

#### Objetivos:
- Tests completos para todos los modelos
- Documentación actualizada
- Métricas de performance

#### Tareas:
1. **Tests unitarios para modelos**
2. **Tests de integración**
3. **Benchmarks de performance**
4. **Documentación de API**

---

## Ejemplos de Implementación

### 🏗️ Modelo Core Mejorado

```python
# models/core.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from .base import BaseTimeStampedModel
from .enums import EstadosCierre, EstadosIncidencias, EstadosConsolidacion
from .managers import CierreNominaManager
from .validators import validate_periodo_format

class CierreNomina(BaseTimeStampedModel):
    """
    Entidad central del sistema de nómina.
    Representa el proceso mensual de cierre para un cliente.
    """
    cliente = models.ForeignKey(
        'api.Cliente', 
        on_delete=models.CASCADE,
        related_name='cierres_nomina'
    )
    periodo = models.CharField(
        max_length=7,
        validators=[validate_periodo_format],
        help_text="Formato: YYYY-MM (ej: 2025-06)"
    )
    
    # Estados del cierre
    estado = models.CharField(
        max_length=40,
        choices=EstadosCierre.choices,
        default=EstadosCierre.PENDIENTE,
        db_index=True
    )
    estado_incidencias = models.CharField(
        max_length=30,
        choices=EstadosIncidencias.choices,
        default=EstadosIncidencias.PENDIENTE
    )
    estado_consolidacion = models.CharField(
        max_length=30,
        choices=EstadosConsolidacion.choices,
        default=EstadosConsolidacion.PENDIENTE
    )
    
    # Usuarios asignados
    usuario_analista = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_como_analista'
    )
    supervisor_asignado = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_como_supervisor'
    )
    
    # Métricas y seguimiento
    total_incidencias = models.PositiveIntegerField(default=0)
    revisiones_realizadas = models.PositiveIntegerField(default=0)
    version_datos = models.PositiveIntegerField(default=1)
    
    # Fechas importantes
    fecha_ultima_revision = models.DateTimeField(null=True, blank=True)
    fecha_consolidacion = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    
    # Campos de control
    puede_consolidar = models.BooleanField(
        default=False,
        help_text="¿Tiene 0 discrepancias y puede consolidarse?"
    )
    observaciones_recarga = models.TextField(
        null=True,
        blank=True,
        help_text="Motivo para solicitar recarga de archivos"
    )
    
    # Manager personalizado
    objects = CierreNominaManager()
    
    class Meta:
        verbose_name = "Cierre de Nómina"
        verbose_name_plural = "Cierres de Nómina"
        unique_together = [['cliente', 'periodo']]
        indexes = [
            models.Index(fields=['cliente', 'periodo']),
            models.Index(fields=['estado', 'created_at']),
            models.Index(fields=['estado_incidencias']),
            models.Index(fields=['puede_consolidar', 'estado']),
        ]
        ordering = ['-periodo', '-created_at']
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo}"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        if self.periodo:
            try:
                año, mes = self.periodo.split('-')
                if int(mes) < 1 or int(mes) > 12:
                    raise ValidationError({'periodo': 'Mes debe estar entre 01 y 12'})
                if int(año) < 2020:
                    raise ValidationError({'periodo': 'Año debe ser mayor a 2020'})
            except ValueError:
                raise ValidationError({'periodo': 'Formato de período inválido'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    # Métodos de negocio mejorados
    def puede_generar_incidencias(self):
        """Verifica si puede generar incidencias consolidadas"""
        return (
            self.estado_consolidacion == EstadosConsolidacion.CONSOLIDADO and
            self.estado_incidencias == EstadosIncidencias.PENDIENTE
        )
    
    def actualizar_estado_automatico(self):
        """Actualiza el estado basado en el progreso de archivos"""
        archivos_status = self._verificar_archivos_listos()
        
        if archivos_status['todos_listos']:
            if self.estado in [EstadosCierre.PENDIENTE, EstadosCierre.CARGANDO_ARCHIVOS]:
                self.estado = EstadosCierre.ARCHIVOS_COMPLETOS
                self.save(update_fields=['estado', 'updated_at'])
        else:
            if self.estado != EstadosCierre.CARGANDO_ARCHIVOS:
                self.estado = EstadosCierre.CARGANDO_ARCHIVOS
                self.save(update_fields=['estado', 'updated_at'])
        
        return self.estado
    
    def _verificar_archivos_listos(self):
        """Verifica que todos los archivos necesarios estén procesados"""
        resultado = {
            'todos_listos': False,
            'detalles': {},
            'archivos_faltantes': []
        }
        
        # Verificar libro de remuneraciones (obligatorio)
        libro = self.libros_remuneraciones.first()
        libro_listo = libro and libro.estado == EstadosUpload.PROCESADO
        resultado['detalles']['libro_remuneraciones'] = {
            'estado': libro.estado if libro else 'no_subido',
            'listo': libro_listo
        }
        
        # Verificar movimientos del mes (obligatorio)
        movimientos = self.movimientos_mes.first()
        movimientos_listo = movimientos and movimientos.estado == EstadosUpload.PROCESADO
        resultado['detalles']['movimientos_mes'] = {
            'estado': movimientos.estado if movimientos else 'no_subido',
            'listo': movimientos_listo
        }
        
        # Al menos un archivo del analista procesado (obligatorio)
        archivos_analista_listos = self.archivos_analista.filter(
            estado=EstadosUpload.PROCESADO
        ).exists()
        resultado['detalles']['archivos_analista'] = {
            'listo': archivos_analista_listos
        }
        
        # Novedades es opcional, pero si existe debe estar procesado
        novedades = self.archivos_novedades.first()
        novedades_ok = not novedades or novedades.estado == EstadosUpload.PROCESADO
        resultado['detalles']['novedades'] = {
            'estado': novedades.estado if novedades else 'no_subido',
            'listo': novedades_ok
        }
        
        resultado['todos_listos'] = all([
            libro_listo,
            movimientos_listo,
            archivos_analista_listos,
            novedades_ok
        ])
        
        return resultado
    
    @property
    def progreso_porcentaje(self):
        """Calcula el porcentaje de progreso del cierre"""
        estados_orden = list(EstadosCierre.values)
        try:
            index_actual = estados_orden.index(self.estado)
            return int((index_actual / (len(estados_orden) - 1)) * 100)
        except ValueError:
            return 0
    
    @property
    def tiempo_en_estado_actual(self):
        """Tiempo transcurrido en el estado actual"""
        return timezone.now() - self.updated_at
    
    def get_resumen_archivos(self):
        """Obtiene resumen del estado de todos los archivos"""
        return {
            'libro_remuneraciones': {
                'subido': self.libros_remuneraciones.exists(),
                'procesado': self.libros_remuneraciones.filter(
                    estado=EstadosUpload.PROCESADO
                ).exists()
            },
            'movimientos_mes': {
                'subido': self.movimientos_mes.exists(),
                'procesado': self.movimientos_mes.filter(
                    estado=EstadosUpload.PROCESADO
                ).exists()
            },
            'archivos_analista': {
                'total': self.archivos_analista.count(),
                'procesados': self.archivos_analista.filter(
                    estado=EstadosUpload.PROCESADO
                ).count()
            },
            'novedades': {
                'subido': self.archivos_novedades.exists(),
                'procesado': self.archivos_novedades.filter(
                    estado=EstadosUpload.PROCESADO
                ).exists()
            }
        }
```

### 🧑 Modelo EmpleadoCierre Mejorado

```python
# models/core.py (continuación)
from .validators import validate_rut_format

class EmpleadoCierre(BaseTimeStampedModel):
    """
    Representa un empleado en el contexto de un cierre específico.
    """
    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name='empleados'
    )
    rut = models.CharField(
        max_length=12,
        validators=[validate_rut_format],
        db_index=True
    )
    nombre = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)
    rut_empresa = models.CharField(max_length=20)
    dias_trabajados = models.IntegerField(null=True, blank=True)
    
    # Manager personalizado
    objects = EmpleadoCierreManager()
    
    class Meta:
        verbose_name = "Empleado del Cierre"
        verbose_name_plural = "Empleados del Cierre"
        unique_together = [['cierre', 'rut']]
        indexes = [
            models.Index(fields=['cierre', 'rut']),
            models.Index(fields=['rut']),
            models.Index(fields=['nombre', 'apellido_paterno']),
        ]
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']
    
    def __str__(self):
        return f"{self.rut} - {self.nombre_completo}"
    
    @property
    def nombre_completo(self):
        """Retorna nombre completo del empleado"""
        nombres = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            nombres.append(self.apellido_materno)
        return ' '.join(nombres)
    
    @property
    def rut_formateado(self):
        """Retorna RUT con formato (ej: 12.345.678-9)"""
        if not self.rut or len(self.rut) < 2:
            return self.rut
        
        cuerpo = self.rut[:-2]
        dv = self.rut[-2:]
        
        # Formatear con puntos
        cuerpo_formateado = '.'.join([
            cuerpo[i:i+3] for i in range(0, len(cuerpo), 3)
        ])
        
        return f"{cuerpo_formateado}-{dv}"
    
    def get_total_conceptos(self):
        """Obtiene total de conceptos asociados"""
        return self.registroconceptoempleado_set.count()
    
    def get_total_liquido(self):
        """Calcula total líquido a pagar"""
        registros = self.registroconceptoempleado_set.select_related('concepto')
        
        total_haberes = 0
        total_descuentos = 0
        
        for registro in registros:
            if registro.concepto and registro.es_numerico:
                monto = registro.monto_numerico
                
                if registro.concepto.clasificacion in [
                    'haberes_imponibles', 
                    'haberes_no_imponibles', 
                    'horas_extras'
                ]:
                    total_haberes += monto
                elif registro.concepto.clasificacion in [
                    'descuentos_legales', 
                    'otros_descuentos'
                ]:
                    total_descuentos += monto
        
        return total_haberes - total_descuentos
    
    def tiene_movimientos_periodo(self):
        """Verifica si tiene movimientos en el período"""
        return any([
            self.movimientoaltabaja_set.exists(),
            self.movimientoausentismo_set.exists(),
            self.movimientovacaciones_set.exists(),
            self.movimientovariacionsueldo_set.exists(),
            self.movimientovariacioncontrato_set.exists(),
        ])
```

---

## Estrategia de Migración

### 🔄 Migración Sin Downtime

#### **Enfoque: Migración Gradual por Módulos**

```python
# Paso 1: Crear modelos nuevos manteniendo los antiguos
# migration_001_crear_nuevos_modelos.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('nomina', '0012_previous_migration'),
    ]
    
    operations = [
        # Crear tabla temporal para nuevo CierreNomina
        migrations.CreateModel(
            name='CierreNominaNuevo',
            fields=[
                # Campos del nuevo modelo
            ],
            options={
                'db_table': 'nomina_cierrenomina_nuevo',
            },
        ),
    ]
```

```python
# Paso 2: Migrar datos del modelo antiguo al nuevo
# migration_002_migrar_datos.py

from django.db import migrations

def migrar_cierres_nomina(apps, schema_editor):
    CierreNominaAntiguo = apps.get_model('nomina', 'CierreNomina')
    CierreNominaNuevo = apps.get_model('nomina', 'CierreNominaNuevo')
    
    for cierre_antiguo in CierreNominaAntiguo.objects.all():
        CierreNominaNuevo.objects.create(
            id=cierre_antiguo.id,
            cliente=cierre_antiguo.cliente,
            periodo=cierre_antiguo.periodo,
            estado=cierre_antiguo.estado,
            # Mapear todos los campos...
        )

class Migration(migrations.Migration):
    dependencies = [
        ('nomina', '0001_crear_nuevos_modelos'),
    ]
    
    operations = [
        migrations.RunPython(
            migrar_cierres_nomina,
            reverse_code=migrations.RunPython.noop
        ),
    ]
```

```python
# Paso 3: Actualizar referencias y eliminar modelo antiguo
# migration_003_actualizar_referencias.py

class Migration(migrations.Migration):
    dependencies = [
        ('nomina', '0002_migrar_datos'),
    ]
    
    operations = [
        # Renombrar tabla nueva a nombre original
        migrations.RunSQL(
            "ALTER TABLE nomina_cierrenomina_nuevo RENAME TO nomina_cierrenomina;",
            reverse_sql="ALTER TABLE nomina_cierrenomina RENAME TO nomina_cierrenomina_nuevo;"
        ),
        
        # Eliminar modelo antiguo si existe tabla temporal
        migrations.DeleteModel(name='CierreNominaAntiguo'),
    ]
```

### 📋 Checklist de Migración

#### **Pre-migración:**
- [ ] Backup completo de base de datos
- [ ] Tests de regresión ejecutándose
- [ ] Plan de rollback definido
- [ ] Métricas de performance baseline

#### **Durante la migración:**
- [ ] Ejecutar migración en ambiente de desarrollo
- [ ] Validar integridad de datos
- [ ] Ejecutar tests completos
- [ ] Verificar performance de consultas

#### **Post-migración:**
- [ ] Actualizar imports en código
- [ ] Actualizar documentación
- [ ] Monitorear logs de errores
- [ ] Validar métricas de performance

---

## Métricas de Éxito

### 📊 KPIs Técnicos

#### **Reducción de Complejidad:**
- **Líneas de código**: Reducir de 1330+ a ~800 líneas
- **Modelos por archivo**: Máximo 5 modelos por archivo
- **Duplicación de código**: Reducir en 80%
- **Complejidad ciclomática**: Reducir en 40%

#### **Performance:**
```python
# Antes (N+1 queries)
def get_empleados_con_conceptos(cierre_id):
    empleados = EmpleadoCierre.objects.filter(cierre_id=cierre_id)
    for empleado in empleados:  # Query por cada empleado
        conceptos = empleado.registroconceptoempleado_set.all()  # Query por cada empleado
    return empleados

# Después (2 queries optimizadas)
def get_empleados_con_conceptos(cierre_id):
    return EmpleadoCierre.objects.filter(cierre_id=cierre_id)\
        .prefetch_related('registroconceptoempleado_set__concepto')\
        .select_related('cierre')
```

**Métricas objetivo:**
- **Tiempo de consultas**: Reducir en 25%
- **Uso de memoria**: Reducir en 20%
- **Queries por página**: Reducir en 50%

#### **Mantenibilidad:**
- **Cobertura de tests**: Aumentar a 90%
- **Documentación**: 100% de modelos documentados
- **Validaciones**: Aumentar en 60%
- **Consistencia**: 100% de patrones estandarizados

### 📈 Métricas de Negocio

#### **Productividad del Desarrollo:**
- **Tiempo de implementación de features**: Reducir en 30%
- **Tiempo de debugging**: Reducir en 40%
- **Onboarding de nuevos desarrolladores**: Reducir en 50%

#### **Calidad del Sistema:**
- **Bugs en producción**: Reducir en 60%
- **Tiempo de resolución de bugs**: Reducir en 45%
- **Incidentes de performance**: Reducir en 70%

---

## Cronograma Detallado

### 📅 Cronograma de 10 Semanas

| Semana | Fase | Actividades | Entregables |
|--------|------|-------------|-------------|
| 1 | Preparación | - Crear estructura de archivos<br>- Implementar modelos base<br>- Definir enums | - Estructura modular<br>- Modelos base abstractos |
| 2 | Preparación | - Crear managers personalizados<br>- Implementar validadores<br>- Setup de tests | - Managers y QuerySets<br>- Validadores personalizados |
| 3 | Core | - Migrar CierreNomina<br>- Migrar EmpleadoCierre<br>- Tests unitarios | - Modelos core migrados<br>- Tests pasando |
| 4 | Archivos | - Migrar modelos de upload<br>- Implementar BaseUploadModel<br>- Optimizar consultas | - Modelos archivos migrados<br>- Performance mejorada |
| 5 | Movimientos | - Migrar movimientos de personal<br>- Aplicar BaseEmpleadoMovimientoModel<br>- Refactoring de relaciones | - Movimientos migrados<br>- Duplicación eliminada |
| 6 | Incidencias | - Migrar sistema de incidencias<br>- Mejorar flujo colaborativo<br>- Optimizar estados | - Sistema incidencias mejorado<br>- Flujos optimizados |
| 7 | Consolidación | - Migrar modelos consolidados<br>- Optimizar consultas complejas<br>- Implementar caching | - Consolidación optimizada<br>- Performance mejorada |
| 8 | Optimización | - Optimizar índices<br>- Refactoring final<br>- Cleanup de código legacy | - Índices optimizados<br>- Código limpio |
| 9 | Testing | - Tests de integración<br>- Benchmarks de performance<br>- Validación de migración | - Suite de tests completa<br>- Métricas validadas |
| 10 | Documentación | - Documentar API<br>- Guías de uso<br>- Deploy a producción | - Documentación completa<br>- Sistema en producción |

---

## Conclusiones y Próximos Pasos

### ✅ Beneficios Esperados

1. **Código más mantenible**: Estructura modular y patrones consistentes
2. **Mejor performance**: Consultas optimizadas y índices mejorados  
3. **Desarrollo más rápido**: Menos duplicación y mejor abstracción
4. **Mayor confiabilidad**: Más tests y validaciones
5. **Escalabilidad mejorada**: Preparado para crecimiento futuro

### 🚀 Próximos Pasos Inmediatos

1. **Semana 1**: Iniciar Fase 1 - Crear estructura base
2. **Setup de entorno**: Configurar branch de desarrollo
3. **Team alignment**: Revisar plan con equipo técnico
4. **Definir criterios de éxito**: Establecer métricas específicas

### 🔧 Herramientas Recomendadas

- **django-extensions**: Para diagramas de modelos
- **django-debug-toolbar**: Para profiling de queries
- **coverage.py**: Para métricas de testing
- **pre-commit**: Para validaciones automáticas
- **black/isort**: Para formateo consistente

---

*Plan creado el 24 de julio de 2025*  
*Versión: 1.0*  
*Autor: Arquitecto de Software*
