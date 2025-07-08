#!/usr/bin/env python
"""
Script para probar la nueva lógica de validación de clasificaciones
que exige clasificación en TODOS los sets, salvo excepciones específicas.
"""

import os
import sys
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('/root/SGM/backend')
django.setup()

from contabilidad.models import (
    Cliente, 
    CierreContable, 
    CuentaContable, 
    MovimientoContable,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
    ExcepcionClasificacionSet,
    Incidencia,
    UploadLog
)
from contabilidad.tasks_libro_mayor import generar_incidencias_libro_mayor
from django.contrib.auth import get_user_model

User = get_user_model()

def crear_datos_prueba():
    """Crear datos de prueba para validar la nueva lógica"""
    print("🔧 Creando datos de prueba...")
    
    # Crear cliente de prueba
    cliente, created = Cliente.objects.get_or_create(
        nombre="Test Clasificaciones",
        defaults={
            'rut': '12345678-9',
            'bilingue': True
        }
    )
    print(f"✓ Cliente: {cliente.nombre} ({'creado' if created else 'existente'})")
    
    # Crear cierre contable
    cierre, created = CierreContable.objects.get_or_create(
        cliente=cliente,
        periodo=202412,
        defaults={'estado': 'procesando'}
    )
    print(f"✓ Cierre: {cierre.periodo} ({'creado' if created else 'existente'})")
    
    # Crear upload log
    user, _ = User.objects.get_or_create(
        correo_bdo='test@test.com',
        defaults={'nombre': 'Test User'}
    )
    
    upload_log, created = UploadLog.objects.get_or_create(
        cliente=cliente,
        cierre=cierre,
        tipo_upload='libro_mayor',
        defaults={
            'nombre_archivo_original': 'test_libro_mayor.xlsx',
            'estado': 'procesando',
            'creada_por': user
        }
    )
    print(f"✓ UploadLog: {upload_log.id} ({'creado' if created else 'existente'})")
    
    # Crear sets de clasificación
    set1, created = ClasificacionSet.objects.get_or_create(
        cliente=cliente,
        nombre='Balance Sheet',
        defaults={'descripcion': 'Clasificación de balance'}
    )
    print(f"✓ Set 1: {set1.nombre} ({'creado' if created else 'existente'})")
    
    set2, created = ClasificacionSet.objects.get_or_create(
        cliente=cliente,
        nombre='Income Statement',
        defaults={'descripcion': 'Clasificación estado de resultados'}
    )
    print(f"✓ Set 2: {set2.nombre} ({'creado' if created else 'existente'})")
    
    # Crear opciones de clasificación
    option1_set1, _ = ClasificacionOption.objects.get_or_create(
        set_clasificacion=set1,
        valor_es='Activos',
        defaults={'valor_en': 'Assets'}
    )
    
    option1_set2, _ = ClasificacionOption.objects.get_or_create(
        set_clasificacion=set2,
        valor_es='Ingresos',
        defaults={'valor_en': 'Revenue'}
    )
    
    # Crear cuentas contables
    cuenta1, created = CuentaContable.objects.get_or_create(
        cliente=cliente,
        codigo='1101',
        defaults={'nombre': 'Caja'}
    )
    print(f"✓ Cuenta 1: {cuenta1.codigo} ({'creada' if created else 'existente'})")
    
    cuenta2, created = CuentaContable.objects.get_or_create(
        cliente=cliente,
        codigo='1102',
        defaults={'nombre': 'Banco'}
    )
    print(f"✓ Cuenta 2: {cuenta2.codigo} ({'creada' if created else 'existente'})")
    
    cuenta3, created = CuentaContable.objects.get_or_create(
        cliente=cliente,
        codigo='4101',
        defaults={'nombre': 'Ventas'}
    )
    print(f"✓ Cuenta 3: {cuenta3.codigo} ({'creada' if created else 'existente'})")
    
    # Crear movimientos contables para que las cuentas aparezcan en el cierre
    MovimientoContable.objects.get_or_create(
        cierre=cierre,
        cuenta=cuenta1,
        defaults={
            'debe': 1000,
            'haber': 0,
            'descripcion': 'Movimiento prueba',
            'tipo_doc_codigo': 'FAC'
        }
    )
    
    MovimientoContable.objects.get_or_create(
        cierre=cierre,
        cuenta=cuenta2,
        defaults={
            'debe': 2000,
            'haber': 0,
            'descripcion': 'Movimiento prueba',
            'tipo_doc_codigo': 'FAC'
        }
    )
    
    MovimientoContable.objects.get_or_create(
        cierre=cierre,
        cuenta=cuenta3,
        defaults={
            'debe': 0,
            'haber': 3000,
            'descripcion': 'Movimiento prueba',
            'tipo_doc_código': 'FAC'
        }
    )
    
    print("✓ Movimientos contables creados")
    
    # Configurar clasificaciones parciales para probar la lógica
    # Cuenta1: clasificada solo en set1
    AccountClassification.objects.get_or_create(
        cuenta=cuenta1,
        clasificacion_option=option1_set1
    )
    print(f"✓ Cuenta {cuenta1.codigo} clasificada en {set1.nombre}")
    
    # Cuenta2: no clasificada en ningún set
    # Cuenta3: clasificada en ambos sets
    AccountClassification.objects.get_or_create(
        cuenta=cuenta3,
        clasificacion_option=option1_set1
    )
    AccountClassification.objects.get_or_create(
        cuenta=cuenta3,
        clasificacion_option=option1_set2
    )
    print(f"✓ Cuenta {cuenta3.codigo} clasificada en ambos sets")
    
    # Crear excepción para cuenta2 en set2 (para probar excepciones)
    ExcepcionClasificacionSet.objects.get_or_create(
        cliente=cliente,
        set_clasificacion=set2,
        codigo_cuenta=cuenta2.codigo,
        defaults={
            'razon': 'Cuenta de balance, no aplica clasificación de estado de resultados',
            'activa': True
        }
    )
    print(f"✓ Excepción creada para cuenta {cuenta2.codigo} en set {set2.nombre}")
    
    return upload_log, cliente, cierre, [set1, set2], [cuenta1, cuenta2, cuenta3]

def probar_nueva_logica():
    """Probar la nueva lógica de validación"""
    print("\n🧪 Probando nueva lógica de validación...")
    
    upload_log, cliente, cierre, sets, cuentas = crear_datos_prueba()
    
    # Limpiar incidencias anteriores
    Incidencia.objects.filter(cierre=cierre).delete()
    
    # Ejecutar la función de generación de incidencias
    print("\n🚀 Ejecutando generar_incidencias_libro_mayor...")
    try:
        resultado = generar_incidencias_libro_mayor(upload_log.id, 'test@test.com')
        print(f"✓ Función ejecutada exitosamente: {resultado}")
    except Exception as e:
        print(f"❌ Error ejecutando función: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verificar incidencias generadas
    print("\n📊 Analizando incidencias generadas:")
    incidencias = Incidencia.objects.filter(
        cierre=cierre,
        tipo=Incidencia.CUENTA_NO_CLASIFICADA
    ).order_by('cuenta_codigo', 'descripcion')
    
    print(f"Total incidencias de clasificación: {incidencias.count()}")
    
    for incidencia in incidencias:
        print(f"  • {incidencia.cuenta_codigo}: {incidencia.descripcion}")
    
    # Verificar lógica esperada
    print("\n🔍 Verificando lógica esperada:")
    
    # Cuenta1 (1101): debería tener incidencia en set2 (Income Statement)
    # ya que está clasificada solo en set1
    incidencia_1101_set2 = incidencias.filter(
        cuenta_codigo='1101',
        descripcion__contains='Income Statement'
    )
    if incidencia_1101_set2.exists():
        print("✓ Cuenta 1101: Correctamente marcada como sin clasificación en Income Statement")
    else:
        print("❌ Cuenta 1101: Falta incidencia en Income Statement")
    
    # Cuenta2 (1102): debería tener incidencia solo en set1 (Balance Sheet)
    # ya que tiene excepción en set2
    incidencia_1102_set1 = incidencias.filter(
        cuenta_codigo='1102',
        descripcion__contains='Balance Sheet'
    )
    incidencia_1102_set2 = incidencias.filter(
        cuenta_codigo='1102',
        descripcion__contains='Income Statement'
    )
    
    if incidencia_1102_set1.exists() and not incidencia_1102_set2.exists():
        print("✓ Cuenta 1102: Correctamente marcada sin clasificación en Balance Sheet pero excenta en Income Statement")
    else:
        print("❌ Cuenta 1102: Lógica de excepciones no funciona correctamente")
    
    # Cuenta3 (4101): no debería tener incidencias (está clasificada en ambos sets)
    incidencia_4101 = incidencias.filter(cuenta_codigo='4101')
    if not incidencia_4101.exists():
        print("✓ Cuenta 4101: Correctamente sin incidencias (clasificada en todos los sets)")
    else:
        print("❌ Cuenta 4101: No debería tener incidencias")
    
    # Verificar excepciones
    print("\n🛡️ Verificando excepciones:")
    excepciones = ExcepcionClasificacionSet.objects.filter(cliente=cliente, activa=True)
    for excepcion in excepciones:
        print(f"  • Cuenta {excepcion.codigo_cuenta} en set '{excepcion.set_clasificacion.nombre}': {excepcion.razon}")

def limpiar_datos_prueba():
    """Limpiar datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    try:
        # Eliminar en orden correcto para evitar problemas de FK
        cliente = Cliente.objects.filter(nombre="Test Clasificaciones").first()
        if cliente:
            cliente.delete()
            print("✓ Datos de prueba eliminados")
        else:
            print("• No hay datos de prueba que limpiar")
    except Exception as e:
        print(f"❌ Error limpiando datos: {e}")

if __name__ == "__main__":
    print("🔬 Iniciando pruebas de nueva lógica de clasificaciones")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            probar_nueva_logica()
            
            respuesta = input("\n¿Desea conservar los datos de prueba? (s/n): ").lower()
            if respuesta != 's':
                print("Revirtiendo transacción...")
                raise Exception("Revertir por solicitud del usuario")
            else:
                print("✓ Datos de prueba conservados")
                
    except Exception as e:
        if "Revertir por solicitud del usuario" in str(e):
            print("✓ Datos de prueba eliminados (transacción revertida)")
        else:
            print(f"❌ Error en las pruebas: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🏁 Pruebas finalizadas")
