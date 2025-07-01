#!/usr/bin/env python
"""
Script para validar que la corrección en el Libro Mayor funciona correctamente.
Simula el procesamiento de un archivo de Libro Mayor y verifica que:
1. Los movimientos se procesen correctamente
2. Las incidencias se generen apropiadamente 
3. El resumen no sobrescriba los valores de movimientos_creados
"""
import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from api.models import Cliente, UploadLog
from contabilidad.models import CierreContable, MovimientoContable, CuentaContable, Incidencia
from django.contrib.auth.models import User

def crear_datos_prueba():
    """Crear datos de prueba para validar la corrección"""
    print("🔧 Creando datos de prueba...")
    
    # Crear usuario si no existe
    usuario, created = User.objects.get_or_create(
        username="test_admin",
        defaults={
            "email": "test@example.com",
            "is_staff": True,
            "is_superuser": True
        }
    )
    
    # Crear cliente si no existe
    cliente, created = Cliente.objects.get_or_create(
        nombre="CLIENTE PRUEBA VALIDACION",
        defaults={
            "activo": True,
            "observaciones": "Cliente de prueba para validar corrección Libro Mayor"
        }
    )
    
    # Crear cierre
    cierre = CierreContable.objects.create(
        cliente=cliente,
        mes="2024-12",
        estado="procesando",
        observaciones="Prueba validación corrección Libro Mayor"
    )
    
    # Crear algunas cuentas
    cuentas = []
    for i in range(1, 4):
        cuenta = CuentaContable.objects.create(
            cliente=cliente,
            codigo=f"1100{i:02d}",
            nombre=f"Cuenta de Prueba {i}",
            tipo="Activo",
            # Una cuenta sin nombre en inglés para generar incidencia
            nombre_en=f"Test Account {i}" if i < 3 else None
        )
        cuentas.append(cuenta)
    
    return usuario, cliente, cierre, cuentas


def simular_procesamiento_inicial(upload_log):
    """Simula el procesamiento inicial que normalmente hace la task 4"""
    print("📊 Simulando procesamiento inicial de movimientos...")
    
    # Simular que se procesaron movimientos exitosamente
    movimientos_procesados = 150  # Valor ejemplo
    errores_procesamiento = 5
    
    # Crear algunos movimientos reales
    from contabilidad.models import CuentaContable
    cuentas = CuentaContable.objects.filter(cliente=upload_log.cliente)[:3]
    
    movimientos_creados = 0
    for i, cuenta in enumerate(cuentas):
        mov = MovimientoContable.objects.create(
            cierre=upload_log.cierre,
            cuenta=cuenta,
            fecha=datetime.now().date(),
            debe=1000 * (i + 1),
            haber=0,
            saldo=1000 * (i + 1),
            descripcion=f"Movimiento de prueba {i+1}",
            # Algunos movimientos incompletos para generar incidencias
            flag_incompleto=(i == 2),
            tipo_doc_codigo="DOC01" if i == 2 else None
        )
        movimientos_creados += 1
    
    # Simular resumen después del procesamiento inicial (task 4)
    resumen_inicial = {
        'movimientos_creados': movimientos_procesados,  # Valor correcto del procesamiento
        'procesamiento': {
            'movimientos_creados': movimientos_procesados,
            'errores': errores_procesamiento,
            'archivo_procesado': True,
            'filas_procesadas': movimientos_procesados + errores_procesamiento
        }
    }
    
    upload_log.resumen = resumen_inicial
    upload_log.save()
    
    print(f"✅ Simulación inicial completada: {movimientos_procesados} movimientos procesados")
    return movimientos_procesados


def ejecutar_task_incidencias(upload_log_id):
    """Ejecuta manualmente la task de generación de incidencias"""
    print("🔍 Ejecutando task de generación de incidencias...")
    
    from contabilidad.tasks_libro_mayor import generar_incidencias_libro_mayor
    
    # Obtener el task como función (no como Celery task)
    task_func = generar_incidencias_libro_mayor
    
    # Crear un mock del self parameter
    class MockTask:
        pass
    
    mock_self = MockTask()
    
    # Ejecutar la función
    resultado = task_func(mock_self, upload_log_id)
    print(f"✅ Task de incidencias ejecutada, resultado: {resultado}")
    
    return resultado


def validar_resultado(upload_log, movimientos_esperados):
    """Valida que el resultado sea correcto"""
    print("🔎 Validando resultado...")
    
    # Refrescar el upload_log
    upload_log.refresh_from_db()
    
    resumen = upload_log.resumen or {}
    movimientos_en_resumen = resumen.get('movimientos_creados', 0)
    incidencias_creadas = resumen.get('incidencias_creadas', 0)
    
    print(f"📋 RESUMEN FINAL:")
    print(f"   Movimientos esperados: {movimientos_esperados}")
    print(f"   Movimientos en resumen: {movimientos_en_resumen}")
    print(f"   Incidencias creadas: {incidencias_creadas}")
    print(f"   Resumen completo: {json.dumps(resumen, indent=2, default=str)}")
    
    # Validaciones
    validaciones_exitosas = 0
    total_validaciones = 3
    
    # 1. Verificar que no se sobrescribió el valor de movimientos
    if movimientos_en_resumen == movimientos_esperados:
        print("✅ VALIDACIÓN 1 EXITOSA: Los movimientos no se sobrescribieron")
        validaciones_exitosas += 1
    else:
        print(f"❌ VALIDACIÓN 1 FALLIDA: Esperado {movimientos_esperados}, obtenido {movimientos_en_resumen}")
    
    # 2. Verificar que se crearon incidencias
    total_incidencias_db = Incidencia.objects.filter(cierre=upload_log.cierre).count()
    if incidencias_creadas > 0 and total_incidencias_db > 0:
        print(f"✅ VALIDACIÓN 2 EXITOSA: Se crearon {incidencias_creadas} incidencias")
        validaciones_exitosas += 1
    else:
        print(f"❌ VALIDACIÓN 2 FALLIDA: No se crearon incidencias apropiadamente")
    
    # 3. Verificar estructura del resumen
    if 'incidencias' in resumen and 'procesamiento' in resumen:
        print("✅ VALIDACIÓN 3 EXITOSA: Estructura del resumen es correcta")
        validaciones_exitosas += 1
    else:
        print("❌ VALIDACIÓN 3 FALLIDA: Estructura del resumen incorrecta")
    
    return validaciones_exitosas == total_validaciones


def main():
    """Función principal de validación"""
    print("🚀 INICIANDO VALIDACIÓN DE CORRECCIÓN LIBRO MAYOR 🚀")
    print("=" * 60)
    
    try:
        # 1. Crear datos de prueba
        usuario, cliente, cierre, cuentas = crear_datos_prueba()
        
        # 2. Crear UploadLog
        upload_log = UploadLog.objects.create(
            usuario=usuario,
            cliente=cliente,
            tipo_archivo="libro_mayor",
            archivo_original="test_libro_mayor.xlsx",
            estado="procesando",
            cierre=cierre
        )
        
        print(f"📄 UploadLog creado con ID: {upload_log.id}")
        
        # 3. Simular procesamiento inicial
        movimientos_esperados = simular_procesamiento_inicial(upload_log)
        
        # 4. Ejecutar task de incidencias
        ejecutar_task_incidencias(upload_log.id)
        
        # 5. Validar resultado
        resultado_exitoso = validar_resultado(upload_log, movimientos_esperados)
        
        print("\n" + "=" * 60)
        if resultado_exitoso:
            print("🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE 🎉")
            print("✅ La corrección funciona correctamente")
            print("✅ Los movimientos no se sobrescriben")
            print("✅ Las incidencias se generan apropiadamente")
        else:
            print("❌ VALIDACIÓN FALLIDA")
            print("⚠️  La corrección necesita revisión")
        
        print("\n📊 Datos de prueba creados:")
        print(f"   Cliente: {cliente.nombre}")
        print(f"   Cierre: {cierre.mes}")
        print(f"   UploadLog ID: {upload_log.id}")
        print(f"   Cuentas creadas: {len(cuentas)}")
        
        return resultado_exitoso
        
    except Exception as e:
        print(f"❌ ERROR DURANTE LA VALIDACIÓN: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    exitoso = main()
    sys.exit(0 if exitoso else 1)
