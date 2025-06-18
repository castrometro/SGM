import pandas as pd
import json
import pathlib
from datetime import datetime, timedelta
import random

def cargar_datos():
    """
    Carga datos simulados basados en los modelos reales de contabilidad
    """
    # Simular un cierre contable específico
    cierre_data = {
        'id': 1,
        'cliente': 'Empresa ABC S.A.',
        'periodo': '2024-12',
        'estado': 'completo',
        'fecha_inicio_libro': '2024-12-01',
        'fecha_fin_libro': '2024-12-31',
        'cuentas_nuevas': 5,
        'parsing_completado': True
    }
    
    # Generar movimientos contables simulados
    movimientos = generar_movimientos_simulados()
    
    # Generar plan de cuentas
    plan_cuentas = generar_plan_cuentas()
    
    # Generar clasificaciones
    clasificaciones = generar_clasificaciones()
    
    # Generar centros de costo
    centros_costo = generar_centros_costo()
    
    # Generar tipos de documento
    tipos_documento = generar_tipos_documento()
    
    return {
        'cierre': cierre_data,
        'movimientos': movimientos,
        'plan_cuentas': plan_cuentas,
        'clasificaciones': clasificaciones,
        'centros_costo': centros_costo,
        'tipos_documento': tipos_documento,
        'resumen_financiero': calcular_resumen_financiero(movimientos, plan_cuentas)
    }

def generar_plan_cuentas():
    """Generar plan de cuentas basado en estructura chilena"""
    cuentas = [
        # ACTIVOS
        {'codigo': '1101', 'nombre': 'Efectivo y Equivalentes de Efectivo', 'nombre_en': 'Cash and Cash Equivalents', 'tipo': 'activo_corriente'},
        {'codigo': '1102', 'nombre': 'Deudores Comerciales', 'nombre_en': 'Trade Receivables', 'tipo': 'activo_corriente'},
        {'codigo': '1103', 'nombre': 'Inventarios', 'nombre_en': 'Inventories', 'tipo': 'activo_corriente'},
        {'codigo': '1104', 'nombre': 'Otros Activos Corrientes', 'nombre_en': 'Other Current Assets', 'tipo': 'activo_corriente'},
        {'codigo': '1201', 'nombre': 'Propiedades, Planta y Equipo', 'nombre_en': 'Property, Plant and Equipment', 'tipo': 'activo_no_corriente'},
        {'codigo': '1202', 'nombre': 'Activos Intangibles', 'nombre_en': 'Intangible Assets', 'tipo': 'activo_no_corriente'},
        
        # PASIVOS
        {'codigo': '2101', 'nombre': 'Cuentas por Pagar Comerciales', 'nombre_en': 'Trade Payables', 'tipo': 'pasivo_corriente'},
        {'codigo': '2102', 'nombre': 'Otras Cuentas por Pagar', 'nombre_en': 'Other Payables', 'tipo': 'pasivo_corriente'},
        {'codigo': '2103', 'nombre': 'Provisiones Corrientes', 'nombre_en': 'Current Provisions', 'tipo': 'pasivo_corriente'},
        {'codigo': '2201', 'nombre': 'Deudas Financieras No Corrientes', 'nombre_en': 'Non-Current Financial Liabilities', 'tipo': 'pasivo_no_corriente'},
        
        # PATRIMONIO
        {'codigo': '3101', 'nombre': 'Capital Pagado', 'nombre_en': 'Paid Capital', 'tipo': 'patrimonio'},
        {'codigo': '3102', 'nombre': 'Reservas', 'nombre_en': 'Reserves', 'tipo': 'patrimonio'},
        {'codigo': '3103', 'nombre': 'Resultados Acumulados', 'nombre_en': 'Retained Earnings', 'tipo': 'patrimonio'},
        
        # INGRESOS
        {'codigo': '4101', 'nombre': 'Ingresos Operacionales', 'nombre_en': 'Operating Revenue', 'tipo': 'ingreso'},
        {'codigo': '4102', 'nombre': 'Otros Ingresos', 'nombre_en': 'Other Income', 'tipo': 'ingreso'},
        
        # COSTOS Y GASTOS
        {'codigo': '5101', 'nombre': 'Costo de Ventas', 'nombre_en': 'Cost of Sales', 'tipo': 'costo'},
        {'codigo': '5201', 'nombre': 'Gastos de Administración', 'nombre_en': 'Administrative Expenses', 'tipo': 'gasto'},
        {'codigo': '5202', 'nombre': 'Gastos de Ventas', 'nombre_en': 'Selling Expenses', 'tipo': 'gasto'},
        {'codigo': '5301', 'nombre': 'Gastos Financieros', 'nombre_en': 'Financial Expenses', 'tipo': 'gasto'},
        {'codigo': '5401', 'nombre': 'Impuesto a la Renta', 'nombre_en': 'Income Tax', 'tipo': 'gasto'}
    ]
    return cuentas

def generar_movimientos_simulados():
    """Generar movimientos contables simulados para el período"""
    movimientos = []
    base_date = datetime(2024, 12, 1)
    
    # Tipos de movimientos típicos
    tipos_movimiento = [
        {'tipo': 'ventas', 'frecuencia': 25},
        {'tipo': 'compras', 'frecuencia': 20},
        {'tipo': 'pagos', 'frecuencia': 15},
        {'tipo': 'cobranzas', 'frecuencia': 15},
        {'tipo': 'gastos', 'frecuencia': 20},
        {'tipo': 'ajustes', 'frecuencia': 5}
    ]
    
    id_mov = 1
    for day in range(31):  # Diciembre completo
        fecha = base_date + timedelta(days=day)
        
        # Generar entre 5-15 movimientos por día
        num_movimientos = random.randint(5, 15)
        
        for _ in range(num_movimientos):
            tipo = random.choices(
                [t['tipo'] for t in tipos_movimiento],
                weights=[t['frecuencia'] for t in tipos_movimiento]
            )[0]
            
            movimiento = generar_movimiento_por_tipo(tipo, fecha, id_mov)
            movimientos.append(movimiento)
            id_mov += 1
    
    return movimientos

def generar_movimiento_por_tipo(tipo, fecha, id_mov):
    """Generar un movimiento específico según el tipo"""
    base_mov = {
        'id': id_mov,
        'fecha': fecha.strftime('%Y-%m-%d'),
        'numero_comprobante': f"COMP-{id_mov:06d}",
        'descripcion': ''
    }
    
    if tipo == 'ventas':
        monto = random.randint(500000, 5000000)
        return {
            **base_mov,
            'tipo': 'Venta',
            'cuenta_codigo': '4101',
            'debe': 0,
            'haber': monto,
            'descripcion': f'Venta factura #{random.randint(1000, 9999)}',
            'tipo_documento': 'FAC',
            'numero_documento': f'F-{random.randint(1000, 9999)}',
            'centro_costo': random.choice(['CC001', 'CC002', 'CC003'])
        }
    
    elif tipo == 'compras':
        monto = random.randint(200000, 2000000)
        return {
            **base_mov,
            'tipo': 'Compra',
            'cuenta_codigo': '5101',
            'debe': monto,
            'haber': 0,
            'descripcion': f'Compra mercadería #{random.randint(1000, 9999)}',
            'tipo_documento': 'FAC',
            'numero_documento': f'FC-{random.randint(1000, 9999)}',
            'centro_costo': random.choice(['CC001', 'CC002'])
        }
    
    elif tipo == 'gastos':
        monto = random.randint(50000, 800000)
        cuenta = random.choice(['5201', '5202', '5301'])
        return {
            **base_mov,
            'tipo': 'Gasto',
            'cuenta_codigo': cuenta,
            'debe': monto,
            'haber': 0,
            'descripcion': f'Gasto operacional',
            'tipo_documento': 'BOL',
            'numero_documento': f'B-{random.randint(1000, 9999)}',
            'centro_costo': random.choice(['CC001', 'CC002', 'CC003'])
        }
    
    elif tipo == 'pagos':
        monto = random.randint(100000, 3000000)
        return {
            **base_mov,
            'tipo': 'Pago',
            'cuenta_codigo': '1101',
            'debe': 0,
            'haber': monto,
            'descripcion': f'Pago a proveedor',
            'tipo_documento': 'CHE',
            'numero_documento': f'CH-{random.randint(1000, 9999)}',
            'centro_costo': 'CC001'
        }
    
    elif tipo == 'cobranzas':
        monto = random.randint(200000, 4000000)
        return {
            **base_mov,
            'tipo': 'Cobranza',
            'cuenta_codigo': '1101',
            'debe': monto,
            'haber': 0,
            'descripcion': f'Cobranza cliente',
            'tipo_documento': 'DEP',
            'numero_documento': f'D-{random.randint(1000, 9999)}',
            'centro_costo': 'CC001'
        }
    
    else:  # ajustes
        monto = random.randint(10000, 500000)
        cuenta = random.choice(['1102', '2101', '3102'])
        return {
            **base_mov,
            'tipo': 'Ajuste',
            'cuenta_codigo': cuenta,
            'debe': monto if random.choice([True, False]) else 0,
            'haber': 0 if monto > 0 else monto,
            'descripcion': f'Ajuste contable período',
            'tipo_documento': 'AJU',
            'numero_documento': f'AJ-{random.randint(100, 999)}',
            'centro_costo': 'CC001'
        }

def generar_clasificaciones():
    """Generar sets de clasificación basados en el modelo"""
    sets_clasificacion = [
        {
            'id': 1,
            'nombre': 'IFRS',
            'descripcion': 'Clasificación según estándares IFRS',
            'idioma': 'en',
            'opciones': [
                {'valor': 'IFRS_001', 'descripcion': 'Current Assets'},
                {'valor': 'IFRS_002', 'descripcion': 'Non-Current Assets'},
                {'valor': 'IFRS_003', 'descripcion': 'Current Liabilities'},
                {'valor': 'IFRS_004', 'descripcion': 'Non-Current Liabilities'},
                {'valor': 'IFRS_005', 'descripcion': 'Equity'},
                {'valor': 'IFRS_006', 'descripcion': 'Revenue'},
                {'valor': 'IFRS_007', 'descripcion': 'Expenses'}
            ]
        },
        {
            'id': 2,
            'nombre': 'Naturaleza',
            'descripcion': 'Clasificación por naturaleza de la cuenta',
            'idioma': 'es',
            'opciones': [
                {'valor': 'NAT_001', 'descripcion': 'Operacional'},
                {'valor': 'NAT_002', 'descripcion': 'Financiero'},
                {'valor': 'NAT_003', 'descripcion': 'Extraordinario'},
                {'valor': 'NAT_004', 'descripcion': 'Fiscal'}
            ]
        },
        {
            'id': 3,
            'nombre': 'Segmento',
            'descripcion': 'Clasificación por segmento de negocio',
            'idioma': 'es',
            'opciones': [
                {'valor': 'SEG_001', 'descripcion': 'Retail'},
                {'valor': 'SEG_002', 'descripcion': 'Corporativo'},
                {'valor': 'SEG_003', 'descripcion': 'Internacional'},
                {'valor': 'SEG_004', 'descripcion': 'Digital'}
            ]
        }
    ]
    return sets_clasificacion

def generar_centros_costo():
    """Generar centros de costo simulados"""
    centros = [
        {'codigo': 'CC001', 'nombre': 'Administración General'},
        {'codigo': 'CC002', 'nombre': 'Ventas'},
        {'codigo': 'CC003', 'nombre': 'Producción'},
        {'codigo': 'CC004', 'nombre': 'Marketing'},
        {'codigo': 'CC005', 'nombre': 'Tecnología'}
    ]
    return centros

def generar_tipos_documento():
    """Generar tipos de documento simulados"""
    tipos = [
        {'codigo': 'FAC', 'descripcion': 'Factura'},
        {'codigo': 'BOL', 'descripcion': 'Boleta'},
        {'codigo': 'CHE', 'descripcion': 'Cheque'},
        {'codigo': 'DEP', 'descripcion': 'Depósito'},
        {'codigo': 'AJU', 'descripcion': 'Ajuste'},
        {'codigo': 'TRA', 'descripcion': 'Transferencia'},
        {'codigo': 'NOT', 'descripcion': 'Nota de Crédito'}
    ]
    return tipos

def calcular_resumen_financiero(movimientos, plan_cuentas):
    """Calcular resumen financiero basado en los movimientos"""
    df_mov = pd.DataFrame(movimientos)
    df_cuentas = pd.DataFrame(plan_cuentas)
    
    # Crear diccionario de tipos de cuenta
    tipo_cuenta_map = {c['codigo']: c['tipo'] for c in plan_cuentas}
    
    # Agregar tipo de cuenta a movimientos
    df_mov['tipo_cuenta'] = df_mov['cuenta_codigo'].map(tipo_cuenta_map)
    
    # Calcular saldos por tipo
    resumen = {}
    
    for tipo in ['activo_corriente', 'activo_no_corriente', 'pasivo_corriente', 
                'pasivo_no_corriente', 'patrimonio', 'ingreso', 'costo', 'gasto']:
        df_tipo = df_mov[df_mov['tipo_cuenta'] == tipo]
        total_debe = df_tipo['debe'].sum()
        total_haber = df_tipo['haber'].sum()
        
        # Para activos y gastos: saldo = debe - haber
        # Para pasivos, patrimonio e ingresos: saldo = haber - debe
        if tipo in ['activo_corriente', 'activo_no_corriente', 'costo', 'gasto']:
            saldo = total_debe - total_haber
        else:
            saldo = total_haber - total_debe
            
        resumen[tipo] = {
            'debe': total_debe,
            'haber': total_haber,
            'saldo': saldo,
            'num_movimientos': len(df_tipo)
        }
    
    # Calcular totales consolidados
    resumen['totales'] = {
        'total_activos': resumen['activo_corriente']['saldo'] + resumen['activo_no_corriente']['saldo'],
        'total_pasivos': resumen['pasivo_corriente']['saldo'] + resumen['pasivo_no_corriente']['saldo'],
        'total_patrimonio': resumen['patrimonio']['saldo'],
        'total_ingresos': resumen['ingreso']['saldo'],
        'total_costos_gastos': resumen['costo']['saldo'] + resumen['gasto']['saldo'],
        'resultado_ejercicio': resumen['ingreso']['saldo'] - (resumen['costo']['saldo'] + resumen['gasto']['saldo'])
    }
    
    return resumen
