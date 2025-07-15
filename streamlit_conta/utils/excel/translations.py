"""
Traducciones centralizadas para templates Excel
"""

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
        'ganancias_brutas': 'GANANCIAS BRUTAS',
        'ganancia_perdida': 'GANANCIA O PÉRDIDA',
        'ganancia_perdida_antes_impuestos': 'GANANCIA ANTES DE IMPUESTOS',
        
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
        'other_changes': 'Otros cambios',
        'final_balance': 'Saldo Final a Junio 2025',
        
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
        'generation_date': 'Fecha de generación',
        'system': 'Sistema',
        'version': 'Versión',
        'total_movements': 'Total movimientos'
    },
    'en': {
        # Títulos principales
        'title_esf': 'STATEMENT OF FINANCIAL POSITION',
        'title_eri': 'STATEMENT OF COMPREHENSIVE INCOME',
        'title_ecp': 'STATEMENT OF CHANGES OF PATRIMONY',
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
        'ganancias_brutas': 'GROSS PROFIT',
        'ganancia_perdida': 'PROFIT OR LOSS',
        'ganancia_perdida_antes_impuestos': 'INCOME BEFORE TAX',
        
        # ECP - Statement of Changes in Patrimony
        'concept': 'Concept',
        'capital': 'Capital',
        'other_reserves': 'Other Reserves',
        'retained_earnings': 'Retained Earnings',
        'attributable_capital': 'Attributable Capital',
        'non_controlling_interests': 'Non-controlling Interests',
        'total': 'Total',
        'initial_balance': 'Initial Balance at January 1',
        'period_profit_loss': 'Profit (loss) for the period',
        'other_changes': 'Other changes',
        'final_balance': 'Final Balance as of, June 2025',
        
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


def get_text(key, language='es'):
    """Obtener texto traducido según el idioma"""
    lang = 'en' if language.lower() in ['en', 'english', 'inglés'] else 'es'
    return TRANSLATIONS.get(lang, {}).get(key, key)


def get_account_name(cuenta, language='es'):
    """Obtener nombre de cuenta según el idioma"""
    if language.lower() in ['en', 'english', 'inglés']:
        return cuenta.get("nombre_en", cuenta.get("nombre_es", ""))
    else:
        return cuenta.get("nombre_es", cuenta.get("nombre_en", ""))
