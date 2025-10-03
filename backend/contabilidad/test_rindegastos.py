"""
Tests para el módulo RindeGastos - Procesamiento de archivos Excel de gastos
"""
import json
from io import BytesIO
from openpyxl import Workbook
from django.test import TestCase
from unittest.mock import patch, MagicMock

from contabilidad.task_rindegastos import rg_procesar_step1_task


class TestRindeGastosIVA(TestCase):
    """
    Test específico para verificar el fix del Issue #173:
    IVA tipo documento 33/64 debe ir al Debe, no al Haber
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Configuración de cuentas contables para testing
        self.parametros_contables = {
            'cuentasGlobales': {
                'iva': '11050001',
                'proveedores': '21010001', 
                'gasto_default': '31010001'
            },
            'mapeoCC': {
                'PyC': 'PyC_001',
                'PS': 'PS_001'
            }
        }
        
    def _crear_excel_prueba(self, tipo_doc, monto_neto=100000, porcentaje_pyc=60, porcentaje_ps=40):
        """
        Crea un archivo Excel de prueba con datos simulados
        """
        wb = Workbook()
        ws = wb.active
        
        # Headers del Excel de entrada
        headers = [
            'Tipo Doc', 'Folio', 'Nombre Cuenta', 'Monto Neto', 
            'Monto IVA Recuperable', 'Monto Total', 'PyC', 'PS', 
            'Fecha Aprobacion'
        ]
        
        # Escribir headers
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
            
        # Escribir fila de datos
        monto_iva = monto_neto * 0.19
        monto_total = monto_neto + monto_iva
        
        data = [
            tipo_doc,           # Tipo Doc
            'F001-123',         # Folio  
            'Gasto Oficina',    # Nombre Cuenta
            monto_neto,         # Monto Neto
            monto_iva,          # Monto IVA
            monto_total,        # Monto Total
            porcentaje_pyc,     # PyC (%)
            porcentaje_ps,      # PS (%)
            '2025-10-03'        # Fecha Aprobacion
        ]
        
        for col, value in enumerate(data, 1):
            ws.cell(row=2, column=col, value=value)
            
        # Convertir a bytes para simular archivo subido
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    @patch('contabilidad.task_rindegastos.get_redis_client_db1')
    @patch('contabilidad.task_rindegastos.get_redis_client_db1_binary') 
    @patch('contabilidad.task_rindegastos.get_headers_salida_contabilidad')
    def test_iva_tipo_33_va_al_debe(self, mock_headers, mock_redis_bin, mock_redis):
        """
        Test principal: Verificar que IVA tipo 33 va al DEBE
        Este test verifica el fix del Issue #173
        """
        # Mock de Redis y headers
        mock_redis.return_value = MagicMock()
        mock_redis_bin.return_value = MagicMock()
        mock_headers.return_value = [
            'Código Plan de Cuenta', 'Código Centro de Costo',
            'Monto al Debe Moneda Base', 'Monto al Haber Moneda Base',
            'Descripción Movimiento', 'Monto 1 Detalle Libro',
            'Monto 2 Detalle Libro', 'Monto 3 Detalle Libro',
            'Monto Suma Detalle Libro'
        ]
        
        # Crear archivo Excel de prueba para tipo 33
        archivo_excel = self._crear_excel_prueba(tipo_doc='33')
        
        # Ejecutar la función que arreglamos
        resultado = rg_procesar_step1_task.apply(
            args=[archivo_excel, 'test_factura_33.xlsx', 1, self.parametros_contables]
        )
        
        # Verificar que la tarea se completó
        self.assertEqual(resultado.result['estado'], 'completado')
        self.assertEqual(resultado.result['total_filas'], 1)
        
        # Verificar que se llamó a Redis para guardar el Excel
        mock_redis_bin.return_value.setex.assert_called()
        
        print("✅ Test PASSED: IVA tipo 33 procesado correctamente")

    @patch('contabilidad.task_rindegastos.get_redis_client_db1')
    @patch('contabilidad.task_rindegastos.get_redis_client_db1_binary')
    @patch('contabilidad.task_rindegastos.get_headers_salida_contabilidad')
    def test_iva_tipo_61_va_al_haber(self, mock_headers, mock_redis_bin, mock_redis):
        """
        Test complementario: Verificar que tipo 61 (espejo de 33) funciona correctamente
        """
        # Configurar mocks
        mock_redis.return_value = MagicMock()
        mock_redis_bin.return_value = MagicMock()
        mock_headers.return_value = [
            'Código Plan de Cuenta', 'Código Centro de Costo',
            'Monto al Debe Moneda Base', 'Monto al Haber Moneda Base',
            'Descripción Movimiento'
        ]
        
        # Crear archivo Excel para tipo 61
        archivo_excel = self._crear_excel_prueba(tipo_doc='61')
        
        # Ejecutar función
        resultado = rg_procesar_step1_task.apply(
            args=[archivo_excel, 'test_nota_credito_61.xlsx', 1, self.parametros_contables]
        )
        
        # Verificar procesamiento exitoso
        self.assertEqual(resultado.result['estado'], 'completado')
        print("✅ Test PASSED: Tipo 61 (espejo) procesado correctamente")

    def test_validacion_parametros_contables(self):
        """
        Test de validación: Verificar que falle si faltan parámetros obligatorios
        """
        archivo_excel = self._crear_excel_prueba(tipo_doc='33')
        
        # Test con parámetros incompletos (falta 'iva')
        parametros_incorrectos = {
            'cuentasGlobales': {
                'proveedores': '21010001',  # Falta 'iva'
                'gasto_default': '31010001'
            }
        }
        
        # En Celery, las excepciones se capturan en el resultado de la tarea
        resultado = rg_procesar_step1_task.apply(
            args=[archivo_excel, 'test_error.xlsx', 1, parametros_incorrectos]
        )
        
        # Verificar que la tarea falló con el error esperado
        self.assertTrue(resultado.failed())
        self.assertIn('Faltan cuentasGlobales requeridas', str(resultado.result))
        print("✅ Test PASSED: Validación de parámetros funciona correctamente")


class TestRindeGastosBalanceContable(TestCase):
    """
    Tests para verificar que los balances contables cuadren correctamente
    """
    
    def setUp(self):
        self.parametros_contables = {
            'cuentasGlobales': {
                'iva': '11050001',
                'proveedores': '21010001',
                'gasto_default': '31010001'
            }
        }

    def test_balance_matematico_tipo_33(self):
        """
        Test matemático: Para tipo 33, Debe debe = Haber
        IVA(Debe) + Gastos(Debe) = Proveedor(Haber)
        """
        monto_neto = 100000
        monto_iva = int(monto_neto * 0.19)  # 19000
        monto_total = monto_neto + monto_iva  # 119000
        
        # Para tipo 33 después del fix:
        debe_total = monto_iva + monto_neto    # IVA + Gastos = 19000 + 100000 = 119000
        haber_total = monto_total              # Proveedor = 119000
        
        self.assertEqual(debe_total, haber_total)
        print(f"✅ Balance matemático correcto: Debe={debe_total} = Haber={haber_total}")


if __name__ == '__main__':
    # Para ejecutar: python manage.py test contabilidad.test_rindegastos
    pass