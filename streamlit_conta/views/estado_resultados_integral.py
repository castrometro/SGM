import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def mostrar(data=None):
    st.header("📊 Estado de Resultados Integral (ERI)")
    st.markdown("**Resultado del ejercicio más otros resultados integrales**")
    
    # Crear datos de ejemplo para el ERI
    datos_eri = {
        'Concepto': [
            'Resultado del Ejercicio',
            '',
            'Otros Resultados Integrales:',
            '',
            'Diferencias de Conversión',
            'Revalorización de Propiedades',
            'Instrumentos Financieros Derivados',
            'Beneficios a Empleados',
            'Ajustes por Inflación',
            '',
            'Total Otros Resultados Integrales',
            '',
            'Resultado Integral Total'
        ],
        'Año Actual': [
            155000000,
            '',
            '',
            '',
            -2500000,
            8500000,
            1200000,
            -3200000,
            5500000,
            '',
            9500000,
            '',
            164500000
        ],
        'Año Anterior': [
            137000000,
            '',
            '',
            '',
            1800000,
            6200000,
            -800000,
            -2100000,
            3800000,
            '',
            8900000,
            '',
            145900000
        ],
        'Variación %': [
            13.14,
            '',
            '',
            '',
            -238.89,
            37.10,
            250.00,
            52.38,
            44.74,
            '',
            6.74,
            '',
            12.75
        ]
    }
    
    df_eri = pd.DataFrame(datos_eri)
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Resultado del Ejercicio",
            value="$155.000.000",
            delta="13,14%"
        )
    
    with col2:
        st.metric(
            label="Otros Resultados Integrales",
            value="$9.500.000",
            delta="6,74%"
        )
    
    with col3:
        st.metric(
            label="Resultado Integral Total",
            value="$164.500.000",
            delta="12,75%"
        )
    
    st.markdown("---")
    
    # Tabla principal y análisis
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Estado de Resultados Integral Detallado")
        
        # Formatear la tabla
        def format_currency(val):
            if pd.isna(val) or val == '' or val == 0:
                return ''
            return f"${val:,.0f}" if isinstance(val, (int, float)) else val
        
        def format_percentage(val):
            if pd.isna(val) or val == '' or val == 0:
                return ''
            return f"{val:.2f}%" if isinstance(val, (int, float)) else val
        
        df_display = df_eri.copy()
        df_display['Año Actual'] = df_display['Año Actual'].apply(format_currency).astype(str)
        df_display['Año Anterior'] = df_display['Año Anterior'].apply(format_currency).astype(str)
        df_display['Variación %'] = df_display['Variación %'].apply(format_percentage)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("💡 Análisis de Composición")
        
        # Composición del resultado integral
        resultado_ejercicio = 155000000
        otros_integrales = 9500000
        total_integral = 164500000
        
        participacion_ejercicio = (resultado_ejercicio / total_integral) * 100
        participacion_otros = (otros_integrales / total_integral) * 100
        
        st.metric("Participación Resultado del Ejercicio", f"{participacion_ejercicio:.1f}%")
        st.metric("Participación Otros Integrales", f"{participacion_otros:.1f}%")
        
        st.info("💡 **Insight:** Los otros resultados integrales representan el 5.8% del resultado integral total, indicando una gestión prudente de los riesgos financieros.")
    
    # Análisis gráfico de los otros resultados integrales
    st.markdown("---")
    st.subheader("📈 Análisis de Otros Resultados Integrales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras de componentes ORI
        ori_componentes = {
            'Componente': [
                'Diferencias de Conversión',
                'Revalorización de Propiedades', 
                'Instrumentos Financieros',
                'Beneficios a Empleados',
                'Ajustes por Inflación'
            ],
            'Año Actual': [-2500000, 8500000, 1200000, -3200000, 5500000],
            'Año Anterior': [1800000, 6200000, -800000, -2100000, 3800000]
        }
        
        df_ori = pd.DataFrame(ori_componentes)
        df_ori_melted = df_ori.melt(id_vars=['Componente'], var_name='Período', value_name='Valor')
        
        fig_ori = px.bar(
            df_ori_melted,
            x='Componente',
            y='Valor',
            color='Período',
            title="Evolución de Otros Resultados Integrales",
            barmode='group'
        )
        fig_ori.update_xaxes(tickangle=45)
        fig_ori.update_layout(yaxis_title="Valor (CLP)")
        st.plotly_chart(fig_ori, use_container_width=True)
    
    with col2:
        # Gráfico de composición actual de ORI
        ori_actual = {
            'Componente': [
                'Revalorización Propiedades',
                'Ajustes por Inflación', 
                'Instrumentos Financieros',
                'Diferencias de Conversión',
                'Beneficios a Empleados'
            ],
            'Valor': [8500000, 5500000, 1200000, -2500000, -3200000]
        }
        
        df_ori_actual = pd.DataFrame(ori_actual)
        # Separar positivos y negativos
        df_ori_pos = df_ori_actual[df_ori_actual['Valor'] > 0]
        df_ori_neg = df_ori_actual[df_ori_actual['Valor'] < 0]
        
        fig_ori_comp = go.Figure()
        
        # Agregar valores positivos
        fig_ori_comp.add_trace(go.Bar(
            name='Positivos',
            x=df_ori_pos['Componente'],
            y=df_ori_pos['Valor'],
            marker_color='green',
            text=df_ori_pos['Valor'],
            texttemplate='$%{text:,.0f}'
        ))
        
        # Agregar valores negativos
        fig_ori_comp.add_trace(go.Bar(
            name='Negativos',
            x=df_ori_neg['Componente'],
            y=df_ori_neg['Valor'],
            marker_color='red',
            text=df_ori_neg['Valor'],
            texttemplate='$%{text:,.0f}'
        ))
        
        fig_ori_comp.update_layout(
            title="Componentes ORI - Año Actual",
            yaxis_title="Valor (CLP)",
            xaxis_tickangle=45
        )
        
        st.plotly_chart(fig_ori_comp, use_container_width=True)
    
    # Evolución del resultado integral
    st.markdown("---")
    st.subheader("📊 Evolución del Resultado Integral")
    
    # Datos para gráfico de evolución
    periodos = ['Año Anterior', 'Año Actual']
    resultado_ejercicio_evol = [137000000, 155000000]
    otros_integrales_evol = [8900000, 9500000]
    resultado_integral_evol = [145900000, 164500000]
    
    fig_evol = go.Figure()
    
    fig_evol.add_trace(go.Bar(
        name='Resultado del Ejercicio',
        x=periodos,
        y=resultado_ejercicio_evol,
        text=resultado_ejercicio_evol,
        texttemplate='$%{text:,.0f}',
        marker_color='lightblue'
    ))
    
    fig_evol.add_trace(go.Bar(
        name='Otros Resultados Integrales',
        x=periodos,
        y=otros_integrales_evol,
        text=otros_integrales_evol,
        texttemplate='$%{text:,.0f}',
        marker_color='orange'
    ))
    
    fig_evol.add_trace(go.Scatter(
        name='Resultado Integral Total',
        x=periodos,
        y=resultado_integral_evol,
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=10),
        text=resultado_integral_evol,
        texttemplate='$%{text:,.0f}',
        textposition='top center'
    ))
    
    fig_evol.update_layout(
        title="Evolución del Resultado Integral Total",
        yaxis_title="Valor (CLP)",
        barmode='stack'
    )
    
    st.plotly_chart(fig_evol, use_container_width=True)
    
    # Indicadores y alertas
    st.markdown("---")
    st.subheader("🚨 Indicadores y Alertas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Volatilidad ORI",
            value="Moderada",
            help="Basado en la variabilidad de los componentes"
        )
    
    with col2:
        variacion_ori = ((9500000 - 8900000) / 8900000) * 100
        st.metric(
            label="Crecimiento ORI",
            value=f"{variacion_ori:.1f}%",
            delta=f"{variacion_ori:.1f}%"
        )
    
    with col3:
        ratio_ori = (9500000 / 155000000) * 100
        st.metric(
            label="Ratio ORI/Resultado",
            value=f"{ratio_ori:.1f}%",
            help="Otros Integrales vs Resultado del Ejercicio"
        )
    
    with col4:
        st.metric(
            label="Estabilidad",
            value="Alta",
            help="Resultado integral muestra crecimiento sostenido"
        )
    
    # Notas explicativas
    with st.expander("📝 Notas Metodológicas"):
        st.markdown("""
        **Otros Resultados Integrales incluyen:**
        
        - **Diferencias de Conversión:** Variaciones por tipo de cambio en subsidiarias extranjeras
        - **Revalorización de Propiedades:** Ajustes al valor justo de propiedades de inversión
        - **Instrumentos Financieros Derivados:** Cambios en el valor justo de coberturas
        - **Beneficios a Empleados:** Ganancias/pérdidas actuariales en planes de beneficios
        - **Ajustes por Inflación:** Corrección monetaria según UF/IPC
        
        **Interpretación:**
        - Los ORI representan cambios en el patrimonio que no pasan por resultados
        - Su análisis es crucial para evaluar la situación financiera integral
        - La volatilidad de estos componentes puede indicar exposición a riesgos específicos
        """)
