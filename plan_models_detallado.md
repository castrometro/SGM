# Plan detallado para dividir models.py (1,551 líneas)

## 🎯 Mapeo de Modelos por Archivo

### models/base.py (~400 líneas)
- CierreNomina (líneas 41-428) - Modelo principal con toda la lógica de negocio
- EmpleadoCierre (líneas 429-443) - Empleados por cierre

### models/uploads.py (~300 líneas)  
- LibroRemuneracionesUpload (líneas 626-648)
- MovimientosMesUpload (líneas 649-669)
- ArchivoAnalistaUpload (líneas 670-689)
- ArchivoNovedadesUpload (líneas 690-709)
- ChecklistItem (líneas 710-729)

### models/movimientos.py (~400 líneas)
- MovimientoAltaBaja (líneas 499-525)
- MovimientoAusentismo (líneas 526-551) 
- MovimientoVacaciones (líneas 552-576)
- MovimientoVariacionSueldo (líneas 577-602)
- MovimientoVariacionContrato (líneas 603-625)

### models/conceptos.py (~200 líneas)
- ConceptoRemuneracion (líneas 445-465)
- RegistroConceptoEmpleado (líneas 466-498)

### models/incidencias.py (~500 líneas)
- EstadoCierreIncidencias, TipoIncidencia, EstadoIncidencia (TextChoices)
- IncidenciaCierre (líneas ~850-1100)
- ResolucionIncidencia (líneas ~1100-1200)

### models/consolidacion.py (~200 líneas)
- NominaConsolidada (líneas ~1500-1550) 
- ConceptoConsolidado (líneas ~1550-1552)

### models/analisis.py (~300 líneas)
- AnalisisDatosCierre (líneas ~1200-1350)
- IncidenciaVariacionSalarial (líneas ~1350-1450)
- TipoDiscrepancia, DiscrepanciaCierre (líneas ~1450-1500)

### models/novedades.py (~200 líneas)
- EmpleadoCierreNovedades (líneas ~730-750)
- ConceptoRemuneracionNovedades (líneas ~750-820)
- RegistroConceptoEmpleadoNovedades (líneas ~820-850)
- AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso (líneas ~750-850)

## 📋 Estrategia de Migración

1. **Extraer funciones auxiliares primero** (upload_to functions)
2. **Migrar modelos sin dependencias** (TextChoices, modelos simples)
3. **Migrar modelos con ForeignKeys** (mantener referencias)
4. **Crear models/__init__.py** con todos los imports
5. **Validar que no se rompa nada** (makemigrations, tests)

## 🔧 Archivo models/__init__.py (Compatibilidad Total)

```python
# Mantener compatibilidad total con imports existentes
from .base import CierreNomina, EmpleadoCierre
from .uploads import (
    LibroRemuneracionesUpload, MovimientosMesUpload, 
    ArchivoAnalistaUpload, ArchivoNovedadesUpload, ChecklistItem
)
from .movimientos import (
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
    MovimientoVariacionSueldo, MovimientoVariacionContrato
)
from .conceptos import ConceptoRemuneracion, RegistroConceptoEmpleado
from .incidencias import (
    EstadoCierreIncidencias, TipoIncidencia, EstadoIncidencia,
    IncidenciaCierre, ResolucionIncidencia
)
from .consolidacion import NominaConsolidada, ConceptoConsolidado
from .analisis import (
    AnalisisDatosCierre, IncidenciaVariacionSalarial, 
    TipoDiscrepancia, DiscrepanciaCierre
)
from .novedades import (
    EmpleadoCierreNovedades, ConceptoRemuneracionNovedades,
    RegistroConceptoEmpleadoNovedades, AnalistaFiniquito,
    AnalistaIncidencia, AnalistaIngreso
)

# Mantener constantes disponibles
from .base import CLASIFICACION_CHOICES

# Upload functions
from .uploads import (
    libro_remuneraciones_upload_to, movimientos_mes_upload_to,
    analista_upload_to, novedades_upload_to, resolucion_upload_to
)

__all__ = [
    # Base
    'CierreNomina', 'EmpleadoCierre', 'CLASIFICACION_CHOICES',
    
    # Uploads  
    'LibroRemuneracionesUpload', 'MovimientosMesUpload',
    'ArchivoAnalistaUpload', 'ArchivoNovedadesUpload', 'ChecklistItem',
    'libro_remuneraciones_upload_to', 'movimientos_mes_upload_to',
    'analista_upload_to', 'novedades_upload_to', 'resolucion_upload_to',
    
    # Movimientos
    'MovimientoAltaBaja', 'MovimientoAusentismo', 'MovimientoVacaciones',
    'MovimientoVariacionSueldo', 'MovimientoVariacionContrato',
    
    # Conceptos
    'ConceptoRemuneracion', 'RegistroConceptoEmpleado',
    
    # Incidencias
    'EstadoCierreIncidencias', 'TipoIncidencia', 'EstadoIncidencia',
    'IncidenciaCierre', 'ResolucionIncidencia',
    
    # Consolidación
    'NominaConsolidada', 'ConceptoConsolidado',
    
    # Análisis
    'AnalisisDatosCierre', 'IncidenciaVariacionSalarial',
    'TipoDiscrepancia', 'DiscrepanciaCierre',
    
    # Novedades
    'EmpleadoCierreNovedades', 'ConceptoRemuneracionNovedades',
    'RegistroConceptoEmpleadoNovedades', 'AnalistaFiniquito',
    'AnalistaIncidencia', 'AnalistaIngreso',
]
```

## ✅ Validación Post-Migración

```bash
# 1. Verificar que no hay errores de sintaxis
python manage.py check

# 2. Verificar migraciones
python manage.py makemigrations nomina --dry-run

# 3. Ejecutar tests específicos  
python manage.py test nomina.tests

# 4. Verificar imports en otros archivos
grep -r "from nomina.models import" backend/
grep -r "from .models import" backend/nomina/
```

## 🎯 Resultado Final

- ✅ **models.py eliminado** (1,551 líneas → 0)
- ✅ **8 archivos nuevos** (~200-500 líneas cada uno)
- ✅ **Compatibilidad 100%** (todos los imports existentes funcionan)
- ✅ **Más fácil mantenimiento** (cambios localizados)
- ✅ **Sin tocar tasks.py ni views.py** (como solicitaste)
