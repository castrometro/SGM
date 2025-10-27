"""
Script para generar un Excel de prueba para Movimientos del Mes
Formato esperado por procesar_movimientos_mes_con_logging

Este Excel contiene 5 hojas con diferentes tipos de movimientos:
1. Altas/Bajas - Ingresos y finiquitos
2. Ausentismos - Licencias médicas, permisos, etc.
3. Vacaciones - Periodos de vacaciones
4. Variaciones de Sueldo - Cambios en remuneración
5. Variaciones de Contrato - Cambios en tipo de contrato

Headers en fila 3 (índice 2) según estándar del sistema.

USO:
  Desde el contenedor Django (recomendado):
    docker compose cp docs/smoke-tests/flujo-2-movimientos-mes/generar_excel_movimientos_mes.py django:/tmp/
    docker compose exec django python /tmp/generar_excel_movimientos_mes.py
    docker compose cp django:/tmp/movimientos_mes_smoke_test.xlsx docs/smoke-tests/flujo-2-movimientos-mes/

  O ejecutar directamente si tienes pandas instalado:
    cd docs/smoke-tests/flujo-2-movimientos-mes
    python3 generar_excel_movimientos_mes.py
"""
import pandas as pd
from datetime import date, timedelta
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener la ruta del directorio donde está este script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "movimientos_mes_smoke_test.xlsx")
PERIODO = "2025-10"

# ============================================================================
# DATOS - ALTAS Y BAJAS
# ============================================================================

# Empleados que INGRESAN (altas)
altas = [
    {
        "NOMBRE": "Juan Nuevo Empleado",
        "RUT": "66666666-6",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Analista Jr",
        "CENTRO DE COSTO": "Administración",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2025-10-01",
        "FECHA RETIRO": None,
        "TIPO CONTRATO": "Indefinido",
        "DIAS TRABAJADOS": 31,
        "SUELDO BASE": 800000,
        "ALTA / BAJA": "ALTA",
        "MOTIVO": "Nueva contratación"
    },
    {
        "NOMBRE": "María Nueva Empleada",
        "RUT": "77777777-7",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Secretaria",
        "CENTRO DE COSTO": "Administración",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2025-10-01",
        "FECHA RETIRO": None,
        "TIPO CONTRATO": "Plazo Fijo",
        "DIAS TRABAJADOS": 31,
        "SUELDO BASE": 750000,
        "ALTA / BAJA": "ALTA",
        "MOTIVO": "Reemplazo"
    },
    {
        "NOMBRE": "Pedro Nuevo Empleado",
        "RUT": "88888888-8",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Operario",
        "CENTRO DE COSTO": "Producción",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2025-10-15",
        "FECHA RETIRO": None,
        "TIPO CONTRATO": "Indefinido",
        "DIAS TRABAJADOS": 17,
        "SUELDO BASE": 650000,
        "ALTA / BAJA": "ALTA",
        "MOTIVO": "Expansión de planta"
    }
]

# Empleados que SALEN (bajas/finiquitos)
# Estos RUTs corresponden a empleados creados en Flujo 1
bajas = [
    {
        "NOMBRE": "Juan Pérez",
        "RUT": "11111111-1",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Gerente",
        "CENTRO DE COSTO": "Administración",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2020-01-01",
        "FECHA RETIRO": "2025-10-31",
        "TIPO CONTRATO": "Indefinido",
        "DIAS TRABAJADOS": 31,
        "SUELDO BASE": 1000000,
        "ALTA / BAJA": "BAJA",
        "MOTIVO": "Renuncia voluntaria"
    },
    {
        "NOMBRE": "María González",
        "RUT": "22222222-2",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Analista",
        "CENTRO DE COSTO": "Finanzas",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2021-03-15",
        "FECHA RETIRO": "2025-10-31",
        "TIPO CONTRATO": "Indefinido",
        "DIAS TRABAJADOS": 31,
        "SUELDO BASE": 1200000,
        "ALTA / BAJA": "BAJA",
        "MOTIVO": "Término de contrato"
    }
]

# Combinar altas y bajas
altas_bajas_data = altas + bajas

# ============================================================================
# DATOS - AUSENTISMOS
# ============================================================================

ausentismos_data = [
    {
        "NOMBRE": "Pedro Rodríguez",
        "RUT": "33333333-3",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Supervisor",
        "CENTRO DE COSTO": "Operaciones",
        "SUCURSAL": "Casa Matriz",
        "FECHA INICIO AUSENCIA": "2025-10-10",
        "FECHA FIN AUSENCIA": "2025-10-12",
        "DIAS": 3,
        "TIPO DE AUSENTISMO": "Licencia Médica",
        "MOTIVO": "Gripe",
        "OBSERVACIONES": "Certificado médico adjunto"
    },
    {
        "NOMBRE": "Ana Martínez",
        "RUT": "44444444-4",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Contador",
        "CENTRO DE COSTO": "Contabilidad",
        "SUCURSAL": "Casa Matriz",
        "FECHA INICIO AUSENCIA": "2025-10-20",
        "FECHA FIN AUSENCIA": "2025-10-20",
        "DIAS": 1,
        "TIPO DE AUSENTISMO": "Permiso Personal",
        "MOTIVO": "Trámite bancario",
        "OBSERVACIONES": "Con autorización de gerencia"
    }
]

# ============================================================================
# DATOS - VACACIONES
# ============================================================================

vacaciones_data = [
    {
        "NOMBRE": "Carlos López",
        "RUT": "55555555-5",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Asistente",
        "CENTRO DE COSTO": "Ventas",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2022-05-01",
        "FECHA INICIAL": "2025-10-15",
        "FECHA FIN VACACIONES": "2025-10-25",
        "FECHA RETORNO": "2025-10-26",
        "CANTIDAD DE DIAS": 10
    }
]

# ============================================================================
# DATOS - VARIACIONES DE SUELDO
# ============================================================================

variaciones_sueldo_data = [
    {
        "NOMBRE": "Carlos López",
        "RUT": "55555555-5",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Asistente",
        "CENTRO DE COSTO": "Ventas",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2022-05-01",
        "TIPO CONTRATO": "Indefinido",
        "SUELDO BASE ANTERIOR": 950000,
        "SUELDO BASE ACTUAL": 1050000,
        "% DE REAJUSTE": 10.53,
        "VARIACIÓN ($)": 100000
    },
    {
        "NOMBRE": "Pedro Rodríguez",
        "RUT": "33333333-3",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Supervisor",
        "CENTRO DE COSTO": "Operaciones",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2020-07-01",
        "TIPO CONTRATO": "Indefinido",
        "SUELDO BASE ANTERIOR": 900000,
        "SUELDO BASE ACTUAL": 980000,
        "% DE REAJUSTE": 8.89,
        "VARIACIÓN ($)": 80000
    }
]

# ============================================================================
# DATOS - VARIACIONES DE CONTRATO
# ============================================================================

variaciones_contrato_data = [
    {
        "NOMBRE": "Pedro Rodríguez",
        "RUT": "33333333-3",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Supervisor",
        "CENTRO DE COSTO": "Operaciones",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2020-07-01",
        "TIPO CONTRATO ANTERIOR": "Indefinido",
        "TIPO CONTRATO ACTUAL": "Plazo Fijo"
    },
    {
        "NOMBRE": "Ana Martínez",
        "RUT": "44444444-4",
        "EMPRESA": "EMPRESA SMOKE TEST",
        "CARGO": "Contador",
        "CENTRO DE COSTO": "Contabilidad",
        "SUCURSAL": "Casa Matriz",
        "FECHA INGRESO": "2021-06-01",
        "TIPO CONTRATO ANTERIOR": "Jornada Completa",
        "TIPO CONTRATO ACTUAL": "Part-Time"
    }
]

# ============================================================================
# GENERAR EXCEL
# ============================================================================

def generar_excel():
    """Genera el archivo Excel con todas las hojas de movimientos"""
    
    print("🔧 Generando Excel de Movimientos del Mes...")
    
    # Crear DataFrames
    df_altas_bajas = pd.DataFrame(altas_bajas_data)
    df_ausentismos = pd.DataFrame(ausentismos_data)
    df_vacaciones = pd.DataFrame(vacaciones_data)
    df_variaciones_sueldo = pd.DataFrame(variaciones_sueldo_data)
    df_variaciones_contrato = pd.DataFrame(variaciones_contrato_data)
    
    # Crear archivo Excel con múltiples hojas
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Hoja 1: Altas y Bajas
        # Headers en fila 3 (índice 2) - agregar 2 filas vacías antes
        pd.DataFrame([[""], [""]]).to_excel(writer, sheet_name='ALTAS_BAJAS', index=False, header=False)
        df_altas_bajas.to_excel(writer, sheet_name='ALTAS_BAJAS', startrow=2, index=False)
        
        # Hoja 2: Ausentismos
        pd.DataFrame([[""], [""]]).to_excel(writer, sheet_name='AUSENTISMOS', index=False, header=False)
        df_ausentismos.to_excel(writer, sheet_name='AUSENTISMOS', startrow=2, index=False)
        
        # Hoja 3: Vacaciones
        pd.DataFrame([[""], [""]]).to_excel(writer, sheet_name='VACACIONES', index=False, header=False)
        df_vacaciones.to_excel(writer, sheet_name='VACACIONES', startrow=2, index=False)
        
        # Hoja 4: Variaciones de Sueldo
        pd.DataFrame([[""], [""]]).to_excel(writer, sheet_name='VARIACIONES_SUELDO', index=False, header=False)
        df_variaciones_sueldo.to_excel(writer, sheet_name='VARIACIONES_SUELDO', startrow=2, index=False)
        
        # Hoja 5: Variaciones de Contrato
        pd.DataFrame([[""], [""]]).to_excel(writer, sheet_name='VARIACIONES_CONTRATO', index=False, header=False)
        df_variaciones_contrato.to_excel(writer, sheet_name='VARIACIONES_CONTRATO', startrow=2, index=False)
    
    print(f"\n✅ Excel generado exitosamente: {OUTPUT_FILE}")
    print("\n📊 RESUMEN DE MOVIMIENTOS:")
    print(f"   📥 Altas (ingresos): {len(altas)}")
    print(f"   📤 Bajas (finiquitos): {len(bajas)}")
    print(f"   🏥 Ausentismos: {len(ausentismos_data)}")
    print(f"   🏖️  Vacaciones: {len(vacaciones_data)}")
    print(f"   💰 Variaciones de sueldo: {len(variaciones_sueldo_data)}")
    print(f"   📄 Variaciones de contrato: {len(variaciones_contrato_data)}")
    print(f"\n   📦 Total movimientos: {len(altas_bajas_data) + len(ausentismos_data) + len(vacaciones_data) + len(variaciones_sueldo_data) + len(variaciones_contrato_data)}")
    print("\n📍 Ubicación:", OUTPUT_FILE)
    print("\n🎯 Listo para usar en Smoke Test Flujo 2")
    print("   URL: http://172.17.11.18:5174/nomina/cierre/35")
    
    return OUTPUT_FILE

if __name__ == "__main__":
    generar_excel()
