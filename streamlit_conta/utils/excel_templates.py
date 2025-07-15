"""
Utilidades para crear y manejar templates de Excel para los informes contables.
Genera archivos Excel con formato profesional basado en los datos del dashboard.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
import pandas as pd
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExcelTemplateGenerator:
    """Generador de templates Excel para informes contables"""
    
    def __init__(self):
        # Estilos predefinidos
        self.styles = {
            'title': Font(name='Arial', size=16, bold=True, color='FFFFFF'),
            'header': Font(name='Arial', size=12, bold=True, color='FFFFFF'),
            'subheader': Font(name='Arial', size=11, bold=True, color='000000'),
            'data': Font(name='Arial', size=10, color='000000'),
            'total': Font(name='Arial', size=11, bold=True, color='FFFFFF'),
            'metadata': Font(name='Arial', size=9, italic=True, color='666666')
        }
        
        self.fills = {
            'title': PatternFill(start_color='0A58CA', end_color='0A58CA', fill_type='solid'),
            'header': PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid'),
            'subheader': PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid'),
            'total': PatternFill(start_color='2F5233', end_color='2F5233', fill_type='solid'),
            'alternate': PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
        }
        
        self.borders = {
            'thin': Border(
                left=Side(border_style='thin'),
                right=Side(border_style='thin'),
                top=Side(border_style='thin'),
                bottom=Side(border_style='thin')
            ),
            'thick': Border(
                left=Side(border_style='thick'),
                right=Side(border_style='thick'),
                top=Side(border_style='thick'),
                bottom=Side(border_style='thick')
            )
        }

    def _apply_header_style(self, worksheet, start_row, start_col, end_col, title=""):
        """Aplicar estilo de encabezado a un rango de celdas"""
        if title:
            cell = worksheet.cell(row=start_row, column=start_col)
            cell.value = title
            cell.font = self.styles['title']
            cell.fill = self.fills['title']
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Combinar celdas para el título
            if end_col > start_col:
                worksheet.merge_cells(
                    start_row=start_row, start_column=start_col,
                    end_row=start_row, end_column=end_col
                )

    def _apply_data_formatting(self, worksheet, start_row, end_row, start_col, end_col):
        """Aplicar formato a los datos"""
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = worksheet.cell(row=row, column=col)
                cell.border = self.borders['thin']
                cell.font = self.styles['data']
                
                # Alternar colores de fila
                if row % 2 == 0:
                    cell.fill = self.fills['alternate']

    def _add_metadata_sheet(self, workbook, metadata):
        """Agregar hoja con metadatos del informe"""
        ws = workbook.create_sheet("Información del Reporte")
        
        # Título
        ws.cell(row=1, column=1, value="INFORMACIÓN DEL REPORTE")
        ws.cell(row=1, column=1).font = self.styles['title']
        ws.cell(row=1, column=1).fill = self.fills['title']
        ws.merge_cells('A1:B1')
        
        # Metadatos
        info_data = [
            ("Cliente:", metadata.get('cliente_nombre', 'N/A')),
            ("Período:", metadata.get('periodo', 'N/A')),
            ("Moneda:", metadata.get('moneda', 'CLP')),
            ("Idioma:", metadata.get('idioma', 'Español')),
            ("Fecha de generación:", datetime.now().strftime("%d/%m/%Y %H:%M")),
            ("Sistema:", "SGM Dashboard Contable"),
            ("Versión:", "v1.0")
        ]
        
        for i, (label, value) in enumerate(info_data, start=3):
            ws.cell(row=i, column=1, value=label).font = self.styles['subheader']
            ws.cell(row=i, column=2, value=value).font = self.styles['data']
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30

    def generate_esf_template(self, data_esf, metadata):
        """Generar template Excel para Estado de Situación Financiera"""
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = "Estado de Situación Financiera"
        
        # Título principal
        ws.cell(row=1, column=1, value="ESTADO DE SITUACIÓN FINANCIERA")
        self._apply_header_style(ws, 1, 1, 4, "ESTADO DE SITUACIÓN FINANCIERA")
        
        # Información del período
        current_row = 3
        ws.cell(row=current_row, column=1, value=f"Cliente: {metadata.get('cliente_nombre', 'N/A')}")
        ws.cell(row=current_row, column=3, value=f"Período: {metadata.get('periodo', 'N/A')}")
        current_row += 1
        ws.cell(row=current_row, column=1, value=f"Moneda: {metadata.get('moneda', 'CLP')}")
        ws.cell(row=current_row, column=3, value=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        current_row += 2
        
        # Extraer y procesar datos
        if data_esf:
            # ACTIVOS
            ws.cell(row=current_row, column=1, value="ACTIVOS").font = self.styles['header']
            ws.cell(row=current_row, column=1).fill = self.fills['header']
            current_row += 1
            
            # Activos Corrientes
            activos_corrientes = data_esf.get("activos", {}).get("corrientes", {})
            current_row = self._add_esf_section(ws, current_row, "Activos Corrientes", activos_corrientes, metadata.get("moneda", "CLP"))
            
            # Activos No Corrientes
            activos_no_corrientes = data_esf.get("activos", {}).get("no_corrientes", {})
            current_row = self._add_esf_section(ws, current_row, "Activos No Corrientes", activos_no_corrientes, metadata.get("moneda", "CLP"))
            
            current_row += 1
            
            # PASIVOS Y PATRIMONIO
            ws.cell(row=current_row, column=1, value="PASIVOS Y PATRIMONIO").font = self.styles['header']
            ws.cell(row=current_row, column=1).fill = self.fills['header']
            current_row += 1
            
            # Pasivos Corrientes
            pasivos_corrientes = data_esf.get("pasivos", {}).get("corrientes", {})
            current_row = self._add_esf_section(ws, current_row, "Pasivos Corrientes", pasivos_corrientes, metadata.get("moneda", "CLP"))
            
            # Pasivos No Corrientes
            pasivos_no_corrientes = data_esf.get("pasivos", {}).get("no_corrientes", {})
            current_row = self._add_esf_section(ws, current_row, "Pasivos No Corrientes", pasivos_no_corrientes, metadata.get("moneda", "CLP"))
            
            # Patrimonio
            patrimonio = data_esf.get("patrimonio", {})
            current_row = self._add_esf_section(ws, current_row, "Patrimonio", patrimonio, metadata.get("moneda", "CLP"))
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        
        # Agregar hoja de metadatos
        self._add_metadata_sheet(workbook, metadata)
        
        return workbook

    def _add_esf_section(self, ws, start_row, section_title, section_data, moneda):
        """Agregar una sección del ESF al worksheet"""
        current_row = start_row
        
        # Título de la sección
        ws.cell(row=current_row, column=1, value=section_title).font = self.styles['subheader']
        ws.cell(row=current_row, column=1).fill = self.fills['subheader']
        current_row += 1
        
        total_section = 0
        
        if isinstance(section_data, dict):
            if "grupos" in section_data:
                # Formato con grupos
                for grupo_nombre, grupo_data in section_data.get("grupos", {}).items():
                    ws.cell(row=current_row, column=1, value=f"  {grupo_nombre}").font = self.styles['data']
                    current_row += 1
                    
                    for cuenta in grupo_data.get("cuentas", []):
                        codigo = cuenta.get("codigo", "")
                        nombre = cuenta.get("nombre_es", cuenta.get("nombre_en", ""))
                        saldo = cuenta.get("saldo_final", 0)
                        
                        ws.cell(row=current_row, column=1, value=f"    {codigo} - {nombre}")
                        ws.cell(row=current_row, column=2, value=self._format_amount(saldo, moneda))
                        current_row += 1
                        total_section += saldo
                        
            elif "cuentas" in section_data:
                # Formato con cuentas directas
                for cuenta in section_data.get("cuentas", []):
                    codigo = cuenta.get("codigo", "")
                    nombre = cuenta.get("nombre_es", cuenta.get("nombre_en", ""))
                    saldo = cuenta.get("saldo_final", 0)
                    
                    ws.cell(row=current_row, column=1, value=f"  {codigo} - {nombre}")
                    ws.cell(row=current_row, column=2, value=self._format_amount(saldo, moneda))
                    current_row += 1
                    total_section += saldo
            
            # Total de la sección
            if "total" in section_data:
                total_section = section_data["total"]
            
            if total_section != 0:
                ws.cell(row=current_row, column=1, value=f"TOTAL {section_title.upper()}").font = self.styles['total']
                ws.cell(row=current_row, column=2, value=self._format_amount(total_section, moneda)).font = self.styles['total']
                ws.cell(row=current_row, column=1).fill = self.fills['total']
                ws.cell(row=current_row, column=2).fill = self.fills['total']
                current_row += 2
        
        return current_row

    def generate_eri_template(self, data_eri, metadata):
        """Generar template Excel para Estado de Resultado Integral"""
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = "Estado de Resultado Integral"
        
        # Título principal
        self._apply_header_style(ws, 1, 1, 4, "ESTADO DE RESULTADO INTEGRAL")
        
        # Información del período
        current_row = 3
        ws.cell(row=current_row, column=1, value=f"Cliente: {metadata.get('cliente_nombre', 'N/A')}")
        ws.cell(row=current_row, column=3, value=f"Período: {metadata.get('periodo', 'N/A')}")
        current_row += 2
        
        if data_eri:
            # Definir bloques ERI a procesar
            bloques_eri = [
                "ganancias_brutas",
                "ganancia_perdida", 
                "ganancia_perdida_antes_impuestos"
            ]
            
            total_general = 0
            
            for bloque_key in bloques_eri:
                bloque_data = data_eri.get(bloque_key)
                if bloque_data:
                    current_row, total_bloque = self._add_eri_section(ws, current_row, bloque_key, bloque_data, metadata.get("moneda", "CLP"))
                    total_general += total_bloque
            
            # Total General
            current_row += 1
            ws.cell(row=current_row, column=1, value="TOTAL GENERAL (Ganancia/Pérdida)").font = self.styles['total']
            ws.cell(row=current_row, column=2, value=self._format_amount(total_general, metadata.get("moneda", "CLP"))).font = self.styles['total']
            ws.cell(row=current_row, column=1).fill = self.fills['total']
            ws.cell(row=current_row, column=2).fill = self.fills['total']
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        
        # Agregar hoja de metadatos
        self._add_metadata_sheet(workbook, metadata)
        
        return workbook

    def _add_eri_section(self, ws, start_row, bloque_key, bloque_data, moneda):
        """Agregar una sección del ERI al worksheet"""
        current_row = start_row
        
        # Título del bloque
        titulo_bloque = bloque_key.replace("_", " ").title()
        ws.cell(row=current_row, column=1, value=titulo_bloque).font = self.styles['subheader']
        ws.cell(row=current_row, column=1).fill = self.fills['subheader']
        current_row += 1
        
        total_bloque = 0
        
        if isinstance(bloque_data, dict):
            if "grupos" in bloque_data:
                for grupo_nombre, grupo_data in bloque_data.get("grupos", {}).items():
                    ws.cell(row=current_row, column=1, value=f"  {grupo_nombre}").font = self.styles['data']
                    current_row += 1
                    
                    for cuenta in grupo_data.get("cuentas", []):
                        codigo = cuenta.get("codigo", "")
                        nombre = cuenta.get("nombre_es", cuenta.get("nombre_en", ""))
                        saldo = cuenta.get("saldo_final", 0)
                        
                        ws.cell(row=current_row, column=1, value=f"    {codigo} - {nombre}")
                        ws.cell(row=current_row, column=2, value=self._format_amount(saldo, moneda))
                        current_row += 1
                        total_bloque += saldo
            
            # Total del bloque
            if "total" in bloque_data:
                total_bloque = bloque_data["total"]
            
            if total_bloque != 0:
                ws.cell(row=current_row, column=1, value=f"TOTAL {titulo_bloque.upper()}").font = self.styles['total']
                ws.cell(row=current_row, column=2, value=self._format_amount(total_bloque, moneda)).font = self.styles['total']
                ws.cell(row=current_row, column=1).fill = self.fills['total']
                ws.cell(row=current_row, column=2).fill = self.fills['total']
                current_row += 2
        
        return current_row, total_bloque

    def generate_movimientos_template(self, df_movimientos, metadata, tipo_vista="Todos los movimientos"):
        """Generar template Excel para movimientos contables"""
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = "Movimientos Contables"
        
        # Título principal
        self._apply_header_style(ws, 1, 1, len(df_movimientos.columns), f"MOVIMIENTOS CONTABLES - {tipo_vista.upper()}")
        
        # Información del período
        current_row = 3
        ws.cell(row=current_row, column=1, value=f"Cliente: {metadata.get('cliente_nombre', 'N/A')}")
        ws.cell(row=current_row, column=4, value=f"Período: {metadata.get('periodo', 'N/A')}")
        current_row += 1
        ws.cell(row=current_row, column=1, value=f"Total movimientos: {len(df_movimientos)}")
        ws.cell(row=current_row, column=4, value=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        current_row += 2
        
        # Encabezados de columna
        for col_idx, column_name in enumerate(df_movimientos.columns, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=column_name)
            cell.font = self.styles['header']
            cell.fill = self.fills['header']
            cell.alignment = Alignment(horizontal='center')
        
        current_row += 1
        
        # Datos
        for row_idx, row in df_movimientos.iterrows():
            for col_idx, value in enumerate(row, 1):
                cell = ws.cell(row=current_row, column=col_idx, value=value)
                cell.font = self.styles['data']
                cell.border = self.borders['thin']
                
                # Alternar colores de fila
                if current_row % 2 == 0:
                    cell.fill = self.fills['alternate']
            
            current_row += 1
        
        # Totales si aplica
        if "Debe" in df_movimientos.columns and "Haber" in df_movimientos.columns:
            current_row += 1
            debe_col = list(df_movimientos.columns).index("Debe") + 1
            haber_col = list(df_movimientos.columns).index("Haber") + 1
            
            ws.cell(row=current_row, column=debe_col - 1, value="TOTALES:").font = self.styles['total']
            ws.cell(row=current_row, column=debe_col, value=self._format_amount(df_movimientos["Debe"].sum(), metadata.get("moneda", "CLP"))).font = self.styles['total']
            ws.cell(row=current_row, column=haber_col, value=self._format_amount(df_movimientos["Haber"].sum(), metadata.get("moneda", "CLP"))).font = self.styles['total']
        
        # Ajustar anchos de columna
        for col_idx in range(1, len(df_movimientos.columns) + 1):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 15
        
        # Agregar hoja de metadatos
        self._add_metadata_sheet(workbook, metadata)
        
        return workbook

    def generate_ecp_template(self, data_ecp, metadata, data_eri=None):
        """Generar template Excel para Estado de Cambios en el Patrimonio"""
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.title = "Estado de Cambios Patrimonio"
        
        # Título principal
        self._apply_header_style(ws, 1, 1, 7, "ESTADO DE CAMBIOS EN EL PATRIMONIO")
        
        # Información del período
        current_row = 3
        ws.cell(row=current_row, column=1, value=f"Cliente: {metadata.get('cliente_nombre', 'N/A')}")
        ws.cell(row=current_row, column=5, value=f"Período: {metadata.get('periodo', 'N/A')}")
        current_row += 2
        
        # Encabezados de columnas
        headers = ["Concepto", "Capital", "Otras Reservas", "Resultados Acumulados", 
                  "Capital Atribuible", "Participaciones no Controladoras", "Total"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=header)
            cell.font = self.styles['header']
            cell.fill = self.fills['header']
            cell.alignment = Alignment(horizontal='center')
        
        current_row += 1
        
        if data_ecp:
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
            total_eri = 0
            if data_eri:
                # Calcular total del ERI
                for bloque_key in ["ganancias_brutas", "ganancia_perdida", "ganancia_perdida_antes_impuestos"]:
                    bloque_data = data_eri.get(bloque_key)
                    if bloque_data and "total" in bloque_data:
                        total_eri += bloque_data["total"]
            
            # Datos de las filas
            filas_ecp = [
                {
                    "Concepto": "Saldo Inicial al 1 de Enero",
                    "Capital": capital_inicial,
                    "Otras Reservas": otras_reservas_inicial,
                    "Resultados Acumulados": 0,  # Simplificado
                    "Capital Atribuible": capital_inicial + otras_reservas_inicial,
                    "Participaciones no Controladoras": 0,
                    "Total": capital_inicial + otras_reservas_inicial
                },
                {
                    "Concepto": "Resultado del ejercicio",
                    "Capital": 0,
                    "Otras Reservas": 0,
                    "Resultados Acumulados": total_eri,
                    "Capital Atribuible": total_eri,
                    "Participaciones no Controladoras": 0,
                    "Total": total_eri
                },
                {
                    "Concepto": "Otros cambios",
                    "Capital": capital_cambios,
                    "Otras Reservas": otras_reservas_cambios,
                    "Resultados Acumulados": 0,
                    "Capital Atribuible": capital_cambios + otras_reservas_cambios,
                    "Participaciones no Controladoras": 0,
                    "Total": capital_cambios + otras_reservas_cambios
                },
                {
                    "Concepto": "Saldo Final",
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
                    if fila["Concepto"] in ["Saldo Inicial al 1 de Enero", "Saldo Final"]:
                        cell.fill = self.fills['total']
                        cell.font = self.styles['total']
                
                current_row += 1
        
        # Ajustar anchos de columna
        for col_idx in range(1, 8):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 18
        
        # Agregar hoja de metadatos
        self._add_metadata_sheet(workbook, metadata)
        
        return workbook

    def _format_amount(self, amount, moneda="CLP"):
        """Formatear monto según la moneda"""
        if pd.isna(amount) or amount is None:
            return 0
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return 0
        
        if moneda == "USD":
            return f"${amount:,.2f}"
        elif moneda == "EUR":
            return f"€{amount:,.2f}"
        else:  # CLP por defecto
            return f"${amount:,.0f}"

    def workbook_to_bytes(self, workbook):
        """Convertir workbook a bytes para descarga"""
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


# Instancia global del generador
excel_generator = ExcelTemplateGenerator()
