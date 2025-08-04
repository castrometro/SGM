import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show(data, metadata):
    """Mostrar análisis de personal y RRHH"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #6f42c1, #e83e8c); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
        <h1>👥 Análisis de Personal</h1>
        <p>Movimientos, indicadores y métricas de recursos humanos</p>
    </div>
    """, unsafe_allow_html=True)
    
    movimientos = data.get('movimientos', {})
    metricas = data.get('metricas_basicas', {})
    
    # Métricas de personal
    st.markdown("### 👥 Métricas de Personal")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        dotacion_total = metricas.get('dotacion_total', 0)
        st.metric("👥 Dotación Total", f"{dotacion_total:,}")
    
    with col2:
        ingresos = movimientos.get('empleados_nuevos', 0)
        st.metric("🆕 Nuevos Ingresos", f"{ingresos:,}")
    
    with col3:
        finiquitos = movimientos.get('empleados_finiquitados', 0)
        st.metric("📤 Finiquitos", f"{finiquitos:,}")
    
    with col4:
        ausencias = movimientos.get('empleados_con_ausencias', 0)
        st.metric("🏥 Con Ausencias", f"{ausencias:,}")
    
    st.markdown("---")
    
    # Análisis de movimientos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔄 Flujo de Personal")
        
        # Datos para el gráfico de flujo
        flujo_data = {
            'Movimiento': ['Ingresos', 'Finiquitos', 'Ausencias'],
            'Cantidad': [ingresos, finiquitos, ausencias],
            'Tipo': ['Positivo', 'Negativo', 'Neutral']
        }
        
        df_flujo = pd.DataFrame(flujo_data)
        df_flujo = df_flujo[df_flujo['Cantidad'] > 0]
        
        if not df_flujo.empty:
            # Colores según el tipo de movimiento
            color_map = {'Positivo': '#28a745', 'Negativo': '#dc3545', 'Neutral': '#ffc107'}
            
            fig_flujo = px.bar(
                df_flujo,
                x='Movimiento',
                y='Cantidad',
                color='Tipo',
                color_discrete_map=color_map,
                text='Cantidad'
            )
            
            fig_flujo.update_layout(
                height=350,
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            fig_flujo.update_traces(textposition='outside')
            st.plotly_chart(fig_flujo, use_container_width=True)
        else:
            st.info("No hay movimientos de personal registrados")
    
    with col2:
        st.markdown("#### 📊 Indicadores de Gestión")
        
        # Calcular indicadores
        dotacion_activa = metricas.get('dotacion_activa', dotacion_total)
        rotacion = metricas.get('rotacion_porcentaje', 0)
        ausentismo = metricas.get('ausentismo_porcentaje', 0)
        
        # Datos para gráfico de indicadores
        indicadores_data = {
            'Indicador': ['Rotación %', 'Ausentismo %'],
            'Valor Actual': [rotacion, ausentismo],
            'Meta': [8, 3],  # Metas típicas de la industria
            'Límite Superior': [12, 5]
        }
        
        df_indicadores = pd.DataFrame(indicadores_data)
        
        fig_indicadores = go.Figure()
        
        # Barras del valor actual
        colors = []
        for i, row in df_indicadores.iterrows():
            if row['Valor Actual'] <= row['Meta']:
                colors.append('#28a745')  # Verde si está bajo la meta
            elif row['Valor Actual'] <= row['Límite Superior']:
                colors.append('#ffc107')  # Amarillo si está en rango aceptable
            else:
                colors.append('#dc3545')  # Rojo si está sobre el límite
        
        fig_indicadores.add_trace(go.Bar(
            name='Valor Actual',
            x=df_indicadores['Indicador'],
            y=df_indicadores['Valor Actual'],
            marker_color=colors,
            text=df_indicadores['Valor Actual'],
            texttemplate='%{text:.1f}%',
            textposition='outside'
        ))
        
        # Línea de meta
        fig_indicadores.add_trace(go.Scatter(
            name='Meta',
            x=df_indicadores['Indicador'],
            y=df_indicadores['Meta'],
            mode='markers+lines',
            marker=dict(color='orange', size=10),
            line=dict(color='orange', dash='dash', width=2)
        ))
        
        fig_indicadores.update_layout(
            height=350,
            yaxis_title="Porcentaje (%)",
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_indicadores, use_container_width=True)
    
    # Análisis detallado de dotación
    st.markdown("### 📋 Análisis de Dotación")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 👔 Información Laboral")
        st.write(f"• **Dotación total:** {dotacion_total:,}")
        st.write(f"• **Dotación activa:** {dotacion_activa:,}")
        
        if dotacion_total > 0:
            porcentaje_activos = (dotacion_activa / dotacion_total) * 100
            st.write(f"• **% Activos:** {porcentaje_activos:.1f}%")
        
        # Cálculo de rotación neta
        rotacion_neta = ingresos - finiquitos
        st.write(f"• **Rotación neta:** {rotacion_neta:+,}")
    
    with col2:
        st.markdown("#### 📈 Indicadores Calculados")
        
        if dotacion_activa > 0:
            # Tasa de ingresos
            tasa_ingresos = (ingresos / dotacion_activa) * 100
            st.write(f"• **Tasa de ingresos:** {tasa_ingresos:.1f}%")
            
            # Tasa de salidas
            tasa_salidas = (finiquitos / dotacion_activa) * 100
            st.write(f"• **Tasa de salidas:** {tasa_salidas:.1f}%")
            
            # Tasa de ausentismo
            if ausencias > 0:
                tasa_ausencias = (ausencias / dotacion_activa) * 100
                st.write(f"• **Tasa de ausencias:** {tasa_ausencias:.1f}%")
            else:
                st.write("• **Tasa de ausencias:** 0.0%")
        else:
            st.info("No hay empleados activos para calcular indicadores")
    
    with col3:
        st.markdown("#### 🎯 Evaluación de Indicadores")
        
        # Evaluación de rotación
        if rotacion <= 8:
            st.success(f"✅ Rotación: {rotacion:.1f}% (Excelente)")
        elif rotacion <= 12:
            st.warning(f"⚠️ Rotación: {rotacion:.1f}% (Aceptable)")
        else:
            st.error(f"❌ Rotación: {rotacion:.1f}% (Alto)")
        
        # Evaluación de ausentismo
        if ausentismo <= 3:
            st.success(f"✅ Ausentismo: {ausentismo:.1f}% (Bajo)")
        elif ausentismo <= 5:
            st.warning(f"⚠️ Ausentismo: {ausentismo:.1f}% (Moderado)")
        else:
            st.error(f"❌ Ausentismo: {ausentismo:.1f}% (Alto)")
        
        # Evaluación de crecimiento
        if rotacion_neta > 0:
            st.info(f"📈 Crecimiento: +{rotacion_neta} empleados")
        elif rotacion_neta < 0:
            st.info(f"📉 Reducción: {rotacion_neta} empleados")
        else:
            st.info("➡️ Dotación estable")
    
    # Tabla resumen de movimientos
    if any([ingresos, finiquitos, ausencias]):
        st.markdown("### 📊 Resumen de Movimientos")
        
        resumen_movimientos = {
            'Concepto': [
                'Empleados Nuevos',
                'Finiquitos',
                'Empleados con Ausencias',
                'Dotación Final Estimada'
            ],
            'Cantidad': [
                ingresos,
                finiquitos,
                ausencias,
                dotacion_activa
            ],
            'Observaciones': [
                'Ingresos durante el período',
                'Salidas durante el período', 
                'Empleados que tuvieron ausencias',
                'Dotación activa al final del período'
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_movimientos)
        
        # Formatear la tabla
        st.dataframe(
            df_resumen,
            use_container_width=True,
            hide_index=True
        )
    
    # Recomendaciones
    st.markdown("### 💡 Recomendaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Análisis de Riesgos")
        
        if rotacion > 12:
            st.warning("⚠️ **Alta rotación detectada**")
            st.write("- Revisar procesos de selección")
            st.write("- Evaluar clima laboral")
            st.write("- Analizar competitividad salarial")
        
        if ausentismo > 5:
            st.warning("⚠️ **Alto ausentismo detectado**")
            st.write("- Implementar programas de bienestar")
            st.write("- Revisar cargas de trabajo")
            st.write("- Evaluar ambiente laboral")
    
    with col2:
        st.markdown("#### 📈 Oportunidades de Mejora")
        
        if rotacion <= 8 and ausentismo <= 3:
            st.success("✅ **Indicadores en rango óptimo**")
            st.write("- Mantener políticas actuales")
            st.write("- Documentar mejores prácticas")
            st.write("- Considerar benchmarking")
        
        if dotacion_activa > 0:
            # Sugerir basado en el crecimiento
            if rotacion_neta > dotacion_activa * 0.1:  # Crecimiento > 10%
                st.info("📈 **Crecimiento acelerado**")
                st.write("- Planificar integración de nuevos empleados")
                st.write("- Reforzar procesos de onboarding")
            elif rotacion_neta < 0:
                st.info("📉 **Reducción de dotación**")
                st.write("- Evaluar impacto en operaciones")
                st.write("- Considerar redistribución de cargas")
