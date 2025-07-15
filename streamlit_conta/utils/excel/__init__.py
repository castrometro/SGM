"""
Módulo de templates Excel modularizado para informes contables
"""

from .esf_template import ESFTemplate
from .eri_template import ERITemplate
from .ecp_template import ECPTemplate
from .movimientos_template import MovimientosTemplate
from .base import BaseExcelTemplate

# Instancias globales de los templates
esf_template = ESFTemplate()
eri_template = ERITemplate()
ecp_template = ECPTemplate()
movimientos_template = MovimientosTemplate()

# Mantener compatibilidad con el código existente
class ExcelTemplateGenerator:
    """Generador de templates Excel con compatibilidad hacia atrás"""
    
    def __init__(self):
        self.esf_template = ESFTemplate()
        self.eri_template = ERITemplate()
        self.ecp_template = ECPTemplate()
        self.movimientos_template = MovimientosTemplate()
        
    def generate_esf_template(self, data_esf, metadata, data_eri=None):
        """Generar template Excel para Estado de Situación Financiera"""
        return self.esf_template.generate(data_esf, metadata, data_eri)
    
    def generate_eri_template(self, data_eri, metadata):
        """Generar template Excel para Estado de Resultado Integral"""
        return self.eri_template.generate(data_eri, metadata)
    
    def generate_ecp_template(self, data_ecp, metadata, data_eri=None):
        """Generar template Excel para Estado de Cambios en el Patrimonio"""
        return self.ecp_template.generate(data_ecp, metadata, data_eri)
    
    def generate_movimientos_template(self, df_movimientos, metadata, tipo_vista="Todos los movimientos"):
        """Generar template Excel para movimientos contables"""
        return self.movimientos_template.generate(df_movimientos, metadata, tipo_vista)
    
    def workbook_to_bytes(self, workbook):
        """Convertir workbook a bytes para descarga"""
        return self.esf_template.workbook_to_bytes(workbook)

# Instancia global del generador
excel_generator = ExcelTemplateGenerator()

__all__ = [
    'ESFTemplate',
    'ERITemplate',
    'ECPTemplate', 
    'MovimientosTemplate',
    'BaseExcelTemplate',
    'ExcelTemplateGenerator',
    'excel_generator',
    'esf_template',
    'eri_template',
    'ecp_template',
    'movimientos_template'
]
