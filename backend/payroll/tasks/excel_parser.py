# backend/payroll/tasks/excel_parser.py
# Utilidades especializadas para parsing de archivos Excel de payroll

import pandas as pd
import openpyxl
from decimal import Decimal, InvalidOperation
import re
import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class ExcelPayrollParser:
    """
    Parser especializado para archivos Excel de libro de remuneraciones.
    
    Maneja diferentes formatos y estructuras de archivos Excel,
    detecta automáticamente columnas y tipos de datos.
    """
    
    def __init__(self, archivo_path: str):
        self.archivo_path = archivo_path
        self.df = None
        self.metadata = {}
        
    def cargar_archivo(self) -> bool:
        """Carga el archivo Excel y detecta su estructura"""
        try:
            # Intentar con pandas primero
            self.df = pd.read_excel(self.archivo_path, header=0)
            
            # Metadata básica
            self.metadata = {
                'filas_total': len(self.df),
                'columnas_total': len(self.df.columns),
                'columnas_nombres': list(self.df.columns),
                'archivo_valido': True
            }
            
            logger.info(f"📊 Excel cargado: {self.metadata['filas_total']} filas, {self.metadata['columnas_total']} columnas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando Excel: {str(e)}")
            self.metadata['archivo_valido'] = False
            return False
    
    def detectar_estructura_empleados(self) -> Dict[str, int]:
        """
        Detecta automáticamente las columnas de empleados.
        Retorna índices de columnas: {'rut': 0, 'nombre': 1, 'apellido_pat': 2, 'apellido_mat': 3}
        """
        if self.df is None:
            return {}
        
        estructura = {}
        columnas = list(self.df.columns)
        
        # Buscar RUT (primera columna que contenga RUTs válidos)
        for idx, columna in enumerate(columnas):
            muestra = self.df[columna].dropna().head(5).astype(str)
            ruts_validos = sum(1 for val in muestra if self._es_rut_valido(val))
            
            if ruts_validos >= 3:  # Al menos 3 RUTs válidos en la muestra
                estructura['rut'] = idx
                break
        
        # Asumir estructura típica después del RUT
        if 'rut' in estructura:
            base_idx = estructura['rut']
            estructura.update({
                'nombre': base_idx + 1 if base_idx + 1 < len(columnas) else None,
                'apellido_pat': base_idx + 2 if base_idx + 2 < len(columnas) else None,
                'apellido_mat': base_idx + 3 if base_idx + 3 < len(columnas) else None
            })
        
        logger.info(f"🔍 Estructura empleados detectada: {estructura}")
        return estructura
    
    def detectar_conceptos_remuneracion(self) -> List[Dict[str, Any]]:
        """
        Detecta automáticamente las columnas de conceptos de remuneración.
        Retorna lista de conceptos con metadata.
        """
        if self.df is None:
            return []
        
        conceptos = []
        estructura_emp = self.detectar_estructura_empleados()
        
        # Identificar donde terminan las columnas de empleado
        inicio_conceptos = max(estructura_emp.values()) + 1 if estructura_emp else 4
        
        # Procesar columnas de conceptos
        for idx, columna in enumerate(self.df.columns[inicio_conceptos:], start=inicio_conceptos):
            concepto = {
                'indice': idx,
                'codigo_columna': self._get_excel_column_name(idx),
                'nombre_original': str(columna),
                'nombre_normalizado': self._normalizar_concepto(str(columna)),
                'tipo_concepto': self._detectar_tipo_concepto(str(columna)),
                'tiene_valores_numericos': self._tiene_valores_numericos(columna),
                'valores_unicos': len(self.df[columna].dropna().unique())
            }
            
            conceptos.append(concepto)
        
        logger.info(f"📋 Conceptos detectados: {len(conceptos)}")
        return conceptos
    
    def extraer_empleados(self, estructura: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """Extrae lista de empleados con datos básicos"""
        if self.df is None:
            return []
        
        if estructura is None:
            estructura = self.detectar_estructura_empleados()
        
        empleados = []
        
        for idx, row in self.df.iterrows():
            # Extraer datos básicos
            rut_raw = row.iloc[estructura.get('rut', 0)] if estructura.get('rut') is not None else ""
            nombre = row.iloc[estructura.get('nombre', 1)] if estructura.get('nombre') is not None else ""
            apellido_pat = row.iloc[estructura.get('apellido_pat', 2)] if estructura.get('apellido_pat') is not None else ""
            apellido_mat = row.iloc[estructura.get('apellido_mat', 3)] if estructura.get('apellido_mat') is not None else ""
            
            # Limpiar RUT
            rut_limpio = self._limpiar_rut(str(rut_raw))
            if not rut_limpio:
                continue  # Saltar filas sin RUT válido
            
            empleado = {
                'fila_excel': idx + 2,  # +2 por header y base-1
                'rut_trabajador': rut_limpio,
                'nombre': str(nombre) if not pd.isna(nombre) else "",
                'apellido_paterno': str(apellido_pat) if not pd.isna(apellido_pat) else "",
                'apellido_materno': str(apellido_mat) if not pd.isna(apellido_mat) else "",
                'datos_validos': True
            }
            
            empleados.append(empleado)
        
        logger.info(f"👥 Empleados extraídos: {len(empleados)}")
        return empleados
    
    def extraer_valores_matriz(self, empleados: List[Dict], conceptos: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extrae la matriz completa empleado x concepto.
        Retorna lista de valores individuales.
        """
        if self.df is None:
            return []
        
        valores = []
        
        for emp_data in empleados:
            fila_idx = emp_data['fila_excel'] - 2  # Convertir a índice pandas
            
            for concepto in conceptos:
                col_idx = concepto['indice']
                
                # Obtener valor
                valor_raw = self.df.iloc[fila_idx, col_idx] if fila_idx < len(self.df) else None
                valor_str = str(valor_raw) if not pd.isna(valor_raw) else ""
                
                # Procesar valor
                valor_numerico, es_numerico = self._procesar_valor(valor_str)
                
                valor = {
                    'empleado_rut': emp_data['rut_trabajador'],
                    'concepto_codigo': concepto['codigo_columna'],
                    'fila_excel': emp_data['fila_excel'],
                    'columna_excel': concepto['codigo_columna'],
                    'valor_original': valor_str,
                    'valor_numerico': valor_numerico,
                    'valor_texto': valor_str if not es_numerico else "",
                    'es_numerico': es_numerico
                }
                
                valores.append(valor)
        
        logger.info(f"💰 Valores extraídos: {len(valores)}")
        return valores
    
    # =============================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # =============================================================================
    
    def _es_rut_valido(self, rut_str: str) -> bool:
        """Valida formato básico de RUT chileno"""
        rut_limpio = self._limpiar_rut(str(rut_str))
        return len(rut_limpio) >= 8 and len(rut_limpio) <= 10 and rut_limpio[:-1].isdigit()
    
    def _limpiar_rut(self, rut_raw: str) -> str:
        """Limpia y normaliza RUT"""
        if not rut_raw or pd.isna(rut_raw):
            return ""
        
        # Remover puntos, guiones y espacios
        rut_limpio = re.sub(r'[.\s-]', '', str(rut_raw).strip())
        
        # Validar longitud
        if len(rut_limpio) >= 8 and len(rut_limpio) <= 10:
            return rut_limpio.upper()
        
        return ""
    
    def _detectar_tipo_concepto(self, nombre_concepto: str) -> str:
        """Detecta el tipo de concepto basado en palabras clave"""
        nombre_lower = nombre_concepto.lower()
        
        # Descuentos
        if any(palabra in nombre_lower for palabra in [
            'descuento', 'desc', 'rebaja', 'multa', 'anticipo', 
            'prestamo', 'préstamo', 'pension', 'pensión', 'salud'
        ]):
            return 'descuento'
        
        # Totales
        elif any(palabra in nombre_lower for palabra in [
            'total', 'liquido', 'líquido', 'neto', 'pagar'
        ]):
            return 'total'
        
        # Haberes
        elif any(palabra in nombre_lower for palabra in [
            'sueldo', 'gratif', 'bono', 'haber', 'asignacion', 'asignación',
            'overtime', 'extra', 'comision', 'comisión', 'incentivo'
        ]):
            return 'haber'
        
        # Informativos
        else:
            return 'informativo'
    
    def _normalizar_concepto(self, nombre_concepto: str) -> str:
        """Normaliza nombre de concepto"""
        # Limpiar espacios múltiples y convertir a title case
        normalizado = re.sub(r'\s+', ' ', str(nombre_concepto).strip())
        return normalizado.title()
    
    def _tiene_valores_numericos(self, columna_nombre: str) -> bool:
        """Verifica si una columna contiene principalmente valores numéricos"""
        if columna_nombre not in self.df.columns:
            return False
        
        muestra = self.df[columna_nombre].dropna().head(10)
        numericos = 0
        
        for valor in muestra:
            _, es_numerico = self._procesar_valor(str(valor))
            if es_numerico:
                numericos += 1
        
        return numericos > len(muestra) * 0.5  # >50% numéricos
    
    def _procesar_valor(self, valor_str: str) -> Tuple[Optional[Decimal], bool]:
        """Procesa un valor y determina si es numérico"""
        if not valor_str or pd.isna(valor_str) or str(valor_str).lower() in ['nan', 'none', '']:
            return None, False
        
        # Limpiar valor
        valor_limpio = str(valor_str).replace(',', '').replace('$', '').replace('.', '').strip()
        
        # Manejar separadores decimales
        if ',' in str(valor_str):
            partes = str(valor_str).split(',')
            if len(partes) == 2 and len(partes[1]) <= 2:  # Formato: 1.234,56
                valor_limpio = partes[0].replace('.', '') + '.' + partes[1]
        
        try:
            valor_decimal = Decimal(valor_limpio)
            return valor_decimal, True
        except (InvalidOperation, ValueError):
            return None, False
    
    def _get_excel_column_name(self, index: int) -> str:
        """Convierte índice numérico a nombre de columna Excel (A, B, C...)"""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result


# =============================================================================
# FUNCIONES DE UTILIDAD STANDALONE
# =============================================================================

def validar_archivo_excel(archivo_path: str) -> Dict[str, Any]:
    """
    Valida un archivo Excel antes del procesamiento.
    Retorna diccionario con información de validación.
    """
    parser = ExcelPayrollParser(archivo_path)
    
    if not parser.cargar_archivo():
        return {'valido': False, 'error': 'No se pudo cargar el archivo'}
    
    # Validaciones básicas
    validaciones = {
        'archivo_cargado': True,
        'tiene_filas': parser.metadata['filas_total'] > 0,
        'tiene_columnas': parser.metadata['columnas_total'] > 0,
        'estructura_empleados': bool(parser.detectar_estructura_empleados()),
        'conceptos_detectados': len(parser.detectar_conceptos_remuneracion()) > 0
    }
    
    return {
        'valido': all(validaciones.values()),
        'validaciones': validaciones,
        'metadata': parser.metadata
    }
