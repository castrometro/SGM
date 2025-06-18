import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def mostrar(data=None):
    st.header("💰 Estado de Cambio de Patrimonio (ECP)")
    st.markdown("**Movimientos en las cuentas patrimoniales durante el período**")
    
    # Crear datos de ejemplo para el ECP
    cuentas_patrimonio = [
        'Capital Pagado',
        'Reservas de Revalorización',
        'Reservas de Utilidades',
        'Otras Reservas',
        'Resultados Acumulados',
        'Resultado del Ejercicio',
        'Otros Resultados Integrales Acumulados',
        'Total Patrimonio'
    ]
    
    datos_ecp = {
        'Cuenta': cuentas_patrimonio,
        'Saldo Inicial': [500000000, 25000000, 80000000, 15000000, 120000000, 137000000, 35000000, 912000000],
        'Aumento de Capital': [50000000, 0, 0, 0, 0, 0, 0, 50000000],
        'Distribución de Dividendos': [0, 0, 0, 0, 0, -95000000, 0, -95000000],
        'Traspaso a Reservas': [0, 0, 42000000, 0, 0, -42000000, 0, 0],
        'Resultado del Ejercicio': [0, 0, 0, 0, 0, 155000000, 0, 155000000],
        'Otros Resultados Integrales': [0, 8500000, 0, 0, 0, 0, 1000000, 9500000],
        'Otros Movimientos': [0, 0, 0, 5000000, 15000000, 0, 0, 20000000],
        'Saldo Final': [550000000, 33500000, 122000000, 20000000, 135000000, 155000000, 36000000, 1051500000]
    }
    
    df_ecp = pd.DataFrame(datos_ecp)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Patrimonio Total",
            value="$1.051.500.000",
            delta="15,29%"
        )
    
    with col2:
        variacion_patrimonio = 1051500000 - 912000000
        st.metric(
            label="Variación Patrimonio",
            value=f"${variacion_patrimonio:,.0f}",
            delta=f"${variacion_patrimonio:,.0f}"
        )
    
    with col3:
        st.metric(
            label="Capital Pagado",
            value="$550.000.000",
            delta="10,00%"
        )
    
    with col4:
        st.metric(
            label="Dividendos Distribuidos",
            value="$95.000.000",
            delta="$95.000.000"
        )
    
    st.markdown("---")
    
    # Tabla principal del ECP
    st.subheader("📋 Estado de Cambio de Patrimonio Detallado")
    
    # Formatear la tabla para mejor visualización
    def format_currency(val):
        if pd.isna(val) or val == 0:
            return '$0'
        return f"${val:,.0f}" if val > 0 else f"(${abs(val):,.0f})"
    
    df_display = df_ecp.copy()
    for col in df_display.columns[1:]:  # Todas excepto 'Cuenta'
        df_display[col] = df_display[col].apply(format_currency).astype(str)
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Análisis gráfico
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Evolución del Patrimonio")
        
        # Gráfico de cascada mostrando los movimientos
        movimientos = {
            'Concepto': [
                'Saldo Inicial',
                'Aumento Capital',
                'Dividendos',
                'Resultado Ejercicio',
                'Otros Integrales',
                'Otros Movimientos',
                'Saldo Final'
            ],
            'Valor': [912000000, 50000000, -95000000, 155000000, 9500000, 20000000, 1051500000],
            'Tipo': ['inicial', 'positivo', 'negativo', 'positivo', 'positivo', 'positivo', 'final']
        }
        
        df_mov = pd.DataFrame(movimientos)
        
        # Crear gráfico de cascada
        fig_cascade = go.Figure()
        
        colors = {
            'inicial': 'blue',
            'positivo': 'green', 
            'negativo': 'red',
            'final': 'purple'
        }
        
        for i, row in df_mov.iterrows():
            fig_cascade.add_trace(go.Bar(
                name=row['Concepto'],
                x=[row['Concepto']],
                y=[row['Valor']],
                marker_color=colors[row['Tipo']],
                text=f"${row['Valor']:,.0f}",
                textposition='outside'
            ))
        
        fig_cascade.update_layout(
            title="Movimientos del Patrimonio",
            yaxis_title="Valor (CLP)",
            showlegend=False,
            xaxis_tickangle=45
        )
        
        st.plotly_chart(fig_cascade, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Composición del Patrimonio Final")
        
        # Gráfico circular de la composición final
        patrimonio_final = {
            'Cuenta': [
                'Capital Pagado',
                'Resultado del Ejercicio',
                'Resultados Acumulados',
                'Reservas de Utilidades',
                'Otras Cuentas'
            ],
            'Valor': [
                550000000,
                155000000,
                135000000,
                122000000,
                89500000  # Suma de reservas de revalorización, otras reservas y ORI
            ]
        }
        
        df_comp = pd.DataFrame(patrimonio_final)
        
        fig_pie = px.pie(
            df_comp,
            values='Valor',
            names='Cuenta',
            title="Composición del Patrimonio Final"
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Análisis de indicadores patrimoniales
    st.markdown("---")
    st.subheader("📈 Indicadores Patrimoniales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ratios patrimoniales
        st.markdown("#### 🔢 Ratios Financieros")
        
        # Calcular ratios
        capital_pagado = 550000000
        patrimonio_total = 1051500000
        resultado_ejercicio = 155000000
        dividendos = 95000000
        
        ratio_capital = (capital_pagado / patrimonio_total) * 100
        ratio_autofinanciamiento = ((patrimonio_total - capital_pagado) / patrimonio_total) * 100
        ratio_payout = (dividendos / 137000000) * 100  # Dividendos del resultado anterior
        roe = (resultado_ejercicio / ((912000000 + patrimonio_total) / 2)) * 100  # ROE promedio
        
        col_ratio1, col_ratio2 = st.columns(2)
        
        with col_ratio1:
            st.metric("Ratio Capital/Patrimonio", f"{ratio_capital:.1f}%")
            st.metric("Ratio Autofinanciamiento", f"{ratio_autofinanciamiento:.1f}%")
        
        with col_ratio2:
            st.metric("Payout Ratio", f"{ratio_payout:.1f}%")
            st.metric("ROE Estimado", f"{roe:.1f}%")
    
    with col2:
        # Evolución comparativa
        st.markdown("#### 📊 Evolución Anual")
        
        evolucion_data = {
            'Período': ['Año Anterior', 'Año Actual'],
            'Patrimonio Total': [912000000, 1051500000],
            'Capital Pagado': [500000000, 550000000],
            'Reservas Totales': [120000000, 175000000],
            'Resultados': [137000000, 155000000]
        }
        
        df_evol = pd.DataFrame(evolucion_data)
        df_evol_melted = df_evol.melt(id_vars=['Período'], var_name='Concepto', value_name='Valor')
        
        fig_evol = px.bar(
            df_evol_melted,
            x='Concepto',
            y='Valor',
            color='Período',
            title="Evolución de Componentes Patrimoniales",
            barmode='group'
        )
        fig_evol.update_xaxes(tickangle=45)
        fig_evol.update_layout(yaxis_title="Valor (CLP)")
        
        st.plotly_chart(fig_evol, use_container_width=True)
    
    # Análisis de movimientos detallado
    st.markdown("---")
    st.subheader("🔍 Análisis Detallado de Movimientos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### 💰 Aportes de Capital")
        st.info("""
        **Aumento de Capital: $50.000.000**
        - Representa un 10% de aumento
        - Fortalece la estructura patrimonial
        - Mejora la capacidad de endeudamiento
        """)
    
    with col2:
        st.markdown("##### 📤 Distribución de Dividendos")
        st.warning("""
        **Dividendos Pagados: $95.000.000**
        - 69.3% del resultado anterior
        - Política de dividendos conservadora
        - Retiene 30.7% para reinversión
        """)
    
    with col3:
        st.markdown("##### 🔄 Gestión de Reservas")
        st.success("""
        **Traspaso a Reservas: $42.000.000**
        - Fortalece reservas de utilidades
        - Mejora estabilidad financiera
        - Estrategia de capitalización interna
        """)
    
    # Proyecciones y alertas
    st.markdown("---")
    st.subheader("🎯 Proyecciones y Alertas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        crecimiento_patrimonio = ((patrimonio_total - 912000000) / 912000000) * 100
        st.metric(
            label="Crecimiento Patrimonio",
            value=f"{crecimiento_patrimonio:.1f}%",
            delta=f"{crecimiento_patrimonio:.1f}%",
            help="Crecimiento anual del patrimonio total"
        )
    
    with col2:
        apalancamiento = capital_pagado / (patrimonio_total - capital_pagado)
        st.metric(
            label="Apalancamiento Interno",
            value=f"{apalancamiento:.2f}",
            help="Capital pagado vs autofinanciamiento"
        )
    
    with col3:
        eficiencia_capital = resultado_ejercicio / capital_pagado * 100
        st.metric(
            label="Eficiencia Capital",
            value=f"{eficiencia_capital:.1f}%",
            help="Resultado ejercicio vs capital pagado"
        )
    
    with col4:
        st.metric(
            label="Solidez Patrimonial",
            value="Alta",
            help="Evaluación cualitativa de la estructura patrimonial"
        )
    
    # Notas explicativas
    with st.expander("📝 Notas Metodológicas - Estado de Cambio de Patrimonio"):
        st.markdown("""
        **Componentes del Estado de Cambio de Patrimonio:**
        
        ✅ **Movimientos Registrados:**
        - **Aumento de Capital:** Nuevos aportes de socios
        - **Distribución de Dividendos:** Reparto de utilidades período anterior
        - **Traspaso a Reservas:** Capitalización de resultados
        - **Resultado del Ejercicio:** Ganancia/pérdida del período actual
        - **Otros Resultados Integrales:** Ajustes patrimoniales sin impacto en resultados
        - **Otros Movimientos:** Ajustes diversos (corrección de errores, cambios contables)
        
        📊 **Análisis de Ratios:**
        - **Ratio Capital/Patrimonio:** Mide participación del capital aportado
        - **Autofinanciamiento:** Capacidad de generar recursos propios
        - **Payout Ratio:** Proporción de utilidades distribuidas como dividendos
        - **ROE:** Rentabilidad sobre patrimonio promedio
        
        🎯 **Indicadores de Gestión:**
        - Crecimiento patrimonial sostenido
        - Política de dividendos balanceada
        - Fortalecimiento de reservas
        - Estructura patrimonial sólida
        """)
