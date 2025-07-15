"""
Template Excel específico para Estado de Cambios en el Patrimonio (ECP)
"""

import openpyxl
import logging
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from .base import BaseExcelTemplate

logger = logging.getLogger(__name__)


class ECPTemplate(BaseExcelTemplate):
    """Template Excel para Estado de Cambios en el Patrimonio"""

    def generate(self, data_ecp, metadata, data_eri=None):
        """Generar template Excel para Estado de Cambios en el Patrimonio"""
        # Obtener idioma de los metadatos
        language = metadata.get('idioma', 'es')
        
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = self._get_text('title_ecp', language)
        
        # Título principal
        title_text = self._get_text('title_ecp', language)
        self._apply_header_style(ws, 1, 1, 7, title_text)
        
        # Información del período
        current_row = 3
        ws.cell(row=current_row, column=1, value=f"{self._get_text('client', language)}: {metadata.get('cliente_nombre', 'N/A')}")
        ws.cell(row=current_row, column=5, value=f"{self._get_text('period', language)}: {metadata.get('periodo', 'N/A')}")
        current_row += 2
        
        # Encabezados de columnas
        headers = [
            self._get_text('concept', language),
            self._get_text('capital', language),
            self._get_text('other_reserves', language),
            self._get_text('retained_earnings', language),
            self._get_text('attributable_capital', language),
            self._get_text('non_controlling_interests', language),
            self._get_text('total', language)
        ]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=header)
            cell.font = self.styles['header']
            cell.fill = self.fills['header']
            cell.alignment = Alignment(horizontal='center')
        
        current_row += 1
        
        if data_ecp:
            current_row = self._add_ecp_data(ws, current_row, data_ecp, data_eri, metadata, language)
        
        # Ajustar anchos de columna
        for col_idx in range(1, 8):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 18
        
        # Agregar hoja de metadatos
        self._add_metadata_sheet(workbook, metadata, language)
        
        return workbook

    def _add_ecp_data(self, ws, current_row, data_ecp, data_eri, metadata, language):
        """Agregar datos del ECP al worksheet"""
        # Procesar datos del ECP
        patrimonio_data = data_ecp.get("patrimonio", {})
        capital_data = patrimonio_data.get("capital", {})
        otras_reservas_data = patrimonio_data.get("otras_reservas", {})
        
        # Calcular totales
        capital_inicial = capital_data.get("saldo_anterior", 0)
        capital_cambios = capital_data.get("cambios", 0)
        otras_reservas_inicial = otras_reservas_data.get("saldo_anterior", 0)
        otras_reservas_cambios = otras_reservas_data.get("cambios", 0)
        
        # Resultado del ejercicio del ERI
        total_eri = self._calcular_total_eri(data_eri)
        
        # Datos de las filas
        filas_ecp = [
            {
                "Concepto": self._get_text('initial_balance', language),
                "Capital": capital_inicial,
                "Otras Reservas": otras_reservas_inicial,
                "Resultados Acumulados": 0,  # Simplificado
                "Capital Atribuible": capital_inicial + otras_reservas_inicial,
                "Participaciones no Controladoras": 0,
                "Total": capital_inicial + otras_reservas_inicial
            },
            {
                "Concepto": self._get_text('period_profit_loss', language),
                "Capital": 0,
                "Otras Reservas": 0,
                "Resultados Acumulados": total_eri,
                "Capital Atribuible": total_eri,
                "Participaciones no Controladoras": 0,
                "Total": total_eri
            },
            {
                "Concepto": self._get_text('other_changes', language),
                "Capital": capital_cambios,
                "Otras Reservas": otras_reservas_cambios,
                "Resultados Acumulados": 0,
                "Capital Atribuible": capital_cambios + otras_reservas_cambios,
                "Participaciones no Controladoras": 0,
                "Total": capital_cambios + otras_reservas_cambios
            },
            {
                "Concepto": self._get_text('final_balance', language),
                "Capital": capital_inicial + capital_cambios,
                "Otras Reservas": otras_reservas_inicial + otras_reservas_cambios,
                "Resultados Acumulados": total_eri,
                "Capital Atribuible": capital_inicial + capital_cambios + otras_reservas_inicial + otras_reservas_cambios + total_eri,
                "Participaciones no Controladoras": 0,
                "Total": capital_inicial + capital_cambios + otras_reservas_inicial + otras_reservas_cambios + total_eri
            }
        ]
        
        # Agregar filas de datos
        for fila in filas_ecp:
            for col_idx, (key, value) in enumerate(fila.items(), 1):
                cell = ws.cell(row=current_row, column=col_idx)
                if col_idx == 1:  # Concepto
                    cell.value = value
                    cell.font = self.styles['subheader']
                else:  # Valores numéricos
                    cell.value = self._format_amount(value, metadata.get("moneda", "CLP"))
                    cell.font = self.styles['data']
                
                cell.border = self.borders['thin']
                
                # Resaltar filas de saldo inicial y final
                balance_texts = [
                    self._get_text('initial_balance', language),
                    self._get_text('final_balance', language)
                ]
                if fila["Concepto"] in balance_texts:
                    cell.fill = self.fills['total']
                    cell.font = self.styles['total']
            
            current_row += 1
        
        return current_row

    def _calcular_total_eri(self, data_eri):
        """Calcular el total de ganancia/pérdida del ERI"""
        if not data_eri:
            return 0
        
        total_eri = 0
        # Sumar todos los bloques del ERI
        bloques_eri = [
            "ganancias_brutas",
            "ganancia_perdida", 
            "ganancia_perdida_antes_impuestos"
        ]
        
        for bloque_key in bloques_eri:
            bloque_data = data_eri.get(bloque_key, {})
            if isinstance(bloque_data, dict) and "total" in bloque_data:
                total_eri += bloque_data["total"]
        
        return total_eri
