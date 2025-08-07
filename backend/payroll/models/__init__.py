# ============================================================================
#                    PAYROLL MODELS - IMPORTS CENTRALIZADOS
# ============================================================================

# Modelo base y constantes
from .base import (
    BasePayrollModel,
    ClientRelatedMixin,
    StatusMixin,
    FileRelatedMixin,
    
    # Constantes
    CLOSURE_STATUS_CHOICES,
    FILE_TYPE_CHOICES,
    FILE_STATUS_CHOICES,
    VALIDATION_STATUS_CHOICES,
    DISCREPANCY_TYPE_CHOICES,
    SEVERITY_CHOICES,
    
    # Utilidades
    generate_upload_path,
    serialize_for_cache,
    get_redis_key,
)

# Modelo principal
from .closure import PayrollClosure

# Fase 1: Upload & Validation
from .phase1 import (
    PayrollFileUpload,
    ParsedDataStorage,
    DiscrepancyResult,
    ValidationRun,
    ComparisonResult,
    ValidationRule,
)

# Fase 2: Consolidation (se agregará después)
# from .phase2 import (
#     ConsolidatedEmployee,
#     ConsolidatedPayrollItem,
# )

# Fase 3: Comparison (se agregará después)
# from .phase3 import (
#     MonthlyComparison,
#     ComparisonIncidence,
# )

# Fase 4: Finalization (se agregará después)
# from .phase4 import (
#     PayrollReport,
#     ReportData,
# )

# Modelos compartidos
from .shared import (
    PayrollActivityLog,
    AuditTrail,
    PerformanceLog,
    RedisCache,
)

# Lista de todos los modelos para migraciones
__all__ = [
    # Base
    'BasePayrollModel',
    'ClientRelatedMixin', 
    'StatusMixin',
    'FileRelatedMixin',
    
    # Principal
    'PayrollClosure',
    
    # Fase 1
    'PayrollFileUpload',
    'ParsedDataStorage', 
    'DiscrepancyResult',
    'ValidationRun',
    'ComparisonResult',
    'ValidationRule',
    
    # Shared
    'PayrollActivityLog',
    'AuditTrail',
    'PerformanceLog',
    'RedisCache',
]
