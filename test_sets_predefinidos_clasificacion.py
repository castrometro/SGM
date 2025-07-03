"""
Tests para validar la creación automática y recuperación de sets de clasificación predefinidos
"""
import pytest
from django.test import TestCase
from django.db import transaction
from unittest.mock import patch, MagicMock

from contabilidad.models import ClasificacionSet, ClasificacionOption, UploadLog
from contabilidad.tasks_cuentas_bulk import (
    crear_sets_predefinidos_clasificacion,
    reinstalar_sets_predefinidos_clasificacion,
    recuperar_sets_clasificacion_cliente,
    finalizar_procesamiento_clasificacion_task
)


class MockCliente:
    """Mock del modelo Cliente para tests"""
    def __init__(self, id=1, nombre="Test Cliente", pais="CL", es_bilingue=False):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self.es_bilingue = es_bilingue


class TestSetsPredefinidosClasificacion(TestCase):
    """Tests para validar creación y recuperación de sets predefinidos"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.cliente_mock = MockCliente(id=1, nombre="Cliente Test", es_bilingue=False)
        self.cliente_bilingue_mock = MockCliente(id=2, nombre="Cliente Bilingüe", es_bilingue=True)
    
    @patch('contabilidad.tasks_cuentas_bulk.Cliente')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionSet')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionOption')
    def test_crear_sets_predefinidos_cliente_monolingue(self, mock_option, mock_set, mock_cliente):
        """Test creación de sets predefinidos para cliente monolingüe"""
        # Configurar mocks
        mock_cliente.objects.get.return_value = self.cliente_mock
        mock_set.objects.get_or_create.return_value = (MagicMock(), True)
        mock_option.objects.get_or_create.return_value = (MagicMock(), True)
        
        # Ejecutar función
        resultado = crear_sets_predefinidos_clasificacion(1)
        
        # Validaciones
        self.assertIsInstance(resultado, dict)
        self.assertIn('sets_creados', resultado)
        self.assertIn('opciones_creadas', resultado)
        
        # Verificar que se intentó crear los 4 sets predefinidos
        self.assertEqual(mock_set.objects.get_or_create.call_count, 4)
        
        # Verificar que se crearon opciones (solo en español para cliente monolingüe)
        self.assertGreater(mock_option.objects.get_or_create.call_count, 4)
    
    @patch('contabilidad.tasks_cuentas_bulk.Cliente')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionSet')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionOption')
    def test_crear_sets_predefinidos_cliente_bilingue(self, mock_option, mock_set, mock_cliente):
        """Test creación de sets predefinidos para cliente bilingüe"""
        # Configurar mocks
        mock_cliente.objects.get.return_value = self.cliente_bilingue_mock
        mock_set.objects.get_or_create.return_value = (MagicMock(), True)
        mock_option.objects.get_or_create.return_value = (MagicMock(), True)
        
        # Ejecutar función
        resultado = crear_sets_predefinidos_clasificacion(2)
        
        # Validaciones
        self.assertIsInstance(resultado, dict)
        self.assertIn('sets_creados', resultado)
        self.assertIn('opciones_creadas', resultado)
        
        # Verificar que se intentó crear los 4 sets predefinidos
        self.assertEqual(mock_set.objects.get_or_create.call_count, 4)
        
        # Verificar que se crearon más opciones (español + inglés para cliente bilingüe)
        # Debería ser aproximadamente el doble de opciones
        self.assertGreater(mock_option.objects.get_or_create.call_count, 8)
    
    @patch('contabilidad.tasks_cuentas_bulk.Cliente')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionSet')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionOption')
    def test_reinstalar_sets_predefinidos_con_limpieza(self, mock_option, mock_set, mock_cliente):
        """Test reinstalación de sets predefinidos con limpieza"""
        # Configurar mocks
        mock_cliente.objects.get.return_value = self.cliente_mock
        mock_set_instance = MagicMock()
        mock_set.objects.filter.return_value = [mock_set_instance]
        mock_set.objects.get_or_create.return_value = (MagicMock(), True)
        mock_option.objects.get_or_create.return_value = (MagicMock(), True)
        
        # Ejecutar función con limpieza
        resultado = reinstalar_sets_predefinidos_clasificacion(1, limpiar_existentes=True)
        
        # Validaciones
        self.assertIsInstance(resultado, dict)
        self.assertIn('sets_eliminados', resultado)
        self.assertIn('sets_creados', resultado)
        
        # Verificar que se llamó delete en sets existentes
        mock_set_instance.delete.assert_called()
    
    @patch('contabilidad.tasks_cuentas_bulk.crear_sets_y_opciones_clasificacion_desde_raw')
    @patch('contabilidad.tasks_cuentas_bulk.crear_sets_predefinidos_clasificacion')
    def test_recuperar_sets_clasificacion_cliente_completo(self, mock_predefinidos, mock_raw):
        """Test recuperación completa de sets (RAW + predefinidos)"""
        # Configurar mocks
        mock_raw.return_value = {'sets_creados': 2, 'opciones_creadas': 10}
        mock_predefinidos.return_value = {'sets_creados': 4, 'opciones_creadas': 20}
        
        # Ejecutar función
        resultado = recuperar_sets_clasificacion_cliente(1, incluir_predefinidos=True)
        
        # Validaciones
        self.assertIsInstance(resultado, dict)
        self.assertEqual(resultado['sets_creados'], 6)  # 2 + 4
        self.assertEqual(resultado['opciones_creadas'], 30)  # 10 + 20
        
        # Verificar que se llamaron ambas funciones
        mock_raw.assert_called_once_with(1)
        mock_predefinidos.assert_called_once_with(1)
    
    @patch('contabilidad.tasks_cuentas_bulk.UploadLog')
    @patch('contabilidad.tasks_cuentas_bulk.crear_sets_y_opciones_clasificacion_desde_raw')
    @patch('contabilidad.tasks_cuentas_bulk.crear_sets_predefinidos_clasificacion')
    @patch('contabilidad.tasks_cuentas_bulk.registrar_actividad_tarjeta')
    def test_finalizar_procesamiento_crea_sets_automaticamente(
        self, mock_actividad, mock_predefinidos, mock_raw, mock_upload_log
    ):
        """Test que finalizar_procesamiento_clasificacion_task crea sets automáticamente"""
        # Configurar mocks
        upload_log_mock = MagicMock()
        upload_log_mock.cliente.id = 1
        upload_log_mock.estado = "procesando"
        upload_log_mock.ruta_archivo = None
        upload_log_mock.cierre = None
        upload_log_mock.resumen = {'registros_guardados': 100, 'errores_count': 0}
        
        mock_upload_log.objects.get.return_value = upload_log_mock
        mock_raw.return_value = {'sets_creados': 2, 'opciones_creadas': 10}
        mock_predefinidos.return_value = {'sets_creados': 4, 'opciones_creadas': 20}
        
        # Ejecutar función
        with patch('os.path.exists', return_value=False):
            resultado = finalizar_procesamiento_clasificacion_task(1)
        
        # Validaciones
        self.assertIn("Completado", resultado)
        
        # Verificar que se llamaron las funciones de creación de sets
        mock_raw.assert_called_once_with(1)
        mock_predefinidos.assert_called_once_with(1)
        
        # Verificar que se actualizó el estado
        self.assertEqual(upload_log_mock.estado, "completado")
        upload_log_mock.save.assert_called()
        
        # Verificar que se registró la actividad
        mock_actividad.assert_called_once()


class TestValidacionSetsObligatorios(TestCase):
    """Tests para validar que siempre existen los sets obligatorios"""
    
    SETS_OBLIGATORIOS = [
        "Tipo de Cuenta",
        "Clasificacion Balance", 
        "Categoria IFRS",
        "AGRUPACION CLIENTE"
    ]
    
    @patch('contabilidad.tasks_cuentas_bulk.Cliente')
    @patch('contabilidad.tasks_cuentas_bulk.ClasificacionSet')
    def test_sets_obligatorios_siempre_creados(self, mock_set, mock_cliente):
        """Test que valida que siempre se crean los 4 sets obligatorios"""
        # Configurar mocks
        mock_cliente.objects.get.return_value = MockCliente()
        mock_set.objects.get_or_create.return_value = (MagicMock(), True)
        
        # Ejecutar función
        crear_sets_predefinidos_clasificacion(1)
        
        # Verificar que se intentaron crear exactamente los 4 sets obligatorios
        llamadas_set = mock_set.objects.get_or_create.call_args_list
        sets_creados = [call[1]['nombre'] for call in llamadas_set]
        
        for set_obligatorio in self.SETS_OBLIGATORIOS:
            self.assertIn(set_obligatorio, sets_creados)


if __name__ == '__main__':
    # Instrucciones para ejecutar los tests
    print("Para ejecutar estos tests:")
    print("python manage.py test contabilidad.tests.test_sets_predefinidos")
    print("")
    print("O para ejecutar un test específico:")
    print("python manage.py test contabilidad.tests.test_sets_predefinidos.TestSetsPredefinidosClasificacion.test_crear_sets_predefinidos_cliente_monolingue")
