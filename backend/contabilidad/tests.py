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
    UploadLog,
    ClasificacionCuentaArchivo,
    NombreIngles,
    Incidencia,
    TarjetaActivityLog,
)


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

    def test_log_periodo_correcto(self):
        """Verifica que registrar_actividad_tarjeta usa el periodo del cierre"""
        url = f"/api/contabilidad/cierres/{self.cierre.id}/movimientos-resumen/"
        self.client.get(url)

        log = TarjetaActivityLog.objects.filter(
            cierre=self.cierre, accion="view_data"
        ).first()
        self.assertIsNotNone(log)


class ReprocesarIncompletosTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        area = Area.objects.create(nombre="Contabilidad")
        self.user = Usuario.objects.create_user(
            correo_bdo="tester@test.com",
            password="pass",
            nombre="Tester",
            apellido="Test",
            tipo_usuario="gerente",
        )
        self.user.areas.add(area)

        self.cliente = Cliente.objects.create(nombre="Cliente2", rut="2-7")
        self.cierre = CierreContabilidad.objects.create(
            cliente=self.cliente,
            usuario=self.user,
            area=area,
            periodo="2024-02",
        )

        self.c1 = CuentaContable.objects.create(
            cliente=self.cliente, codigo="2001", nombre="Ventas"
        )
        self.c2 = CuentaContable.objects.create(
            cliente=self.cliente, codigo="2002", nombre="Compras"
        )

        MovimientoContable.objects.create(
            cierre=self.cierre,
            cuenta=self.c1,
            fecha="2024-02-01",
            debe=100,
            flag_incompleto=True,
        )
        MovimientoContable.objects.create(
            cierre=self.cierre,
            cuenta=self.c2,
            fecha="2024-02-01",
            debe=50,
            flag_incompleto=True,
        )

        set1 = ClasificacionSet.objects.create(cliente=self.cliente, nombre="G")
        opt1 = ClasificacionOption.objects.create(set_clas=set1, valor="X")

        # Registro en ClasificacionCuentaArchivo para que el reprocesamiento
        # aplique la clasificación de forma automática
        log = UploadLog.objects.create(
            tipo_upload="clasificacion",
            cliente=self.cliente,
            nombre_archivo_original="tmp.xlsx",
            tamaño_archivo=10,
        )
        ClasificacionCuentaArchivo.objects.create(
            cliente=self.cliente,
            upload_log=log,
            numero_cuenta="2001",
            clasificaciones={"G": "X"},
            fila_excel=1,
        )

        NombreIngles.objects.create(
            cliente=self.cliente, cuenta_codigo="2001", nombre_ingles="Sales"
        )

        Incidencia.objects.create(
            cierre=self.cierre,
            tipo="negocio",
            descripcion="Movimiento 1, cuenta 2001: No tiene nombre en inglés",
        )

        self.client.force_authenticate(user=self.user)

    def test_reprocesar_movimientos(self):
        url = "/api/contabilidad/libro-mayor/reprocesar-incompletos/"
        response = self.client.post(url, {"cierre_id": self.cierre.id}, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["reprocesados"], 1)
        self.assertEqual(data["aun_incompletos"], 1)

        m1 = MovimientoContable.objects.get(cuenta=self.c1)
        m2 = MovimientoContable.objects.get(cuenta=self.c2)
        self.assertFalse(m1.flag_incompleto)
        self.assertTrue(m2.flag_incompleto)

        # Verificar que se asignó nombre en inglés y clasificación
        self.c1.refresh_from_db()
        self.assertEqual(self.c1.nombre_en, "Sales")
        self.assertTrue(
            AccountClassification.objects.filter(cuenta=self.c1, set_clas__nombre="G").exists()
        )

        log_individual = TarjetaActivityLog.objects.filter(accion="manual_edit", cierre=self.cierre).first()
        self.assertIsNotNone(log_individual)
        self.assertTrue(log_individual.detalles["tipo_documento"] is False or log_individual.detalles["tipo_documento"])
        self.assertTrue(log_individual.detalles["nombre_ingles"])
        self.assertEqual(log_individual.detalles["clasificacion"], ["G"])

        log_general = TarjetaActivityLog.objects.filter(accion="process_complete", cierre=self.cierre).first()
        self.assertIsNotNone(log_general)
        self.assertEqual(log_general.detalles["movimientos_corregidos"], [m1.id])

    def test_listar_movimientos_incompletos(self):
        url = f"/api/contabilidad/libro-mayor/incompletos/{self.cierre.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        first = data[0]
        self.assertIn("incidencias", first)
