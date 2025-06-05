from django.test import SimpleTestCase
import pandas as pd
from tempfile import NamedTemporaryFile

from nomina.utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones


class ObtenerHeadersLibroRemuneracionesTests(SimpleTestCase):
    def _get_headers(self, data):
        df = pd.DataFrame(data)
        with NamedTemporaryFile(suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False)
            return obtener_headers_libro_remuneraciones(tmp.name)

    def test_employee_columns_removed(self):
        headers = self._get_headers({
            'A\u00d1O': [2024],
            'MES': [5],
            'RUT_EMPRESA': ['12345678-9'],
            'RUT_TRABAJADOR': ['11111111'],
            'DV_TRABAJADOR': ['1'],
            'NOMBRES': ['Ana'],
            'APELLIDO_PATERNO': ['Gomez'],
            'APELLIDO_MATERNO': ['Luna'],
            'SUELDO BASE': [1000],
            'BONO': [100],
        })

        self.assertEqual(headers, ['SUELDO BASE', 'BONO'])

    def test_rut_empresa_with_spaces_removed(self):
        headers = self._get_headers({
            'Rut de la Empresa': ['12345678-9'],
            'RUT_TRABAJADOR': ['11111111'],
            'NOMBRES': ['Ana'],
            'SUELDO BASE': [1000],
        })

        self.assertEqual(headers, ['SUELDO BASE'])

    def test_sample_excel_headers_removed(self):
        headers = self._get_headers({
            'A\u00f1o': [2024],
            'Mes': [5],
            'Rut de la Empresa': ['12345678-9'],
            'Rut del Trabajador': ['11111111'],
            'Nombre': ['Ana'],
            'Apellido Paterno': ['Gomez'],
            'Apellido Materno': ['Luna'],
            'Sueldo Base': [1000],
        })
        self.assertEqual(headers, ['Sueldo Base'])

