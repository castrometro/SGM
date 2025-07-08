import streamlit as st
import pandas as pd
import plotly.express as px
def mostrar(data=None):
    st.header("📊 Resumen General de Nómina")
    st.markdown("**Visión general del cierre de remuneraciones**")
    if not data:
        st.error("No hay datos disponibles")
        return
    mostrar_info_general(data)
    mostrar_kpis_principales(data)
    mostrar_analisis_centros_costo(data)
    mostrar_resumen_conceptos(data)
    mostrar_analisis_incidencias(data)
def mostrar_info_general(data):
    """Muestra información general del cierre"""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cliente", data.get("cliente_nombre", "N/A"))
    with col2:
        st.metric("Período", data.get("periodo", "N/A"))
    with col3:
        st.metric("RUT Cliente", data.get("cliente_rut", "N/A"))
    with col4:
        st.metric("Generado por", data.get("generado_por", "N/A"))
def mostrar_kpis_principales(data):
    """Muestra los KPIs principales de dotación y costos"""
    dotacion = data.get("resumen_dotacion", {})
    costos = data.get("resumen_costos", {})
    st.markdown("---")
    st.subheader("📈 KPIs Principales")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        dotacion_final = dotacion.get("dotacion_final", 0) or 0
        ingresos_mes = dotacion.get("ingresos_mes", 0) or 0
        finiquitos_mes = dotacion.get("finiquitos_mes", 0) or 0
        st.metric(
            "Dotación Final", 
            dotacion_final,
            delta=f"{ingresos_mes - finiquitos_mes:+d}" if (ingresos_mes - finiquitos_mes) != 0 else None
        )
    with col2:
        rotacion_pct = dotacion.get("rotacion_pct", 0) or 0
        st.metric(
            "Rotación", 
            f"{rotacion_pct:.1f}%"
        )
    with col3:
        total_haberes = costos.get("total_haberes", 0) or 0
        variacion_pct = costos.get('variacion_remuneraciones_pct', 0)
        if variacion_pct and variacion_pct != 0:
            delta_text = f"{variacion_pct:+.1f}%"
        else:
            delta_text = None
        st.metric(
            "Total Haberes", 
            f"${total_haberes:,.0f}",
            delta=delta_text
        )
    with col4:
        costo_empresa = costos.get("costo_empresa", 0) or 0
        st.metric(
            "Costo Empresa", 
            f"${costo_empresa:,.0f}"
        )
def mostrar_analisis_centros_costo(data):
    """Muestra análisis mejorado de centros de costo"""
    st.markdown("---")
    st.subheader("🏢 Análisis por Centro de Costo")
    remuneracion_data = data.get("remuneracion_promedio", {})
    por_centro = remuneracion_data.get("por_centro_costo", [])
    if not por_centro:
        st.info("No hay datos de centros de costo disponibles")
        return
    df_centros = pd.DataFrame(por_centro)
    col1, col2 = st.columns([2, 1])
    with col1:
        num_centros = len(df_centros)
        if num_centros <= 8:
            fig = px.bar(
                df_centros.sort_values('promedio', ascending=True),
                x='promedio',
                y='centro_costo',
                orientation='h',
                title='Remuneración Promedio por Centro de Costo',
                labels={'promedio': 'Remuneración Promedio ($)', 'centro_costo': 'Centro de Costo'},
                color='promedio',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=max(300, num_centros * 50),  
                showlegend=False,
                xaxis_tickformat='$,.0f'
            )
            fig.update_traces(texttemplate='$%{x:,.0f}', textposition='outside')
        else:
            fig = px.bar(
                df_centros.sort_values('promedio', ascending=False),
                x='centro_costo',
                y='promedio',
                title='Remuneración Promedio por Centro de Costo',
                labels={'promedio': 'Remuneración Promedio ($)', 'centro_costo': 'Centro de Costo'},
                color='promedio',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=500,
                showlegend=False,
                xaxis_tickangle=-45,  
                yaxis_tickformat='$,.0f'
            )
            fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**Resumen de Centros**")
        df_centros_stats = df_centros.copy()
        df_centros_stats['promedio_fmt'] = df_centros_stats['promedio'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(
            df_centros_stats[['centro_costo', 'promedio_fmt']].rename(columns={
                'centro_costo': 'Centro de Costo',
                'promedio_fmt': 'Remuneración Promedio'
            }),
            use_container_width=True,
            hide_index=True
        )
        st.markdown("---")
        st.markdown("**Estadísticas:**")
        st.metric("Promedio General", f"${remuneracion_data.get('global', 0):,.0f}")
        st.metric("Diferencia Máx-Mín", f"${df_centros['promedio'].max() - df_centros['promedio'].min():,.0f}")
def mostrar_resumen_conceptos(data):
    """Muestra resumen de conceptos de nómina"""
    st.markdown("---")
    st.subheader("💰 Resumen de Conceptos")
    conceptos = data.get("conceptos_resumidos", [])
    if not conceptos:
        st.info("No hay datos de conceptos disponibles")
        return
    df_conceptos = pd.DataFrame(conceptos)
    col1, col2 = st.columns(2)
    with col1:
        conceptos_por_categoria = df_conceptos.groupby('categoria')['total_monto'].sum().reset_index()
        fig_categoria = px.pie(
            conceptos_por_categoria,
            values='total_monto',
            names='categoria',
            title='Distribución por Categoría'
        )
        st.plotly_chart(fig_categoria, use_container_width=True)
    with col2:
        fig_conceptos = px.bar(
            df_conceptos.sort_values('total_monto', ascending=True),
            x='total_monto',
            y='concepto',
            orientation='h',
            title='Monto por Concepto',
            color='categoria'
        )
        fig_conceptos.update_layout(
            height=max(300, len(df_conceptos) * 40),
            xaxis_tickformat='$,.0f'
        )
        st.plotly_chart(fig_conceptos, use_container_width=True)
def mostrar_analisis_incidencias(data):
    """Muestra análisis detallado de incidencias"""
    st.markdown("---")
    st.subheader("⚠️ Análisis de Incidencias")
    incidencias = []
    for key, value in data.items():
        if key.startswith("incidencias_fase_") and isinstance(value, list):
            incidencias.extend(value)
    if not incidencias:
        st.info("No hay incidencias registradas en este período")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Incidencias", len(incidencias))
    with col2:
        conceptos_unicos = len(set(inc.get('concepto', '') for inc in incidencias))
        st.metric("Conceptos Diferentes", conceptos_unicos)
    with col3:
        trabajadores_afectados = len(set(inc.get('rut', '') for inc in incidencias))
        st.metric("Trabajadores Afectados", trabajadores_afectados)
    st.markdown("**Distribución por Concepto**")
    df_incidencias = pd.DataFrame(incidencias)
    if not df_incidencias.empty:
        conceptos_count = df_incidencias['concepto'].value_counts().reset_index()
        conceptos_count.columns = ['concepto', 'cantidad']
        conceptos_count['porcentaje'] = (conceptos_count['cantidad'] / len(incidencias) * 100).round(1)
        col1, col2 = st.columns([2, 1])
        with col1:
            fig_conceptos = px.bar(
                conceptos_count,
                x='concepto',
                y='cantidad',
                title='Incidencias por Concepto',
                labels={'cantidad': 'Número de Incidencias', 'concepto': 'Concepto'},
                color='cantidad',
                color_continuous_scale='Reds'
            )
            fig_conceptos.update_layout(
                xaxis_tickangle=-45,
                showlegend=False
            )
            fig_conceptos.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig_conceptos, use_container_width=True)
        with col2:
            st.markdown("**Distribución Porcentual**")
            tabla_conceptos = conceptos_count.copy()
            tabla_conceptos['porcentaje_fmt'] = tabla_conceptos['porcentaje'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                tabla_conceptos[['concepto', 'cantidad', 'porcentaje_fmt']].rename(columns={
                    'concepto': 'Concepto',
                    'cantidad': 'Cantidad',
                    'porcentaje_fmt': 'Porcentaje'
                }),
                use_container_width=True,
                hide_index=True
            )
    st.markdown("---")
    st.markdown("**Detalle de Incidencias**")
    with st.expander("Ver todas las incidencias"):
        if not df_incidencias.empty:
            df_display = df_incidencias.copy()
            if 'detalle_actual' in df_display.columns:
                df_display['dias_actual'] = df_display['detalle_actual'].apply(
                    lambda x: x.get('dias', 0) if isinstance(x, dict) else 0
                )
            if 'detalle_mes_anterior' in df_display.columns:
                df_display['dias_anterior'] = df_display['detalle_mes_anterior'].apply(
                    lambda x: x.get('dias', 0) if isinstance(x, dict) else 0
                )
            columnas_mostrar = ['rut', 'nombre', 'concepto', 'variacion', 'observacion']
            if 'dias_actual' in df_display.columns:
                columnas_mostrar.append('dias_actual')
            if 'dias_anterior' in df_display.columns:
                columnas_mostrar.append('dias_anterior')
            columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
            st.dataframe(
                df_display[columnas_disponibles],
                use_container_width=True,
                hide_index=True
            )
