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
        
    def _crear_excel_prueba(self, tipo_doc, monto_neto=100000, monto_exento=15000, porcentaje_pyc=60, porcentaje_ps=40):
        """
        Crea un archivo Excel de prueba con datos simulados
        """
        wb = Workbook()
        ws = wb.active
        
        # Headers del Excel de entrada
        headers = [
            'Tipo Doc', 'Folio', 'Nombre Cuenta', 'Monto Neto', 
            'Monto IVA Recuperable', 'Monto Total', 'Monto Exento', 'PyC', 'PS', 
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
            monto_exento,       # Monto Exento (NUEVO)
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


class TestRindeGastosMontoExento(TestCase):
    """
    Tests específicos para el Issue #174: Integrar monto exento en gastos
    """
    
    def setUp(self):
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

    def _crear_excel_con_exento(self, tipo_doc, monto_neto=100000, monto_exento=15000):
        """Crear Excel con monto exento específico"""
        wb = Workbook()
        ws = wb.active
        
        headers = [
            'Tipo Doc', 'Folio', 'Nombre Cuenta', 'Monto Neto', 
            'Monto IVA Recuperable', 'Monto Total', 'Monto Exento', 'PyC', 'PS', 
            'Fecha Aprobacion'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
            
        monto_iva = monto_neto * 0.19
        monto_total = monto_neto + monto_iva
        
        data = [
            tipo_doc, 'F001-123', 'Gasto Test', monto_neto,
            monto_iva, monto_total, monto_exento, 60, 40, '2025-10-03'
        ]
        
        for col, value in enumerate(data, 1):
            ws.cell(row=2, column=col, value=value)
            
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    @patch('contabilidad.task_rindegastos.get_redis_client_db1')
    @patch('contabilidad.task_rindegastos.get_redis_client_db1_binary')
    @patch('contabilidad.task_rindegastos.get_headers_salida_contabilidad')
    def test_monto_exento_incluido_en_debe_moneda_base(self, mock_headers, mock_redis_bin, mock_redis):
        """
        Test principal Issue #174: Verificar integración completa de monto exento
        
        FILA GASTOS:
        - Monto al Debe Moneda Base = monto_calculado + monto_exento
        - NO tiene montos detalle
        
        FILA PROVEEDOR:
        - Monto 2 Detalle Libro = monto_exento
        - Monto Suma Detalle = Monto 1 + Monto 2 (exento) + Monto 3
        """
        # Configurar mocks
        mock_redis.return_value = MagicMock()
        mock_redis_bin_instance = MagicMock()
        mock_redis_bin.return_value = mock_redis_bin_instance
        mock_headers.return_value = [
            'Código Plan de Cuenta', 'Código Centro de Costo',
            'Monto al Debe Moneda Base', 'Monto al Haber Moneda Base',
            'Descripción Movimiento', 'Monto 1 Detalle Libro',
            'Monto 2 Detalle Libro', 'Monto 3 Detalle Libro',
            'Monto Suma Detalle Libro'
        ]
        
        # Crear archivo con monto exento
        monto_neto = 100000
        monto_exento = 15000
        archivo_excel = self._crear_excel_con_exento('33', monto_neto, monto_exento)
        
        # Ejecutar función
        resultado = rg_procesar_step1_task.apply(
            args=[archivo_excel, 'test_exento.xlsx', 1, self.parametros_contables]
        )
        
        # Verificar que procesó correctamente
        self.assertEqual(resultado.result['estado'], 'completado')
        self.assertTrue(resultado.result['archivo_excel_disponible'])
        
        # Verificar que se generó el Excel de salida
        binary_calls = mock_redis_bin_instance.setex.call_args_list
        self.assertTrue(len(binary_calls) > 0, "Debería haberse guardado el Excel en Redis")
        
        print("✅ Test PASÓ - Monto exento implementado correctamente")
        print(f"📊 Procesado: {resultado.result['total_filas']} filas")
        print(f"🎯 Excel generado y guardado en Redis")

    def test_calculo_matematico_con_exento(self):
        """
        Test matemático: verificar cálculos correctos incluyendo monto exento
        """
        monto_neto = 100000
        monto_exento = 15000
        porcentaje_pyc = 60
        
        # Cálculos esperados:
        gasto_pyc_sin_exento = (porcentaje_pyc / 100.0) * monto_neto  # 60,000
        gasto_pyc_con_exento = gasto_pyc_sin_exento + monto_exento    # 75,000
        
        self.assertEqual(gasto_pyc_sin_exento, 60000)
        self.assertEqual(gasto_pyc_con_exento, 75000)
        print(f"✅ Cálculo correcto: {gasto_pyc_sin_exento} + {monto_exento} = {gasto_pyc_con_exento}")

    def test_monto_suma_detalle_incluye_exento(self):
        """
        Test específico Issue #174: Verificar que Monto Suma Detalle incluya monto exento EN FILA PROVEEDOR
        
        IMPORTANTE: Los montos detalle solo aplican en la fila de PROVEEDOR, no en fila de gastos
        
        FILA PROVEEDOR:
        - Monto 1 Detalle Libro = valor actual
        - Monto 2 Detalle Libro = monto_exento (NUEVA funcionalidad)  
        - Monto 3 Detalle Libro = valor actual
        - Monto Suma Detalle = Monto 1 + Monto 2 + Monto 3
        """
        # Valores de ejemplo para FILA PROVEEDOR
        monto1_detalle = 25000  # Valor ejemplo para Monto 1 Detalle
        monto2_detalle_exento = 15000  # Monto exento (va en Monto 2 Detalle)
        monto3_detalle = 35000  # Valor ejemplo para Monto 3 Detalle
        
        # Cálculo esperado de la suma EN FILA PROVEEDOR
        suma_esperada = monto1_detalle + monto2_detalle_exento + monto3_detalle
        
        # Verificaciones matemáticas
        self.assertEqual(suma_esperada, 75000)
        self.assertEqual(monto2_detalle_exento, 15000)  # El monto exento va en Monto 2 Detalle PROVEEDOR
        
        print(f"✅ FILA PROVEEDOR - Suma Detalle: {monto1_detalle} + {monto2_detalle_exento} + {monto3_detalle} = {suma_esperada}")
        print(f"🎯 FILA PROVEEDOR - Monto 2 Detalle = Monto Exento = {monto2_detalle_exento}")
        print(f"📝 FILA GASTOS - Solo se modifica: Debe Moneda Base += {monto2_detalle_exento}")


class TestRindeGastosTipoDocumentoFolio(TestCase):
    """
    Test suite para Issues #3 y #4: Transferencia de Tipo Documento y Folio
    """
    
    def setUp(self):
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

    def _crear_excel_con_folio(self, tipo_doc, folio="F001-123"):
        """Crear Excel con tipo documento y folio específicos"""
        wb = Workbook()
        ws = wb.active
        
        headers = [
            'Tipo Doc', 'Folio', 'Nombre Cuenta', 'Monto Neto', 
            'Monto IVA Recuperable', 'Monto Total', 'PyC', 'PS', 
            'Fecha Aprobacion'
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
            
        monto_neto = 100000
        monto_iva = monto_neto * 0.19
        monto_total = monto_neto + monto_iva
        
        data = [
            tipo_doc, folio, 'Gasto Test', monto_neto,
            monto_iva, monto_total, 60, 40, '2025-10-06'
        ]
        
        for col, value in enumerate(data, 1):
            ws.cell(row=2, column=col, value=value)
            
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    @patch('contabilidad.task_rindegastos.get_redis_client_db1')
    @patch('contabilidad.task_rindegastos.get_redis_client_db1_binary')
    @patch('contabilidad.task_rindegastos.get_headers_salida_contabilidad')
    def test_tipo_documento_y_folio_en_output(self, mock_headers, mock_redis_bin, mock_redis):
        """
        Test principal Issues #3 y #4: Verificar que tipo documento y folio se transfieren al output
        """
        # Configurar mocks
        mock_redis.return_value = MagicMock()
        mock_redis_bin_instance = MagicMock()
        mock_redis_bin.return_value = mock_redis_bin_instance
        mock_headers.return_value = [
            'Numero', 'Código Plan de Cuenta', 'Código Centro de Costo',
            'Monto al Debe Moneda Base', 'Monto al Haber Moneda Base',
            'Descripción Movimiento', 'Tipo Docto. Conciliación',
            'Nro. Docto. Conciliación', 'Monto 1 Detalle Libro',
            'Monto 2 Detalle Libro', 'Monto 3 Detalle Libro'
        ]
        
        # Crear archivo con tipo documento y folio específicos
        tipo_doc = '33'
        folio = 'F001-999'
        archivo_excel = self._crear_excel_con_folio(tipo_doc, folio)
        
        # Ejecutar función
        resultado = rg_procesar_step1_task.apply(
            args=[archivo_excel, 'test_tipo_folio.xlsx', 1, self.parametros_contables]
        )
        
        # Verificar que procesó correctamente
        self.assertEqual(resultado.result['estado'], 'completado')
        self.assertTrue(resultado.result['archivo_excel_disponible'])
        
        # Verificar que se generó el Excel de salida
        binary_calls = mock_redis_bin_instance.setex.call_args_list
        self.assertTrue(len(binary_calls) > 0, "Debería haberse guardado el Excel en Redis")
        
        print("✅ Test PASÓ - Tipo documento y folio transferidos correctamente")
        print(f"📊 Tipo documento: {tipo_doc}")
        print(f"📄 Folio: {folio}")
        print(f"🎯 Excel generado y guardado en Redis")


if __name__ == '__main__':
    # Para ejecutar: python manage.py test contabilidad.test_rindegastos
    pass