"""
Traducciones centralizadas para templates Excel
"""

def obtener_periodo_cierre(periodo_str):
    """
    Obtener el período de cierre a partir de un string de período
    
    Args:
        periodo_str: String del período en formato 'YYYY-MM', 'Mes YYYY', etc.
        
    Returns:
        tuple: (año, mes, nombre_mes_es, nombre_mes_en)
    """
    import re
    from datetime import datetime
    
    # Mapeo de meses
    meses_map = {
        'enero': 1, 'january': 1,
        'febrero': 2, 'february': 2,
        'marzo': 3, 'march': 3,
        'abril': 4, 'april': 4,
        'mayo': 5, 'may': 5,
        'junio': 6, 'june': 6,
        'julio': 7, 'july': 7,
        'agosto': 8, 'august': 8,
        'septiembre': 9, 'september': 9,
        'octubre': 10, 'october': 10,
        'noviembre': 11, 'november': 11,
        'diciembre': 12, 'december': 12
    }
    
    nombres_meses = {
        1: {'es': 'Enero', 'en': 'January'},
        2: {'es': 'Febrero', 'en': 'February'},
        3: {'es': 'Marzo', 'en': 'March'},
        4: {'es': 'Abril', 'en': 'April'},
        5: {'es': 'Mayo', 'en': 'May'},
        6: {'es': 'Junio', 'en': 'June'},
        7: {'es': 'Julio', 'en': 'July'},
        8: {'es': 'Agosto', 'en': 'August'},
        9: {'es': 'Septiembre', 'en': 'September'},
        10: {'es': 'Octubre', 'en': 'October'},
        11: {'es': 'Noviembre', 'en': 'November'},
        12: {'es': 'Diciembre', 'en': 'December'}
    }
    
    if not periodo_str:
        año_actual = datetime.now().year
        return año_actual, 12, 'Diciembre', 'December'
    
    # Formato YYYY-MM
    if re.match(r'\d{4}-\d{1,2}', periodo_str):
        año, mes = periodo_str.split('-')
        año = int(año)
        mes = int(mes)
        return año, mes, nombres_meses[mes]['es'], nombres_meses[mes]['en']
    
    # Formato "Mes YYYY"
    match = re.search(r'(\w+)\s+(\d{4})', periodo_str)
    if match:
        mes_nombre = match.group(1).lower()
        año = int(match.group(2))
        
        if mes_nombre in meses_map:
            mes = meses_map[mes_nombre]
            return año, mes, nombres_meses[mes]['es'], nombres_meses[mes]['en']
    
    # Formato "YYYY Mes"
    match = re.search(r'(\d{4})\s+(\w+)', periodo_str)
    if match:
        año = int(match.group(1))
        mes_nombre = match.group(2).lower()
        
        if mes_nombre in meses_map:
            mes = meses_map[mes_nombre]
            return año, mes, nombres_meses[mes]['es'], nombres_meses[mes]['en']
    
    # Por defecto, usar diciembre del año actual
    año_actual = datetime.now().year
    return año_actual, 12, 'Diciembre', 'December'


def generar_textos_dinamicos(periodo_str, language='es'):
    """
    Generar textos con períodos dinámicos basados en el período proporcionado
    
    Args:
        periodo_str: String del período
        language: Idioma ('es' o 'en')
        
    Returns:
        dict: Diccionario con textos dinámicos
    """
    año, mes, nombre_mes_es, nombre_mes_en = obtener_periodo_cierre(periodo_str)
    
    if language.lower() in ['en', 'english', 'inglés']:
        return {
            'initial_balance': f'Initial Balance at January 1, {año}',
            'final_balance': f'Final Balance as of {nombre_mes_en} {año}',
            'total_period_change': f'Total Period Change'
        }
    else:
        return {
            'initial_balance': f'Saldo Inicial al 1 de Enero {año}',
            'final_balance': f'Saldo Final al {nombre_mes_es} {año}',
            'total_period_change': f'Cambio Total del Período'
        }


def detect_language_improved(metadata):
    """
    Detectar el idioma de manera mejorada usando múltiples indicadores
    
    Args:
        metadata: Diccionario con metadatos que puede contener lang_field
        
    Returns:
        str: 'es' o 'en'
    """
    # Revisar múltiples campos para detectar idioma
    lang_field = metadata.get('lang_field', '').lower()
    idioma = metadata.get('idioma', '').lower()
    language = metadata.get('language', '').lower()
    
    # Indicadores de inglés
    english_indicators = [
        'en', 'english', 'inglés', 'ing', 'english', 'statement', 'balance', 
        'income', 'comprehensive', 'assets', 'liabilities', 'equity', 'revenue',
        'expenses', 'profit', 'loss', 'changes', 'position', 'financial'
    ]
    
    # Indicadores de español
    spanish_indicators = [
        'es', 'español', 'spanish', 'esp', 'estado', 'balance', 'resultado', 
        'integral', 'activos', 'pasivos', 'patrimonio', 'ingresos', 'gastos', 
        'ganancia', 'pérdida', 'cambios', 'situación', 'financiera'
    ]
    
    # Buscar indicadores en todos los campos
    all_text = f"{lang_field} {idioma} {language}".lower()
    
    # Primero buscar indicadores específicos de inglés
    for indicator in english_indicators:
        if indicator in all_text:
            return 'en'
    
    # Luego buscar indicadores específicos de español
    for indicator in spanish_indicators:
        if indicator in all_text:
            return 'es'
    
    # Por defecto, español
    return 'es'


TRANSLATIONS = {
    'es': {
        # Títulos principales
        'title_esf': 'ESTADO DE SITUACIÓN FINANCIERA',
        'title_eri': 'ESTADO DE RESULTADO INTEGRAL',
        'title_ecp': 'ESTADO DE CAMBIOS EN EL PATRIMONIO',
        'title_movimientos': 'MOVIMIENTOS CONTABLES',
        
        # ESF - Estado de Situación Financiera
        'assets': 'ACTIVOS',
        'current_assets': 'Activos Corrientes',
        'non_current_assets': 'Activos No Corrientes',
        'total_assets': 'TOTAL ACTIVOS',
        'liabilities_equity': 'PASIVOS Y PATRIMONIO',
        'current_liabilities': 'Pasivos Corrientes',
        'non_current_liabilities': 'Pasivos No Corrientes',
        'total_liabilities': 'TOTAL PASIVOS',
        'equity': 'PATRIMONIO',
        'total_equity': 'TOTAL PATRIMONIO',
        'total_liabilities_equity': 'TOTAL PASIVOS Y PATRIMONIO',
        'period_result': 'Resultado del Ejercicio',
        'profit_loss': 'Ganancia del Ejercicio',
        'loss': 'Pérdida del Ejercicio',
        'total_period_result': 'TOTAL RESULTADO DEL EJERCICIO',
        
        # ERI - Estado de Resultado Integral
        'revenue': 'INGRESOS',
        'cost_of_sales': 'COSTO DE VENTAS',
        'gross_profit': 'GANANCIA BRUTA',
        'operating_expenses': 'GASTOS OPERACIONALES',
        'operating_income': 'GANANCIA OPERACIONAL',
        'financial_income': 'INGRESOS FINANCIEROS',
        'financial_expenses': 'GASTOS FINANCIEROS',
        'income_before_tax': 'GANANCIA ANTES DE IMPUESTOS',
        'income_tax': 'IMPUESTO A LA RENTA',
        'net_income': 'GANANCIA NETA',
        'other_comprehensive_income': 'OTROS RESULTADOS INTEGRALES',
        'total_comprehensive_income': 'TOTAL RESULTADO INTEGRAL',
        'ganancias_brutas': 'Ganancias Brutas',
        'ganancia_perdida': 'Ganancia (Pérdida)',
        'ganancia_perdida_antes_impuestos': 'Ganancia (Pérdida) Antes de Impuestos',
        
        # ECP - Estado de Cambios en el Patrimonio
        'concept': 'Concepto',
        'capital': 'Capital',
        'other_reserves': 'Otras Reservas',
        'retained_earnings': 'Resultados Acumulados',
        'attributable_capital': 'Capital Atribuible',
        'non_controlling_interests': 'Participaciones no Controladoras',
        'total': 'Total',
        'initial_balance': 'Saldo Inicial al 1 de Enero',
        'period_profit_loss': 'Resultado del ejercicio',
        'period_result_ecp': 'Resultado del ejercicio',
        'other_changes': 'Otros cambios',
        'final_balance': 'Saldo Final',
        'total_period_change': 'Cambio Total del Período',
        
        # Campos comunes
        'client': 'Cliente',
        'period': 'Período',
        'currency': 'Moneda',
        'date': 'Fecha',
        'no_movements': '(Sin movimientos)',
        'no_data': '(Sin datos disponibles)',
        'totals': 'TOTALES:',
        'total_general': 'TOTAL GENERAL (Ganancia/Pérdida)',
        'info_sheet': 'Información del Reporte',
        'report_info': 'INFORMACIÓN DEL REPORTE',
        'language': 'Idioma',
        'spanish': 'Español',
        'english': 'Inglés',
        'generation_date': 'Fecha de generación',
        'system': 'Sistema',
        'version': 'Versión',
        'total_movements': 'Total movimientos'
    },
    'en': {
        # Títulos principales
        'title_esf': 'STATUS OF FINANCIAL SITUATION',
        'title_eri': 'STATEMENTS OF COMPREHENSIVE INCOME, BY FUNCTION',
        'title_ecp': 'STATE OF CHANGE OF PATRIMONY',
        'title_movimientos': 'ACCOUNTING TRANSACTIONS',
        
        # ESF - Statement of Financial Position
        'assets': 'ASSETS',
        'current_assets': 'Current Assets',
        'non_current_assets': 'Non-Current Assets',
        'total_assets': 'TOTAL ASSETS',
        'liabilities_equity': 'LIABILITIES AND PATRIMONY',
        'current_liabilities': 'Current Liabilities',
        'non_current_liabilities': 'Non-Current Liabilities',
        'total_liabilities': 'TOTAL LIABILITIES',
        'equity': 'PATRIMONY',
        'total_equity': 'TOTAL PATRIMONY',
        'total_liabilities_equity': 'TOTAL LIABILITIES AND PATRIMONY',
        'period_result': 'Period Result',
        'profit_loss': 'Profit for the Period',
        'loss': 'Loss for the Period',
        'total_period_result': 'TOTAL PERIOD RESULT',
        
        # ERI - Statement of Comprehensive Income
        'revenue': 'REVENUE',
        'cost_of_sales': 'COST OF SALES',
        'gross_profit': 'GROSS PROFIT',
        'operating_expenses': 'OPERATING EXPENSES',
        'operating_income': 'OPERATING INCOME',
        'financial_income': 'FINANCIAL INCOME',
        'financial_expenses': 'FINANCIAL EXPENSES',
        'income_before_tax': 'INCOME BEFORE TAX',
        'income_tax': 'INCOME TAX',
        'net_income': 'NET INCOME',
        'other_comprehensive_income': 'OTHER COMPREHENSIVE INCOME',
        'total_comprehensive_income': 'TOTAL COMPREHENSIVE INCOME',
        'ganancias_brutas': 'Gross Earnings',
        'ganancia_perdida': 'Earnings (Loss)',
        'ganancia_perdida_antes_impuestos': 'Earnings (Loss) Before Taxes',
        
        # ECP - Statement of Changes in Equity
        'concept': 'Concept',
        'capital': 'Capital',
        'other_reserves': 'Other Reserves',
        'retained_earnings': 'Retained Earnings',
        'attributable_capital': 'Attributable Capital',
        'non_controlling_interests': 'Non-controlling Interests',
        'total': 'Total',
        'initial_balance': 'Initial Balance at January 1',
        'period_profit_loss': 'Profit (loss) for the period',
        'period_result_ecp': 'Result of the Exercise',
        'other_changes': 'Other changes',
        'final_balance': 'Final Balance',
        'total_period_change': 'Total Period Change',
        
        # Campos comunes
        'client': 'Client',
        'period': 'Period',
        'currency': 'Currency',
        'date': 'Date',
        'no_movements': '(No movements)',
        'no_data': '(No data available)',
        'totals': 'TOTALS:',
        'total_general': 'TOTAL GENERAL (Profit/Loss)',
        'info_sheet': 'Report Information',
        'report_info': 'REPORT INFORMATION',
        'language': 'Language',
        'spanish': 'Spanish',
        'english': 'English',
        'generation_date': 'Generation Date',
        'system': 'System',
        'version': 'Version',
        'total_movements': 'Total movements'
    }
}


def get_text(key, language='es', metadata=None):
    """
    Obtener texto traducido según el idioma, con soporte para textos dinámicos
    
    Args:
        key: Clave del texto
        language: Idioma ('es' o 'en')
        metadata: Metadatos para generar textos dinámicos
        
    Returns:
        str: Texto traducido
    """
    # Detectar idioma mejorado si se proporcionan metadatos
    if metadata:
        language = detect_language_improved(metadata)
    
    # Generar textos dinámicos si está disponible el período
    if metadata and 'periodo' in metadata:
        textos_dinamicos = generar_textos_dinamicos(metadata['periodo'], language)
        if key in textos_dinamicos:
            return textos_dinamicos[key]
    
    # Usar traducciones estáticas
    lang = 'en' if language.lower() in ['en', 'english', 'inglés'] else 'es'
    return TRANSLATIONS.get(lang, {}).get(key, key)


def get_account_name(cuenta, language='es'):
    """Obtener nombre de cuenta según el idioma"""
    if language.lower() in ['en', 'english', 'inglés']:
        return cuenta.get("nombre_en", cuenta.get("nombre_es", ""))
    else:
        return cuenta.get("nombre_es", cuenta.get("nombre_en", ""))
