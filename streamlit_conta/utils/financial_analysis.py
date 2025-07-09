"""
Utilidades para análisis financiero y procesamiento de datos contables
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple

def calcular_ratios_financieros(esf_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcular ratios financieros básicos a partir del ESF
    """
    ratios = {}
    
    # Extraer totales principales
    activos = esf_data.get('total_activos', 0)
    pasivos = esf_data.get('total_pasivos', 0)
    patrimonio = esf_data.get('total_patrimonio', 0)
    
    # Detalles de activos
    activo_corriente = 0
    activo_no_corriente = 0
    
    if 'activos' in esf_data:
        for categoria, subcategorias in esf_data['activos'].items():
            if 'corriente' in categoria.lower():
                activo_corriente += sum(subcategorias.values()) if isinstance(subcategorias, dict) else subcategorias
            elif 'no_corriente' in categoria.lower() or 'fijo' in categoria.lower():
                activo_no_corriente += sum(subcategorias.values()) if isinstance(subcategorias, dict) else subcategorias
    
    # Detalles de pasivos
    pasivo_corriente = 0
    pasivo_no_corriente = 0
    
    if 'pasivos' in esf_data:
        for categoria, subcategorias in esf_data['pasivos'].items():
            if 'corriente' in categoria.lower():
                pasivo_corriente += sum(subcategorias.values()) if isinstance(subcategorias, dict) else subcategorias
            elif 'no_corriente' in categoria.lower() or 'largo_plazo' in categoria.lower():
                pasivo_no_corriente += sum(subcategorias.values()) if isinstance(subcategorias, dict) else subcategorias
    
    # Ratios de liquidez
    if pasivo_corriente > 0:
        ratios['liquidez_corriente'] = activo_corriente / pasivo_corriente
        ratios['prueba_acida'] = activo_corriente / pasivo_corriente  # Simplificado
    
    # Ratios de endeudamiento
    if activos > 0:
        ratios['endeudamiento_total'] = pasivos / activos
        ratios['participacion_patrimonio'] = patrimonio / activos
    
    if pasivos > 0:
        ratios['solidez'] = patrimonio / pasivos
    
    # Ratio de apalancamiento
    if patrimonio > 0:
        ratios['apalancamiento'] = activos / patrimonio
    
    # Estructura de capital
    if activos > 0:
        ratios['activo_corriente_pct'] = activo_corriente / activos * 100
        ratios['activo_no_corriente_pct'] = activo_no_corriente / activos * 100
        
    if pasivos > 0:
        ratios['pasivo_corriente_pct'] = pasivo_corriente / pasivos * 100
        ratios['pasivo_no_corriente_pct'] = pasivo_no_corriente / pasivos * 100
    
    return ratios

def procesar_movimientos_para_grafico(movimientos_data: List[Dict]) -> pd.DataFrame:
    """
    Procesar datos de movimientos para visualización
    """
    if not movimientos_data:
        return pd.DataFrame()
    
    # Convertir a DataFrame
    df = pd.DataFrame(movimientos_data)
    
    # Asegurar columnas necesarias
    required_cols = ['fecha', 'cuenta', 'descripcion', 'debe', 'haber', 'saldo']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col in ['debe', 'haber', 'saldo'] else ''
    
    # Convertir tipos de datos
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    for col in ['debe', 'haber', 'saldo']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Agregar columnas calculadas
    df['movimiento_neto'] = df['debe'] - df['haber']
    df['tipo_movimiento'] = df.apply(
        lambda row: 'Débito' if row['debe'] > row['haber'] else 'Crédito', axis=1
    )
    
    return df

def analizar_estructura_activos(esf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizar la estructura de activos
    """
    if 'activos' not in esf_data:
        return {}
    
    activos = esf_data['activos']
    total_activos = esf_data.get('total_activos', 0)
    
    estructura = {
        'categorias': {},
        'composicion_pct': {},
        'liquidez_index': 0
    }
    
    for categoria, valor in activos.items():
        if isinstance(valor, dict):
            total_categoria = sum(valor.values())
        else:
            total_categoria = valor
            
        estructura['categorias'][categoria] = total_categoria
        
        if total_activos > 0:
            estructura['composicion_pct'][categoria] = (total_categoria / total_activos) * 100
    
    # Calcular índice de liquidez (activos corrientes vs no corrientes)
    activo_corriente = 0
    for cat in estructura['categorias']:
        if 'corriente' in cat.lower() or 'liquido' in cat.lower():
            activo_corriente += estructura['categorias'][cat]
    
    if total_activos > 0:
        estructura['liquidez_index'] = (activo_corriente / total_activos) * 100
    
    return estructura

def analizar_estructura_pasivos(esf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizar la estructura de pasivos
    """
    if 'pasivos' not in esf_data:
        return {}
    
    pasivos = esf_data['pasivos']
    total_pasivos = esf_data.get('total_pasivos', 0)
    
    estructura = {
        'categorias': {},
        'composicion_pct': {},
        'exigibilidad_index': 0
    }
    
    for categoria, valor in pasivos.items():
        if isinstance(valor, dict):
            total_categoria = sum(valor.values())
        else:
            total_categoria = valor
            
        estructura['categorias'][categoria] = total_categoria
        
        if total_pasivos > 0:
            estructura['composicion_pct'][categoria] = (total_categoria / total_pasivos) * 100
    
    # Calcular índice de exigibilidad (pasivos corrientes vs no corrientes)
    pasivo_corriente = 0
    for cat in estructura['categorias']:
        if 'corriente' in cat.lower() or 'corto' in cat.lower():
            pasivo_corriente += estructura['categorias'][cat]
    
    if total_pasivos > 0:
        estructura['exigibilidad_index'] = (pasivo_corriente / total_pasivos) * 100
    
    return estructura

def generar_alertas_financieras(ratios: Dict[str, float]) -> List[Dict[str, str]]:
    """
    Generar alertas basadas en ratios financieros
    """
    alertas = []
    
    # Alerta de liquidez
    if 'liquidez_corriente' in ratios:
        if ratios['liquidez_corriente'] < 1.0:
            alertas.append({
                'tipo': 'danger',
                'titulo': 'Liquidez Crítica',
                'mensaje': f'Ratio de liquidez corriente: {ratios["liquidez_corriente"]:.2f}. Por debajo de 1.0'
            })
        elif ratios['liquidez_corriente'] < 1.5:
            alertas.append({
                'tipo': 'warning', 
                'titulo': 'Liquidez Baja',
                'mensaje': f'Ratio de liquidez corriente: {ratios["liquidez_corriente"]:.2f}. Considerar mejorar'
            })
    
    # Alerta de endeudamiento
    if 'endeudamiento_total' in ratios:
        if ratios['endeudamiento_total'] > 0.7:
            alertas.append({
                'tipo': 'danger',
                'titulo': 'Endeudamiento Alto',
                'mensaje': f'Endeudamiento: {ratios["endeudamiento_total"]*100:.1f}%. Superior al 70%'
            })
        elif ratios['endeudamiento_total'] > 0.5:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Endeudamiento Moderado',
                'mensaje': f'Endeudamiento: {ratios["endeudamiento_total"]*100:.1f}%. Monitorear evolución'
            })
    
    # Alerta de solidez
    if 'solidez' in ratios:
        if ratios['solidez'] < 0.5:
            alertas.append({
                'tipo': 'danger',
                'titulo': 'Solidez Baja',
                'mensaje': f'Ratio de solidez: {ratios["solidez"]:.2f}. Patrimonio insuficiente vs pasivos'
            })
        elif ratios['solidez'] < 1.0:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Solidez Moderada',
                'mensaje': f'Ratio de solidez: {ratios["solidez"]:.2f}. Mejorar estructura patrimonial'
            })
    
    return alertas

def preparar_datos_comparativos(historico_data: List[Dict]) -> pd.DataFrame:
    """
    Preparar datos históricos para análisis comparativo
    """
    if not historico_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(historico_data)
    
    # Asegurar columnas de fecha
    if 'periodo' in df.columns:
        df['fecha'] = pd.to_datetime(df['periodo'], errors='coerce')
    
    # Ordenar por fecha
    if 'fecha' in df.columns:
        df = df.sort_values('fecha')
    
    # Calcular variaciones período a período
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[f'{col}_variacion'] = df[col].pct_change() * 100
        df[f'{col}_variacion_abs'] = df[col].diff()
    
    return df

def calcular_kpis_dashboard(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcular KPIs principales para el dashboard
    """
    kpis = {}
    
    if 'esf' in data:
        esf = data['esf']
        
        # KPIs básicos
        kpis['total_activos'] = esf.get('total_activos', 0)
        kpis['total_pasivos'] = esf.get('total_pasivos', 0)
        kpis['total_patrimonio'] = esf.get('total_patrimonio', 0)
        
        # KPIs calculados
        ratios = calcular_ratios_financieros(esf)
        kpis.update(ratios)
        
        # KPIs de estructura
        estructura_activos = analizar_estructura_activos(esf)
        kpis['liquidez_index'] = estructura_activos.get('liquidez_index', 0)
        
        estructura_pasivos = analizar_estructura_pasivos(esf)
        kpis['exigibilidad_index'] = estructura_pasivos.get('exigibilidad_index', 0)
    
    # Timestamp de cálculo
    kpis['fecha_calculo'] = pd.Timestamp.now().isoformat()
    
    return kpis

def validar_balance_contable(esf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validar el balance contable (Activos = Pasivos + Patrimonio)
    """
    resultado = {
        'balanceado': False,
        'diferencia': 0,
        'precision': 0.01,  # Tolerancia de centavos
        'detalles': {}
    }
    
    activos = esf_data.get('total_activos', 0)
    pasivos = esf_data.get('total_pasivos', 0)
    patrimonio = esf_data.get('total_patrimonio', 0)
    
    suma_pasivos_patrimonio = pasivos + patrimonio
    diferencia = activos - suma_pasivos_patrimonio
    
    resultado['diferencia'] = diferencia
    resultado['balanceado'] = abs(diferencia) <= resultado['precision']
    
    resultado['detalles'] = {
        'activos': activos,
        'pasivos': pasivos,
        'patrimonio': patrimonio,
        'suma_pasivos_patrimonio': suma_pasivos_patrimonio,
        'ecuacion_ok': resultado['balanceado']
    }
    
    return resultado
