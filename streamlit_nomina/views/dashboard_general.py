import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def mostrar(data=None):
    """Dashboard principal con vista general de los datos"""
    st.title("📊 Dashboard General - Nómina")
    
    if not data:
        st.warning("No hay datos disponibles para mostrar")
        return
    
    # Header con información del cliente
    mostrar_header_cliente(data)
    
    # KPIs principales
    mostrar_kpis_principales_nuevos(data)
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    with col1:
        mostrar_distribucion_afiliaciones(data)
    with col2:
        mostrar_conceptos_principales(data)
    
    # Segunda fila de gráficos
    col1, col2 = st.columns(2)
    with col1:
        mostrar_horas_extras(data)
    with col2:
        mostrar_centros_costo(data)
    
    # Análisis detallado
    mostrar_analisis_costos(data)

def mostrar_header_cliente(data):
    """Muestra header con información del cliente"""
    st.markdown("---")
    
    # Información básica
    cliente = data.get("cliente_nombre", "Cliente no especificado")
    periodo = data.get("periodo", "Período no especificado") 
    generado_por = data.get("generado_por", "Usuario no especificado")
    fecha_gen = data.get("generado_fecha", "")
    
    if fecha_gen:
        try:
            fecha_obj = datetime.fromisoformat(fecha_gen.replace('Z', '+00:00'))
            fecha_fmt = fecha_obj.strftime("%d/%m/%Y %H:%M")
        except:
            fecha_fmt = fecha_gen
    else:
        fecha_fmt = "No especificada"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1f77b4, #17becf); color: white; padding: 15px; border-radius: 10px; text-align: center;">
            <h3 style="margin: 0; color: white;">🏢 {cliente}</h3>
            <p style="margin: 5px 0 0 0; color: white;">Cliente</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #ff7f0e, #ffbb78); color: white; padding: 15px; border-radius: 10px; text-align: center;">
            <h3 style="margin: 0; color: white;">📅 {periodo}</h3>
            <p style="margin: 5px 0 0 0; color: white;">Período</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #2ca02c, #98df8a); color: white; padding: 15px; border-radius: 10px; text-align: center;">
            <h3 style="margin: 0; color: white;">👤 {generado_por}</h3>
            <p style="margin: 5px 0 0 0; color: white;">Generado: {fecha_fmt}</p>
        </div>
        """, unsafe_allow_html=True)

def mostrar_kpis_principales_nuevos(data):
    """Muestra KPIs principales con diseño moderno"""
    st.markdown("---")
    st.subheader("📈 Indicadores Clave")
    
    # Extraer datos
    dotacion = data.get("resumen_dotacion", {})
    costos = data.get("resumen_costos", {})
    horas = data.get("horas_extras", {})
    remuneracion = data.get("remuneracion_promedio", {})
    
    dotacion_final = dotacion.get("dotacion_final", 0)
    dotacion_inicial = dotacion.get("dotacion_inicial", 0)
    costo_empresa = costos.get("costo_empresa", 0)
    rotacion = dotacion.get("rotacion_pct", 0)
    total_horas_extras = horas.get("total_horas_50", 0) + horas.get("total_horas_100", 0)
    variacion_dotacion = dotacion_final - dotacion_inicial
    promedio_remuneracion = remuneracion.get("global", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_text = None
        if variacion_dotacion > 0:
            delta_text = f"+{variacion_dotacion} trabajadores"
        elif variacion_dotacion < 0:
            delta_text = f"{variacion_dotacion} trabajadores"
        
        st.metric(
            label="👥 Dotación Total",
            value=f"{dotacion_final:,}",
            delta=delta_text
        )
    
    with col2:
        variacion_pct = costos.get('variacion_remuneraciones_pct')
        delta_text = None
        if variacion_pct:
            delta_text = f"{variacion_pct:+.1f}% vs mes anterior"
        
        st.metric(
            label="💰 Costo Total Empresa",
            value=f"${costo_empresa:,.0f}",
            delta=delta_text
        )
    
    with col3:
        delta_text = None
        if rotacion == 0:
            delta_text = "🟢 Sin rotación"
        elif rotacion < 5:
            delta_text = "🟡 Rotación baja"
        else:
            delta_text = "🔴 Rotación alta"
        
        st.metric(
            label="🔄 Tasa Rotación",
            value=f"{rotacion:.1f}%",
            delta=delta_text
        )
    
    with col4:
        monto_horas = horas.get('total_monto_50', 0) + horas.get('total_monto_100', 0)
        st.metric(
            label="⏰ Horas Extras",
            value=f"{total_horas_extras:,} hrs",
            delta=f"${monto_horas:,.0f}"
        )
    
    # Segunda fila de KPIs
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ingresos = dotacion.get("ingresos_mes", 0)
        st.metric(
            label="📈 Nuevos Ingresos",
            value=f"{ingresos}",
            delta=f"{dotacion.get('tasa_ingreso_pct', 0):.1f}% de la dotación"
        )
    
    with col2:
        finiquitos = dotacion.get("finiquitos_mes", 0)
        st.metric(
            label="📉 Finiquitos",
            value=f"{finiquitos}",
            delta=f"{dotacion.get('tasa_finiquitos_pct', 0):.1f}% de la dotación"
        )
    
    with col3:
        st.metric(
            label="💵 Remuneración Promedio",
            value=f"${promedio_remuneracion:,.0f}",
            delta="Por trabajador"
        )
    
    with col4:
        incidencias = len(data.get("incidencias_fase_1_5", []))
        delta_text = "🟢 Sin incidencias" if incidencias == 0 else f"⚠️ {incidencias} casos"
        st.metric(
            label="🚨 Incidencias",
            value=f"{incidencias}",
            delta=delta_text
        )

def mostrar_distribucion_afiliaciones(data):
    """Muestra distribución de afiliaciones AFP y Salud"""
    st.markdown("#### 🏥 Sistema de Salud y Previsión")
    
    afiliaciones = data.get("resumen_afiliaciones", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        # AFP
        afp_data = afiliaciones.get("afp", {})
        if afp_data:
            df_afp = pd.DataFrame([
                {"AFP": k, "Trabajadores": v} for k, v in afp_data.items()
            ])
            
            fig_afp = px.pie(
                df_afp, 
                values='Trabajadores', 
                names='AFP',
                title='Distribución por AFP',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_afp.update_traces(textposition='inside', textinfo='percent+label')
            fig_afp.update_layout(height=300, showlegend=True, legend=dict(orientation="v", x=1, y=0.5))
            st.plotly_chart(fig_afp, use_container_width=True)
    
    with col2:
        # Salud
        salud_data = afiliaciones.get("salud", {})
        if salud_data:
            df_salud = pd.DataFrame([
                {"Sistema": k, "Trabajadores": v} for k, v in salud_data.items()
            ])
            
            fig_salud = px.pie(
                df_salud, 
                values='Trabajadores', 
                names='Sistema',
                title='Distribución Sistema de Salud',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_salud.update_traces(textposition='inside', textinfo='percent+label')
            fig_salud.update_layout(height=300, showlegend=True, legend=dict(orientation="v", x=1, y=0.5))
            st.plotly_chart(fig_salud, use_container_width=True)

def mostrar_conceptos_principales(data):
    """Muestra conceptos principales de remuneración"""
    st.markdown("#### 💸 Conceptos Principales")
    
    conceptos = data.get("conceptos_resumidos", [])
    if conceptos:
        df_conceptos = pd.DataFrame(conceptos)
        
        fig_conceptos = px.bar(
            df_conceptos.sort_values('total_monto', ascending=True),
            x='total_monto',
            y='concepto',
            orientation='h',
            title='Monto por Concepto',
            color='categoria',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_conceptos.update_layout(
            height=300,
            xaxis_tickformat='$,.0f'
        )
        st.plotly_chart(fig_conceptos, use_container_width=True)

def mostrar_horas_extras(data):
    """Muestra análisis de horas extras"""
    st.markdown("#### ⏰ Análisis Horas Extras")
    
    horas = data.get("horas_extras", {})
    if horas:
        datos_horas = [
            {"Tipo": "50%", "Horas": horas.get("total_horas_50", 0), "Monto": horas.get("total_monto_50", 0)},
            {"Tipo": "100%", "Horas": horas.get("total_horas_100", 0), "Monto": horas.get("total_monto_100", 0)}
        ]
        
        df_horas = pd.DataFrame(datos_horas)
        
        fig_horas = px.bar(
            df_horas,
            x='Tipo',
            y='Monto',
            title='Monto Horas Extras',
            color='Tipo',
            color_discrete_sequence=['#ff7f0e', '#d62728']
        )
        fig_horas.update_layout(height=300, yaxis_tickformat='$,.0f')
        st.plotly_chart(fig_horas, use_container_width=True)

def mostrar_centros_costo(data):
    """Muestra remuneración por centro de costo"""
    st.markdown("#### 🏭 Centros de Costo")
    
    remuneracion = data.get("remuneracion_promedio", {})
    centros = remuneracion.get("por_centro_costo", [])
    
    if centros:
        df_centros = pd.DataFrame(centros)
        
        fig_centros = px.bar(
            df_centros,
            x='centro_costo',
            y='promedio',
            title='Remuneración Promedio por Centro',
            color='promedio',
            color_continuous_scale='Viridis'
        )
        fig_centros.update_layout(
            height=300,
            yaxis_tickformat='$,.0f',
            showlegend=False
        )
        st.plotly_chart(fig_centros, use_container_width=True)

def mostrar_analisis_costos(data):
    """Muestra análisis detallado de costos"""
    st.markdown("---")
    st.subheader("💰 Análisis de Costos")
    
    costos = data.get("resumen_costos", {})
    if not costos:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Breakdown de haberes
        haberes_data = [
            {"Tipo": "Haberes Imponibles", "Monto": costos.get("total_haberes_imponibles", 0)},
            {"Tipo": "Haberes No Imponibles", "Monto": costos.get("total_haberes_no_imponibles", 0)}
        ]
        df_haberes = pd.DataFrame(haberes_data)
        
        fig_haberes = px.pie(
            df_haberes,
            values='Monto',
            names='Tipo',
            title='Distribución Haberes',
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        st.plotly_chart(fig_haberes, use_container_width=True)
    
    with col2:
        # Breakdown de descuentos
        descuentos_data = [
            {"Tipo": "Descuentos Legales", "Monto": costos.get("total_descuentos_legales", 0)},
            {"Tipo": "Otros Descuentos", "Monto": costos.get("total_otros_descuentos", 0)}
        ]
        df_descuentos = pd.DataFrame(descuentos_data)
        
        fig_descuentos = px.pie(
            df_descuentos,
            values='Monto',
            names='Tipo',
            title='Distribución Descuentos',
            color_discrete_sequence=['#d62728', '#2ca02c']
        )
        st.plotly_chart(fig_descuentos, use_container_width=True)
    
    # Tabla resumen
    st.markdown("**Resumen Financiero:**")
    resumen_financiero = pd.DataFrame([
        {"Concepto": "Total Haberes", "Monto": f"${costos.get('total_haberes', 0):,.0f}"},
        {"Concepto": "Total Descuentos", "Monto": f"${costos.get('total_descuentos_legales', 0) + costos.get('total_otros_descuentos', 0):,.0f}"},
        {"Concepto": "Aportes Patronales", "Monto": f"${costos.get('total_aportes_patronales', 0):,.0f}"},
        {"Concepto": "Costo Empresa", "Monto": f"${costos.get('costo_empresa', 0):,.0f}"}
    ])
    
    st.dataframe(resumen_financiero, use_container_width=True, hide_index=True)

# Funciones de compatibilidad (para no romper otros imports)
def mostrar_dashboard_general(data):
    """Wrapper para compatibilidad"""
    return mostrar(data)

def mostrar_info_general(data):
    """Función legacy - redirige al nuevo header"""
    mostrar_header_cliente(data)

def mostrar_kpis_principales(data):
    """Función legacy - redirige a los nuevos KPIs"""
    mostrar_kpis_principales_nuevos(data)

def mostrar_analisis_centros_costo(data):
    """Función legacy - redirige al nuevo análisis"""
    mostrar_centros_costo(data)

def mostrar_resumen_conceptos(data):
    """Función legacy - redirige al nuevo análisis"""
    mostrar_conceptos_principales(data)

def mostrar_analisis_incidencias(data):
    """Función legacy - análisis mejorado de incidencias"""
    incidencias = data.get("incidencias_fase_1_5", [])
    if incidencias:
        st.markdown("---")
        st.subheader("⚠️ Análisis de Incidencias")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Casos", len(incidencias))
        with col2:
            trabajadores_afectados = len(set(inc.get('rut', '') for inc in incidencias))
            st.metric("Trabajadores Afectados", trabajadores_afectados)
        with col3:
            conceptos_unicos = len(set(inc.get('concepto', '') for inc in incidencias))
            st.metric("Tipos de Incidencias", conceptos_unicos)
        
        # Tabla de incidencias
        df_incidencias = pd.DataFrame(incidencias)
        if not df_incidencias.empty:
            # Preparar datos para mostrar
            display_data = []
            for inc in incidencias:
                display_data.append({
                    "Trabajador": inc.get('nombre', 'N/A'),
                    "Concepto": inc.get('concepto', 'N/A'),
                    "Variación": inc.get('variacion', 'N/A'),
                    "Observación": inc.get('observacion', 'N/A')[:100] + "..." if len(inc.get('observacion', '')) > 100 else inc.get('observacion', 'N/A')
                })
            
            df_display = pd.DataFrame(display_data)
            st.markdown("**Detalle de Incidencias:**")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.markdown("---")
        st.subheader("✅ Estado de Incidencias")
        st.success("🎉 No se registraron incidencias en este período")

def mostrar_remuneracion_promedio(data):
    """Función legacy - redirige al nuevo análisis"""
    mostrar_centros_costo(data)
