from django.test import SimpleTestCase, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from nomina.models import (
    Cliente,
    CierreNomina,
    LibroRemuneracionesUpload,
    EmpleadoCierre,
    ConceptoRemuneracion,
    RegistroConceptoEmpleado,
)
from nomina.tasks import actualizar_empleados_desde_libro, guardar_registros_nomina
import pandas as pd
from tempfile import NamedTemporaryFile

from nomina.utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones


class ObtenerHeadersLibroRemuneracionesTests(SimpleTestCase):
    def test_employee_columns_removed(self):
        df = pd.DataFrame(
            {
                "Año": [2024],
                "Mes": [5],
                "Rut de la Empresa": ["12345678-9"],
                "Rut del Trabajador": ["11111111"],
                "DV Trabajador": ["1"],
                "Nombre": ["Ana"],
                "Apellido Paterno": ["Gomez"],
                "Apellido Materno": ["Luna"],
                "SUELDO BASE": [1000],
                "BONO": [100],
            }
        )
        with NamedTemporaryFile(suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False)
            headers = obtener_headers_libro_remuneraciones(tmp.name)

        self.assertEqual(headers, ["SUELDO BASE", "BONO"])


class GuardarRegistrosNominaTests(TestCase):
    databases = {"default"}

    def setUp(self):
        self.cliente = Cliente.objects.create(nombre="Test")
        self.cierre = CierreNomina.objects.create(
            cliente=self.cliente, periodo="2025-01"
        )

        df = pd.DataFrame(
            {
                "Año": [2025],
                "Mes": [1],
                "Rut de la Empresa": ["12345678-9"],
                "Rut del Trabajador": ["11111111"],
                "Nombre": ["Ana"],
                "Apellido Paterno": ["Gomez"],
                "Apellido Materno": ["Luna"],
                "SUELDO BASE": [1000],
            }
        )
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            tmp.seek(0)
            content = tmp.read()

        upload = SimpleUploadedFile("libro.xlsx", content)
        self.libro = LibroRemuneracionesUpload.objects.create(
            cierre=self.cierre,
            archivo=upload,
            header_json=["SUELDO BASE"],
        )

    def test_tasks_create_registros(self):
        actualizar_empleados_desde_libro({"libro_id": self.libro.id})
        ConceptoRemuneracion.objects.create(
            cliente=self.cliente, nombre_concepto="SUELDO BASE", clasificacion="haber"
        )
        guardar_registros_nomina({"libro_id": self.libro.id})

        empleado = EmpleadoCierre.objects.get(cierre=self.cierre, rut="11111111")
        registro = RegistroConceptoEmpleado.objects.get(
            empleado=empleado, nombre_concepto_original="SUELDO BASE"
        )
        self.assertEqual(registro.monto, 1000)
        self.assertIsNotNone(registro.concepto)
