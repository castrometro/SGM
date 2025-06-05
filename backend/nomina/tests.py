from django.test import SimpleTestCase
import pandas as pd
from tempfile import NamedTemporaryFile

from nomina.utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones


class ObtenerHeadersLibroRemuneracionesTests(SimpleTestCase):
    def test_employee_columns_removed(self):
        df = pd.DataFrame({
            'Año': [2024],
            'Mes': [5],
            'Rut de la Empresa': ['12345678-9'],
            'Rut del Trabajador': ['11111111'],
            'DV Trabajador': ['1'],
            'Nombre': ['Ana'],
            'Apellido Paterno': ['Gomez'],
            'Apellido Materno': ['Luna'],
            'SUELDO BASE': [1000],
            'BONO': [100],
        })
        with NamedTemporaryFile(suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False)
            headers = obtener_headers_libro_remuneraciones(tmp.name)

        self.assertEqual(headers, ['SUELDO BASE', 'BONO'])

