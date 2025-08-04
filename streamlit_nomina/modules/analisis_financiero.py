import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show(data, metadata):
    """Mostrar análisis financiero detallado"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #28a745, #20c997); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
        <h1>💰 Análisis Financiero</h1>
        <p>Desglose detallado de costos y análisis previsional</p>
    </div>
    """, unsafe_allow_html=True)
    
    metricas = data.get('metricas_basicas', {})
    desglose = data.get('desglose_previsional', [])
    
    # Métricas financieras principales
    st.markdown("### 💵 Métricas Financieras")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        costo_empresa = metricas.get('costo_empresa_total', 0)
        st.metric("💰 Costo Empresa", f"${costo_empresa:,.0f}")
    
    with col2:
        liquido_total = metricas.get('liquido_total', 0)
        st.metric("💵 Total Líquido", f"${liquido_total:,.0f}")
    
    with col3:
        descuentos = metricas.get('descuentos_legales_total', 0)
        st.metric("📉 Descuentos", f"${descuentos:,.0f}")
    
    with col4:
        horas_extras = metricas.get('horas_extras_total', 0)
        st.metric("⏰ Horas Extras", f"${horas_extras:,.0f}")
    
    st.markdown("---")
    
    # Análisis de composición de costos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Composición de Costos")
        
        # Preparar datos para el análisis
        componentes_costo = {
            'Concepto': [
                'Sueldos Base',
                'Horas Extras', 
                'Gratificación',
                'Otros Haberes',
                'Descuentos Legales',
                'Provisiones'
            ],
            'Monto': [
                metricas.get('sueldos_base_total', 0),
                horas_extras,
                metricas.get('gratificacion_total', 0),
                metricas.get('otros_haberes_total', 0),
                descuentos,
                metricas.get('provisiones_total', 0)
            ]
        }
        
        df_costos = pd.DataFrame(componentes_costo)
        df_costos = df_costos[df_costos['Monto'] > 0].sort_values('Monto', ascending=True)
        
        if not df_costos.empty:
            fig_costos = px.bar(
                df_costos,
                y='Concepto',
                x='Monto',
                orientation='h',
                color='Monto',
                color_continuous_scale='Blues',
                text='Monto'
            )
            
            fig_costos.update_layout(
                height=400,
                xaxis_title="Monto ($)",
                yaxis_title="",
                coloraxis_showscale=False
            )
            fig_costos.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_costos, use_container_width=True)
        else:
            st.info("No hay datos de composición de costos disponibles")
    
    with col2:
        st.markdown("#### 📊 Distribución Porcentual")
        
        if not df_costos.empty:
            # Crear gráfico de torta
            fig_pie = px.pie(
                df_costos,
                values='Monto',
                names='Concepto',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig_pie.update_layout(
                height=400,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para mostrar distribución")
    
    # Desglose previsional
    if desglose:
        st.markdown("### 🏥 Desglose Previsional")
        
        # Crear DataFrame del desglose
        df_previsional = pd.DataFrame(desglose)
        
        if not df_previsional.empty:
            df_previsional = df_previsional.sort_values('monto_total', ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### 📋 Instituciones Previsionales")
                
                # Gráfico de barras horizontal
                fig_previsional = px.bar(
                    df_previsional,
                    y='institucion',
                    x='monto_total',
                    orientation='h',
                    text='cantidad_empleados',
                    color='monto_total',
                    color_continuous_scale='Viridis',
                    labels={'monto_total': 'Monto Total ($)', 'institucion': 'Institución'}
                )
                
                fig_previsional.update_layout(
                    height=400,
                    coloraxis_showscale=False
                )
                fig_previsional.update_traces(
                    texttemplate='%{text} empleados',
                    textposition='outside'
                )
                st.plotly_chart(fig_previsional, use_container_width=True)
            
            with col2:
                st.markdown("#### 📊 Resumen Previsional")
                
                # Mostrar tabla resumen
                df_display = df_previsional.copy()
                df_display['monto_total'] = df_display['monto_total'].apply(lambda x: f"${x:,.0f}")
                df_display = df_display.rename(columns={
                    'institucion': 'Institución',
                    'monto_total': 'Monto Total',
                    'cantidad_empleados': 'Empleados'
                })
                
                st.dataframe(df_display, use_container_width=True)
                
                # Totales
                total_empleados_previsional = df_previsional['cantidad_empleados'].sum()
                total_monto_previsional = df_previsional['monto_total'].sum()
                
                st.markdown("**Totales:**")
                st.write(f"• Empleados: {total_empleados_previsional:,}")
                st.write(f"• Monto total: ${total_monto_previsional:,.0f}")
    else:
        st.markdown("### 🏥 Desglose Previsional")
        st.info("No hay información previsional disponible para este período")
    
    # Análisis de ratios financieros
    st.markdown("### 📈 Análisis de Ratios")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 💼 Eficiencia Operacional")
        
        dotacion_activa = metricas.get('dotacion_activa', 1)
        if dotacion_activa > 0:
            costo_por_empleado = costo_empresa / dotacion_activa
            liquido_por_empleado = liquido_total / dotacion_activa
            
            st.metric("💰 Costo/Empleado", f"${costo_por_empleado:,.0f}")
            st.metric("💵 Líquido/Empleado", f"${liquido_por_empleado:,.0f}")
            
            if horas_extras > 0:
                ratio_horas_extras = (horas_extras / costo_empresa) * 100
                st.metric("⏰ % Horas Extras", f"{ratio_horas_extras:.1f}%")
        else:
            st.info("No hay empleados activos para calcular ratios")
    
    with col2:
        st.markdown("#### 🔄 Composición del Costo")
        
        if costo_empresa > 0:
            ratio_liquido = (liquido_total / costo_empresa) * 100
            ratio_descuentos = (descuentos / costo_empresa) * 100
            ratio_otros = 100 - ratio_liquido - ratio_descuentos
            
            st.metric("💵 % Líquido", f"{ratio_liquido:.1f}%")
            st.metric("📉 % Descuentos", f"{ratio_descuentos:.1f}%")
            st.metric("📊 % Otros", f"{ratio_otros:.1f}%")
        else:
            st.info("No hay datos de costo para calcular ratios")
    
    with col3:
        st.markdown("#### 📊 Indicadores Adicionales")
        
        # Carga previsional promedio
        if desglose and len(desglose) > 0:
            promedio_previsional = sum(item['monto_total'] for item in desglose) / len(desglose)
            st.metric("🏥 Promedio Previsional", f"${promedio_previsional:,.0f}")
        
        # Ratio de gratificación si existe
        gratificacion = metricas.get('gratificacion_total', 0)
        if gratificacion > 0 and costo_empresa > 0:
            ratio_gratificacion = (gratificacion / costo_empresa) * 100
            st.metric("🎁 % Gratificación", f"{ratio_gratificacion:.1f}%")
        
        # Carga tributaria
        if costo_empresa > 0:
            otros_costos = costo_empresa - liquido_total - descuentos
            if otros_costos > 0:
                ratio_carga = (otros_costos / costo_empresa) * 100
                st.metric("🏛️ % Carga Emp.", f"{ratio_carga:.1f}%")
