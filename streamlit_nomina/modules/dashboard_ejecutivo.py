import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def show(data, metadata):
    """Mostrar dashboard ejecutivo con KPIs principales"""
    
    # Header del dashboard
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4e79, #2e86de); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
        <h1>📊 Dashboard Ejecutivo</h1>
        <p>Métricas principales del período de nómina</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información del período
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Cliente:** {metadata.get('cliente_nombre', 'N/A')}")
    with col2:
        st.info(f"**Período:** {metadata.get('periodo', 'N/A')}")
    with col3:
        fecha_gen = metadata.get('fecha_generacion')
        if fecha_gen:
            try:
                if isinstance(fecha_gen, str):
                    fecha_obj = datetime.fromisoformat(fecha_gen.replace('Z', '+00:00'))
                    fecha_formato = fecha_obj.strftime('%d/%m/%Y %H:%M')
                else:
                    fecha_formato = str(fecha_gen)
            except:
                fecha_formato = str(fecha_gen)
        else:
            fecha_formato = 'N/A'
        st.info(f"**Generado:** {fecha_formato}")
    
    # Obtener métricas
    metricas = data.get('metricas_basicas', {})
    movimientos = data.get('movimientos', {})
    
    # KPIs Principales
    st.markdown("### 💼 Métricas Principales")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        dotacion_total = metricas.get('dotacion_total', 0)
        dotacion_activa = metricas.get('dotacion_activa', 0)
        st.metric(
            "👥 Dotación Total",
            f"{dotacion_total:,}",
            delta=f"{dotacion_activa:,} activos"
        )
    
    with col2:
        costo_total = metricas.get('costo_empresa_total', 0)
        st.metric(
            "💰 Costo Total",
            f"${costo_total:,.0f}",
            help="Costo total empresa para este período"
        )
    
    with col3:
        liquido_total = metricas.get('liquido_total', 0)
        st.metric(
            "💵 Líquido Total",
            f"${liquido_total:,.0f}",
            help="Total líquido pagado a empleados"
        )
    
    with col4:
        rotacion = metricas.get('rotacion_porcentaje', 0)
        delta_rotacion = rotacion - 5 if rotacion > 5 else None
        st.metric(
            "🔄 Rotación",
            f"{rotacion:.1f}%",
            delta=f"{delta_rotacion:.1f}%" if delta_rotacion else None,
            delta_color="inverse" if delta_rotacion and delta_rotacion > 0 else "normal"
        )
    
    with col5:
        ausentismo = metricas.get('ausentismo_porcentaje', 0)
        delta_ausentismo = ausentismo - 3 if ausentismo > 3 else None
        st.metric(
            "🏥 Ausentismo",
            f"{ausentismo:.1f}%",
            delta=f"{delta_ausentismo:.1f}%" if delta_ausentismo else None,
            delta_color="inverse" if delta_ausentismo and delta_ausentismo > 0 else "normal"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Distribución de Costos")
        
        # Crear gráfico de dona
        valores = [
            liquido_total,
            metricas.get('descuentos_legales_total', 0),
            costo_total - liquido_total - metricas.get('descuentos_legales_total', 0)
        ]
        labels = ['Líquido Empleados', 'Descuentos Legales', 'Otros Costos']
        
        # Filtrar valores cero
        datos_filtrados = [(l, v) for l, v in zip(labels, valores) if v > 0]
        if datos_filtrados:
            labels_filtrados, valores_filtrados = zip(*datos_filtrados)
            
            fig_dona = go.Figure(data=[go.Pie(
                labels=labels_filtrados,
                values=valores_filtrados,
                hole=0.4,
                marker_colors=['#2e86de', '#ff6b6b', '#48cae4']
            )])
            
            fig_dona.update_layout(
                height=300, 
                showlegend=True,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_dona, use_container_width=True)
        else:
            st.info("No hay datos de costos disponibles")
    
    with col2:
        st.markdown("#### 🔄 Movimientos de Personal")
        
        # Crear gráfico de barras
        movimientos_data = {
            'Tipo': ['Nuevos Ingresos', 'Finiquitos', 'Con Ausencias'],
            'Cantidad': [
                movimientos.get('empleados_nuevos', 0),
                movimientos.get('empleados_finiquitados', 0),
                movimientos.get('empleados_con_ausencias', 0)
            ]
        }
        
        df_movimientos = pd.DataFrame(movimientos_data)
        
        if df_movimientos['Cantidad'].sum() > 0:
            fig_barras = px.bar(
                df_movimientos,
                x='Tipo',
                y='Cantidad',
                color='Cantidad',
                color_continuous_scale='Blues',
                text='Cantidad'
            )
            
            fig_barras.update_layout(
                height=300,
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            fig_barras.update_traces(textposition='outside')
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.info("No hay movimientos de personal en este período")
    
    # Resumen adicional
    st.markdown("### 📋 Resumen del Período")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💼 Información Laboral**")
        st.write(f"• Empleados activos: {metricas.get('dotacion_activa', 0):,}")
        st.write(f"• Empleados totales: {dotacion_total:,}")
        st.write(f"• Nuevos ingresos: {movimientos.get('empleados_nuevos', 0):,}")
        st.write(f"• Finiquitos: {movimientos.get('empleados_finiquitados', 0):,}")
    
    with col2:
        st.markdown("**💰 Información Financiera**")
        st.write(f"• Costo empresa: ${costo_total:,.0f}")
        st.write(f"• Total líquido: ${liquido_total:,.0f}")
        st.write(f"• Descuentos legales: ${metricas.get('descuentos_legales_total', 0):,.0f}")
        st.write(f"• Horas extras: ${metricas.get('horas_extras_total', 0):,.0f}")
    
    with col3:
        st.markdown("**📊 Indicadores**")
        st.write(f"• Rotación: {rotacion:.1f}%")
        st.write(f"• Ausentismo: {ausentismo:.1f}%")
        
        # Calcular eficiencia de costo
        if dotacion_activa > 0:
            costo_por_empleado = costo_total / dotacion_activa
            st.write(f"• Costo/empleado: ${costo_por_empleado:,.0f}")
        else:
            st.write("• Costo/empleado: N/A")
        
        # Ratio líquido vs costo
        if costo_total > 0:
            ratio_liquido = (liquido_total / costo_total) * 100
            st.write(f"• % Líquido del costo: {ratio_liquido:.1f}%")
        else:
            st.write("• % Líquido del costo: N/A")
