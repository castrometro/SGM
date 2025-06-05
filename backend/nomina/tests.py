from django.test import SimpleTestCase
import pandas as pd
from tempfile import NamedTemporaryFile

from nomina.utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones


class ObtenerHeadersLibroRemuneracionesTests(SimpleTestCase):
    def test_employee_columns_removed(self):
        df = pd.DataFrame({
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
        with NamedTemporaryFile(suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False)
            headers = obtener_headers_libro_remuneraciones(tmp.name)

        self.assertEqual(headers, ['SUELDO BASE', 'BONO'])

