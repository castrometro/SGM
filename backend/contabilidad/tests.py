from django.test import TestCase
from rest_framework.test import APIClient
from api.models import Cliente, Usuario, Area
from contabilidad.models import (
    CierreContabilidad,
    CuentaContable,
    AperturaCuenta,
    MovimientoContable,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
)
from contabilidad.utils import obtener_cierre_activo


class MovimientosResumenTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        area = Area.objects.create(nombre="Contabilidad")
        self.user = Usuario.objects.create_user(
            correo_bdo="gerente@test.com",
            password="pass",
            nombre="Gerente",
            apellido="Test",
            tipo_usuario="gerente",
        )
        self.user.areas.add(area)

        self.cliente = Cliente.objects.create(nombre="Cliente", rut="1-9")
        self.cierre = CierreContabilidad.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            area=area,
            periodo="2024-01",
        )

        self.c1 = CuentaContable.objects.create(
            cliente=self.cliente, codigo="1001", nombre="Caja"
        )
        self.c2 = CuentaContable.objects.create(
            cliente=self.cliente, codigo="1002", nombre="Banco"
        )

        AperturaCuenta.objects.create(
            cierre=self.cierre, cuenta=self.c1, saldo_anterior=100
        )
        AperturaCuenta.objects.create(
            cierre=self.cierre, cuenta=self.c2, saldo_anterior=200
        )

        MovimientoContable.objects.create(
            cierre=self.cierre, cuenta=self.c1, fecha="2024-01-01", debe=50, haber=0
        )
        MovimientoContable.objects.create(
            cierre=self.cierre, cuenta=self.c1, fecha="2024-01-02", debe=0, haber=20
        )
        MovimientoContable.objects.create(
            cierre=self.cierre, cuenta=self.c2, fecha="2024-01-01", debe=10, haber=5
        )

        self.client.force_authenticate(user=self.user)

    def test_resumen_totales(self):
        url = f"/api/contabilidad/cierres/{self.cierre.id}/movimientos-resumen/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = {d["cuenta_id"]: d for d in response.json()}

        c1 = data[self.c1.id]
        self.assertEqual(float(c1["total_debe"]), 50)
        self.assertEqual(float(c1["total_haber"]), 20)
        self.assertEqual(float(c1["saldo_final"]), 130)

        c2 = data[self.c2.id]
        self.assertEqual(float(c2["total_debe"]), 10)
        self.assertEqual(float(c2["total_haber"]), 5)
        self.assertEqual(float(c2["saldo_final"]), 205)

    def test_filtrado_por_clasificacion(self):
        set1 = ClasificacionSet.objects.create(cliente=self.cliente, nombre="Tipo")
        opt1 = ClasificacionOption.objects.create(set_clas=set1, valor="A")
        opt2 = ClasificacionOption.objects.create(set_clas=set1, valor="B")

        AccountClassification.objects.create(cuenta=self.c1, set_clas=set1, opcion=opt1, asignado_por=self.user)
        AccountClassification.objects.create(cuenta=self.c2, set_clas=set1, opcion=opt2, asignado_por=self.user)

        url = f"/api/contabilidad/cierres/{self.cierre.id}/movimientos-resumen/?set_id={set1.id}&opcion_id={opt1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["cuenta_id"], self.c1.id)


class ObtenerCierreActivoTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Contabilidad")
        self.user = Usuario.objects.create_user(
            correo_bdo="tester@test.com",
            password="pass",
            nombre="Tester",
            apellido="User",
            tipo_usuario="gerente",
        )
        self.user.areas.add(area)
        self.cliente = Cliente.objects.create(nombre="Cliente", rut="1-9")
        self.cierre1 = CierreContabilidad.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            area=area,
            periodo="2024-01",
            estado="pendiente",
        )
        self.cierre2 = CierreContabilidad.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            area=area,
            periodo="2024-02",
            estado="clasificacion",
        )

    def test_devuelve_cierre_por_id(self):
        cierre = obtener_cierre_activo(self.cliente, self.cierre1.id)
        self.assertEqual(cierre, self.cierre1)

    def test_devuelve_ultimo_cierre_activo(self):
        cierre = obtener_cierre_activo(self.cliente)
        self.assertEqual(cierre, self.cierre2)

    def test_cierre_id_invalido_devuelve_ultimo(self):
        cierre = obtener_cierre_activo(self.cliente, 99999)
        self.assertEqual(cierre, self.cierre2)

    def test_sin_cierre_abierto(self):
        self.cierre1.estado = "completo"
        self.cierre1.save()
        self.cierre2.estado = "aprobado"
        self.cierre2.save()
        cierre = obtener_cierre_activo(self.cliente)
        self.assertIsNone(cierre)

